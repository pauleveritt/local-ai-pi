import os
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

import harness.runner as runner
from harness.grading import GradeResult
from harness.runner import RunResult, run_agentclinic_phase1


def _grade_result() -> GradeResult:
    return GradeResult(
        accepted=True,
        tests_executed=4,
        tests_expected=4,
        returncode=0,
        stdout="4 passed\n",
        stderr="",
        refused_config=(),
    )


def test_run_agentclinic_phase1_calls_pi_and_returns_its_result(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    events = []

    @contextmanager
    def fake_workspace(source=None):
        assert source is None
        events.append("workspace")
        yield workspace

    def fake_liveness():
        events.append("liveness")

    def fake_run(command, **kwargs):
        if command[:2] == ["git", "rev-parse"]:
            events.append("initial-commit")
            return SimpleNamespace(stdout="initial\n")
        if command[0] == "pi":
            events.append("pi")
            assert kwargs["cwd"] == workspace
            assert kwargs["check"] is False
            assert kwargs["capture_output"] is True
            return SimpleNamespace(
                stdout="model output", stderr="model diagnostics", returncode=0
            )
        if command[:2] == ["git", "add"]:
            events.append("stage")
            return SimpleNamespace()
        if command[:2] == ["git", "diff"]:
            events.append("diff")
            return SimpleNamespace(stdout="diff --cached")
        raise AssertionError(f"unexpected command: {command}")

    def fake_grade(actual_workspace, suite):
        events.append("grade")
        assert actual_workspace == workspace
        assert suite == runner.PHASE_1 / "acceptance" / "test_acceptance.py"
        return _grade_result()

    monkeypatch.setattr(runner, "check_model_server_alive", fake_liveness)
    monkeypatch.setattr(runner, "prepare_workspace", fake_workspace)
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner, "grade", fake_grade)

    result = run_agentclinic_phase1()

    assert events == [
        "liveness",
        "workspace",
        "initial-commit",
        "pi",
        "stage",
        "diff",
        "grade",
    ]
    assert result == RunResult(
        diff="diff --cached",
        grade=_grade_result(),
        pi_stdout="model output",
        pi_stderr="model diagnostics",
        pi_returncode=0,
    )


@pytest.mark.skipif(
    os.environ.get("SATYRN_LIVE") != "1",
    reason="set SATYRN_LIVE=1 to require an actual Pi/model run",
)
def test_run_agentclinic_phase1_produces_live_model_evidence():
    result = run_agentclinic_phase1()

    assert result.pi_returncode == 0
    assert result.pi_stdout.strip()
    assert result.grade.accepted is True
    assert result.grade.tests_executed == result.grade.tests_expected == 4
