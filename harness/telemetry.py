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
    timestamped_events = 0

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
                timestamped_events += 1
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
            except ValueError:
                continue

    # This pi version's --mode json stream carries a top-level "timestamp"
    # on only the initial "session" event — no other event type has one.
    # With a single timestamped event, first_ts == last_ts and the naive
    # subtraction silently yields 0.0 instead of the "uncomputable" None
    # this function's contract promises. Require at least two distinct
    # timestamped events before reporting a real duration.
    if first_ts is None or last_ts is None or timestamped_events < 2:
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


# ---------------------------------------------------------------------------
# Task 7 (grading-path reboot) -- standing behavioral instrumentation.
# Amendment 2 named these as the metrics its failure-mode-incidence doctrine
# depends on; the 2026-07-24 forensics report and write-vs-edit experiment
# established them empirically before they existed as standing metrics here.
# ---------------------------------------------------------------------------

@dataclass
class InheritedFileActivity:
    """How a run touched files it inherited from a phase seed, not created
    itself this run. write_attempts and edit_touches are disjoint -- a file
    touched by both counts only as a write attempt (see classification)."""
    write_attempts: list[str] = field(default_factory=list)
    edit_touches: list[str] = field(default_factory=list)

    @property
    def classification(self) -> str:
        """'replace' if any inherited file was targeted by a whole-file
        `write` attempt (lessons.md #12) -- blocked or failed attempts
        still count, since the attempt itself is the behavior this metric
        names, not whether it succeeded. 'extend' if inherited files were
        touched only via `edit`. 'untouched' if none were touched at all
        (always true for an unseeded phase-1 run).

        Rule 8 review, 2026-07-26 (Fable): the 2026-07-24 forensics
        report's 8/8 correlation (every run that incrementally edited an
        inherited file passed, every run that replaced one from scratch
        failed) was measured on the inherited TEST SUITE specifically
        (tests/test_app.py), not on any-inherited-file at the run level.
        Re-running this run-level classification against the same 8
        forensics artifacts gives 6/8, not 8/8 -- one old-oracle passer
        (3ff54760771a) whole-file-wrote app.py while incrementally
        editing the test suite. The per-file write_attempts/edit_touches
        above retain what's needed to recover the test-suite-scoped
        signal specifically; do not cite "8/8" for this run-level
        classification."""
        if self.write_attempts:
            return "replace"
        if self.edit_touches:
            return "extend"
        return "untouched"


def inherited_file_activity(
    stream_path: str | Path, inherited_files: frozenset[str],
) -> InheritedFileActivity:
    """Classify how a run touched files present at session start (the
    `inherited_files` set, e.g. from harness.workspace.seed_file_paths).

    A `write` tool call's args carry the target under "path" (verified
    against real captured artifacts, 2026-07-26); same for `edit`. Only
    tool_execution_start events are read -- sufficient to detect an
    *attempt*, which is the metric (a blocked or failed write is still
    evidence of the behavior the metric names)."""
    activity = InheritedFileActivity()
    if not inherited_files:
        return activity
    path = Path(stream_path)
    if not path.exists():
        return activity

    seen_write: set[str] = set()
    seen_edit: set[str] = set()
    for line in path.read_text().splitlines():
        try:
            event = json.loads(line.strip())
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict) or event.get("type") != "tool_execution_start":
            continue
        tool_name = event.get("toolName")
        if tool_name not in ("write", "edit"):
            continue
        args = event.get("args", {})
        if not isinstance(args, dict):
            continue
        file_path = args.get("path")
        if not isinstance(file_path, str) or file_path not in inherited_files:
            continue
        (seen_write if tool_name == "write" else seen_edit).add(file_path)

    activity.write_attempts = sorted(seen_write)
    activity.edit_touches = sorted(seen_edit - seen_write)
    return activity


def is_false_self_report(model_tests_pass: bool | None, tests_pass: bool) -> bool:
    """The model's own suite passed (it believes/reports success) while the
    harness's independent acceptance grade disagreed -- Amendment 2's
    motivating incident (both Phase 2 failures ended with the model
    asserting completion while pytest disagreed). None (not evaluated)
    is not a false report -- there is nothing to disagree with."""
    return bool(model_tests_pass) and not tests_pass
