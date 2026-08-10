"""Run one bounded attempt against a real repository, deliver a candidate.

The CLI path comes first on purpose: the roadmap defers a live Pi tool
entry point until this is stable, so there is exactly one way in while
the lifecycle is still settling.

What a contributor gets: their repository untouched, and either a
durable ref they can read, cherry-pick or delete, or nothing at all plus
a receipt saying why. There is no promotion, no merge, and no write to
the working tree in either case.

    uv run python -m tools.deliver_candidate \\
        --repo . --task add-iter --prompt-file brief.md \\
        --validation "pytest -q" --writable "src/**"
"""

import argparse
import json
import shlex
import sys
from collections.abc import Sequence
from pathlib import Path

import harness.screen as screen
from harness.candidate import DeliveryRefused, deliver
from harness.processes import ProcessResult, run_process
from harness.runner import _pi_command, pi_env


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--task", required=True)
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument(
        "--validation", required=True,
        help="shell-quoted command run inside the candidate worktree",
    )
    parser.add_argument(
        "--writable", action="append", default=None,
        help="glob a candidate may write; repeatable. Omit to allow anything",
    )
    parser.add_argument("--model", default="omlx/gemma-4-12B-it-MLX-8bit")
    parser.add_argument("--tools", default="read,bash,edit,write")
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument("--validation-timeout", type=float, default=900.0)
    parser.add_argument("--receipt", type=Path, default=None)
    args = parser.parse_args(argv)

    prompt = args.prompt_file.read_text()
    extensions = (screen.PROBE_EXTENSION,)

    def run_model(worktree: Path) -> ProcessResult:
        argv_pi = _pi_command(args.model, prompt, extensions)
        argv_pi = argv_pi[:-1] + ["--tools", args.tools] + argv_pi[-1:]
        return run_process(
            argv_pi, cwd=worktree, timeout=args.timeout, env=pi_env()
        )

    try:
        receipt = deliver(
            args.repo,
            args.task,
            prompt,
            run_model,
            tuple(shlex.split(args.validation)),
            writable=tuple(args.writable or ()),
            cell=screen.resolve_cell(args.model, args.tools, extensions, args.timeout),
            validation_timeout=args.validation_timeout,
        )
    except DeliveryRefused as refusal:
        # A refusal is not a failure of the model or the candidate; it is
        # the flow declining to start. Exit 2 so a caller can tell the two
        # apart without parsing prose.
        print(f"refused: {refusal}", file=sys.stderr)
        return 2

    payload = receipt.payload()
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    print(f"outcome:   {receipt.outcome}")
    if receipt.outcome == "candidate-created":
        print(f"ref:       {receipt.candidate_ref}")
        print(f"commit:    {receipt.candidate_commit}")
        print(f"changed:   {', '.join(receipt.changed_paths)}")
        print(f"\n  git show {receipt.candidate_ref}")
        print(f"  git cherry-pick {receipt.candidate_commit}")
        print(f"  git update-ref -d {receipt.candidate_ref}   # discard")
    else:
        print(f"reason:    {receipt.refusal}")
        if receipt.out_of_scope:
            print(f"outside:   {', '.join(receipt.out_of_scope)}")
        if receipt.validation_tail:
            print(f"\nvalidation tail:\n{receipt.validation_tail[-800:]}")
    return 0 if receipt.outcome == "candidate-created" else 1


if __name__ == "__main__":
    sys.exit(main())
