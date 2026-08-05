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
import re
import statistics
from collections import Counter
from pathlib import Path

from harness.checkpoint import load_checkpoint
from harness.telemetry import read_telemetry

EVIDENCE = Path.home() / "local-ai-pi-evidence"
ARMS = {
    "cycle 4 — as-shipped orchestrator": EVIDENCE
    / "satyrn-phase5-cycle4-user-story-sdd-n16.jsonl",
    "cycle 7 — tech stack": EVIDENCE / "satyrn-phase5-cycle7-stack-n6-t300.jsonl",
    "cycle 8 — + stop rule": EVIDENCE / "satyrn-phase5-cycle8-childfix-n6-t300.jsonl",
    "cycle 9 — hermetic child": EVIDENCE / "satyrn-phase5-cycle9-hermetic-n6-t300.jsonl",
    "cycle 10 — n=16 at 600 s": EVIDENCE
    / "satyrn-phase5-cycle10-hermetic-n16-t600.jsonl",
    # Cycle 11's control arms. Neither delegates -- they carry no subagent
    # extension -- so every child column reads 0 by construction, and that
    # zero is the point rather than a gap: it is what makes their cost
    # comparable with cycle 10's on the parent's own terms.
    "cycle 11 — bare (control floor)": EVIDENCE
    / "satyrn-phase5-cycle11-bare-hermetic-n16-t600.jsonl",
    "cycle 11 — facts-only (control)": EVIDENCE
    / "satyrn-phase5-cycle11-stackonly-v2-n16-t600.jsonl",
}


# The loop-breaker's refusal text, as the *child* sees it. Phase 5 cycle 9
# proved the guard loads in the child (a threshold-0 copy refused the child's
# first call) -- but `loop_broken` entries are appended in the child's own
# session, and the parent's stream never carries them: the parent reported
# zero while every child call was being blocked. So a child-side block is
# only visible as the refusal arriving back as a tool result.
BLOCK_MARKER = "Do not repeat it."


def child_calls(pi_stdout: str) -> tuple[list[str], str | None, int, int]:
    """(the child's tool calls, its stopReason, its message count, its blocks).

    Each update carries that delegation's transcript so far, so the last
    update *per `toolCallId`* is the fullest view of it. Every delegation in
    a run is read, and every result within each.
    """
    # One entry per `toolCallId`, holding that delegation's latest update.
    # Keeping only the stream-final event would drop every earlier
    # delegation: cycle 4 run 7 made six, and cycle 7 runs 4 and 5 made two
    # apiece. No published number moved when this was corrected -- the worst
    # repeats happened to live in the last stream -- but "the final update is
    # the fullest view" is true per call and false across calls, which is the
    # same silent-narrowing shape as the rejection-counted-as-success bug an
    # earlier audit found. Found by review, 2026-08-04.
    latest: dict[str, dict] = {}
    for line in pi_stdout.split("\n"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            event.get("type") == "tool_execution_update"
            and event.get("toolName") == "subagent"
        ):
            latest[event.get("toolCallId")] = event

    calls: list[str] = []
    blocks = 0
    steps = 0
    stop = None
    for event in latest.values():
        details = event.get("partialResult", {}).get("details") or {}
        for child in details.get("results") or []:
            messages = child.get("messages") or []
            steps += len(messages)
            stop = child.get("stopReason") or stop
            for message in messages:
                if message.get("role") == "toolResult":
                    if BLOCK_MARKER in json.dumps(message.get("content")):
                        blocks += 1
                    continue
                if message.get("role") != "assistant":
                    continue
                for block in message.get("content") or []:
                    if block.get("type") != "toolCall":
                        continue
                    name = block.get("name")
                    args = block.get("arguments") or {}
                    # `bash` is where the loop lives, and its `command` is the
                    # thing repeated. Other tools are keyed by their whole
                    # argument set so a repeated write is visible too.
                    if name == "bash":
                        calls.append(f"bash: {args.get('command', '')}")
                    else:
                        calls.append(f"{name}: {json.dumps(args, sort_keys=True)}")
    return calls, stop, steps, blocks


def parent_blocks(pi_stdout: str) -> int:
    """Loop-breaker refusals served to the *parent*, counted once each.

    Added phase 5 cycle 11, when the control arms carried the loop breaker
    with nothing to delegate to, so `child_calls` reported zero for every
    refusal that actually happened.

    **A raw substring count of the marker over-reports by roughly 5x**: Pi
    emits the same refusal inside `tool_execution_end`, `message_start`,
    `message_end`, `turn_end` and `agent_end`. One cycle-11 run reads 55 by
    substring and 11 here. `tool_execution_end` is the event that means "a
    call was refused" exactly once, so it is the one counted.
    """
    refusals = 0
    for line in pi_stdout.split("\n"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "tool_execution_end":
            continue
        if BLOCK_MARKER in json.dumps(event.get("result")):
            refusals += 1
    return refusals


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
            "child steps | child tool calls | blocked (child) | "
            "blocked (parent) | worst repeat | that command | stopReason |"
        )
        print("|---|---|---|---|---|---|---|---|---|---|---|---|")

        worsts = []
        blocked_total = 0
        parent_total = 0
        for i, record in enumerate(records, 1):
            telemetry = read_telemetry(record.pi_stdout)
            calls, stop, steps, blocks = child_calls(record.pi_stdout)
            refused = parent_blocks(record.pi_stdout)
            counts = Counter(calls)
            command, worst = counts.most_common(1)[0] if counts else ("—", 0)
            worsts.append(worst)
            blocked_total += blocks
            parent_total += refused
            shown = command if len(command) <= 44 else command[:41] + "..."
            print(
                f"| {i} | {record.accepted} | {record.grade.accepted} | "
                f"{record.pi_timed_out} | {telemetry.child_turns} | {steps} | "
                f"{len(calls)} | {blocks} | {refused} | "
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
        print(f"- child calls refused by the loop breaker: {blocked_total}")
        print(f"- parent calls refused by the loop breaker: {parent_total}")
        _cost_table(records)
        print()


def _cost_table(records) -> None:
    """The size, context, turn and throughput figures cycles 8-10 publish.

    Added after review found that roughly half of those cycles' tables had
    no recompute path, while the records claimed every figure recomputed
    from this script. Emitting them here makes the claim true rather than
    softening it.

    **Throughput is a crude wall-clock proxy** and is labelled as such
    wherever it is used. Output tokens ride on `turn_end`, which a killed
    run never emits, so a timed-out run contributes its full duration and
    none of its tokens. Both figures are printed: a run that times out
    depresses the all-runs number, so the comparison that matters excludes
    them.
    """
    stamps = re.compile(r'"timestamp":\s*(\d{13})')

    def wall_seconds(record) -> float:
        found = [int(value) for value in stamps.findall(record.pi_stdout)]
        return (max(found) - min(found)) / 1000 if len(found) >= 2 else 0.0

    megabytes = [len(r.pi_stdout) / 1e6 for r in records]
    contexts = [read_telemetry(r.pi_stdout).total_context_processed for r in records]
    turns = [read_telemetry(r.pi_stdout).total_turns for r in records]

    def throughput(pool) -> str:
        seconds = sum(wall_seconds(r) for r in pool)
        tokens = sum(read_telemetry(r.pi_stdout).total_output_tokens for r in pool)
        return f"{tokens / seconds:.2f}" if seconds else "n/a"

    finished = [r for r in records if not r.pi_timed_out]
    print(
        f"- run transcript MB: median {statistics.median(megabytes):.2f}, "
        f"max {max(megabytes):.2f}"
    )
    print(
        f"- total context_processed: median {statistics.median(contexts):,.0f}, "
        f"max {max(contexts):,.0f}"
    )
    print(f"- total turns: median {statistics.median(turns):.1f}, max {max(turns)}")
    print(
        f"- throughput tok/s: {throughput(records)} all runs, "
        f"{throughput(finished)} excluding timeouts"
    )


if __name__ == "__main__":
    main()
