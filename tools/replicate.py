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
    parser.add_argument("--guards", action="store_true")
    parser.add_argument("--cell", type=Path, default=None)
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    log = args.out / "driver.log"

    # Task-major rather than replicate-major on purpose: if the run is cut
    # short, task-major leaves some tasks fully measured and others
    # untouched, which is analysable. Replicate-major would leave every
    # task with a partial, unequal sample.
    for task in args.task:
        for n in range(1, args.replicates + 1):
            target = args.out / f"{task}__r{n}"
            if (target / f"{task}.json").is_file():
                print(f"{task} r{n}: present, skipped", flush=True)
                continue
            command = [
                sys.executable, "-m", "tools.screen_workload",
                "--cohort", str(args.cohort), "--model", args.model,
                "--server", args.server, "--tools", args.tools,
                "--probe", "--timeout", args.timeout,
                "--task", task, "--out", str(target),
            ]
            if args.contract_draft_dir is not None:
                command += ["--contract-draft-dir", str(args.contract_draft_dir)]
            if args.guards:
                command += ["--guards"]
            if args.cell is not None:
                command += ["--cell", str(args.cell)]
            with log.open("a") as handle:
                code = subprocess.run(
                    command, stdout=handle, stderr=subprocess.STDOUT
                ).returncode
            record = target / f"{task}.json"
            outcome = "FAILED"
            if record.is_file():
                data = json.loads(record.read_text())
                outcome = f"{data['outcome']} gap={data['gap_closed']:.0%}"
            print(f"{task:24} r{n}  exit {code}  {outcome}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
