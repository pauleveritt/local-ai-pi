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
ENVELOPE_TOOLS = "read,write"
ENVELOPE_EXTENSION = (
    Path(__file__).resolve().parents[1] / "extensions" / "envelope-cap.ts"
)


@dataclass(frozen=True)
class Attempt:
    """One model attempt against one task, with its grading."""

    task_id: str
    manifest_sha256: str
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


def screen_task(
    manifest: Manifest,
    clone: Path,
    env: CohortEnv,
    model: str,
    timeout: float = 900.0,
    suite_timeout: float = 300.0,
) -> Attempt:
    """Run one bounded attempt at `manifest`'s task and grade it.

    Grading mirrors qualification's two relevant conditions, both against
    the model's own workspace: the preservation suite runs in place, and
    the oracle runs on a *copy* with the hidden tests overlaid, so the
    workspace the model touched never contains an oracle file.
    """
    manifest_hash = sha256_file(manifest.task_dir / "manifest.toml")
    brief = manifest.brief_path.read_text()

    with materialize(clone, manifest.base_sha) as workspace:
        argv = _pi_command(model, brief, (ENVELOPE_EXTENSION,))
        argv = argv[:-1] + ["--tools", ENVELOPE_TOOLS] + argv[-1:]

        started = time.monotonic()
        child = run_process(argv, cwd=workspace, timeout=timeout, env=pi_env())
        model_seconds = time.monotonic() - started

        changed = _changed_paths(workspace)
        out_of_scope = _out_of_scope(changed, manifest.writable)

        if not changed:
            return Attempt(
                task_id=manifest.task_id,
                manifest_sha256=manifest_hash,
                accepted=False,
                outcome="no-changes",
                changed_paths=changed,
                out_of_scope=out_of_scope,
                model_seconds=model_seconds,
                model_timed_out=child.timed_out,
                preservation=None,
                oracle=None,
                argv=tuple(argv),
            )

        preservation_command = tuple(manifest.preservation_command) + tuple(
            argument
            for entry in manifest.deselects
            for argument in ("--deselect", entry)
        )

        # BOTH suites run on the same overlaid copy. Grading preservation
        # against the *base* test files while grading the oracle against
        # the *target* ones asks the candidate to satisfy two
        # contradictory specifications at once.
        #
        # flask-extensions is the case that exposed it: the task moves the
        # registry from app.config to app.extensions, and the base's own
        # tests assert the old location. A correct implementation makes
        # the oracle pass 19/19 and necessarily breaks those two base
        # tests -- which the target commit updates, which is precisely why
        # they are oracle files. Scored against base tests it looked like
        # repository damage; it was the task being done right.
        #
        # This mirrors qualification's target_preservation condition,
        # which runs on the target tree where the test files are already
        # the target's own.
        with disposable_dir("satyrn-grade-") as grading:
            shutil.copytree(workspace, grading, dirs_exist_ok=True)
            overlay_oracle(clone, manifest, grading)
            preservation = run_suite(grading, preservation_command, env, suite_timeout)
            oracle = run_suite(grading, manifest.oracle_command, env, suite_timeout)

    accepted = (
        preservation.reason_class == "pass"
        and oracle.reason_class == "pass"
        and not out_of_scope
    )
    if accepted:
        outcome = "accepted"
    elif oracle.reason_class == "pass":
        # The hidden tests pass but something else does not: a broken
        # preservation suite or a write outside the declared scope. Worth
        # its own name, because "the feature works but the repository is
        # damaged" is exactly the failure this whole line of work is about.
        outcome = "oracle-pass-but-rejected"
    elif preservation.reason_class != "pass":
        outcome = "preservation-broken"
    else:
        outcome = "oracle-failed"

    return Attempt(
        task_id=manifest.task_id,
        manifest_sha256=manifest_hash,
        accepted=accepted,
        outcome=outcome,
        changed_paths=changed,
        out_of_scope=out_of_scope,
        model_seconds=model_seconds,
        model_timed_out=child.timed_out,
        preservation=preservation,
        oracle=oracle,
        argv=tuple(argv),
    )


def write_attempt(path: Path, attempt: Attempt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(attempt.payload(), indent=2, sort_keys=True) + "\n")
