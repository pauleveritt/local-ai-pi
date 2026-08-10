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
from harness.validity import assess as validity_of


def reference_for(task_id: str, root: Path = Path("workloads/svcs/reference-patches")):
    """The ceiling replay's saved patch for this task, when it exists.

    Read from disk rather than recomputed: the same bytes the ceiling
    replay graded, so the overlap number and the winnability check are
    talking about one artifact.
    """
    path = root / f"{task_id}.patch"
    return path.read_text() if path.is_file() else None


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

        # Validity is re-derived from the transcript rather than read
        # back from the record, because records written before validity
        # existed have no such field and a missing field would default
        # to "valid" -- which would silently launder the one attempt
        # this whole mechanism exists to catch. The transcript is the
        # evidence; the record is only a cache of a judgement about it.
        transcript = args.candidates / f"{task_id}.jsonl"
        validity, evidence = (
            validity_of(transcript.read_text())
            if transcript.is_file()
            else ("void:no-transcript", ("no transcript saved beside this candidate",))
        )

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
            reference_patch=reference_for(task_id),
            model_timeout_seconds=float(prior.get("model_timeout_seconds", 0.0)),
            validity=validity,
            validity_evidence=evidence,
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

    # The cached summary is derived, and a derived file that is not
    # rewritten outlives the truth it summarised. `cycle1/summary.json`
    # still called the stolen `autowire` attempt "accepted" long after
    # the record beside it said `void:left-workspace` -- a stale artifact
    # that reads as authoritative is worse than no artifact, because
    # nothing about it looks wrong.
    #
    # Arm metadata (model, server, tools, budgets) is preserved: it
    # describes the run and cannot be recomputed from grades.
    summary_path = args.candidates / "summary.json"
    if summary_path.is_file() and rows:
        summary = json.loads(summary_path.read_text())
        summary["outcomes"] = {r.task_id: r.outcome for r in rows}
        summary["accepted"] = accepted
        summary["attempted"] = len(rows)
        summary["void"] = sum(1 for r in rows if r.validity != "valid")
        summary["rule_version"] = screen.GRADING_RULE_VERSION
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        print(f"rewrote {summary_path}")

    print(
        f"\n{accepted}/{len(rows)} accepted; {changed} outcome(s) changed under the new rule"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
