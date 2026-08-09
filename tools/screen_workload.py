"""Screen a frozen replay cohort with one bounded model attempt per task.

NOT EVIDENCE. One attempt per task, no repetition, no interleaving, no
pre-registered margins. Its job is to find out whether the cohort spreads
outcomes at all -- a cohort that is entirely floor or entirely ceiling
cannot distinguish anything, however rigorously it was qualified.

The arm is brief-only: the executor sees the task brief and the base
tree. Contracts are not authored yet, so nothing here speaks to what a
complete contract would do.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import harness.screen as screen
import harness.workload as workload
from harness.liveness import check_model_server_alive
from harness.runner import DEFAULT_MODEL


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", required=True, type=Path)
    parser.add_argument("--cache", type=Path, default=Path(".workloads"))
    parser.add_argument("--task", action="append", default=None)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--server",
        default="http://127.0.0.1:8001",
        help=(
            "model server to liveness-check; must match the provider baseUrl "
            "the --model prefix resolves to in pi-agent-dir/models.json"
        ),
    )
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument(
        "--tools",
        default=screen.ENVELOPE_TOOLS,
        help="Pi tool allowlist for the arm (default: Phase 7-pre's read,write)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("workloads/svcs/screen"),
        help="where per-task attempt records are written",
    )
    args = parser.parse_args(argv)

    check_model_server_alive(args.server)
    cohort = workload.load_cohort(args.cohort, require_accounting=True)
    task_ids = args.task or list(cohort.included)

    clone = workload.ensure_clone(cohort.upstream, args.cache)
    env = workload.ensure_cohort_env(cohort.env_dir, args.cache)

    rows = []
    for task_id in task_ids:
        print(f"{task_id:26} running...", flush=True)
        manifest = workload.load_manifest(cohort.task_dir(task_id))
        attempt, patch = screen.screen_task(
            manifest, clone, env, args.model, tools=args.tools, timeout=args.timeout
        )
        # The patch is the expensive artifact: it is what a later
        # grading change can be replayed against without paying for the
        # model call again.
        screen.write_attempt(args.out / f"{task_id}.json", attempt)
        (args.out / f"{task_id}.patch").write_text(patch)
        rows.append(attempt)
        oracle = attempt.oracle
        detail = (
            f"oracle {oracle.tests_passed}/{len(oracle.outcomes)}"
            if oracle is not None
            else "no changes written"
        )
        flag = " OUT-OF-SCOPE" if attempt.out_of_scope else ""
        print(
            f"{task_id:26} {'ACCEPT' if attempt.accepted else 'reject':7} "
            f"{attempt.outcome:24} {detail:22} {attempt.model_seconds:6.1f}s{flag}"
        )

    accepted = sum(1 for r in rows if r.accepted)
    print(f"\n{accepted}/{len(rows)} accepted")
    (args.out / "summary.json").write_text(
        json.dumps(
            {
                "model": args.model,
                "server": args.server,
                "arm": f"brief-only:{args.tools}",
                "tools": args.tools,
                "accepted": accepted,
                "attempted": len(rows),
                "outcomes": {r.task_id: r.outcome for r in rows},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
