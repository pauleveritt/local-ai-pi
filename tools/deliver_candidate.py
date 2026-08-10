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

**Three things must be true before this works**, and the server check
below exists because the first one fails silently: Pi answers `pi
--version`; `--model` names an entry Pi can resolve; and the server
backing that entry is up. A model server that is down does not make Pi
exit nonzero -- it exits 0 having written nothing, which reaches the
lifecycle as a candidate that declined to act.
"""

import argparse
import json
import shlex
import sys
from collections.abc import Sequence
from pathlib import Path

import harness.screen as screen
from harness.candidate import DeliveryRefused, deliver
from harness.liveness import ModelServerDown, check_model_server_alive
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
    parser.add_argument(
        "--server",
        default="http://127.0.0.1:8001",
        help="model server to check for life before spending a call",
    )
    parser.add_argument(
        "--skip-server-check",
        action="store_true",
        help="for a hosted model, or a server this cannot see",
    )
    parser.add_argument("--tools", default="read,bash,edit,write")
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument("--validation-timeout", type=float, default=900.0)
    parser.add_argument("--receipt", type=Path, default=None)
    args = parser.parse_args(argv)

    prompt = args.prompt_file.read_text()
    extensions = (screen.PROBE_EXTENSION,)

    # Before the worktree, before the call. A dead server is the one
    # failure that does not announce itself: Pi exits 0 with an empty
    # transcript, the tree is unchanged, and without this the receipt says
    # `candidate changed nothing` -- a verdict on the model for what is a
    # verdict on the setup.
    if not args.skip_server_check:
        try:
            check_model_server_alive(args.server)
        except ModelServerDown as down:
            print(
                f"refused: {down}\n"
                "Start the model server, or pass --server / --skip-server-check "
                "if the model is hosted elsewhere.",
                file=sys.stderr,
            )
            return 2

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
        print(f"model exit: {receipt.child_exit}", end="")
        print(" (timed out)" if receipt.child_timed_out else "")
        if receipt.out_of_scope:
            print(f"outside:   {', '.join(receipt.out_of_scope)}")
        if receipt.validation_tail:
            print(f"\nvalidation tail:\n{receipt.validation_tail[-800:]}")
    # Three exit codes, because they mean three different things to a
    # caller: 0 the candidate exists, 1 the candidate was judged and
    # discarded, 3 nothing was judged because the setup is broken. Folding
    # the last into 1 is what made a dead server read as a bad model.
    if receipt.outcome == "candidate-created":
        return 0
    return 3 if receipt.outcome == "infrastructure-failure" else 1


if __name__ == "__main__":
    sys.exit(main())
