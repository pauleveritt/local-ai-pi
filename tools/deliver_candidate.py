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

import harness.cell as cell_module
import harness.screen as screen
from harness.candidate import DeliveryRefused, deliver
from harness.liveness import ModelServerDown, check_model_server_alive
from harness.processes import ProcessResult, run_process
from harness.runner import _pi_command, pi_env
from harness.typed_contract import TypedHandoff, build_typed_handoff

# The 2026-08-11 re-plan's step 4 executor extension: `read`/`write`/`edit`
# mediated by the mutation engine, not raw Pi tools. Not in `harness/screen.py`
# alongside the other named extensions because it is orchestration, not a
# measurement probe -- it belongs beside the module it wires together.
IMPLEMENTER_EXTENSION = (
    Path(__file__).resolve().parents[1] / "extensions" / "orchestration" / "implementer.ts"
)

CONTRACT_ENV = "SATYRN_HANDOFF_CONTRACT"
BASELINES_ENV = "SATYRN_FILE_BASELINES"


def _render_contract_prompt(contract: dict[str, object]) -> str:
    """A minimal, faithful-enough echo of `handoff-contract.ts`'s `renderContract`.

    The system prompt `implementer.ts` injects (`promptFor`) states the
    bounded-writer rules; it never repeats `contract.task`. That has to
    reach the child through the ordinary user prompt, the same as any
    other `deliver_candidate` invocation.
    """
    writable = "\n".join(f"- `{f['path']}`" for f in contract["writableFiles"]) or "None"
    return (
        f"## Task\n\n{contract['task']}\n\n"
        f"## Writable Files\n\n{writable}\n\n"
        f"## Validation (run by the parent)\n\n{contract['validation']}\n"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--task", required=True)
    parser.add_argument(
        "--prompt-file", type=Path,
        help="required unless --contract-task supplies the prompt",
    )
    parser.add_argument(
        "--validation",
        help="shell-quoted command run inside the candidate worktree; "
        "required unless --contract-task supplies it (the task's preservation "
        "command -- the same one the child's contract names as what the "
        "parent will run). The task's oracle command, if any, is exposed "
        "only informationally in the receipt: running it here would require "
        "overlaying hidden target test files this tool has no access to, and "
        "reporting an unoverlaid run as an oracle result would be misleading.",
    )
    parser.add_argument(
        "--writable", action="append", default=None,
        help="glob a candidate may write; repeatable. Omit to allow anything "
        "(or, with --contract-task, to take the task's own manifest policy)",
    )
    # Required unless --cell supplies it. The old bare default named this
    # laptop's local model, so anyone else's first run failed inside Pi
    # rather than at the command line, where the fix is legible.
    parser.add_argument(
        "--model", help="a model name your Pi can resolve; required unless --cell supplies one"
    )
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
    parser.add_argument(
        "--agent-dir",
        type=Path,
        default=None,
        help="Pi agent directory; default is your own ~/.pi/agent, so your "
        "own models resolve. Pass this repo's pi-agent-dir/ to reproduce a "
        "measured run instead",
    )
    parser.add_argument("--tools", default="read,bash,edit,write")
    parser.add_argument(
        "--cell", type=Path, default=None,
        help="a workloads/svcs/cells/*.toml file; supplies and verifies "
        "model/tools/timeout against the live configuration before any call. "
        "Explicit --model/--tools/--timeout are refused alongside it, so "
        "there is exactly one source of truth for the arm.",
    )
    parser.add_argument(
        "--contract-task", default=None,
        help="a workloads/svcs/tasks/<id> task id; builds the typed "
        "HandoffContract and file baselines from its manifest and locating "
        "contract, and drives the implementer extension instead of a bare "
        "prompt file. See harness/typed_contract.py -- this is a smoke-test "
        "bridge, not general contract authoring.",
    )
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument("--validation-timeout", type=float, default=900.0)
    parser.add_argument("--receipt", type=Path, default=None)
    args = parser.parse_args(argv)

    if args.cell is not None and (args.model or args.tools != "read,bash,edit,write"):
        parser.error("--cell supplies --model/--tools; do not also pass them explicitly")
    if args.cell is None and not args.model:
        parser.error("--model is required unless --cell is given")
    if args.contract_task is None and not args.prompt_file:
        parser.error("--prompt-file is required unless --contract-task is given")
    if args.contract_task is not None and args.prompt_file:
        parser.error("--contract-task supplies the prompt; do not also pass --prompt-file")

    declared_cell = None
    if args.cell is not None:
        declared_cell = cell_module.load_cell(args.cell)
        pinned = declared_cell.pinned
        args.model = pinned["model"]
        args.tools = pinned["tools"]
        args.timeout = float(pinned["wall_clock_seconds"])

    handoff: TypedHandoff | None = None
    if args.contract_task is not None:
        # Read from `args.repo` itself, not the candidate worktree the call
        # below will create -- `deliver()`'s own `preflight` refuses a dirty
        # repository before `run_model` ever runs, so a clean `args.repo`'s
        # working tree and the freshly created worktree are the same
        # content. That equivalence is what lets the contract (and the
        # prompt hash `deliver()` records) be fixed before the worktree
        # exists, rather than tangled in a build-the-prompt-from-inside-the-
        # callback ordering problem.
        handoff = build_typed_handoff(args.contract_task, args.repo)
        prompt = _render_contract_prompt(handoff.contract)
        if args.validation is None:
            # The same command the contract itself tells the child the
            # parent will run (handoff.contract["validation"]), not
            # handoff.oracle_command: the oracle test files are hidden
            # target-revision content this tool has no clone to overlay,
            # so running the oracle command against the plain worktree
            # would exercise whatever pre-target version of that file
            # happens to already be there -- silently weaker than an
            # actual oracle check, and worse, indistinguishable from one
            # in the receipt.
            args.validation = str(handoff.contract["validation"])
        if args.writable is None:
            args.writable = list(handoff.writable_glob)
    else:
        prompt = args.prompt_file.read_text() if args.prompt_file else ""

    extensions = (IMPLEMENTER_EXTENSION,) if args.contract_task is not None else (screen.PROBE_EXTENSION,)

    if declared_cell is not None:
        # Before liveness and before the first call: a mismatch here means
        # this run is not the arm it claims to be, and every receipt it
        # produces would be mislabelled.
        declared_cell.verify(screen.resolve_cell(args.model, args.tools, extensions, args.timeout))
        print(f"cell {declared_cell.name}: live configuration verified", flush=True)

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
        env = pi_env(agent_dir=args.agent_dir)
        if handoff is not None:
            # The only seam that reaches the child: implementer.ts reads
            # these two, not the prompt, to build the mutation engine's
            # revision-checked baseline and the model's tool-call policy.
            env[CONTRACT_ENV] = json.dumps(handoff.contract)
            env[BASELINES_ENV] = json.dumps(handoff.baselines)
        return run_process(
            argv_pi,
            cwd=worktree,
            timeout=args.timeout,
            # Your agent directory, not this repo's. The harness pins its own
            # to keep measured runs hermetic; this is not a measured run, and
            # pinning it here means your --model does not resolve unless you
            # have replicated this laptop.
            env=env,
        )

    if args.validation is None:
        parser.error("--validation is required unless --contract-task supplies it")

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
    if handoff is not None:
        # Informational only -- not what gated `outcome` above. See
        # --validation's help text for why this tool does not run it
        # itself: no clone to overlay the hidden target test files onto.
        payload["task_oracle_command_unverified"] = list(handoff.oracle_command)
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    print(f"outcome:   {receipt.outcome}")
    if receipt.outcome == "candidate-created":
        print(f"ref:       {receipt.candidate_ref}")
        print(f"commit:    {receipt.candidate_commit}")
        print(f"changed:   {', '.join(receipt.changed_paths)}")
        if handoff is not None:
            print(
                f"note:      validated against the preservation suite only; "
                f"the task's own oracle command ({' '.join(handoff.oracle_command)}) "
                "was not run -- this tool has no overlay for its hidden target test files"
            )
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
