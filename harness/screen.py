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
import shutil
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
    disposable_dir,
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
    """One model attempt against one task, with its grading."""

    task_id: str
    manifest_sha256: str
    tools: str
    accepted: bool
    outcome: str
    changed_paths: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    model_seconds: float
    model_timed_out: bool
    preservation: SuiteResult | None
    oracle: SuiteResult | None
    argv: tuple[str, ...] = field(default=(), repr=False)

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
            "tools": self.tools,
            "accepted": self.accepted,
            "outcome": self.outcome,
            "changed_paths": list(self.changed_paths),
            "out_of_scope": list(self.out_of_scope),
            "model_seconds": round(self.model_seconds, 2),
            "model_timed_out": self.model_timed_out,
            "preservation": suite(self.preservation),
            "oracle": suite(self.oracle),
            "argv": list(self.argv),
        }


def capture_candidate(workspace: Path) -> str:
    """The model's whole contribution, as a patch.

    This is what makes grading replayable. Every defect found in this
    harness so far has been in the *acceptance rule*, not in the model's
    output -- and each one cost a fresh sweep of model calls to re-score
    work that was already correct. A saved patch turns re-scoring into a
    pure function over (patch, manifest, environment) that runs offline
    in seconds.

    The roadmap already asked for this at cycle 5, for admitting
    components by replay. It applies just as well to the screen that
    produces the candidates in the first place.
    """
    subprocess.run(
        ["git", "add", "-A"], cwd=workspace, capture_output=True, env=GIT_ENV
    )
    diff = subprocess.run(
        ["git", "diff", "--cached", "--binary"],
        cwd=workspace,
        capture_output=True,
        text=True,
        env=GIT_ENV,
    )
    return diff.stdout


def apply_candidate(workspace: Path, patch: str) -> None:
    """Reapply a saved candidate to a freshly materialized base."""
    if not patch.strip():
        return
    result = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "-"],
        cwd=workspace,
        input=patch,
        capture_output=True,
        text=True,
        env=GIT_ENV,
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

    Two independent questions, deliberately measured separately:

    - the **oracle** runs on a copy with the hidden tests overlaid, and
      says whether the feature works;
    - **preservation** runs on that same overlaid copy but ignores the
      oracle files, and says whether anything else survived.

    Overlaying for both is what lets a task legitimately change an
    existing test's expectations. Ignoring the oracle files in
    preservation is what stops the oracle being counted twice, which
    would make "feature incomplete" indistinguishable from "repository
    damaged".
    """
    manifest_hash = sha256_file(manifest.task_dir / "manifest.toml")

    with materialize(clone, manifest.base_sha) as workspace:
        apply_candidate(workspace, patch)
        changed = _changed_paths(workspace)
        out_of_scope = _out_of_scope(changed, manifest.writable)

        if not changed:
            return Attempt(
                task_id=manifest.task_id,
                manifest_sha256=manifest_hash,
                tools=tools,
                accepted=False,
                outcome="no-changes",
                changed_paths=changed,
                out_of_scope=out_of_scope,
                model_seconds=model_seconds,
                model_timed_out=model_timed_out,
                preservation=None,
                oracle=None,
                argv=argv,
            )

        preservation_command = tuple(manifest.preservation_command) + tuple(
            argument
            for entry in manifest.deselects
            for argument in ("--deselect", entry)
        )
        ignore_oracle = tuple(
            argument
            for oracle_file in manifest.oracle_files
            for argument in ("--ignore", oracle_file)
        )
        with disposable_dir("satyrn-grade-") as grading:
            shutil.copytree(workspace, grading, dirs_exist_ok=True)
            overlay_oracle(clone, manifest, grading)
            preservation = run_suite(
                grading, preservation_command + ignore_oracle, env, suite_timeout
            )
            oracle = run_suite(grading, manifest.oracle_command, env, suite_timeout)

    accepted = (
        preservation.reason_class == "pass"
        and oracle.reason_class == "pass"
        and not out_of_scope
    )
    if accepted:
        outcome = "accepted"
    elif out_of_scope and oracle.reason_class == "pass":
        outcome = "out-of-scope"
    elif oracle.reason_class != "pass" and preservation.reason_class != "pass":
        outcome = "broke-and-missed"
    elif preservation.reason_class != "pass":
        # The feature works but something else regressed -- "the tests
        # pass and the repository is damaged" is the failure this whole
        # line of work exists to catch, so it gets its own name.
        outcome = "preservation-broken"
    else:
        outcome = "oracle-failed"

    return Attempt(
        task_id=manifest.task_id,
        manifest_sha256=manifest_hash,
        tools=tools,
        accepted=accepted,
        outcome=outcome,
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

    The model call is the only expensive step and the only one that
    cannot be repeated cheaply, so it happens exactly once and its whole
    result is handed back as a patch. Everything downstream is
    `grade_candidate`, which can be re-run offline whenever the
    acceptance rule changes -- and it has changed three times.
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
