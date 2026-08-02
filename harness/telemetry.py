"""Structured measurements derived from one Pi run's captured stdout.

**A turn is one `turn_end` event.** This definition is load-bearing and
must not drift: any change to it invalidates comparison against every
number this instrument has produced. A prior effort counted assistant
messages in one lesson and a session-level field in another, producing 45
turns versus 6 for comparable work, and poisoned the trend it was
measuring.

**When `complete` is `False`, every count here is a lower bound.** A run
killed mid-flight loses the tokens of its unfinished turn entirely, and
leaves tool calls whose outcome is unknown rather than successful.

This is a derived, recomputable view and never load-bearing storage -- but
only because checkpoints retain raw `pi_stdout`. Trimming stdout from
checkpoint records would make every telemetry number ever computed
unreproducible.
"""

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCall:
    name: str
    is_error: bool | None  # None = started but never finished


@dataclass(frozen=True)
class RunTelemetry:
    turns: int
    tool_calls: tuple[ToolCall, ...]
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    complete: bool  # the run finished normally; counts are lower bounds if False

    @property
    def context_processed(self) -> int:
        return self.input_tokens + self.cache_read_tokens + self.cache_write_tokens


def read_telemetry(pi_stdout: str) -> RunTelemetry:
    turns = 0
    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0
    cache_write_tokens = 0
    started: dict[str, str] = {}  # toolCallId -> toolName, in start order
    ended: dict[str, bool | None] = {}  # toolCallId -> isError
    agent_ended = False

    for line in pi_stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            # A process killed mid-write leaves a partial final line.
            # Tolerated, as harness/checkpoint.py already tolerates one.
            continue
        match event.get("type"):
            case "turn_end":
                turns += 1
                # Usage is per-turn, not cumulative -- verified across all
                # 16 runs of the real batch, where per-turn input is
                # non-monotonic. Reading only the final event would
                # undercount badly.
                usage = event.get("message", {}).get("usage", {})
                input_tokens += usage.get("input", 0)
                # Reasoning tokens are generated output. Folding them in
                # rather than giving them their own field means a future
                # reasoning-capable model's tokens cannot vanish
                # silently, and no assertion has to fire to prevent it.
                output_tokens += usage.get("output", 0) + usage.get("reasoning", 0)
                cache_read_tokens += usage.get("cacheRead", 0)
                cache_write_tokens += usage.get("cacheWrite", 0)
            case "tool_execution_start":
                started[event["toolCallId"]] = event["toolName"]
            case "tool_execution_end":
                ended[event["toolCallId"]] = event.get("isError")
            case "agent_end":
                agent_ended = True

    tool_calls = tuple(
        ToolCall(name=name, is_error=ended.get(call_id))
        for call_id, name in started.items()
    )

    return RunTelemetry(
        turns=turns,
        tool_calls=tool_calls,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
        # Checked against `ended`'s keys rather than its values so that a
        # matched call carrying no `isError` field still counts as
        # complete, while an unmatched one never does.
        complete=agent_ended and started.keys() <= ended.keys(),
    )
