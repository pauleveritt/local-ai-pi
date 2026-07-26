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
    """The fixture has only one timestamped event (session start) — as real
    pi 0.82.0 --mode json streams do, since no other event type carries a
    top-level timestamp. A single timestamped event cannot yield a real
    duration, so this must be None, not a fabricated 0.0 (which is
    indistinguishable from a genuine zero-duration run in any aggregate)."""
    from harness.telemetry import compute_task_duration_s
    duration = compute_task_duration_s(sample_session_path)
    assert duration is None


def test_compute_task_duration_s_empty_file(tmp_path: Path):
    from harness.telemetry import compute_task_duration_s
    f = tmp_path / "empty.jsonl"
    f.write_text("")
    assert compute_task_duration_s(f) is None


def test_compute_task_duration_s_nonexistent_file():
    from harness.telemetry import compute_task_duration_s
    assert compute_task_duration_s("/nonexistent/task.jsonl") is None


def test_compute_task_duration_s_single_event(tmp_path: Path):
    """A single timestamped event cannot yield a real duration — must be
    None, not a fabricated 0.0."""
    from harness.telemetry import compute_task_duration_s
    f = tmp_path / "single.jsonl"
    f.write_text('{"type": "session", "timestamp": "2026-07-23T09:38:11.322Z"}\n')
    duration = compute_task_duration_s(f)
    assert duration is None


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


# ---------------------------------------------------------------------------
# Task 7 -- standing behavioral instrumentation.
# ---------------------------------------------------------------------------

def test_inherited_file_activity_classifies_replace(tmp_path: Path):
    """A whole-file `write` attempt on an inherited file classifies as
    'replace' (real args shape verified against a captured artifact). See
    InheritedFileActivity.classification for the scope of the 2026-07-24
    forensics report's correlation -- it was measured on the inherited
    test suite specifically, not this run-level classification."""
    from harness.telemetry import inherited_file_activity
    f = tmp_path / "session.jsonl"
    f.write_text(
        '{"type": "tool_execution_start", "toolCallId": "a", "toolName": "write", '
        '"args": {"content": "...", "path": "tests/test_app.py"}}\n'
    )
    activity = inherited_file_activity(f, frozenset({"tests/test_app.py", "app.py"}))
    assert activity.write_attempts == ["tests/test_app.py"]
    assert activity.edit_touches == []
    assert activity.classification == "replace"


def test_inherited_file_activity_classifies_extend(tmp_path: Path):
    from harness.telemetry import inherited_file_activity
    f = tmp_path / "session.jsonl"
    f.write_text(
        '{"type": "tool_execution_start", "toolCallId": "a", "toolName": "edit", '
        '"args": {"edits": [{"oldText": "x", "newText": "y", "path": "app.py"}], "path": "app.py"}}\n'
    )
    activity = inherited_file_activity(f, frozenset({"app.py"}))
    assert activity.edit_touches == ["app.py"]
    assert activity.write_attempts == []
    assert activity.classification == "extend"


def test_inherited_file_activity_write_then_edit_still_classifies_replace(tmp_path: Path):
    """A file both written and edited counts only as a write attempt --
    the whole-file replace already happened; 'extend' would understate it."""
    from harness.telemetry import inherited_file_activity
    f = tmp_path / "session.jsonl"
    f.write_text(
        '{"type": "tool_execution_start", "toolCallId": "a", "toolName": "write", '
        '"args": {"content": "...", "path": "app.py"}}\n'
        '{"type": "tool_execution_start", "toolCallId": "b", "toolName": "edit", '
        '"args": {"edits": [], "path": "app.py"}}\n'
    )
    activity = inherited_file_activity(f, frozenset({"app.py"}))
    assert activity.write_attempts == ["app.py"]
    assert activity.edit_touches == []
    assert activity.classification == "replace"


def test_inherited_file_activity_untouched_when_no_inherited_file_touched(tmp_path: Path):
    from harness.telemetry import inherited_file_activity
    f = tmp_path / "session.jsonl"
    f.write_text(
        '{"type": "tool_execution_start", "toolCallId": "a", "toolName": "write", '
        '"args": {"content": "...", "path": "models.py"}}\n'
    )
    activity = inherited_file_activity(f, frozenset({"app.py"}))
    assert activity.classification == "untouched"


def test_inherited_file_activity_empty_inherited_set_is_untouched(tmp_path: Path):
    """An unseeded phase-1 run has no inherited files -- always 'untouched'."""
    from harness.telemetry import inherited_file_activity
    f = tmp_path / "session.jsonl"
    f.write_text(
        '{"type": "tool_execution_start", "toolCallId": "a", "toolName": "write", '
        '"args": {"content": "...", "path": "app.py"}}\n'
    )
    activity = inherited_file_activity(f, frozenset())
    assert activity.classification == "untouched"


def test_inherited_file_activity_nonexistent_file():
    from harness.telemetry import inherited_file_activity
    activity = inherited_file_activity("/nonexistent/session.jsonl", frozenset({"app.py"}))
    assert activity.classification == "untouched"


def test_is_false_self_report_true_when_model_passed_but_harness_disagreed():
    from harness.telemetry import is_false_self_report
    assert is_false_self_report(model_tests_pass=True, tests_pass=False) is True


def test_is_false_self_report_false_when_both_agree():
    from harness.telemetry import is_false_self_report
    assert is_false_self_report(model_tests_pass=True, tests_pass=True) is False
    assert is_false_self_report(model_tests_pass=False, tests_pass=False) is False


def test_is_false_self_report_false_when_not_evaluated():
    """model_tests_pass=None (not evaluated) is not a false report --
    there is nothing to disagree with."""
    from harness.telemetry import is_false_self_report
    assert is_false_self_report(model_tests_pass=None, tests_pass=False) is False
