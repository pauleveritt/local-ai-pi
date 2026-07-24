# tests/test_telemetry.py
from pathlib import Path

from harness.telemetry import RunTelemetry, read_run


def test_read_run_extracts_prompts(sample_session_path: Path):
    result = read_run(sample_session_path)
    assert isinstance(result, RunTelemetry)
    assert len(result.prompts) >= 1, "should extract at least one prompt"
    assert all(isinstance(p, str) for p in result.prompts)


def test_read_run_extracts_tool_calls(sample_session_path: Path):
    result = read_run(sample_session_path)
    assert isinstance(result.tool_calls, list)
    assert len(result.tool_calls) > 0, "should extract at least one tool call"
    for tc in result.tool_calls:
        assert isinstance(tc.name, str)
        assert tc.name != "unknown"


def test_read_run_extracts_tool_args(sample_session_path: Path):
    """Args are on tool_execution_start, correlated by toolCallId."""
    result = read_run(sample_session_path)
    # At least one tool call should have non-empty args
    calls_with_args = [tc for tc in result.tool_calls if tc.args]
    assert len(calls_with_args) > 0, "should capture args from tool_execution_start"
    # The first tool call in the fixture is 'mkdir -p templates tests'
    bash_call = next((tc for tc in result.tool_calls if tc.name == "bash"), None)
    if bash_call:
        assert "command" in bash_call.args, f"bash call should have args, got: {bash_call.args}"


def test_read_run_counts_turns(sample_session_path: Path):
    result = read_run(sample_session_path)
    assert result.turns > 0, "should count at least one turn"


def test_read_run_handles_empty_stream(tmp_path: Path):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    result = read_run(empty)
    assert result.prompts == []
    assert result.tool_calls == []
    assert result.turns == 0


def test_read_run_handles_malformed_lines(tmp_path: Path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"type": "turn_end"}\nnot json\n{"type": "turn_end"}\n')
    result = read_run(bad)
    assert result.turns == 2  # both valid lines counted, malformed skipped


def test_read_run_handles_nonexistent_file():
    result = read_run("/nonexistent/path.jsonl")
    assert result.prompts == []
    assert result.turns == 0


def test_read_run_is_error_is_bool(sample_session_path: Path):
    """The isError field in the fixture is a string 'True'/'False' — we convert to bool."""
    result = read_run(sample_session_path)
    for tc in result.tool_calls:
        assert isinstance(tc.is_error, bool)


def test_has_subagent_calls_detects_subagent(tmp_path: Path):
    """has_subagent_calls True when JSONL contains tool_execution_end with toolName=subagent."""
    from harness.telemetry import has_subagent_calls
    f = tmp_path / "session.jsonl"
    f.write_text('{"type": "tool_execution_start", "toolCallId": "a", "toolName": "bash", "args": {}}\n{"type": "tool_execution_end", "toolCallId": "a", "toolName": "bash", "isError": "False"}\n{"type": "tool_execution_start", "toolCallId": "b", "toolName": "subagent", "args": {"task": "test"}}\n{"type": "tool_execution_end", "toolCallId": "b", "toolName": "subagent", "isError": "False"}\n')
    assert has_subagent_calls(f) is True


def test_has_subagent_calls_no_subagent(tmp_path: Path):
    from harness.telemetry import has_subagent_calls
    f = tmp_path / "session.jsonl"
    f.write_text('{"type": "tool_execution_end", "toolName": "bash", "isError": "False"}\n')
    assert has_subagent_calls(f) is False


def test_has_subagent_calls_empty_file(tmp_path: Path):
    from harness.telemetry import has_subagent_calls
    f = tmp_path / "empty.jsonl"
    f.write_text("")
    assert has_subagent_calls(f) is False


def test_has_subagent_calls_nonexistent_file():
    from harness.telemetry import has_subagent_calls
    assert has_subagent_calls("/nonexistent/subagent.jsonl") is False


def test_compute_task_duration_s_from_fixture(sample_session_path: Path):
    """task_duration_s from the sample fixture should be a non-negative float.
    The fixture has only one timestamped event (session start), so duration is 0.0."""
    from harness.telemetry import compute_task_duration_s
    duration = compute_task_duration_s(sample_session_path)
    assert duration is not None
    assert duration >= 0.0
    assert isinstance(duration, float)


def test_compute_task_duration_s_empty_file(tmp_path: Path):
    from harness.telemetry import compute_task_duration_s
    f = tmp_path / "empty.jsonl"
    f.write_text("")
    assert compute_task_duration_s(f) is None


def test_compute_task_duration_s_nonexistent_file():
    from harness.telemetry import compute_task_duration_s
    assert compute_task_duration_s("/nonexistent/task.jsonl") is None


def test_compute_task_duration_s_single_event(tmp_path: Path):
    """A single timestamped event should yield duration 0."""
    from harness.telemetry import compute_task_duration_s
    f = tmp_path / "single.jsonl"
    f.write_text('{"type": "session", "timestamp": "2026-07-23T09:38:11.322Z"}\n')
    duration = compute_task_duration_s(f)
    assert duration == 0.0


def test_compute_task_duration_s_two_events(tmp_path: Path):
    """Two events 5 seconds apart should yield duration ~5.0."""
    from harness.telemetry import compute_task_duration_s
    f = tmp_path / "two.jsonl"
    f.write_text(
        '{"type": "session", "timestamp": "2026-07-23T09:38:10.000Z"}\n'
        '{"type": "agent_settled", "timestamp": "2026-07-23T09:38:15.000Z"}\n'
    )
    duration = compute_task_duration_s(f)
    assert duration == 5.0
