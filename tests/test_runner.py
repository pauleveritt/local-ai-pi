# tests/test_runner.py
from pathlib import Path

from harness.runner import BaselineReport, write_report
from harness.session import SessionResult
from harness.telemetry import RunTelemetry


def _make_result(run_id: str, tests_pass: bool, changed_files: list[str] | None = None,
                 outcome: str = "exited", task_duration_s: float | None = 10.0,
                 inherited_write_attempts: list[str] | None = None,
                 shared_file_classification: str = "untouched",
                 false_self_report: bool = False) -> SessionResult:
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
        inherited_write_attempts=inherited_write_attempts or [],
        shared_file_classification=shared_file_classification,
        false_self_report=false_self_report,
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


def test_write_report_never_fabricates_oracle_validation(tmp_path: Path):
    """F4 plan-mandated gate: a report must never claim the oracle is green
    -- write_report never runs tests/test_oracle.py itself, so it cannot
    honestly make that claim, regardless of whether this run's own tests
    passed or failed. Checked as "oracle" absent entirely, not just the
    literal lowercase "green" -- the tier section legitimately says GREEN
    for a different, honest claim (an artifact-backed success count), and
    a case-sensitive check on "green" alone would not catch a reintroduced
    "**Oracle status:** GREEN" (Rule 8 review, 2026-07-26 -- Fable)."""
    results = [_make_result("r1", tests_pass=False, outcome="timeout", task_duration_s=None)]
    report = BaselineReport(phase="Phase 1", n=1, model="test/model", results=results)
    out = tmp_path / "report.md"
    write_report(report, out)
    content = out.read_text()
    assert "oracle" not in content.lower()


def test_write_report_includes_pi_version(tmp_path: Path, monkeypatch):
    """Task 4: pi --version in the report header for provenance."""
    import harness.runner as mod

    monkeypatch.setattr(mod, "_pi_version", lambda: "pi 0.82.0")
    results = [_make_result("r1", True)]
    report = BaselineReport(phase="Phase 1", n=1, model="test/model", results=results)
    out = tmp_path / "report.md"
    write_report(report, out)
    content = out.read_text()
    assert "pi 0.82.0" in content


def test_write_report_omits_pi_version_line_when_unavailable(tmp_path: Path, monkeypatch):
    import harness.runner as mod

    monkeypatch.setattr(mod, "_pi_version", lambda: None)
    results = [_make_result("r1", True)]
    report = BaselineReport(phase="Phase 1", n=1, model="test/model", results=results)
    out = tmp_path / "report.md"
    write_report(report, out)
    content = out.read_text()
    assert "pi version" not in content


def test_write_report_tier_reflects_real_outcome_mix(tmp_path: Path):
    """Tier lines are derived from this run's actual facts, not fixed
    template text (F5): a run with zero success-eligible outcomes must not
    claim timing data it does not have, and the outcome mix must be the
    real per-outcome counts."""
    results = [
        _make_result("r1", tests_pass=False, outcome="timeout", task_duration_s=None),
        _make_result("r2", tests_pass=False, outcome="timeout", task_duration_s=None),
    ]
    report = BaselineReport(phase="Phase 1", n=2, model="test/model", results=results)
    out = tmp_path / "report.md"
    write_report(report, out)
    content = out.read_text()
    assert "no timing data to report" in content
    assert "2 timeout" in content


def test_write_report_tier_claims_timing_when_present(tmp_path: Path):
    results = [_make_result("r1", True), _make_result("r2", True)]
    report = BaselineReport(phase="Phase 1", n=2, model="test/model", results=results)
    out = tmp_path / "report.md"
    write_report(report, out)
    content = out.read_text()
    assert "Timing / turns:** real but noisy" in content
    assert "2 exited" in content


def test_baseline_report_behavioral_instrumentation_counts():
    """Task 7 (grading-path reboot): the three Amendment-2 standing
    metrics aggregate correctly across a batch."""
    results = [
        _make_result("r1", True, inherited_write_attempts=["tests/test_app.py"],
                     shared_file_classification="replace", false_self_report=True),
        _make_result("r2", True, shared_file_classification="extend"),
        _make_result("r3", False, shared_file_classification="untouched"),
    ]
    report = BaselineReport(phase="Phase 2", n=3, model="test/model", results=results)
    assert report.inherited_write_attempt_count == 1
    assert report.shared_file_replace_count == 1
    assert report.shared_file_extend_count == 1
    assert report.false_self_report_count == 1


def test_write_report_shows_all_three_behavioral_counts(tmp_path: Path):
    """Task 7's plan-mandated gate: a report from any batch shows all three
    counts (inherited-file write attempts, replace-vs-extend, false
    self-report), not just when they're non-zero."""
    results = [_make_result("r1", True), _make_result("r2", False)]
    report = BaselineReport(phase="Phase 1", n=2, model="test/model", results=results)
    out = tmp_path / "report.md"
    write_report(report, out)
    content = out.read_text()
    assert "Inherited-file write attempts:" in content
    assert "Shared-file replace-vs-extend:" in content
    assert "False self-report:" in content


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
    assert "checkpoint_path" in params


# ---------------------------------------------------------------------------
# Batch durability (Task 8 precondition): checkpoint per run, resume a
# killed batch instead of restarting it.
# ---------------------------------------------------------------------------

def test_checkpoint_round_trips_a_session_result(tmp_path: Path):
    from harness.runner import _append_checkpoint, _load_checkpoint

    result = _make_result("r1", True, inherited_write_attempts=["app.py"],
                          shared_file_classification="replace", false_self_report=True)
    checkpoint = tmp_path / "checkpoint.jsonl"
    _append_checkpoint(checkpoint, result)

    loaded = _load_checkpoint(checkpoint)

    assert len(loaded) == 1
    assert loaded[0].run_id == "r1"
    assert loaded[0].tests_pass is True
    assert loaded[0].inherited_write_attempts == ["app.py"]
    assert loaded[0].shared_file_classification == "replace"
    assert loaded[0].false_self_report is True
    assert loaded[0].telemetry.turns == 5
    assert loaded[0].telemetry.prompts == ["test"]


def test_checkpoint_appends_multiple_runs_in_order(tmp_path: Path):
    from harness.runner import _append_checkpoint, _load_checkpoint

    checkpoint = tmp_path / "checkpoint.jsonl"
    _append_checkpoint(checkpoint, _make_result("r1", True))
    _append_checkpoint(checkpoint, _make_result("r2", False))

    loaded = _load_checkpoint(checkpoint)

    assert [r.run_id for r in loaded] == ["r1", "r2"]


def test_load_checkpoint_missing_file_returns_empty(tmp_path: Path):
    from harness.runner import _load_checkpoint
    assert _load_checkpoint(tmp_path / "does-not-exist.jsonl") == []


def test_load_checkpoint_drops_truncated_final_line(tmp_path: Path, capsys):
    """Rule 8 review, 2026-07-26 (Fable): a process killed mid-_append_checkpoint
    write can leave a truncated final line -- the exact scenario this
    mechanism exists to survive. It must not crash the resume it exists to
    enable; that run just gets re-run."""
    from harness.runner import _append_checkpoint, _load_checkpoint

    checkpoint = tmp_path / "checkpoint.jsonl"
    _append_checkpoint(checkpoint, _make_result("r1", True))
    with open(checkpoint, "a") as f:
        f.write('{"run_id": "r2", "outcome": "exi')  # truncated, no newline

    loaded = _load_checkpoint(checkpoint)

    assert [r.run_id for r in loaded] == ["r1"]
    assert "truncated" in capsys.readouterr().out


def test_load_checkpoint_raises_on_malformed_non_trailing_line(tmp_path: Path):
    """A malformed line that is NOT the last one means the checkpoint file
    itself is corrupt, not just an in-flight write -- that should not be
    silently swallowed the way a trailing truncation is."""
    from harness.runner import _load_checkpoint

    checkpoint = tmp_path / "checkpoint.jsonl"
    checkpoint.write_text('{"run_id": "r1", "broken\n{"run_id": "r2"}\n')

    import pytest
    with pytest.raises(Exception):
        _load_checkpoint(checkpoint)


def test_run_baseline_rejects_checkpoint_with_more_results_than_n(tmp_path: Path):
    """A checkpoint with more results than n looks like it belongs to a
    different batch -- fail loudly rather than silently produce a report
    with a wrong n in every ratio."""
    from harness.runner import run_baseline, _append_checkpoint
    from harness.session import InvocationProfile

    checkpoint = tmp_path / "checkpoint.jsonl"
    _append_checkpoint(checkpoint, _make_result("r1", True))
    _append_checkpoint(checkpoint, _make_result("r2", True))

    import pytest
    with pytest.raises(ValueError, match="different batch"):
        run_baseline(
            phase_prompt="## Phase 1 — Home Page",
            app_source=tmp_path,
            model="test/model",
            profile=InvocationProfile.sp1(),
            n=1,
            checkpoint_path=checkpoint,
        )


def test_write_report_notes_no_seed_for_behavioral_instrumentation(tmp_path: Path):
    """An unseeded (phase-1) batch has no inherited files -- the report
    should say so rather than silently show replace=0 extend=0 as if the
    metric were meaningfully assessed."""
    results = [_make_result("r1", True)]
    report = BaselineReport(phase="Phase 1", n=1, model="test/model", results=results)
    assert report.start_state == "empty (no seed)"
    out = tmp_path / "report.md"
    write_report(report, out)
    content = out.read_text()
    assert "not applicable" in content


def test_run_baseline_resumes_from_checkpoint(tmp_path: Path):
    """A batch with 1/3 runs already checkpointed must not re-run them --
    only the 2 remaining runs execute, and the final report has all 3."""
    from unittest.mock import patch
    from harness.runner import run_baseline, _append_checkpoint
    from harness.session import InvocationProfile

    checkpoint = tmp_path / "checkpoint.jsonl"
    _append_checkpoint(checkpoint, _make_result("already-done", True))

    call_count = {"n": 0}

    def fake_run_session(*args, **kwargs):
        call_count["n"] += 1
        return _make_result(f"resumed-{call_count['n']}", True)

    fake_ws = tmp_path / "fake-ws"
    fake_ws.mkdir()

    with patch("harness.runner.prepare_workspace", return_value=(fake_ws, "deadbeef")), \
         patch("harness.runner.run_session", side_effect=fake_run_session), \
         patch("harness.runner.shutil.rmtree"):
        report = run_baseline(
            phase_prompt="## Phase 1 — Home Page",
            app_source=tmp_path,
            model="test/model",
            profile=InvocationProfile.sp1(),
            n=3,
            checkpoint_path=checkpoint,
        )

    assert call_count["n"] == 2, "only the 2 remaining runs should have executed"
    assert len(report.results) == 3
    assert report.results[0].run_id == "already-done"


def test_run_baseline_without_checkpoint_path_runs_all_n(tmp_path: Path):
    """No checkpoint_path -- unchanged behavior, every run executes."""
    from unittest.mock import patch
    from harness.runner import run_baseline
    from harness.session import InvocationProfile

    call_count = {"n": 0}

    def fake_run_session(*args, **kwargs):
        call_count["n"] += 1
        return _make_result(f"r{call_count['n']}", True)

    fake_ws = tmp_path / "fake-ws"
    fake_ws.mkdir()

    with patch("harness.runner.prepare_workspace", return_value=(fake_ws, "deadbeef")), \
         patch("harness.runner.run_session", side_effect=fake_run_session), \
         patch("harness.runner.shutil.rmtree"):
        report = run_baseline(
            phase_prompt="## Phase 1 — Home Page",
            app_source=tmp_path,
            model="test/model",
            profile=InvocationProfile.sp1(),
            n=2,
        )

    assert call_count["n"] == 2
    assert len(report.results) == 2
