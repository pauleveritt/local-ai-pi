"""
Telemetry reader for pi --mode json stdout streams.

Schema captured from pi 0.81.1 against omlx/gemma-4-12B-it-MLX-8bit
on 2026-07-23. Event types observed: agent_end, agent_settled, agent_start,
message_end, message_start, message_update, session, tool_execution_end,
tool_execution_start, tool_execution_update, turn_end, turn_start.

Key findings:
- No token usage data in --mode json mode. Token data IS available via
  --mode rpc and the get_session_stats command; that path is deferred
  to a future iteration.
- No evidence/appendEntry events appear in --mode json stdout.
- isError is a string ("True"/"False"), not a boolean.
- args live on tool_execution_start, result/isError on tool_execution_end —
  correlated by toolCallId.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ToolCall:
    name: str
    args: dict
    result: str | None = None
    is_error: bool = False


@dataclass
class RunTelemetry:
    prompts: list[str] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)
    turns: int = 0
    # Token usage not available from --mode json (verified in schema capture).
    # Token data IS available via --mode rpc get_session_stats; see the
    # course's future chapters or the Pi RPC docs for that path.


def read_run(stream_path: str | Path) -> RunTelemetry:
    """Parse a `pi --mode json` stdout JSONL file into structured telemetry.

    Reads line-by-line. Malformed lines (truncated writes, mid-write kills)
    are skipped rather than raised, so partial captures return whatever was
    successfully parsed.

    Correlates tool_execution_start (args) with tool_execution_end
    (result, isError) by toolCallId.
    """
    path = Path(stream_path)
    prompts: list[str] = []
    turns = 0

    # Collect args from tool_execution_start, then merge with results.
    pending_args: dict[str, dict] = {}  # toolCallId -> args
    tool_calls: list[ToolCall] = []

    if not path.exists():
        return RunTelemetry()

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if not isinstance(event, dict):
            continue

        etype = event.get("type", "")

        # --- user prompts from message_end ---
        if etype == "message_end":
            message = event.get("message", {})
            if isinstance(message, dict) and message.get("role") == "user":
                content = message.get("content", [])
                # content is a list of content blocks, extract text
                for block in content if isinstance(content, list) else [content]:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        if isinstance(text, str) and text.strip():
                            prompts.append(text.strip())

        # --- args from tool_execution_start ---
        elif etype == "tool_execution_start":
            call_id = event.get("toolCallId", "")
            if call_id:
                args = event.get("args", {})
                if isinstance(args, dict):
                    pending_args[call_id] = args

        # --- result from tool_execution_end ---
        elif etype == "tool_execution_end":
            call_id = event.get("toolCallId", "")
            args = pending_args.pop(call_id, {})

            is_error_str = event.get("isError", "False")
            is_error = is_error_str == "True" if isinstance(is_error_str, str) else bool(is_error_str)

            tool_calls.append(ToolCall(
                name=event.get("toolName", "unknown"),
                args=args if isinstance(args, dict) else {},
                result=event.get("result"),
                is_error=is_error,
            ))

        # --- turns from turn_end ---
        elif etype == "turn_end":
            turns += 1

    # Any pending starts without an end — include them with what we have.
    for call_id, args in pending_args.items():
        tool_calls.append(ToolCall(
            name="unknown",
            args=args,
            is_error=True,  # no end event = assume error
        ))

    return RunTelemetry(
        prompts=prompts,
        tool_calls=tool_calls,
        turns=turns,
    )


def has_subagent_calls(stream_path: str | Path) -> bool:
    """True if the session includes at least one subagent tool call."""
    path = Path(stream_path)
    if not path.exists():
        return False
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line.strip())
            if event.get("type") == "tool_execution_end" and event.get("toolName") == "subagent":
                return True
        except json.JSONDecodeError:
            continue
    return False
