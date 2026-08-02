import json
import os
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

import harness.runner as runner
from harness.checkpoint import append_checkpoint, load_checkpoint
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


def test_run_result_rejects_a_nonzero_pi_exit_even_when_the_grade_accepted():
    result = RunResult(
        diff="partial diff",
        grade=_grade_result(),
        pi_stdout="partial output",
        pi_stderr="failure details",
        pi_returncode=1,
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
    conditions = RunConditions("model", ("pi",), "0.82.0", "sha", "rev", 600, 30, ("digest",))
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


def test_run_batch_resumes_after_existing_records(tmp_path, monkeypatch):
    checkpoint = tmp_path / "runs.jsonl"
    conditions = RunConditions("model", ("pi",), "0.82.0", "sha", "rev", 600, 30, ("digest",))
    first = RunResult("first", _grade_result(), "out", "", 0, conditions=conditions)
    append_checkpoint(checkpoint, first)
    calls = []

    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    monkeypatch.setattr(runner, "preflight_model", lambda model: calls.append("preflight"))
    monkeypatch.setattr(
        runner,
        "run_agentclinic_phase1",
        lambda model: (calls.append("run") or RunResult(
            "second", _grade_result(), "out", "", 0, conditions=conditions
        )),
    )

    records = runner.run_batch(checkpoint, target=2, model="model")

    assert [record.diff for record in records] == ["first", "second"]
    assert calls == ["preflight", "run"]


def test_run_batch_refuses_a_record_without_matching_conditions(tmp_path, monkeypatch):
    checkpoint = tmp_path / "runs.jsonl"
    append_checkpoint(checkpoint, RunResult("old", _grade_result(), "", "", 0))
    monkeypatch.setattr(
        runner,
        "_conditions",
        lambda *args: RunConditions(
            "model", ("pi",), "0.82.0", "sha", "rev", 600, 30, ("digest",)
        ),
    )
    monkeypatch.setattr(runner, "preflight_model", lambda model: pytest.fail("preflight called"))
    monkeypatch.setattr(runner, "run_agentclinic_phase1", lambda model: pytest.fail("run called"))

    with pytest.raises(ValueError, match="conditions"):
        runner.run_batch(checkpoint, target=2, model="model")


def test_run_batch_preflight_failure_leaves_checkpoint_unchanged(tmp_path, monkeypatch):
    checkpoint = tmp_path / "runs.jsonl"
    conditions = RunConditions("model", ("pi",), "0.82.0", "sha", "rev", 600, 30, ("digest",))

    def fail_preflight(model):
        raise RuntimeError("down")

    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    monkeypatch.setattr(runner, "preflight_model", fail_preflight)
    monkeypatch.setattr(runner, "run_agentclinic_phase1", lambda model: pytest.fail("run called"))

    with pytest.raises(RuntimeError, match="down"):
        runner.run_batch(checkpoint, target=1, model="model")

    assert not checkpoint.exists()


def test_run_batch_does_not_preflight_when_target_is_already_reached(tmp_path, monkeypatch):
    checkpoint = tmp_path / "runs.jsonl"
    conditions = RunConditions("model", ("pi",), "0.82.0", "sha", "rev", 600, 30, ("digest",))
    for _ in range(2):
        append_checkpoint(
            checkpoint,
            RunResult("diff", _grade_result(), "", "", 0, conditions=conditions),
        )
    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    monkeypatch.setattr(runner, "preflight_model", lambda model: pytest.fail("preflight called"))
    monkeypatch.setattr(runner, "run_agentclinic_phase1", lambda model: pytest.fail("run called"))

    assert len(runner.run_batch(checkpoint, target=2, model="model")) == 2


def test_run_batch_appends_rejected_attempt_before_continuing(tmp_path, monkeypatch):
    checkpoint = tmp_path / "runs.jsonl"
    conditions = RunConditions("model", ("pi",), "0.82.0", "sha", "rev", 600, 30, ("digest",))
    calls = []
    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    monkeypatch.setattr(runner, "preflight_model", lambda model: None)

    def fake_run(model):
        calls.append(len(load_checkpoint(checkpoint)))
        if len(calls) == 1:
            return RunResult(
                "timed out", _grade_result(), "partial", "", None,
                pi_timed_out=True, conditions=conditions,
            )
        return RunResult("accepted", _grade_result(), "out", "", 0, conditions=conditions)

    monkeypatch.setattr(runner, "run_agentclinic_phase1", fake_run)

    records = runner.run_batch(checkpoint, target=2, model="model")

    assert calls == [0, 1]
    assert records[0].accepted is False
    assert records[1].accepted is True


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


def test_pi_command_emits_one_extension_flag_per_path_in_order():
    command = _pi_command(
        "model-name", "task text", extensions=(Path("/a/one.ts"), Path("/b/two.ts"))
    )

    flagged = [
        command[i + 1] for i, item in enumerate(command) if item == "--extension"
    ]
    assert flagged == ["/a/one.ts", "/b/two.ts"]


def test_pi_command_defaults_to_the_projects_extensions():
    command = _pi_command("model-name", "task text")

    assert command.count("--extension") == len(runner.EXTENSIONS)
    for extension in runner.EXTENSIONS:
        assert str(extension) in command


@pytest.mark.skipif(
    os.environ.get("SATYRN_LIVE") != "1",
    reason="set SATYRN_LIVE=1 to require an actual Pi/model run",
)
def test_the_extension_emits_an_evidence_entry_into_captured_stdout():
    # The cycle's whole claim: one entry travels extension -> stdout.
    #
    # Parsed tolerantly rather than substring-filtered: an assistant
    # message quoting "entry_appended", or a truncated final line, would
    # otherwise crash this test instead of failing it -- and a crash
    # reads as a broken test rather than a falsified hypothesis.
    appended = []
    for line in run_agentclinic_phase1().pi_stdout.split("\n"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("type") == "entry_appended":
            appended.append(event)

    assert appended, "no entry_appended event reached stdout"
    assert any(
        event.get("entry", {}).get("customType") == "evidence"
        for event in appended
    )


def test_extension_digest_changes_with_file_content(tmp_path):
    extension = tmp_path / "ext.ts"
    extension.write_text("one")
    first = runner._extension_digest(extension)
    extension.write_text("two")

    assert runner._extension_digest(extension) != first


def test_extension_digest_raises_on_a_directory(tmp_path):
    # Pi's shipped subagent extension is a directory. Cycle 2 must
    # decide how a tree is hashed, not inherit a plausible wrong answer.
    with pytest.raises(ValueError, match="directory"):
        runner._extension_digest(tmp_path)


def test_extension_digest_raises_on_a_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        runner._extension_digest(tmp_path / "absent.ts")


def test_conditions_record_a_digest_per_extension(monkeypatch, tmp_path):
    # _conditions shells out to `git rev-parse` and `pi --version`.
    # Every other unit test in this file monkeypatches _conditions
    # away for that reason; this one needs the real thing, so it stubs
    # the subprocesses instead. The suite stays fixture-only -- no test
    # here may depend on the `pi` binary being installed.
    extension = tmp_path / "ext.ts"
    extension.write_text("contents")
    monkeypatch.setattr(runner, "EXTENSIONS", (extension,))
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="stubbed\n"),
    )

    conditions = runner._conditions("model", ["pi"], 600)

    assert len(conditions.extension_digests) == 1
    assert len(conditions.extension_digests[0]) == 64


def test_run_batch_refuses_a_record_recorded_under_a_different_extension(
    tmp_path, monkeypatch
):
    from harness.checkpoint import append_checkpoint

    checkpoint = tmp_path / "checkpoint.jsonl"
    recorded = RunConditions(
        "model", ("pi",), "0.82.0", "sha", "rev", 600, 30, ("old-digest",)
    )
    append_checkpoint(
        checkpoint,
        RunResult("d", _grade_result(), "out", "", 0, conditions=recorded),
    )
    monkeypatch.setattr(
        runner,
        "_conditions",
        lambda *args: RunConditions(
            "model", ("pi",), "0.82.0", "sha", "rev", 600, 30, ("new-digest",)
        ),
    )

    with pytest.raises(ValueError, match="checkpoint conditions do not match"):
        runner.run_batch(checkpoint, target=1, model="model")
