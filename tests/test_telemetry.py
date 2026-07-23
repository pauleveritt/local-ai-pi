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
