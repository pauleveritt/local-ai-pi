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


def compute_task_duration_s(stream_path: str | Path) -> float | None:
    """Return wall-clock duration from the artifact's first event timestamp
    to its terminal event (agent_settled or last event), in seconds.

    For clean exited runs this approximates wall_time_s. For hang/retry runs
    it measures the real work, excluding the dead attempt and the wait-to-kill.
    Returns None when the artifact is missing, empty, or has no timestamped events.
    """
    path = Path(stream_path)
    if not path.exists():
        return None

    from datetime import datetime, timezone

    first_ts: datetime | None = None
    last_ts: datetime | None = None

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

        ts_str = event.get("timestamp")
        if ts_str:
            try:
                # Parse ISO 8601 with optional fractional seconds and Z suffix.
                ts_str_clean = ts_str.replace("Z", "+00:00")
                ts = datetime.fromisoformat(ts_str_clean)
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
            except ValueError:
                continue

    if first_ts is None or last_ts is None:
        return None

    return (last_ts - first_ts).total_seconds()


# ---------------------------------------------------------------------------
# Drift detection — measures whether the implementer deviates from the packet.
# ---------------------------------------------------------------------------

# Files expected per phase (not exhaustive — the phase contract's
# allowed-files list). Any file in changed_files NOT in this set for
# the current phase is classified as overreach.
PHASE_EXPECTED_FILES: dict[int, frozenset[str]] = {
    1: frozenset({"app.py", "templates/base.html", "templates/home.html",
                   "tests/test_app.py"}),
    2: frozenset({"app.py", "models.py",
                   "templates/base.html", "templates/home.html",
                   "templates/complaints.html",
                   "tests/test_app.py"}),
    3: frozenset({"app.py", "models.py",
                   "templates/base.html", "templates/home.html",
                   "templates/complaints.html",
                   "tests/test_app.py"}),
}

# Files that are never overreach — scaffolding the model may legitimately
# create in any phase (uv.lock, __init__.py for import workarounds, etc.).
_NEVER_OVERREACH: frozenset[str] = frozenset({
    "uv.lock", "__init__.py", "tests/__init__.py",
})


def detect_overreach(changed_files: list[str], phase: int) -> bool:
    """True if any changed file is outside the phase's expected set."""
    expected = PHASE_EXPECTED_FILES.get(phase)
    if expected is None:
        return False
    for f in changed_files:
        if f in _NEVER_OVERREACH:
            continue
        if f not in expected:
            return True
    return False


def detect_validation_drift(artifact_path: str | Path) -> bool:
    """True if the implementer ran a pytest command different from the
    packet-specified `uv run pytest -q`.

    Parses the subagent tool result from the parent JSONL for the exact
    pytest invocation. If no subagent result is present or the command
    can't be determined, returns False (conservative — no evidence of drift).
    """
    path = Path(artifact_path)
    if not path.exists():
        return False
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line.strip())
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "tool_execution_end" and event.get("toolName") == "subagent":
            result = event.get("result", "")
            if not isinstance(result, str):
                continue
            # Look for any pytest invocation in the result text.
            import re
            pytest_cmds = re.findall(r'uv run pytest[^\n"]*', result)
            for cmd in pytest_cmds:
                cmd = cmd.strip()
                # The canonical command is exactly `uv run pytest -q`.
                # Any narrowing (e.g. `uv run pytest -q tests/test_app.py`)
                # or alteration is drift.
                if cmd != "uv run pytest -q":
                    return True
            return False
    return False


def has_subagent_calls(stream_path: str | Path) -> bool:
    """True if the session includes at least one subagent tool call.

    Only checks tool_execution_end events — sufficient because the caller
    only invokes this when outcome is "exited" (not "timeout"), so all
    tool calls that started completed normally.
    """
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


@dataclass
class SubagentStats:
    """Metrics extracted from parent JSONL about subagent delegations.

    Packet fidelity (verbatim literal matching) and implementer self-report
    vs harness verdict agreement are deferred to a future iteration.
    """
    invocations: int = 0
    packet_size_total: int = 0       # sum of task field sizes (bytes)


def subagent_stats_from(stream_path: str | Path) -> SubagentStats:
    """Extract subagent delegation metrics from a parent session JSONL."""
    path = Path(stream_path)
    stats = SubagentStats()
    if not path.exists():
        return stats
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line.strip())
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "tool_execution_start" and event.get("toolName") == "subagent":
            stats.invocations += 1
            args = event.get("args", {})
            if isinstance(args, dict):
                task = args.get("task", "")
                if isinstance(task, str):
                    stats.packet_size_total += len(task)
        elif event.get("type") == "tool_execution_end" and event.get("toolName") == "subagent":
            # tool_execution_end for subagent also counts as an invocation
            # (start+end both fire for each call; we count starts only above)
            pass
    return stats
