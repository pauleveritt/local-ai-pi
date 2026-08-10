"""Author a draft contract from a staged packet, read-only.

The author's whole world is the packet: the base tree and the brief. It
gets `--tools read` and nothing else, which is the firewall's teeth --
the packet's location outside `.workloads/` is only layout hygiene, and
a model with a shell has already demonstrated in this phase what it does
when an answer key is reachable.

The transcript is saved and must be audited before any arm result built
on the draft is believed. A draft authored by a model that saw the
oracle is a contaminated contract, and the only place that evidence
exists is the transcript.

Drafts are written to a directory, never into `workloads/svcs/tasks/`,
so no manifest changes and no `manifest_sha256` moves. Correcting a
draft into a real `contract.md` is a separate, attended step.
"""

import argparse
import hashlib
import json
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from harness.processes import run_process
from harness.runner import _pi_command, pi_env
from harness.screen import PROBE_EXTENSION


def extract_contract(text: str) -> str:
    """The contract body, without the model's conversation around it.

    The author has no write tool, so it hands the contract back as prose:
    the first draft opened "I don't have a write tool available, so I'll
    present the complete contract content here" and fenced the document
    in a markdown block. Appended raw to a brief, that preamble becomes
    part of the executor's instructions and the arm partly measures the
    author's apology.

    The largest fenced block wins when one exists; otherwise the text is
    used as-is, because a model that simply wrote the contract plainly
    should not be punished for it.
    """
    lines = text.splitlines()
    fences = [i for i, line in enumerate(lines) if line.lstrip().startswith("```")]
    if len(fences) < 2:
        return text.strip()
    # Outermost span, not the first matched pair: a contract legitimately
    # contains ```python examples, and a toggle parser closes on the first
    # of them -- which is exactly how the first attempt at this returned
    # the preamble untouched.
    body = "\n".join(lines[fences[0] + 1 : fences[-1]])
    return body.strip() if len(body) > 0.5 * len(text) else text.strip()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--packets", type=Path, default=Path.home() / ".satyrn-authoring")
    parser.add_argument("--prompt", type=Path, default=Path("workloads/svcs/authoring-prompt.md"))
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument(
        "--min-chars",
        type=int,
        default=400,
        help="shortest draft accepted as a contract (stubs ran 29-80 chars)",
    )
    args = parser.parse_args(argv)

    packet = args.packets / args.task
    repo, brief = packet / "repo", packet / "brief.md"
    for path in (repo, brief, args.prompt):
        if not path.exists():
            raise SystemExit(f"missing {path}")

    instruction = args.prompt.read_text().strip()
    prompt = f"{instruction}\n\n---\n\n{brief.read_text().strip()}\n"

    # read only: no bash, no edit, no write. The author cannot go looking
    # and cannot modify the tree it is describing.
    argv_pi = _pi_command(args.model, prompt, (PROBE_EXTENSION,))
    argv_pi = argv_pi[:-1] + ["--tools", "read"] + argv_pi[-1:]

    started = time.monotonic()
    child = run_process(argv_pi, cwd=repo, timeout=args.timeout, env=pi_env())
    elapsed = time.monotonic() - started

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
                    c.get("text", "") for c in message.get("content", []) if c.get("type") == "text"
                )
                if body.strip():
                    text = body

    # The stop reason, and whether the author actually finished. Three of
    # the first eight drafts were 29-80 byte preambles -- "Now I'll write
    # the contract:" and nothing after it -- from runs that ended before
    # producing anything. All three were recorded as authored, appended
    # to briefs as if they were contracts, and confounded the arm they
    # were measured in.
    stop_reason = "unknown"
    for line in child.stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "message_end":
            message = event.get("message", {})
            if message.get("role") == "assistant":
                stop_reason = message.get("stopReason") or stop_reason

    contract = extract_contract(text)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / f"{args.task}.md").write_text(contract + "\n")
    (args.out / f"{args.task}.raw.md").write_text(text)
    (args.out / f"{args.task}.jsonl").write_text(child.stdout)
    (args.out / f"{args.task}.provenance.json").write_text(
        json.dumps(
            {
                "task_id": args.task,
                "model": args.model,
                "tools": "read",
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "authoring_prompt_sha256": hashlib.sha256(instruction.encode()).hexdigest(),
                "packet": str(packet),
                "elapsed_seconds": round(elapsed, 1),
                "timed_out": child.timed_out,
                "draft_chars": len(contract),
                "stop_reason": stop_reason,
                "raw_chars": len(text),
                "argv": list(argv_pi[:-1]),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    # A draft has to be long enough to be a contract and has to come from
    # a run that ended deliberately. Any nonempty string used to count as
    # success, which is how the stubs got through.
    problems = []
    if len(contract.strip()) < args.min_chars:
        problems.append(f"only {len(contract.strip())} chars (min {args.min_chars})")
    if child.timed_out:
        problems.append("timed out")
    if stop_reason not in ("stop", "toolUse"):
        problems.append(f"stopReason={stop_reason}")

    status = "ok" if not problems else "REJECTED: " + "; ".join(problems)
    print(f"{args.task:26} {len(contract):6} chars  {elapsed:6.1f}s  {status}")
    if problems:
        # Removed rather than left on disk: a rejected draft that stays
        # is a draft the next sweep will silently use.
        (args.out / f"{args.task}.md").unlink(missing_ok=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
