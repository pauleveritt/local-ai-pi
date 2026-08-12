"""Decide whether a task is well-formed enough to measure against.

Split out of `harness/workload.py` (2026-08-12). That module had grown
to 1,211 lines holding five separate jobs -- clone materialization,
cohort environments, pytest classification, manifest parsing, and this
-- and the seam mattered for a concrete reason: qualification has no
caller on the product path. `deliver_candidate`, the confirmatory batch
driver, `typed_contract` and `screen` all need the *manifest*; none of
them qualifies anything. Only `tools/qualify_workload.py` and the tests
call `qualify()`.

That mattered because the collaborator export derives its file list from
the product's import graph, and a single module meant qualification came
along whether or not it was wanted -- with the test file arguing for
itself. A review put it plainly: tests should not determine the product
boundary. Now they don't.

Nothing here changed in the move; the split is where the import graph
already was.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import harness.workload as workload
from harness.workload import CohortEnv, Manifest, SuiteResult, WorkloadError

# Functions are called through the module (`workload.materialize(...)`),
# not bound here by name. A `from ... import materialize` would capture
# the function object at import time, and the qualification tests patch
# `harness.workload.materialize` to simulate a flaky or sabotaged run --
# a bound name silently ignores that patch, which is how the first
# version of this split turned seven real tests green-for-the-wrong-
# reason before failing them.

CONDITIONS = (
    "base_preservation",
    "base_oracle",
    "target_preservation",
    "target_oracle",
)

# A qualified task means something only if the run that qualified it was
# at full strength. Callers may make qualification *harder* (more
# repeats, a tighter budget) but never easier.
MIN_REPEATS = 3
MAX_SECONDS_CEILING = 60.0


@dataclass(frozen=True)
class ConditionRun:
    """One condition, run `repeats` times, each in its own materialization."""

    name: str
    results: tuple[SuiteResult, ...]

    @property
    def first(self) -> SuiteResult:
        return self.results[0]

    @property
    def stable(self) -> bool:
        return all(r.fingerprint == self.results[0].fingerprint for r in self.results)

    @property
    def slowest(self) -> float:
        return max(r.wall_seconds for r in self.results)

    def payload(self) -> dict[str, object]:
        """The committed evidence for one condition.

        Every non-passing node is listed by name and phase, and every
        repeat contributes a fingerprint hash. Together those make
        "exactly the pre-registered failures, three times" auditable
        from the committed record without rerunning anything. Passing
        nodes are summarised by count rather than enumerated -- naming
        all 137 of them would bury the three that matter.
        """
        return {
            "reason_class": self.first.reason_class,
            "returncode": self.first.returncode,
            "tests_passed": self.first.tests_passed,
            "runs": len(self.results),
            "stable": self.stable,
            "wall_seconds": [round(r.wall_seconds, 3) for r in self.results],
            "node_count": len(self.first.outcomes),
            "nodes": sorted(self.first.outcomes),
            "failures": dict(sorted(self.first.failures.items())),
            "collection_errors": dict(sorted(self.first.collection_errors.items())),
            "fingerprint_sha256": [r.fingerprint_sha256 for r in self.results],
        }


def _run_condition(
    name: str,
    clone: Path,
    sha: str,
    command: Sequence[str],
    env: CohortEnv,
    manifest: Manifest,
    overlay: bool,
    repeats: int,
    timeout: float,
) -> ConditionRun:
    """Run one condition `repeats` times, each in a fresh materialization.

    Freshness is the point. Repeating inside a single workspace tells
    you whether a suite is idempotent within a directory -- a weaker and
    different property than whether two independent runs of the same
    commit agree, which is what a replay task needs.
    """
    results = []
    for _ in range(repeats):
        with workload.materialize(clone, sha) as workspace:
            if overlay:
                workload.overlay_oracle(clone, manifest, workspace)
            results.append(workload.run_suite(workspace, command, env, timeout))
    return ConditionRun(name=name, results=tuple(results))


def _rejection_mismatch(manifest: Manifest, observed: SuiteResult) -> str | None:
    """Compare the observed base rejection against the pre-registered fingerprint.

    A class alone is not evidence. `collection-error` is produced both
    by "the API this task adds does not exist yet" and by "the oracle
    file has a typo in an unrelated import", and only the first is a
    task. So the manifest names either the symbols expected to be
    missing or the nodes expected to fail, and both are checked.

    Searched against full output rather than the tail: a verbose
    collection error can push a symbol name past the last 4000
    characters and disqualify a task that was fine.
    """
    if observed.reason_class != manifest.base_rejection:
        return f"base was {observed.reason_class}, manifest declares {manifest.base_rejection}"

    if manifest.rejection_missing_symbols:
        # Searched in the *collection failures* only, not anywhere in
        # output. A symbol name appears in stdout merely by being on the
        # source line pytest echoes back, which proves nothing about
        # what caused the error.
        if not observed.collection_errors:
            return (
                "manifest declares missing symbols, but the run recorded no "
                "collection failure to attribute them to"
            )
        reasons = " ".join(observed.collection_errors.values())
        for symbol in manifest.rejection_missing_symbols:
            if symbol not in reasons:
                return (
                    f"expected the collection failure to name {symbol!r}, "
                    f"but it says: {reasons[:200]}"
                )

    if manifest.rejection_failing_nodes:
        # Exact equality, not a subset. A base that fails the three
        # declared nodes *and* four undeclared ones is not the task the
        # manifest describes, and admitting it would let unrelated
        # breakage ride along inside a qualified task.
        failed = set(observed.failures)
        expected = set(manifest.rejection_failing_nodes)
        if failed != expected:
            missing = sorted(expected - failed)
            extra = sorted(failed - expected)
            return (
                "declared failing nodes do not match observed; "
                f"missing={missing} unexpected={extra}"
            )
    return None


def qualify(
    manifest: Manifest,
    clone: Path,
    env: CohortEnv,
    repeats: int = 3,
    timeout: float = 300.0,
    max_seconds: float = 60.0,
) -> dict[str, object]:
    """Prove one task is a real replay task. No model calls.

    Four conditions, in the only order that makes sense: a base that
    cannot pass its own suite is not a starting point; an oracle that
    does not reject that base for the pre-registered reason is not
    measuring the task; a target that cannot pass both is not a
    solution. Each runs `repeats` times in fresh materializations, and
    all runs must agree at node level.

    `max_seconds` enforces the sub-minute validation the design
    requires. `timeout` is the far larger backstop that kills a hung
    child; a suite landing between the two is a qualification failure,
    not a crash.

    Refuses weakened parameters outright rather than returning a weaker
    verdict. `repeats=1` would make every task trivially "stable", and a
    raised `max_seconds` would retire the threshold the design commits
    to -- and both would still emit `status="qualified"`, which is the
    word the whole cohort is reported under.
    """
    if repeats < MIN_REPEATS:
        raise WorkloadError(
            f"repeats={repeats} cannot qualify anything: {MIN_REPEATS} is the minimum, "
            "and one run makes every task trivially stable"
        )
    if max_seconds > MAX_SECONDS_CEILING:
        raise WorkloadError(
            f"max_seconds={max_seconds} exceeds the {MAX_SECONDS_CEILING}s ceiling the "
            "design commits to; a tighter budget is allowed, a looser one is not"
        )
    report: dict[str, object] = {
        "task_id": manifest.task_id,
        "role": manifest.role,
        "base_sha": manifest.base_sha,
        "target_sha": manifest.target_sha,
        "manifest_sha256": workload.sha256_file(manifest.task_dir / "manifest.toml"),
        "env_id": manifest.env_id,
        "env_lock_sha256": env.lock_sha256,
        "env_python": env.python_version,
        "manifest_env_python": manifest.env_python,
        "env_platform": env.platform,
        "preservation_command": list(manifest.preservation_command),
        "oracle_command": list(manifest.oracle_command),
        "deselects": list(manifest.deselects),
        "recorded_at": datetime.now(UTC).isoformat(),
        "repeats": repeats,
        "max_seconds": max_seconds,
        "conditions": {},
    }

    def _disqualify(gate: str, detail: str) -> dict[str, object]:
        report["status"] = "disqualified"
        report["failed_gate"] = gate
        report["detail"] = detail
        return report

    if manifest.env_lock_sha256 != env.lock_sha256:
        return _disqualify(
            "environment",
            f"manifest declares lock {manifest.env_lock_sha256[:12]}, "
            f"cohort env is {env.lock_sha256[:12]}",
        )
    if manifest.env_python != env.python_version:
        # Always compared, never opt-in. Leaving this to a CLI flag meant
        # the freeze held only when someone remembered to ask for it.
        return _disqualify(
            "environment",
            f"manifest declares Python {manifest.env_python}, "
            f"cohort env is {env.python_version}",
        )

    conditions = report["conditions"]
    assert isinstance(conditions, dict)
    # Deselects are applied here, not merely recorded. load_manifest
    # validated them and the report lists them; a manifest whose list was
    # silently ignored would run the full suite and then disqualify for a
    # failure it had already declared out of scope.
    preservation = tuple(manifest.preservation_command) + tuple(
        argument for entry in manifest.deselects for argument in ("--deselect", entry)
    )
    report["effective_preservation_command"] = list(preservation)
    plan = (
        ("base_preservation", manifest.base_sha, preservation, False),
        ("base_oracle", manifest.base_sha, manifest.oracle_command, True),
        ("target_preservation", manifest.target_sha, preservation, False),
        ("target_oracle", manifest.target_sha, manifest.oracle_command, True),
    )

    runs: dict[str, ConditionRun] = {}
    for name, sha, command, overlay in plan:
        run = _run_condition(
            name, clone, sha, command, env, manifest, overlay, repeats, timeout
        )
        runs[name] = run
        conditions[name] = run.payload()

        if name == "base_oracle":
            # Every repeat, not just the first. A collection error records
            # no nodes, so its fingerprint is ("collection-error", 2, ())
            # and any two collection errors compare stable no matter what
            # caused them. Checking only run one would let a base reject
            # for the pre-registered symbol once and for something else
            # twice and still qualify -- in the exact condition this
            # instrument exists to establish.
            for index, attempt in enumerate(run.results):
                mismatch = _rejection_mismatch(manifest, attempt)
                if mismatch is not None:
                    report["base_oracle_tail"] = attempt.stdout_tail
                    return _disqualify("base_rejection", f"run {index + 1}: {mismatch}")
        elif run.first.reason_class != "pass":
            report[f"{name}_tail"] = run.first.stdout_tail
            return _disqualify(
                name, f"{name} is {run.first.reason_class}, expected pass"
            )

    unstable = [name for name, run in runs.items() if not run.stable]
    if unstable:
        return _disqualify("stability", f"runs disagreed at node level for: {unstable}")

    slow = {
        name: round(run.slowest, 3)
        for name, run in runs.items()
        if run.slowest > max_seconds
    }
    if slow:
        return _disqualify("runtime", f"conditions exceeded {max_seconds}s: {slow}")

    report["status"] = "qualified"
    return report
