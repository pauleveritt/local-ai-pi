"""Re-score saved candidates. No model calls.

The screen's model calls are the only expensive, unrepeatable step, so
they are paid once and their whole result is saved as a patch. When the
acceptance rule changes -- and it has changed three times, each time
because a real task exposed a flaw in it -- this replays every saved
candidate under the new rule in seconds instead of re-running the sweep.

That inversion is the point. Grading defects should cost a coffee, not
an afternoon.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import harness.screen as screen
import harness.workload as workload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", required=True, type=Path)
    parser.add_argument(
        "--candidates", required=True, type=Path, help="a screen output directory"
    )
    parser.add_argument("--cache", type=Path, default=Path(".workloads"))
    args = parser.parse_args(argv)

    cohort = workload.load_cohort(args.cohort)
    clone = workload.ensure_clone(cohort.upstream, args.cache)
    env = workload.ensure_cohort_env(cohort.env_dir, args.cache)

    changed = 0
    rows = []
    for patch_path in sorted(args.candidates.glob("*.patch")):
        task_id = patch_path.stem
        manifest = workload.load_manifest(cohort.task_dir(task_id))
        record = args.candidates / f"{task_id}.json"
        prior = json.loads(record.read_text()) if record.is_file() else {}
        previous = prior.get("outcome")

        # Model-side fields are carried through, never re-stamped. A
        # regrade re-scores a saved candidate; it does not re-run the
        # model, so defaulting these would erase real facts -- most
        # sharply `model_timed_out`, which is the difference between a
        # finished attempt and a truncated one.
        attempt = screen.grade_candidate(
            manifest,
            clone,
            env,
            patch_path.read_text(),
            model_seconds=float(prior.get("model_seconds", 0.0)),
            model_timed_out=bool(prior.get("model_timed_out", False)),
            tools=str(prior.get("tools", screen.ENVELOPE_TOOLS)),
            argv=tuple(prior.get("argv", ())),
            executor_env_lock_sha256=str(prior.get("executor_env_lock_sha256", "none")),
            budget_exhausted=str(prior.get("budget_exhausted", "none")),
            test_paths=cohort.test_paths,
            model_timeout_seconds=float(prior.get("model_timeout_seconds", 0.0)),
        )

        screen.write_attempt(record, attempt)
        rows.append(attempt)

        moved = previous is not None and previous != attempt.outcome
        changed += moved
        arrow = f"  ({previous} -> {attempt.outcome})" if moved else ""
        print(
            f"{task_id:26} {'ACCEPT' if attempt.accepted else 'reject':7} {attempt.outcome:20}{arrow}",
            flush=True,
        )

    accepted = sum(1 for r in rows if r.accepted)
    print(
        f"\n{accepted}/{len(rows)} accepted; {changed} outcome(s) changed under the new rule"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
