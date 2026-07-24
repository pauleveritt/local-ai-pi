# tests/test_runner.py
from pathlib import Path

from harness.runner import BaselineReport, write_report
from harness.session import SessionResult
from harness.telemetry import RunTelemetry


def _make_result(run_id: str, tests_pass: bool, changed_files: list[str] | None = None,
                 outcome: str = "exited", task_duration_s: float | None = 10.0) -> SessionResult:
    """Factory for mock session results."""
    if changed_files is None:
        changed_files = ["app.py"] if tests_pass else []
    return SessionResult(
        run_id=run_id,
        outcome=outcome,
        returncode=0,
        telemetry=RunTelemetry(prompts=["test"], turns=5),
        changed_files=changed_files,
        diff="mock diff",
        tests_pass=tests_pass,
        wall_time_s=10.0,
        artifact_path=f"research/sessions/{run_id}.jsonl",
        task_duration_s=task_duration_s,
        stderr_text="",
    )


def test_baseline_report_fields():
    results = [
        _make_result("r1", True),
        _make_result("r2", False),
    ]
    report = BaselineReport(
        phase="Phase 1 — Home Page",
        n=2,
        model="test/model",
        results=results,
    )
    assert report.phase == "Phase 1 — Home Page"
    assert report.model == "test/model"
    assert report.n == 2
    assert report.success_count == 1
    assert report.success_rate == 0.5


def test_baseline_report_success_rate():
    results = [
        _make_result("r1", True),    # success
        _make_result("r2", False),   # tests fail
        _make_result("r3", True),    # success
        _make_result("r4", True),    # success
        _make_result("r5", False, []),  # null-action
        _make_result("r6", True),    # success
    ]
    report = BaselineReport(
        phase="Phase 1",
        n=6,
        model="test/model",
        results=results,
    )
    assert report.success_rate == 4 / 6
    assert report.n == 6
    assert report.success_count == 4


def test_baseline_report_timeout_not_success():
    timeout = SessionResult(
        run_id="t1",
        outcome="timeout",
        returncode=None,
        telemetry=RunTelemetry(),
        changed_files=[],
        diff="",
        tests_pass=False,
        wall_time_s=300.0,
        artifact_path="sessions/t1.jsonl",
        stderr_text="timeout",
    )
    assert timeout.is_success is False


def test_baseline_report_null_action_not_success():
    null_action = _make_result("n1", True, [])
    assert null_action.is_success is False


def test_write_report_creates_file(tmp_path: Path):
    results = [
        _make_result("r1", True),
        _make_result("r2", False),
    ]
    report = BaselineReport(phase="Phase 1", n=2, model="test/model", results=results)
    out = tmp_path / "report.md"
    write_report(report, out)
    assert out.exists()
    content = out.read_text()
    assert "Phase 1" in content
    assert "test/model" in content
    assert "r1" in content
    assert "r2" in content


def test_baseline_report_mean_fields():
    results = [
        _make_result("r1", True),
        _make_result("r2", True),
    ]
    report = BaselineReport(phase="Phase 1", n=2, model="test/model", results=results)
    assert report.mean_wall_time_s == 10.0
    assert report.mean_turns == 5.0


def test_baseline_report_exited_with_hang_eligible():
    """exited-with-hang runs contribute to success count and mean task duration."""
    results = [
        _make_result("r1", True, outcome="exited", task_duration_s=12.0),
        _make_result("r2", True, outcome="exited-with-hang", task_duration_s=15.0),
        _make_result("r3", False, outcome="timeout", task_duration_s=None),
    ]
    report = BaselineReport(phase="Phase 1", n=3, model="test/model", results=results)
    assert report.success_count == 2
    assert report.success_rate == 2 / 3
    assert report.hang_count == 1
    # Mean task duration over success-eligible: (12.0 + 15.0) / 2 = 13.5
    assert report.mean_wall_time_s == 13.5


def test_baseline_report_hang_count_zero():
    """hang_count is 0 when no exited-with-hang runs."""
    results = [
        _make_result("r1", True),
        _make_result("r2", False, outcome="timeout", task_duration_s=None),
    ]
    report = BaselineReport(phase="Phase 1", n=2, model="test/model", results=results)
    assert report.hang_count == 0


def test_write_report_includes_hang_incidence(tmp_path: Path):
    """When hang_count > 0, the report includes a hang incidence line."""
    results = [
        _make_result("r1", True, outcome="exited"),
        _make_result("r2", True, outcome="exited-with-hang"),
        _make_result("r3", False, outcome="timeout", task_duration_s=None),
    ]
    report = BaselineReport(phase="Phase 1", n=3, model="test/model", results=results)
    out = tmp_path / "report.md"
    write_report(report, out)
    content = out.read_text()
    assert "Hang incidence" in content
    assert "1/3" in content


def test_write_report_no_hang_incidence_when_zero(tmp_path: Path):
    """When hang_count == 0, the report does NOT include a hang incidence line."""
    results = [
        _make_result("r1", True),
        _make_result("r2", True),
    ]
    report = BaselineReport(phase="Phase 1", n=2, model="test/model", results=results)
    out = tmp_path / "report.md"
    write_report(report, out)
    content = out.read_text()
    assert "Hang incidence" not in content


def test_run_baseline_signature():
    """Ensure run_baseline has the expected signature."""
    from harness.runner import run_baseline
    import inspect
    sig = inspect.signature(run_baseline)
    params = list(sig.parameters.keys())
    assert "phase_prompt" in params
    assert "app_source" in params
    assert "model" in params
    assert "profile" in params
    assert "n" in params
