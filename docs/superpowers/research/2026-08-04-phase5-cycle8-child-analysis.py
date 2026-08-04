"""Recompute phase 5 cycle 8's tables: what the delegated child did.

Cycles 5-7 read the *parent's* behaviour. Cycle 8's subject is the child,
which the parent's stream carries in full: the shipped subagent extension
reports the child's whole message list under

    tool_execution_update -> partialResult.details.results[].messages

including the child's own `toolCall` entries. That is the only view we have
of the child -- it is a separate process whose stdout we never see, and the
`tool_execution_end` event never arrives for a run the harness kills, so the
*update* stream is what must be read.

The runaway signature this scores is a repeated identical command: cycle 7's
timed-out runs re-ran one `pytest` invocation 77 times out of 103 bash calls.

    PYTHONPATH=. uv run python \
        docs/superpowers/research/2026-08-04-phase5-cycle8-child-analysis.py

Checkpoints live outside version control in `~/local-ai-pi-evidence/`, so
this reports what it could not find rather than failing silently.
"""

import json
import statistics
from collections import Counter
from pathlib import Path

from harness.checkpoint import load_checkpoint
from harness.telemetry import read_telemetry

EVIDENCE = Path.home() / "local-ai-pi-evidence"
ARMS = {
    "cycle 7 — tech stack": EVIDENCE / "satyrn-phase5-cycle7-stack-n6-t300.jsonl",
    "cycle 8 — + stop rule": EVIDENCE / "satyrn-phase5-cycle8-childfix-n6-t300.jsonl",
}


def child_calls(pi_stdout: str) -> tuple[list[str], str | None, int]:
    """(the child's tool calls as text, its stopReason, its message count).

    Takes the *last* subagent update in the stream: each update carries the
    child's transcript so far, so the final one is the fullest view. Only
    the first result is read -- every arm here delegates one task at a time,
    and a multi-result call would need its own treatment rather than a
    silent flattening.
    """
    latest = None
    for line in pi_stdout.split("\n"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            event.get("type") == "tool_execution_update"
            and event.get("toolName") == "subagent"
        ):
            latest = event
    if latest is None:
        return [], None, 0

    results = (latest.get("partialResult", {}).get("details") or {}).get("results") or []
    if not results:
        return [], None, 0
    child = results[0]

    calls = []
    for message in child.get("messages") or []:
        if message.get("role") != "assistant":
            continue
        for block in message.get("content") or []:
            if block.get("type") != "toolCall":
                continue
            name = block.get("name")
            args = block.get("arguments") or {}
            # `bash` is where the loop lives, and its `command` is the thing
            # repeated. Other tools are keyed by their whole argument set so
            # a repeated write is visible too.
            if name == "bash":
                calls.append(f"bash: {args.get('command', '')}")
            else:
                calls.append(f"{name}: {json.dumps(args, sort_keys=True)}")
    return calls, child.get("stopReason"), len(child.get("messages") or [])


def main() -> None:
    for arm, path in ARMS.items():
        if not path.is_file():
            print(f"## {arm}\n\nMISSING: {path}\n")
            continue
        records = load_checkpoint(path)
        print(f"## {arm} — n={len(records)}\n")
        # `child turns` comes from the child's reported `usage`, which rides
        # on `tool_execution_end` -- an event a killed run never emits, so it
        # reads 0 for exactly the runs this cycle is about. `child steps`
        # counts the child's own messages and survives the kill. Both are
        # shown because disagreement between them means a run delegated more
        # than once and only the earlier call finished.
        print(
            "| # | run-accepted | grader-accepted | timed out | child turns | "
            "child steps | child tool calls | worst repeat | that command | stopReason |"
        )
        print("|---|---|---|---|---|---|---|---|---|---|")

        worsts = []
        for i, record in enumerate(records, 1):
            telemetry = read_telemetry(record.pi_stdout)
            calls, stop, steps = child_calls(record.pi_stdout)
            counts = Counter(calls)
            command, worst = counts.most_common(1)[0] if counts else ("—", 0)
            worsts.append(worst)
            shown = command if len(command) <= 44 else command[:41] + "..."
            print(
                f"| {i} | {record.accepted} | {record.grade.accepted} | "
                f"{record.pi_timed_out} | {telemetry.child_turns} | {steps} | "
                f"{len(calls)} | "
                f"{worst} | `{shown}` | {stop} |"
            )
        print()
        print(f"- run-accepted: {sum(1 for r in records if r.accepted)}/{len(records)}")
        print(
            f"- grader-accepted: "
            f"{sum(1 for r in records if r.grade.accepted)}/{len(records)}"
        )
        print(f"- timed out: {sum(1 for r in records if r.pi_timed_out)}/{len(records)}")
        if worsts:
            print(
                f"- worst repeated command, any run: {max(worsts)}; "
                f"median across runs {statistics.median(worsts):.0f}"
            )
            print(f"- runs repeating one command >=5 times: {sum(1 for w in worsts if w >= 5)}")
        print()


if __name__ == "__main__":
    main()
