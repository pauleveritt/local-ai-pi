"""
Telemetry reader for pi --mode json stdout streams.

Schema captured from pi 0.81.1 against omlx/gemma-4-12B-it-MLX-8bit
on 2026-07-23. Event types observed: agent_end, agent_settled, agent_start,
message_end, message_start, message_update, session, tool_execution_end,
tool_execution_start, tool_execution_update, turn_end, turn_start.

Key findings:
- No token usage data in any event type.
- No evidence/appendEntry events appear in --mode json stdout.
- isError is a string ("True"/"False"), not a boolean.
- args and result are JSON strings, not parsed objects.
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
    # No token usage available from pi --mode json (verified in schema capture).


def read_run(stream_path: str | Path) -> RunTelemetry:
    """Parse a `pi --mode json` stdout JSONL file into structured telemetry.

    Reads line-by-line. Malformed lines (truncated writes, mid-write kills)
    are skipped rather than raised, so partial captures return whatever was
    successfully parsed.
    """
    path = Path(stream_path)
    prompts: list[str] = []
    tool_calls: list[ToolCall] = []
    turns = 0

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

        # --- tool calls from tool_execution_end ---
        elif etype == "tool_execution_end":
            args_raw = {}
            args_str = event.get("args", "{}")
            if isinstance(args_str, str):
                try:
                    args_raw = json.loads(args_str.replace("'", '"'))
                except json.JSONDecodeError:
                    args_raw = {}
            elif isinstance(args_str, dict):
                args_raw = args_str

            is_error_str = event.get("isError", "False")
            is_error = is_error_str == "True" if isinstance(is_error_str, str) else bool(is_error_str)

            tool_calls.append(ToolCall(
                name=event.get("toolName", "unknown"),
                args=args_raw if isinstance(args_raw, dict) else {},
                result=event.get("result"),
                is_error=is_error,
            ))

        # --- turns from turn_end ---
        elif etype == "turn_end":
            turns += 1

    return RunTelemetry(
        prompts=prompts,
        tool_calls=tool_calls,
        turns=turns,
    )
