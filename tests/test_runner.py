import os
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

import harness.runner as runner
from harness.checkpoint import load_checkpoint
from harness.grading import GradeResult
from harness.processes import ProcessResult
from harness.runner import (
    RunConditions,
    RunResult,
    _pi_command,
    preflight_model,
    run_agentclinic_phase1,
)


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
        if command[:2] == ["git", "add"]:
            events.append("stage")
            return SimpleNamespace()
        if command[:2] == ["git", "diff"]:
            events.append("diff")
            return SimpleNamespace(stdout="diff --cached")
        raise AssertionError(f"unexpected command: {command}")

    def fake_process(command, **kwargs):
        events.append("pi")
        assert command[0] == "pi"
        assert kwargs["cwd"] == workspace
        return ProcessResult(0, "model output", "model diagnostics", timed_out=False)

    def fake_grade(actual_workspace, suite):
        events.append("grade")
        assert actual_workspace == workspace
        assert suite == runner.PHASE_1 / "acceptance" / "test_acceptance.py"
        return _grade_result()

    monkeypatch.setattr(runner, "check_model_server_alive", fake_liveness)
    monkeypatch.setattr(runner, "prepare_workspace", fake_workspace)
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner, "run_process", fake_process)
    monkeypatch.setattr(runner, "grade", fake_grade)
    monkeypatch.setattr(runner, "_conditions", lambda model, command, timeout: None)

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
    assert result.accepted is True


def test_run_result_rejects_a_timed_out_pi_even_when_the_grade_accepted():
    result = RunResult(
        diff="partial diff",
        grade=_grade_result(),
        pi_stdout="partial output",
        pi_stderr="",
        pi_returncode=None,
        pi_timed_out=True,
    )

    assert result.accepted is False


def test_pi_command_contains_trusted_session_and_isolation_flags():
    command = _pi_command("model-name", "task text")

    assert command[:8] == [
        "pi", "--print", "--mode", "json", "--no-session", "--model",
        "model-name", "--no-extensions",
    ]
    assert command[-1] == "task text"
    assert "--extension" in command


def test_preflight_requires_real_assistant_content(monkeypatch):
    events = []
    monkeypatch.setattr(runner, "check_model_server_alive", lambda: events.append("liveness"))
    monkeypatch.setattr(
        runner,
        "run_process",
        lambda command, **kwargs: (
            events.append("pi")
            or ProcessResult(
                0,
                '{"message": {"role": "assistant", "content": "SATYRN"}}\n',
                "",
                False,
            )
        ),
    )

    preflight_model("model-name")

    assert events == ["liveness", "pi"]


def test_preflight_accepts_pi_assistant_content_blocks(monkeypatch):
    monkeypatch.setattr(runner, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(
        runner,
        "run_process",
        lambda command, **kwargs: ProcessResult(
            0,
            '{"message": {"role": "assistant", "content": [{"type": "text", "text": "SATYRN"}]}}\n',
            "",
            False,
        ),
    )

    preflight_model("model-name")


def test_preflight_rejects_empty_assistant_content(monkeypatch):
    monkeypatch.setattr(runner, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(
        runner,
        "run_process",
        lambda command, **kwargs: ProcessResult(0, '{"message": {"content": ""}}\n', "", False),
    )

    with pytest.raises(RuntimeError):
        preflight_model("model-name")


def test_preflight_rejects_user_message_content_as_assistant_output(monkeypatch):
    monkeypatch.setattr(runner, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(
        runner,
        "run_process",
        lambda command, **kwargs: ProcessResult(
            0,
            '{"message": {"role": "user", "content": "SATYRN"}}\n',
            "",
            False,
        ),
    )

    with pytest.raises(RuntimeError):
        preflight_model("model-name")


def test_run_batch_runs_remaining_attempts_and_appends_each(tmp_path, monkeypatch):
    checkpoint = tmp_path / "runs.jsonl"
    conditions = RunConditions("model", ("pi",), "0.82.0", "sha", "rev", 600, 30)
    calls = []

    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    monkeypatch.setattr(runner, "preflight_model", lambda model: calls.append("preflight"))

    def fake_run(model):
        calls.append("run")
        return RunResult("diff", _grade_result(), "out", "", 0, conditions=conditions)

    monkeypatch.setattr(runner, "run_agentclinic_phase1", fake_run)

    records = runner.run_batch(checkpoint, target=2, model="model")

    assert len(records) == 2
    assert calls == ["preflight", "run", "run"]
    assert len(load_checkpoint(checkpoint)) == 2


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
