"""The Phase 8 eval CLI: suites and improvements by name, friendly failures.

Cycles 2-4. Hermetic: nothing here invokes Pi or a model. `run_suite` and
`run_batch` are stubbed where they would otherwise reach out; the CLI's own
liveness/version checks are stubbed in the cycle-3 tests.
"""

import json
from dataclasses import asdict, replace
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

import harness.runner as runner
from harness import cli
from harness.grading import GradeResult
from harness.liveness import ModelServerDown
from harness.runner import SUITES, RunConditions, RunResult
from tests.support import make_conditions


def _result(
    accepted: bool = True,
    conditions: RunConditions | None = None,
    pi_timed_out: bool = False,
    pi_returncode: int | None = 0,
    **grade_overrides,
) -> RunResult:
    """A synthetic run result: accepted by default, signals overridable.

    `grade_overrides` reaches `GradeResult` (e.g. `refused_config`,
    `timed_out`); `pi_timed_out` and `pi_returncode` are `RunResult`
    fields and must not.
    """
    grade_fields = {
        "accepted": accepted,
        "tests_executed": 4,
        "tests_expected": 4,
        "returncode": 0,
        "stdout": "",
        "stderr": "",
        "refused_config": (),
    }
    grade_fields.update(grade_overrides)
    grade = GradeResult(**grade_fields)
    return RunResult(
        diff="",
        grade=grade,
        pi_stdout="",
        pi_stderr="",
        pi_returncode=pi_returncode,
        pi_timed_out=pi_timed_out,
        conditions=conditions if conditions is not None else make_conditions(),
    )


def _write_checkpoint(path: Path, results: list[RunResult]) -> None:
    """Write records the same way append_checkpoint would."""
    path.write_text("\n".join(json.dumps(asdict(result)) for result in results) + "\n")


def test_suites_lists_each_key_beside_its_suite_name(capsys):
    assert cli.main(["suites"]) == 0
    out = capsys.readouterr().out
    for key, suite in SUITES.items():
        shown = key if key == suite.name else f"{key} ({suite.name})"
        assert shown in out


def test_improvements_lists_the_keys(capsys):
    assert cli.main(["improvements"]) == 0
    out = capsys.readouterr().out
    for key in cli.IMPROVEMENTS:
        assert key in out


def test_unknown_suite_is_an_argparse_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["one", "--suite", "no-such-suite"])
    assert excinfo.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_unknown_improvement_is_an_argparse_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["one", "--suite", "duration", "--improvement", "no-such"])
    assert excinfo.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_one_prints_an_accepted_verdict(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(
        cli, "run_suite", lambda suite, **kwargs: _result(accepted=True)
    )
    assert cli.main(["one", "--suite", "duration"]) == 0
    assert "accepted: 4/4 tests passed" in capsys.readouterr().out


def test_one_prints_the_signal_behind_a_rejection(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(
        cli,
        "run_suite",
        lambda suite, **kwargs: _result(
            accepted=False, refused_config=("pyproject.toml",)
        ),
    )
    assert cli.main(["one", "--suite", "duration"]) == 0
    assert "rejected: refused_config=pyproject.toml" in capsys.readouterr().out


def test_one_forwards_improvement_model_and_timeout(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)
    seen = {}

    def fake_run_suite(suite, **kwargs):
        seen.update(kwargs)
        return _result(accepted=True)

    monkeypatch.setattr(cli, "run_suite", fake_run_suite)
    assert (
        cli.main(
            [
                "one",
                "--suite",
                "duration",
                "--improvement",
                "tech-stack-only",
                "--model",
                "some-model",
                "--timeout",
                "30",
            ]
        )
        == 0
    )
    assert seen["model"] == "some-model"
    assert seen["timeout"] == 30
    assert seen["improvement"] is not None
    assert seen["improvement"].name == "tech-stack-only"


def test_batch_uses_the_default_checkpoint_path(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)
    captured = {}

    def fake_run_batch(checkpoint_path, **kwargs):
        captured["checkpoint"] = checkpoint_path
        captured["kwargs"] = kwargs
        return [_result(accepted=True)]

    monkeypatch.setattr(cli, "run_batch", fake_run_batch)
    assert cli.main(["batch", "--suite", "duration", "--target", "1"]) == 0
    expected = tmp_path / "evidence" / f"duration-{date.today().isoformat()}.jsonl"
    assert captured["checkpoint"] == expected
    assert captured["kwargs"]["target"] == 1


def test_batch_prints_attempts_and_summary(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(
        cli,
        "run_batch",
        lambda checkpoint_path, **kwargs: [
            _result(accepted=True),
            _result(accepted=False, timed_out=True, pi_timed_out=True),
        ],
    )
    assert cli.main(["batch", "--suite", "duration"]) == 0
    out = capsys.readouterr().out
    assert "run 1: accepted" in out
    assert "run 2: rejected (timed_out)" in out
    assert "batch complete: 1/2 accepted" in out


def test_negative_target_is_refused(monkeypatch, capsys):
    monkeypatch.setattr(
        cli,
        "run_batch",
        lambda *args, **kwargs: pytest.fail("run_batch must not run"),
    )
    assert cli.main(["batch", "--suite", "duration", "--target", "-1"]) == 2
    assert "must not be negative" in capsys.readouterr().err


def test_one_dead_server_is_a_friendly_refusal(monkeypatch, capsys):
    def down():
        raise ModelServerDown(
            "model server not reachable at http://127.0.0.1:8001/v1/models"
        )

    monkeypatch.setattr(cli, "check_model_server_alive", down)
    assert cli.main(["one", "--suite", "duration"]) == 2
    err = capsys.readouterr().err
    assert "omlx start" in err
    assert "Traceback" not in err


def test_batch_version_mismatch_is_a_friendly_refusal(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)

    def wrong_version(*args, **kwargs):
        raise RuntimeError("this harness pins Pi 0.84.1, but 0.83.0 is installed")

    monkeypatch.setattr(cli, "run_batch", wrong_version)
    assert cli.main(["batch", "--suite", "duration"]) == 2
    err = capsys.readouterr().err
    assert "refused:" in err
    assert "pins Pi 0.84.1" in err
    assert "Traceback" not in err


def test_batch_checkpoint_mismatch_is_a_friendly_refusal(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)

    def mismatch(*args, **kwargs):
        raise ValueError("checkpoint conditions do not match this batch")

    monkeypatch.setattr(cli, "run_batch", mismatch)
    assert cli.main(["batch", "--suite", "duration"]) == 2
    err = capsys.readouterr().err
    assert "checkpoint conditions do not match" in err
    assert "Traceback" not in err


class _FakeSubprocess:
    def __init__(self, stdout: str):
        self._stdout = stdout

    def run(self, command, **kwargs):
        return SimpleNamespace(stdout=self._stdout, stderr="", returncode=0)


def test_preflight_reports_ok(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(cli, "subprocess", _FakeSubprocess("0.84.1\n"))
    assert cli.main(["preflight"]) == 0
    out = capsys.readouterr().out
    assert "model server: OK" in out
    assert "pi version: OK (0.84.1)" in out


def test_preflight_reports_a_wrong_pi_version(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(cli, "subprocess", _FakeSubprocess("0.83.0\n"))
    assert cli.main(["preflight"]) == 2
    err = capsys.readouterr().err
    assert "docs/setup.md" in err


def test_preflight_reports_a_dead_server(monkeypatch, capsys):
    def down():
        raise ModelServerDown("model server not reachable")

    monkeypatch.setattr(cli, "check_model_server_alive", down)
    monkeypatch.setattr(cli, "subprocess", _FakeSubprocess("0.84.1\n"))
    assert cli.main(["preflight"]) == 2
    out = capsys.readouterr().out
    assert "model server: DOWN" in out


def test_help_lists_all_six_subcommands(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    for name in (
        "one",
        "batch",
        "preflight",
        "suites",
        "improvements",
        "summarize",
    ):
        assert name in out


def test_summarize_prints_conditions_acceptance_and_rejections(capsys, tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    records = [
        _result(
            accepted=True,
            conditions=make_conditions(
                model="m", improvement_name="none", pi_version="0.84.1"
            ),
        ),
        _result(
            accepted=False,
            refused_config=("pyproject.toml",),
            conditions=make_conditions(
                model="m", improvement_name="none", pi_version="0.84.1"
            ),
        ),
        _result(
            accepted=False,
            timed_out=True,
            pi_timed_out=True,
            conditions=make_conditions(
                model="m", improvement_name="none", pi_version="0.84.1"
            ),
        ),
    ]
    _write_checkpoint(path, records)
    assert cli.main(["summarize", str(path)]) == 0
    out = capsys.readouterr().out
    assert "runs:       3" in out
    assert "accepted:   1" in out
    assert "conditions: model=m  improvement=none  pi=0.84.1" in out
    assert "2   refused_config=pyproject.toml" in out
    assert "3   timed_out" in out


def test_summarize_reports_a_missing_checkpoint(capsys, tmp_path):
    missing = tmp_path / "nope.jsonl"
    assert cli.main(["summarize", str(missing)]) == 2
    err = capsys.readouterr().err
    assert "no such checkpoint" in err
    assert "Traceback" not in err


def test_summarize_reads_an_empty_checkpoint(capsys, tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("")
    assert cli.main(["summarize", str(path)]) == 0
    out = capsys.readouterr().out
    assert "runs:       0" in out


def test_one_reports_a_pi_failure(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(
        cli,
        "run_suite",
        lambda suite, **kwargs: _result(accepted=True, pi_returncode=1),
    )
    assert cli.main(["one", "--suite", "duration"]) == 0
    assert "rejected: pi exited 1" in capsys.readouterr().out


def test_one_reports_a_rejection_without_a_recorded_signal(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(
        cli, "run_suite", lambda suite, **kwargs: _result(accepted=False)
    )
    assert cli.main(["one", "--suite", "duration"]) == 0
    assert "rejected: no recorded signal" in capsys.readouterr().out


def test_summarize_handles_a_checkpoint_without_conditions(capsys, tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    record = replace(_result(accepted=True), conditions=None)
    _write_checkpoint(path, [record])
    assert cli.main(["summarize", str(path)]) == 0
    out = capsys.readouterr().out
    assert "conditions: <none recorded>" in out
    assert "accepted:   1" in out


class _FakeSubprocessMissingPi:
    def run(self, command, **kwargs):
        raise FileNotFoundError("pi not found")


def test_preflight_reports_a_missing_pi(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(cli, "subprocess", _FakeSubprocessMissingPi())
    assert cli.main(["preflight"]) == 2
    out = capsys.readouterr().out
    assert "pi version: MISMATCH (installed '<pi not found>'" in out


def test_one_with_an_improvement_that_needs_pi_is_friendly(monkeypatch, capsys):
    monkeypatch.setattr(cli, "check_model_server_alive", lambda: None)

    def no_pi():
        raise RuntimeError("cannot locate Pi's installed package")

    monkeypatch.setattr(runner, "pi_package_root", no_pi)
    assert (
        cli.main(["one", "--suite", "duration", "--improvement", "sdd-orchestrator"])
        == 2
    )
    err = capsys.readouterr().err
    assert "cannot locate Pi" in err
    assert "Traceback" not in err
