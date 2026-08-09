"""One bounded model attempt per replay task, graded by its hidden oracle.

This is the *screen*, and its job is narrow: find out whether the frozen
cohort spreads outcomes. It is explicitly not evidence. It runs one
attempt per task with no repetition, no interleaving, and no
pre-registered margins, so nothing it produces may be pooled into a
later confirmatory result.

What it does establish is the thing qualification cannot: qualification
proves each task is *well-formed* -- base green, oracle rejects the base
for a declared reason, target green. It says nothing about whether a
small local model lands anywhere other than all-pass or all-fail. A
cohort that is entirely floor or entirely ceiling is AgentClinic Phase 2
rebuilt with more ceremony, and one screening pass is the cheapest way
to find that out before anything is built on top.

**The arm is brief-only.** The executor sees the task's `brief.md` and
the base tree, nothing else -- no contract, because contracts are not
authored yet. In the roadmap's terms this is the concise-brief arm, not
the complete-contract arm, and results must be reported under that name.
"""

import fnmatch
import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from harness.processes import run_process
from harness.runner import _pi_command, pi_env
from harness.workload import (
    CohortEnv,
    Manifest,
    SuiteResult,
    WorkloadError,
    materialize,
    overlay_oracle,
    run_suite,
    sha256_file,
)
from harness.workspace import GIT_ENV

# The envelope, matching Phase 7-pre's `envelope-cap.ts` exactly: one
# call, read and write only, 16 turns, 30 tool calls. The budgets live in
# the extension; the tool allowlist has to be passed on the command line.
# Phase 7-pre's envelope. Kept as the default so the historical arm is
# reproducible by name, but it is now known not to transfer: Pi's built-in
# tools are read, bash, edit, write, and without `bash` there is no way to
# enumerate a repository. On AgentClinic Phase 2 -- three files, named in
# the spec -- that never mattered.
ENVELOPE_TOOLS = "read,write"
ENVELOPE_EXTENSION = (
    Path(__file__).resolve().parents[1] / "extensions" / "envelope-cap.ts"
)


@dataclass(frozen=True)
class Attempt:
    """One model attempt against one task, with its grading.

    `oracle_delta` is the experimental signal; `accepted` is the product
    gate. Keeping both is deliberate: acceptance is binary and throws
    away nearly everything, while a delta of zero against a base that
    already scores 15/18 is the difference between "nearly there" and
    "did nothing" -- a distinction this project got wrong once already.
    """

    task_id: str
    manifest_sha256: str
    rule_version: int
    tools: str
    accepted: bool
    outcome: str
    base_passed: int
    target_total: int
    oracle_delta: int
    gap_closed: float
    missing_nodes: tuple[str, ...]
    changed_paths: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    model_seconds: float
    model_timed_out: bool
    preservation: SuiteResult | None
    oracle: SuiteResult | None
    argv: tuple[str, ...] = field(default=(), repr=False)

    @property
    def summary(self) -> str:
        """The line a human reads, which must never hide the control."""
        candidate = self.oracle.tests_passed if self.oracle else 0
        return (
            f"candidate {candidate}/{self.target_total}; base {self.base_passed}; "
            f"delta {self.oracle_delta:+d}; gap closed {self.gap_closed:.0%}"
        )

    def payload(self) -> dict[str, object]:
        def suite(result: SuiteResult | None) -> dict[str, object] | None:
            if result is None:
                return None
            return {
                "reason_class": result.reason_class,
                "tests_passed": result.tests_passed,
                "node_count": len(result.outcomes),
                "failures": dict(sorted(result.failures.items())),
                "collection_errors": dict(sorted(result.collection_errors.items())),
                "wall_seconds": round(result.wall_seconds, 3),
            }

        return {
            "task_id": self.task_id,
            "manifest_sha256": self.manifest_sha256,
            "rule_version": self.rule_version,
            "tools": self.tools,
            "accepted": self.accepted,
            "outcome": self.outcome,
            "base_passed": self.base_passed,
            "target_total": self.target_total,
            "oracle_delta": self.oracle_delta,
            "gap_closed": self.gap_closed,
            "missing_nodes": list(self.missing_nodes),
            "changed_paths": list(self.changed_paths),
            "out_of_scope": list(self.out_of_scope),
            "model_seconds": round(self.model_seconds, 2),
            "model_timed_out": self.model_timed_out,
            "preservation": suite(self.preservation),
            "oracle": suite(self.oracle),
            "argv": list(self.argv),
        }


def base_commit(workspace: Path) -> str:
    """The root commit `materialize` wrote. Everything is diffed against this."""
    result = subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"],
        cwd=workspace,
        capture_output=True,
        text=True,
        env=GIT_ENV,
    )
    return result.stdout.strip().splitlines()[0]


def capture_candidate(workspace: Path) -> str:
    """The model's whole contribution, as a patch against the base commit.

    Diffed against the *root* commit rather than HEAD. The workspace is a
    real git repository and a model with a shell can commit in it; against
    HEAD, a committed change produces an empty diff and real work would be
    recorded as "no-changes" -- an inversion of exactly the kind this
    harness has already suffered three times.

    Saving the patch is what makes grading replayable. Every defect found
    here has been in the acceptance rule, never in the model's output, and
    each cost a fresh sweep to re-score work that was already correct.
    """
    subprocess.run(
        ["git", "add", "-A"], cwd=workspace, capture_output=True, env=GIT_ENV
    )
    diff = subprocess.run(
        ["git", "diff", "--cached", "--binary", base_commit(workspace)],
        cwd=workspace,
        capture_output=True,
        text=True,
        env=GIT_ENV,
    )
    return diff.stdout


def apply_candidate(
    workspace: Path, patch: str, include: tuple[str, ...] | None = None
) -> None:
    """Reapply a saved candidate, optionally restricted to certain paths.

    `include` is how grading stays honest about *what* it executes. Graded
    workspaces get production paths only, so a model-authored test,
    conftest, or pytest.ini is recorded as out-of-scope but never runs.
    Executing model-written test files would let a candidate grade itself.
    """
    if not patch.strip():
        return
    command = ["git", "apply", "--whitespace=nowarn"]
    for pattern in include or ():
        command.append(f"--include={pattern}")
    command.append("-")
    result = subprocess.run(
        command, cwd=workspace, input=patch, capture_output=True, text=True, env=GIT_ENV
    )
    if result.returncode != 0:
        raise WorkloadError(f"candidate patch did not apply: {result.stderr.strip()}")


def _changed_paths(workspace: Path) -> tuple[str, ...]:
    """Every path the model added, changed, or deleted.

    `git add -A` first: a model's new files start untracked, and a plain
    status would report them as a directory rather than by name.
    """
    subprocess.run(
        ["git", "add", "-A"], cwd=workspace, capture_output=True, env=GIT_ENV
    )
    listing = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=workspace,
        capture_output=True,
        text=True,
        env=GIT_ENV,
    )
    return tuple(sorted(p for p in listing.stdout.splitlines() if p.strip()))


def _out_of_scope(
    changed: tuple[str, ...], writable: tuple[str, ...]
) -> tuple[str, ...]:
    """Changed paths that no writable pattern admits.

    Scope is an explicit contract invariant, so a violation is recorded
    rather than merely noted -- but it is recorded, not blocked. The
    screen observes what the model did; it does not constrain it.
    """
    return tuple(
        path
        for path in changed
        if not any(fnmatch.fnmatch(path, pattern) for pattern in writable)
    )


GRADING_RULE_VERSION = 4
"""Bumped whenever the acceptance rule changes.

Every grade records it, because four rules have now produced different
verdicts on identical candidates and a record that does not say which one
scored it cannot be compared with anything.

  1  preservation on base tests, oracle on target tests -- contradictory
  2  both on the overlaid copy -- oracle counted twice
  3  overlay then --ignore -- a root conftest still loads as a plugin
  4  separate workspaces, production paths only, node inventory
"""


def _expected_nodes(manifest: Manifest) -> tuple[set[str], int, int]:
    """Base preservation inventory, base oracle score, target oracle total.

    Read from the task's own qualification record, which is frozen
    evidence: it is what the base and target actually did under this
    environment, so it is the only defensible reference for "did this
    candidate improve on doing nothing".
    """
    record = json.loads((manifest.task_dir / "qualification.json").read_text())
    conditions = record["conditions"]
    oracle_files = set(manifest.oracle_files)
    preservation_nodes = {
        node
        for node in conditions["base_preservation"]["nodes"]
        if node.split("::")[0] not in oracle_files
    }
    return (
        preservation_nodes,
        int(conditions["base_oracle"]["tests_passed"]),
        int(conditions["target_oracle"]["tests_passed"]),
    )


def grade_candidate(
    manifest: Manifest,
    clone: Path,
    env: CohortEnv,
    patch: str,
    model_seconds: float = 0.0,
    model_timed_out: bool = False,
    tools: str = ENVELOPE_TOOLS,
    argv: tuple[str, ...] = (),
    suite_timeout: float = 300.0,
) -> Attempt:
    """Score one saved candidate. Pure, offline, no model call.

    Two questions, two workspaces, and neither contaminates the other:

    - **preservation**: candidate production over the base tree, base
      tests, oracle test files ignored. No overlay at all -- overlaying
      target files here is what made a comment-only edit read as
      repository damage, because a root `conftest.py` in the oracle loads
      as a pytest plugin no matter what `--ignore` says.
    - **oracle**: candidate production plus the target's oracle files,
      which is the only place target-side tests belong.

    Both workspaces receive *production paths only*. A model-authored
    test, conftest or ini file is recorded as out-of-scope and never
    executed -- otherwise a candidate could grade itself.

    The headline number is the oracle delta over base, not acceptance. A
    candidate scoring 15/18 where the base already scores 15/18 has done
    nothing, and reporting it as a near-miss is how a floor gets mistaken
    for a middle.
    """
    manifest_hash = sha256_file(manifest.task_dir / "manifest.toml")
    expected_nodes, base_passed, target_total = _expected_nodes(manifest)

    preservation_command = tuple(manifest.preservation_command) + tuple(
        argument for entry in manifest.deselects for argument in ("--deselect", entry)
    )
    ignore_oracle = tuple(
        argument
        for oracle_file in manifest.oracle_files
        for argument in ("--ignore", oracle_file)
    )

    with materialize(clone, manifest.base_sha) as inspect:
        apply_candidate(inspect, patch)
        changed = _changed_paths(inspect)
        out_of_scope = _out_of_scope(changed, manifest.writable)

    with materialize(clone, manifest.base_sha) as preserving:
        apply_candidate(preserving, patch, include=manifest.writable)
        preservation = run_suite(
            preserving, preservation_command + ignore_oracle, env, suite_timeout
        )

    with materialize(clone, manifest.base_sha) as grading:
        apply_candidate(grading, patch, include=manifest.writable)
        overlay_oracle(clone, manifest, grading)
        oracle = run_suite(grading, manifest.oracle_command, env, suite_timeout)

    missing_nodes = tuple(sorted(expected_nodes - set(preservation.outcomes)))
    oracle_delta = oracle.tests_passed - base_passed
    gap = target_total - base_passed
    gap_closed = (oracle_delta / gap) if gap > 0 else 0.0

    preserved = preservation.reason_class == "pass" and not missing_nodes
    accepted = preserved and oracle.reason_class == "pass" and not out_of_scope

    if accepted:
        outcome = "accepted"
    elif missing_nodes:
        outcome = "tests-vanished"
    elif out_of_scope and oracle.reason_class == "pass":
        outcome = "out-of-scope"
    elif not preserved and oracle_delta > 0:
        outcome = "progress-but-damaged"
    elif not preserved:
        outcome = "damaged"
    elif oracle_delta > 0:
        outcome = "partial-progress"
    elif oracle_delta < 0:
        outcome = "regressed"
    elif not changed:
        outcome = "no-changes"
    else:
        outcome = "no-progress"

    return Attempt(
        task_id=manifest.task_id,
        manifest_sha256=manifest_hash,
        rule_version=GRADING_RULE_VERSION,
        tools=tools,
        accepted=accepted,
        outcome=outcome,
        base_passed=base_passed,
        target_total=target_total,
        oracle_delta=oracle_delta,
        gap_closed=round(gap_closed, 3),
        missing_nodes=missing_nodes,
        changed_paths=changed,
        out_of_scope=out_of_scope,
        model_seconds=model_seconds,
        model_timed_out=model_timed_out,
        preservation=preservation,
        oracle=oracle,
        argv=argv,
    )


def screen_task(
    manifest: Manifest,
    clone: Path,
    env: CohortEnv,
    model: str,
    tools: str = ENVELOPE_TOOLS,
    timeout: float = 900.0,
    suite_timeout: float = 300.0,
) -> tuple[Attempt, str]:
    """One bounded model attempt, returned with its candidate patch.

    The model call is the only expensive, unrepeatable step, so it happens
    once and its whole result is handed back as a patch. Everything
    downstream is `grade_candidate`, replayable offline whenever the
    acceptance rule changes -- which it has, four times.

    A candidate that changed nothing is graded like any other rather than
    short-circuited. It still has a base score, a delta of zero, and a
    preservation result, and reporting those makes "wrote nothing" and
    "wrote something useless" comparable instead of collapsing both into
    an early return.
    """
    brief = manifest.brief_path.read_text()

    with materialize(clone, manifest.base_sha) as workspace:
        argv = _pi_command(model, brief, (ENVELOPE_EXTENSION,))
        argv = argv[:-1] + ["--tools", tools] + argv[-1:]

        started = time.monotonic()
        child = run_process(argv, cwd=workspace, timeout=timeout, env=pi_env())
        model_seconds = time.monotonic() - started
        patch = capture_candidate(workspace)

    attempt = grade_candidate(
        manifest,
        clone,
        env,
        patch,
        model_seconds=model_seconds,
        model_timed_out=child.timed_out,
        tools=tools,
        argv=tuple(argv),
        suite_timeout=suite_timeout,
    )
    return attempt, patch


def write_attempt(path: Path, attempt: Attempt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(attempt.payload(), indent=2, sort_keys=True) + "\n")
