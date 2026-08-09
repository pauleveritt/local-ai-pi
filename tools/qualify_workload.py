"""Qualify a replay workload cohort.

Deterministic; makes no model calls. Every task is run through the four
qualification conditions and its result is written to
`tasks/<task_id>/qualification.json`, including when it fails -- a
disqualified task keeps its report so the failure is reviewable rather
than merely absent.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

import harness.workload as workload


def _report_line(task_id: str, report: dict[str, object]) -> str:
    status = str(report.get("status", "?"))
    if status == "qualified":
        conditions = report.get("conditions")
        base = (
            conditions.get("base_preservation")
            if isinstance(conditions, dict)
            else None
        )
        detail = (
            f"{base.get('tests_passed', '?')} preserved, slowest {max(base.get('wall_seconds', [0]))}s"
            if isinstance(base, dict)
            else ""
        )
        return f"{task_id:26} qualified      {detail}"
    gate = report.get("failed_gate", "")
    return f"{task_id:26} {status:14} {gate}: {report.get('detail', '')}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cohort", required=True, type=Path, help="path to cohort.toml"
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(".workloads"),
        help="derived state: clone cache and cohort venv",
    )
    parser.add_argument(
        "--task", action="append", default=None, help="qualify only these task ids"
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--max-seconds", type=float, default=60.0)
    parser.add_argument(
        "--require-python", default=None, help="exact interpreter version to demand"
    )
    parser.add_argument(
        "--frozen",
        action="store_true",
        help="require the cohort to account for every candidate as included or excluded",
    )
    args = parser.parse_args(argv)

    cohort = workload.load_cohort(args.cohort, require_accounting=args.frozen)
    task_ids = args.task or list(cohort.tasks)

    clone = workload.ensure_clone(cohort.upstream, args.cache)
    env = workload.ensure_cohort_env(
        cohort.env_dir, args.cache, require_python=args.require_python
    )

    failures = 0
    for task_id in task_ids:
        task_dir = cohort.task_dir(task_id)
        try:
            manifest = workload.load_manifest(task_dir)
            report = workload.qualify(
                manifest,
                clone,
                env,
                repeats=args.repeats,
                timeout=args.timeout,
                max_seconds=args.max_seconds,
            )
        except workload.WorkloadError as error:
            # A manifest that will not load is itself a qualification
            # failure, and is recorded the same way -- an unreadable task
            # must not be quieter than a failing one.
            report = {
                "task_id": task_id,
                "status": "disqualified",
                "failed_gate": "manifest",
                "detail": str(error),
            }
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "qualification.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        if report.get("status") != "qualified":
            failures += 1
        print(_report_line(task_id, report))

    print(f"\n{len(task_ids) - failures}/{len(task_ids)} qualified")
    if cohort.unaccounted and not args.frozen:
        print(f"not yet accounted for in cohort.toml: {list(cohort.unaccounted)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
