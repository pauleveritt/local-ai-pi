# tests/test_session.py
from pathlib import Path

from harness.session import SessionResult

# Tests that don't need pi: just the dataclass shape and a mock path.


def test_session_result_fields():
    from harness.telemetry import RunTelemetry
    r = SessionResult(
        run_id="test-1",
        outcome="exited",
        returncode=0,
        telemetry=RunTelemetry(prompts=["test"], turns=5),
        changed_files=["app.py"],
        diff="+ # hello",
        tests_pass=True,
        wall_time_s=12.3,
        artifact_path="research/sessions/test-1.jsonl",
    )
    assert r.outcome == "exited"
    assert r.tests_pass is True
    assert r.run_id == "test-1"
    assert r.is_success is True  # exited + tests_pass + changed_files > 0


def test_session_result_timeout_not_success():
    from harness.telemetry import RunTelemetry
    r = SessionResult(
        run_id="t1",
        outcome="timeout",
        returncode=None,
        telemetry=RunTelemetry(),
        changed_files=[],
        diff="",
        tests_pass=False,
        wall_time_s=300.0,
        artifact_path="sessions/t1.jsonl",
    )
    assert r.is_success is False


def test_session_result_null_action_not_success():
    from harness.telemetry import RunTelemetry
    r = SessionResult(
        run_id="n1",
        outcome="exited",
        returncode=0,
        telemetry=RunTelemetry(turns=5),
        changed_files=[],
        diff="",
        tests_pass=True,
        wall_time_s=10.0,
        artifact_path="sessions/n1.jsonl",
    )
    assert r.is_success is False


def test_run_session_signature_exists():
    from harness.session import run_session
    import inspect
    sig = inspect.signature(run_session)
    params = list(sig.parameters.keys())
    assert "workspace" in params
    assert "phase_prompt" in params
    assert "model" in params
