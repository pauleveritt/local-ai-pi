"""Grade each task's own target diff through the real grading pipeline.

Qualification proves the *full target tree* passes the oracle. It says
nothing about the writable-restricted diff, which is the only thing
grading ever executes. A task whose target commit needs a change outside
`writable` is unwinnable by construction, and no executor can ever be
accepted on it -- so this runs before any model call is spent.

It is also the control every grading-rule change must clear first. Rule 4
looked correct, passed twelve conformance archetypes, and rejected the
reference answer on four of eight tasks: Sybil node ids are positions, and
positions move when production lines move. "Does the rule still accept the
right answer" is a cheaper question than any of the ones that follow it,
and it had never been asked of rules 1 through 4.

Zero model calls.
"""

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import harness.screen as screen
import harness.workload as workload


def reference_patch(clone: Path, manifest: workload.Manifest) -> str:
    """The target's own diff, restricted to the writable paths.

    Restricted because the control has to be the same shape as what
    grading executes. The target's CHANGELOG, docs and test-adaptation
    edits are real, but no candidate is ever graded on them.
    """
    pathspecs = [
        pattern.removesuffix("**").rstrip("/") or "." for pattern in manifest.writable
    ]
    return subprocess.run(
        ["git", "diff", "--binary", manifest.base_sha, manifest.target_sha, "--"]
        + pathspecs,
        cwd=clone,
        capture_output=True,
        text=True,
        check=True,
        env=workload.GIT_ENV,
    ).stdout


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", required=True, type=Path)
    parser.add_argument("--cache", type=Path, default=Path(".workloads"))
    parser.add_argument("--task", action="append", default=None)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("workloads/svcs/reference-patches"),
        help="where reference patches and their grades are written",
    )
    args = parser.parse_args(argv)

    cohort = workload.load_cohort(args.cohort, require_accounting=True)
    clone = workload.ensure_clone(cohort.upstream, args.cache)
    env = workload.ensure_cohort_env(cohort.env_dir, args.cache)
    args.out.mkdir(parents=True, exist_ok=True)

    unwinnable = []
    task_ids = args.task or list(cohort.included)
    for task_id in task_ids:
        manifest = workload.load_manifest(cohort.task_dir(task_id))
        patch = reference_patch(clone, manifest)
        (args.out / f"{task_id}.patch").write_text(patch)

        attempt = screen.grade_candidate(
            manifest, clone, env, patch, tools="reference-replay"
        )
        screen.write_attempt(args.out / f"{task_id}.json", attempt)

        detail = ""
        if attempt.out_of_scope:
            detail += f" out-of-scope={list(attempt.out_of_scope)}"
        if attempt.missing_nodes:
            detail += f" vanished={list(attempt.missing_nodes)[:3]}"
        print(
            f"{'OK    ' if attempt.accepted else 'UNWIN '}{task_id:26} "
            f"{attempt.outcome:22} {attempt.summary}{detail}",
            flush=True,
        )
        if not attempt.accepted:
            unwinnable.append(task_id)

    print(f"\n{len(task_ids) - len(unwinnable)}/{len(task_ids)} winnable")
    if unwinnable:
        # Not a warning. Either the grading rule is wrong, or the task is,
        # and both have to be settled before a model call is spent here.
        print("NOT WINNABLE: " + ", ".join(unwinnable))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
