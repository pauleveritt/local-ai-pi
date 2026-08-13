"""The Phase 8 eval CLI: suites and improvements by name, friendly failures.

Cycles 2-4. Hermetic: nothing here invokes Pi or a model. `run_suite` and
`run_batch` are stubbed where they would otherwise reach out; the CLI's own
liveness/version checks are stubbed in the cycle-3 tests.
"""

from datetime import date

import pytest

from harness import cli
from harness.grading import GradeResult
from harness.runner import SUITES, RunConditions, RunResult
from tests.support import make_conditions


def _result(
    accepted: bool = True,
    conditions: RunConditions | None = None,
    pi_timed_out: bool = False,
    **grade_overrides,
) -> RunResult:
    """A synthetic run result: accepted by default, signals overridable.

    `grade_overrides` reaches `GradeResult` (e.g. `refused_config`,
    `timed_out`); `pi_timed_out` is a `RunResult` field and must not.
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
        pi_returncode=0,
        pi_timed_out=pi_timed_out,
        conditions=conditions if conditions is not None else make_conditions(),
    )


def test_help_lists_the_cli_subcommands(capsys):
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    for name in ("one", "batch", "suites", "improvements"):
        assert name in out


def test_suites_lists_each_key_beside_its_suite_name(capsys):
    assert cli.main(["suites"]) == 0
    out = capsys.readouterr().out
    for key, suite in SUITES.items():
        assert f"{key} ({suite.name})" in out


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
    monkeypatch.setattr(
        cli, "run_suite", lambda suite, **kwargs: _result(accepted=True)
    )
    assert cli.main(["one", "--suite", "duration"]) == 0
    assert "accepted: 4/4 tests passed" in capsys.readouterr().out


def test_one_prints_the_signal_behind_a_rejection(monkeypatch, capsys):
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
