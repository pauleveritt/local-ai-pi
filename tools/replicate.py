"""Run one cell N times, so an arm effect can be told from noise.

Every comparison this phase has made is n=1 per cell, and last night
showed that is not enough. `local-pings` went accepted to no-changes
between two runs of the *same* arm whose only difference was an output
cap that bound in neither -- both ended `stop`. `registry-iter` went
`tests-vanished` to `damaged`. Three of eight tasks moved in both
directions while the aggregate stayed at 3/8.

So the contract arm's +1 is not a result, and neither is anything else
measured at a single attempt. This tool measures the noise floor: same
model, same arm, same task, repeated, so later comparisons have
something to be significant against.

Replicates are written as `<task>__rN` so each is a normal attempt
record -- audited, validated and regraded by the existing tools with no
special cases.
"""

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path


def _command(args: argparse.Namespace, task: str, out: Path) -> list[str]:
    """The screen_workload invocation for one task/replicate.

    Pure and offline-testable on purpose: this is the one place an
    unattended caller's cell selection actually reaches the subprocess,
    and a mistake here fails every replicate the same way rather than
    showing up in one run out of many.
    """
    command = [
        sys.executable, "-m", "tools.screen_workload",
        "--cohort", str(args.cohort), "--model", args.model,
        "--server", args.server, "--tools", args.tools,
        "--timeout", args.timeout,
        "--task", task, "--out", str(out),
    ]
    if args.probe:
        command.append("--probe")
    if args.contract_draft_dir is not None:
        command += ["--contract-draft-dir", str(args.contract_draft_dir)]
    if args.probe_dir is not None:
        command += ["--probe-dir", str(args.probe_dir)]
    if args.guards:
        command += ["--guards"]
    if args.cell is not None:
        command += ["--cell", str(args.cell)]
    return command


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--server", default="http://127.0.0.1:8001")
    parser.add_argument("--task", action="append", required=True)
    parser.add_argument("--replicates", type=int, default=6)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--tools", default="read,bash,edit,write")
    parser.add_argument("--timeout", default="1800")
    parser.add_argument("--contract-draft-dir", type=Path, default=None)
    parser.add_argument("--probe-dir", type=Path, default=None)
    parser.add_argument(
        "--probe",
        action="store_true",
        help=(
            "select probe-cap.ts budgets instead of envelope-cap.ts. Every "
            "cell measured before tonight used probe budgets, which is why "
            "this used to be unconditional -- but a cell pinning the exact "
            "envelope (read,write, 16/30) fails Cell.verify on every "
            "attempt if this is forced on regardless of --cell"
        ),
    )
    parser.add_argument("--guards", action="store_true")
    parser.add_argument("--cell", type=Path, default=None)
    parser.add_argument(
        "--max-consecutive-failures",
        type=int,
        default=3,
        help=(
            "abort the whole run after this many replicates in a row "
            "produce no attempt record. A model server dying partway "
            "through an unattended run must not turn the remaining hours "
            "into a row of silently recorded failures"
        ),
    )
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    log = args.out / "driver.log"

    consecutive_failures = 0
    # Task-major rather than replicate-major on purpose: if the run is cut
    # short, task-major leaves some tasks fully measured and others
    # untouched, which is analysable. Replicate-major would leave every
    # task with a partial, unequal sample.
    for task in args.task:
        for n in range(1, args.replicates + 1):
            target = args.out / f"{task}__r{n}"
            record = target / f"{task}.json"
            if record.is_file():
                print(f"{task} r{n}: present, skipped", flush=True)
                consecutive_failures = 0
                continue
            command = _command(args, task, target)
            with log.open("a") as handle:
                code = subprocess.run(
                    command, stdout=handle, stderr=subprocess.STDOUT
                ).returncode
            outcome = "FAILED"
            if record.is_file():
                data = json.loads(record.read_text())
                outcome = f"{data['outcome']} gap={data['gap_closed']:.0%}"
                consecutive_failures = 0
            else:
                consecutive_failures += 1
            print(f"{task:24} r{n}  exit {code}  {outcome}", flush=True)
            if consecutive_failures >= args.max_consecutive_failures:
                print(
                    f"\nABORTING: {consecutive_failures} consecutive "
                    f"replicates produced no attempt record. This is the "
                    f"infrastructure-failure shape (dead server, broken "
                    f"cell), not the model-declined-to-act shape -- "
                    f"continuing would spend the rest of the budget "
                    f"recording the same failure.",
                    flush=True,
                )
                return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
