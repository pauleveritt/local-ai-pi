import hashlib
import json
import os
import shutil
import subprocess
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
    run_suite,
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


def test_run_suite_calls_pi_and_returns_its_result(tmp_path, monkeypatch):
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

    def fake_grade(actual_workspace, acceptance, *, source_allowlist):
        events.append("grade")
        assert actual_workspace == workspace
        assert acceptance == runner.AGENTCLINIC_PHASE_1.acceptance
        assert source_allowlist == ("app.py", "templates")
        return _grade_result()

    monkeypatch.setattr(runner, "check_model_server_alive", fake_liveness)
    monkeypatch.setattr(runner, "prepare_workspace", fake_workspace)
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner, "run_process", fake_process)
    monkeypatch.setattr(runner, "grade", fake_grade)
    monkeypatch.setattr(
        runner, "_conditions", lambda suite, model, command, timeout, extensions: None
    )

    result = run_suite(runner.AGENTCLINIC_PHASE_1)

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
    conditions = RunConditions("model", ("pi",), runner.EXPECTED_PI_VERSION, "sha", "rev", 600, 30, ("digest",))
    calls = []

    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    monkeypatch.setattr(runner, "preflight_model", lambda model: calls.append("preflight"))

    def fake_run(suite, *, model):
        calls.append("run")
        return RunResult("diff", _grade_result(), "out", "", 0, conditions=conditions)

    monkeypatch.setattr(runner, "run_suite", fake_run)

    records = runner.run_batch(checkpoint, target=2, model="model", suite=runner.AGENTCLINIC_PHASE_1)

    assert len(records) == 2
    assert calls == ["preflight", "run", "run"]
    assert len(load_checkpoint(checkpoint)) == 2


def test_run_batch_resumes_after_existing_records(tmp_path, monkeypatch):
    checkpoint = tmp_path / "runs.jsonl"
    conditions = RunConditions("model", ("pi",), runner.EXPECTED_PI_VERSION, "sha", "rev", 600, 30, ("digest",))
    first = RunResult("first", _grade_result(), "out", "", 0, conditions=conditions)
    append_checkpoint(checkpoint, first)
    calls = []

    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    monkeypatch.setattr(runner, "preflight_model", lambda model: calls.append("preflight"))
    monkeypatch.setattr(
        runner,
        "run_suite",
        lambda suite, *, model: (calls.append("run") or RunResult(
            "second", _grade_result(), "out", "", 0, conditions=conditions
        )),
    )

    records = runner.run_batch(checkpoint, target=2, model="model", suite=runner.AGENTCLINIC_PHASE_1)

    assert [record.diff for record in records] == ["first", "second"]
    assert calls == ["preflight", "run"]


def test_run_batch_refuses_a_record_without_matching_conditions(tmp_path, monkeypatch):
    checkpoint = tmp_path / "runs.jsonl"
    append_checkpoint(checkpoint, RunResult("old", _grade_result(), "", "", 0))
    monkeypatch.setattr(
        runner,
        "_conditions",
        lambda *args: RunConditions(
            "model", ("pi",), runner.EXPECTED_PI_VERSION, "sha", "rev", 600, 30, ("digest",)
        ),
    )
    monkeypatch.setattr(runner, "preflight_model", lambda model: pytest.fail("preflight called"))
    monkeypatch.setattr(runner, "run_suite", lambda suite, *, model: pytest.fail("run called"))

    with pytest.raises(ValueError, match="conditions"):
        runner.run_batch(checkpoint, target=2, model="model", suite=runner.AGENTCLINIC_PHASE_1)


def test_run_batch_preflight_failure_leaves_checkpoint_unchanged(tmp_path, monkeypatch):
    checkpoint = tmp_path / "runs.jsonl"
    conditions = RunConditions("model", ("pi",), runner.EXPECTED_PI_VERSION, "sha", "rev", 600, 30, ("digest",))

    def fail_preflight(model):
        raise RuntimeError("down")

    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    monkeypatch.setattr(runner, "preflight_model", fail_preflight)
    monkeypatch.setattr(runner, "run_suite", lambda suite, *, model: pytest.fail("run called"))

    with pytest.raises(RuntimeError, match="down"):
        runner.run_batch(checkpoint, target=1, model="model", suite=runner.AGENTCLINIC_PHASE_1)

    assert not checkpoint.exists()


def test_run_batch_does_not_preflight_when_target_is_already_reached(tmp_path, monkeypatch):
    checkpoint = tmp_path / "runs.jsonl"
    conditions = RunConditions("model", ("pi",), runner.EXPECTED_PI_VERSION, "sha", "rev", 600, 30, ("digest",))
    for _ in range(2):
        append_checkpoint(
            checkpoint,
            RunResult("diff", _grade_result(), "", "", 0, conditions=conditions),
        )
    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    monkeypatch.setattr(runner, "preflight_model", lambda model: pytest.fail("preflight called"))
    monkeypatch.setattr(runner, "run_suite", lambda suite, *, model: pytest.fail("run called"))

    assert len(runner.run_batch(checkpoint, target=2, model="model", suite=runner.AGENTCLINIC_PHASE_1)) == 2


def test_run_batch_appends_rejected_attempt_before_continuing(tmp_path, monkeypatch):
    checkpoint = tmp_path / "runs.jsonl"
    conditions = RunConditions("model", ("pi",), runner.EXPECTED_PI_VERSION, "sha", "rev", 600, 30, ("digest",))
    calls = []
    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    monkeypatch.setattr(runner, "preflight_model", lambda model: None)

    def fake_run(suite, *, model):
        calls.append(len(load_checkpoint(checkpoint)))
        if len(calls) == 1:
            return RunResult(
                "timed out", _grade_result(), "partial", "", None,
                pi_timed_out=True, conditions=conditions,
            )
        return RunResult("accepted", _grade_result(), "out", "", 0, conditions=conditions)

    monkeypatch.setattr(runner, "run_suite", fake_run)

    records = runner.run_batch(checkpoint, target=2, model="model", suite=runner.AGENTCLINIC_PHASE_1)

    assert calls == [0, 1]
    assert records[0].accepted is False
    assert records[1].accepted is True


@pytest.mark.skipif(
    os.environ.get("SATYRN_LIVE") != "1",
    reason="set SATYRN_LIVE=1 to require an actual Pi/model run",
)
def test_run_suite_produces_live_model_evidence():
    result = run_suite(runner.AGENTCLINIC_PHASE_1)

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
    for line in run_suite(runner.AGENTCLINIC_PHASE_1).pi_stdout.split("\n"):
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
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="stubbed\n"),
    )

    conditions = runner._conditions(runner.AGENTCLINIC_PHASE_1, "model", ["pi"], 600, (extension,))

    assert conditions.extension_digests == (
        hashlib.sha256(b"contents").hexdigest(),
    )


def test_conditions_digests_the_extension_set_it_is_given_not_the_default(
    monkeypatch, tmp_path
):
    # _pi_command already takes an explicit extension set; _conditions must
    # digest that same set, not fall back to the module-level default --
    # otherwise a caller using a different extension set (e.g. adding Pi's
    # shipped subagent extension) would silently record the wrong digests.
    first = tmp_path / "one.ts"
    second = tmp_path / "two.ts"
    first.write_text("first contents")
    second.write_text("second contents")
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="stubbed\n"),
    )

    conditions = runner._conditions(runner.AGENTCLINIC_PHASE_1, "model", ["pi"], 600, (first, second))

    assert conditions.extension_digests == (
        hashlib.sha256(b"first contents").hexdigest(),
        hashlib.sha256(b"second contents").hexdigest(),
    )
    assert conditions.extension_digests != tuple(
        runner._extension_digest(path) for path in runner.EXTENSIONS
    )


def test_run_batch_refuses_a_record_recorded_under_a_different_extension(
    tmp_path, monkeypatch
):
    from harness.checkpoint import append_checkpoint

    checkpoint = tmp_path / "checkpoint.jsonl"
    recorded = RunConditions(
        "model", ("pi",), runner.EXPECTED_PI_VERSION, "sha", "rev", 600, 30, ("old-digest",)
    )
    append_checkpoint(
        checkpoint,
        RunResult("d", _grade_result(), "out", "", 0, conditions=recorded),
    )
    monkeypatch.setattr(
        runner,
        "_conditions",
        lambda *args: RunConditions(
            "model", ("pi",), runner.EXPECTED_PI_VERSION, "sha", "rev", 600, 30, ("new-digest",)
        ),
    )

    with pytest.raises(ValueError, match="checkpoint conditions do not match"):
        runner.run_batch(checkpoint, target=1, model="model", suite=runner.AGENTCLINIC_PHASE_1)


def test_run_batch_refuses_a_pi_version_other_than_the_pinned_one(
    tmp_path, monkeypatch
):
    # Two contributors on different Pi versions would each produce an
    # internally valid batch, and those batches would be compared as
    # though they were comparable. They are not.
    conditions = RunConditions(
        "model", ("pi",), "0.1.0-not-pinned", "sha", "rev", 600, 30, ("digest",)
    )
    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    # Before the check exists, run_batch falls through to preflight_model,
    # which probes the live server and shells a real `pi`. The red phase
    # must not depend on the model server being up.
    monkeypatch.setattr(runner, "preflight_model", lambda *args, **kwargs: None)

    with pytest.raises(RuntimeError, match="0.1.0-not-pinned"):
        runner.run_batch(tmp_path / "checkpoint.jsonl", target=1, model="model", suite=runner.AGENTCLINIC_PHASE_1)


def test_the_refusal_names_the_version_it_expected(tmp_path, monkeypatch):
    conditions = RunConditions(
        "model", ("pi",), "0.1.0-not-pinned", "sha", "rev", 600, 30, ("digest",)
    )
    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)
    monkeypatch.setattr(runner, "preflight_model", lambda *args, **kwargs: None)

    with pytest.raises(RuntimeError, match=runner.EXPECTED_PI_VERSION):
        runner.run_batch(tmp_path / "checkpoint.jsonl", target=1, model="model", suite=runner.AGENTCLINIC_PHASE_1)


def test_the_version_refusal_precedes_the_checkpoint_conditions_check(
    tmp_path, monkeypatch
):
    # The version check sits above the loop over existing records on
    # purpose: a contributor who upgraded Pi after writing a checkpoint
    # should learn that their Pi is wrong, not read a generic "checkpoint
    # conditions do not match this batch". The two refusal tests above
    # both use a checkpoint that does not exist, so `records` is empty and
    # neither exercises the ordering -- move the check below the loop and
    # they stay green while this scenario silently regresses.
    checkpoint = tmp_path / "checkpoint.jsonl"
    recorded = RunConditions(
        "model", ("pi",), runner.EXPECTED_PI_VERSION, "sha", "rev", 600, 30, ("digest",)
    )
    append_checkpoint(
        checkpoint,
        RunResult("d", _grade_result(), "out", "", 0, conditions=recorded),
    )
    monkeypatch.setattr(
        runner,
        "_conditions",
        lambda *args: RunConditions(
            "model", ("pi",), "0.1.0-not-pinned", "sha", "rev", 600, 30, ("digest",)
        ),
    )
    monkeypatch.setattr(runner, "preflight_model", lambda *args, **kwargs: None)

    # ValueError is not a RuntimeError, so this fails rather than passes if
    # the checkpoint comparison gets there first.
    with pytest.raises(RuntimeError, match="0.1.0-not-pinned"):
        runner.run_batch(checkpoint, target=1, model="model", suite=runner.AGENTCLINIC_PHASE_1)


def test_run_batch_proceeds_on_the_pinned_version(tmp_path, monkeypatch):
    # Without this the check could be refusing every batch and the two
    # tests above would still pass.
    conditions = RunConditions(
        "model", ("pi",), runner.EXPECTED_PI_VERSION, "sha", "rev", 600, 30,
        ("digest",),
    )
    monkeypatch.setattr(runner, "_conditions", lambda *args: conditions)

    records = runner.run_batch(tmp_path / "checkpoint.jsonl", target=0, suite=runner.AGENTCLINIC_PHASE_1)

    assert records == []


def test_the_pinned_version_is_the_installed_version():
    # The one test designed to fail on the next upgrade. That is the
    # point: it turns a silent drift into a red suite. Pi moved 0.82.0 ->
    # 0.83.0 during a working session and nothing caught it; eight
    # file:line citations in a published chapter went stale.
    #
    # Skipped when Pi is absent, because docs/setup.md says Pi is needed
    # only for work that invokes a model, and every other Pi-dependent
    # test here is opt-in. A contributor without Pi has done nothing
    # wrong. A contributor with the *wrong* Pi still fails, which is the
    # case this exists for.
    if shutil.which("pi") is None:
        pytest.skip("Pi is not installed; see docs/setup.md")

    installed = subprocess.run(
        ["pi", "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()

    assert installed == runner.EXPECTED_PI_VERSION
