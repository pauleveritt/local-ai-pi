"""Does the contract disclose the fix? Measured, not inspected.

Two conditions per task, both repo-blind: a model that cannot read anything
is asked to write the changed code from the **brief alone**, then from the
**brief plus the contract**. What the second discloses and the first does
not is the contract's leakage.

The floor condition is what makes this fair, and it is not a formality.
`flask-extensions`'s brief names `app.extensions["svcs_registry"]`, so that
fix reconstructs from the brief with no contract at all. Scored on the
absolute, every contract for that task would be condemned for something no
author wrote.

Repo-blind is enforced with `--no-tools`, not asked for in the prompt. A
model that can read the repository is not reconstructing from the document,
it is looking up the answer, and this whole measurement would then be of
the model's navigation rather than the contract's disclosure.

**This is a gate, not a covariate.** With nine tasks there is nothing to
condition on, and a per-contract leakage score regressed against an arm
result at n=9 is a number that would get cited. It decides admission and is
recorded as audit trail; it never enters an analysis.

    uv run python -m tools.leak_probe --cohort workloads/svcs/cohort.toml \\
        --model omlx/Qwen3.6-27B-8bit --contract-dir workloads/svcs/contracts/locating \\
        --out workloads/svcs/contracts/locating/probe
"""

import argparse
import json
import re
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

import harness.workload as workload
from harness.liveness import check_model_server_alive
from harness.pi_invocation import pi_command, pi_env
from harness.processes import run_process
from harness.reconstruction import (
    Reconstruction,
    added_source_lines,
    contract_hash,
    signals,
)

INSTRUCTION = """\
You cannot read any files. You have no tools. Answer only from the document below.

Write the exact Python code that must be ADDED or CHANGED to make this work.
Write only the code, in one ``` fenced block. Do not explain.

If you cannot know what a line should be, write UNKNOWN on that line rather
than guessing at a plausible implementation. A wrong guess is worse than
UNKNOWN here.
"""


def _fenced(text: str) -> str:
    """The model's code, or its whole reply if it ignored the fence."""
    blocks = re.findall(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
    return "\n".join(blocks) if blocks else text


def _reply(model: str, prompt: str, timeout: float) -> str:
    argv = pi_command(model, prompt, ())
    # Before the prompt, like every other flag: `pi_command` appends the
    # prompt last on purpose.
    argv = argv[:-1] + ["--no-tools"] + argv[-1:]
    child = run_process(argv, cwd=Path.cwd(), timeout=timeout, env=pi_env())
    text = ""
    for line in child.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "message_end":
            message = event.get("message", {})
            if message.get("role") == "assistant":
                body = "".join(
                    part.get("text", "")
                    for part in message.get("content", [])
                    if part.get("type") == "text"
                )
                if body.strip():
                    text = body
    return text


def _majority(samples: list[set[str]], threshold: int) -> tuple[str, ...]:
    """Signals reconstructed in at least `threshold` of the samples.

    A single sample is a coin flip on a small model. Requiring agreement is
    what separates "the document discloses this" from "the model guessed it
    once", and guessing is exactly what a repo-blind model does when the
    document withholds the answer -- which is the case this must not call
    a leak.
    """
    counts: Counter[str] = Counter()
    for sample in samples:
        counts.update(sample)
    return tuple(sorted(name for name, seen in counts.items() if seen >= threshold))


def probe_task(
    task_id: str,
    brief: str,
    contract: str,
    reference: str,
    model: str,
    samples: int,
    threshold: int,
    timeout: float,
    writable_prefixes: tuple[str, ...] = (),
) -> Reconstruction:
    target = tuple(
        sorted(
            signals(
                added_source_lines(reference, only_prefixes=writable_prefixes or None)
            )
        )
    )
    conditions = {
        "brief": f"{INSTRUCTION}\n---\n\n{brief.strip()}\n",
        "contract": f"{INSTRUCTION}\n---\n\n{brief.strip()}\n\n---\n\n{contract.strip()}\n",
    }
    seen: dict[str, tuple[str, ...]] = {}
    for name, prompt in conditions.items():
        drawn = [
            signals(_fenced(_reply(model, prompt, timeout))) & set(target)
            for _ in range(samples)
        ]
        seen[name] = _majority(drawn, threshold)
        print(f"  {task_id:26} {name:9} {len(seen[name]):3}/{len(target)}", flush=True)
    return Reconstruction(
        task_id, target, seen["brief"], seen["contract"], contract_hash(contract)
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--server", default="http://127.0.0.1:8001")
    parser.add_argument("--contract-dir", required=True, type=Path)
    parser.add_argument(
        "--references", type=Path, default=Path("workloads/svcs/reference-patches")
    )
    parser.add_argument("--task", action="append", default=None)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--samples",
        type=int,
        default=5,
        help=(
            "3 produced a full leaked-to-clean flip on identical bytes for "
            "two tasks overnight -- too few for a gate decision"
        ),
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=3,
        help="samples that must agree before a signal counts as reconstructed",
    )
    parser.add_argument("--timeout", type=float, default=600.0)
    args = parser.parse_args(argv)

    check_model_server_alive(args.server)
    cohort = workload.load_cohort(args.cohort, require_accounting=True)
    task_ids = args.task or list(cohort.included)

    args.out.mkdir(parents=True, exist_ok=True)
    results = []
    for task_id in task_ids:
        contract = args.contract_dir / f"{task_id}.md"
        reference = args.references / f"{task_id}.patch"
        if not contract.is_file():
            print(f"  {task_id:26} no contract, skipped", flush=True)
            continue
        if not reference.is_file():
            # Not skippable in silence: with no reference there is nothing to
            # measure disclosure against, and a task counted as clean because
            # it was unmeasurable is the failure this tool exists to prevent.
            raise SystemExit(f"{task_id}: no reference patch at {reference}")
        manifest = workload.load_manifest(cohort.task_dir(task_id))
        result = probe_task(
            task_id,
            manifest.brief_path.read_text(),
            contract.read_text(),
            reference.read_text(),
            args.model,
            args.samples,
            args.threshold,
            args.timeout,
            manifest.writable_prefixes(),
        )
        results.append(result)
        (args.out / f"{task_id}.json").write_text(
            json.dumps(result.payload(), indent=2, sort_keys=True) + "\n"
        )

    print(f"\n{'task':26} {'margin':>7} {'floor':>7} {'ceiling':>8}  leaked")
    for result in results:
        flag = "LEAK" if result.leaked else "ok"
        print(
            f"{result.task_id:26} {result.margin:7.0%} {result.floor:7.0%} "
            f"{result.ceiling:8.0%}  {flag} {', '.join(result.leaked[:3])}"
        )

    leaking = [r.task_id for r in results if r.leaked]
    degenerate = [r.task_id for r in results if r.margin < 0.25]
    if degenerate:
        # Reported, never dropped. Removing a task because it is hard to
        # measure changes the cohort and invites the selection critique.
        print(
            f"\nlow margin (<25%), cannot host this comparison: {', '.join(degenerate)}"
        )
    print(f"{len(results) - len(leaking)}/{len(results)} contracts clear")
    return 1 if leaking else 0


if __name__ == "__main__":
    sys.exit(main())
