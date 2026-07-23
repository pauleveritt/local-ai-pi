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
