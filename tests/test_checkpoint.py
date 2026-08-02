import json
from dataclasses import asdict, replace

import pytest

from harness.checkpoint import append_checkpoint, load_checkpoint
from harness.grading import GradeResult
from harness.runner import RunConditions, RunResult


def _sample_result(accepted: bool = True) -> RunResult:
    return RunResult(
        diff="diff --git a/app.py b/app.py\n+x = 1\n",
        grade=GradeResult(
            accepted=accepted,
            tests_executed=4,
            tests_expected=4,
            returncode=0,
            stdout="4 passed\n",
            stderr="",
            refused_config=(),
        ),
        pi_stdout="I created app.py.\n",
        pi_stderr="",
        pi_returncode=0,
    )


def test_append_then_load_round_trips_a_single_record(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    result = _sample_result()

    append_checkpoint(path, result)
    loaded = load_checkpoint(path)

    assert loaded == [result]


def test_load_checkpoint_returns_records_in_append_order(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    first = _sample_result(accepted=True)
    second = _sample_result(accepted=False)

    append_checkpoint(path, first)
    append_checkpoint(path, second)
    loaded = load_checkpoint(path)

    assert loaded == [first, second]


def test_load_checkpoint_drops_a_truncated_final_line(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    complete = _sample_result()
    append_checkpoint(path, complete)

    with path.open("a") as f:
        f.write('{"diff": "partial, process died mid-writ')

    loaded = load_checkpoint(path)

    assert loaded == [complete]


def test_load_checkpoint_raises_on_a_corrupted_non_final_line(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    path.write_text(
        '{"diff": "corrupted, not the last lin\n'
        + json.dumps(
            {
                "diff": _sample_result().diff,
                "grade": {
                    "accepted": True,
                    "tests_executed": 4,
                    "tests_expected": 4,
                    "returncode": 0,
                    "stdout": "4 passed\n",
                    "stderr": "",
                    "refused_config": [],
                },
                "pi_stdout": _sample_result().pi_stdout,
                "pi_stderr": "",
                "pi_returncode": 0,
            }
        )
        + "\n"
    )

    with pytest.raises(json.JSONDecodeError):
        load_checkpoint(path)


def test_append_checkpoint_cleans_up_a_dangling_truncated_line_first(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    complete = _sample_result()
    append_checkpoint(path, complete)

    with path.open("a") as f:
        f.write('{"diff": "partial, process died mid-writ')

    new_result = _sample_result(accepted=False)
    append_checkpoint(path, new_result)

    loaded = load_checkpoint(path)

    assert loaded == [complete, new_result]


def test_append_checkpoint_never_rewrites_valid_records_while_repairing(
    tmp_path, monkeypatch
):
    path = tmp_path / "checkpoint.jsonl"
    complete = _sample_result()
    append_checkpoint(path, complete)
    with path.open("a") as checkpoint:
        checkpoint.write('{"diff": "partial, process died mid-writ')

    def interrupted_rewrite(self, data, *args, **kwargs):
        with self.open("w") as checkpoint:
            checkpoint.write(data[:1])
        raise OSError("interrupted rewrite")

    monkeypatch.setattr(type(path), "write_text", interrupted_rewrite)
    new_result = _sample_result(accepted=False)

    append_checkpoint(path, new_result)

    assert load_checkpoint(path) == [complete, new_result]


def test_append_checkpoint_preserves_a_complete_final_record_without_a_newline(
    tmp_path,
):
    path = tmp_path / "checkpoint.jsonl"
    first = _sample_result()
    path.write_text(
        json.dumps(
            {
                "diff": first.diff,
                "grade": {
                    "accepted": first.grade.accepted,
                    "tests_executed": first.grade.tests_executed,
                    "tests_expected": first.grade.tests_expected,
                    "returncode": first.grade.returncode,
                    "stdout": first.grade.stdout,
                    "stderr": first.grade.stderr,
                    "refused_config": [],
                },
                "pi_stdout": first.pi_stdout,
                "pi_stderr": first.pi_stderr,
                "pi_returncode": first.pi_returncode,
            }
        )
    )
    second = _sample_result(accepted=False)

    append_checkpoint(path, second)

    assert load_checkpoint(path) == [first, second]


def test_load_checkpoint_preserves_a_pre_returncode_record(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    record = _sample_result()
    path.write_text(
        json.dumps(
            {
                "diff": record.diff,
                "grade": {
                    "accepted": record.grade.accepted,
                    "tests_executed": record.grade.tests_executed,
                    "tests_expected": record.grade.tests_expected,
                    "returncode": record.grade.returncode,
                    "stdout": record.grade.stdout,
                    "stderr": record.grade.stderr,
                    "refused_config": [],
                },
                "pi_stdout": record.pi_stdout,
                "pi_stderr": record.pi_stderr,
            }
        )
        + "\n"
    )

    loaded = load_checkpoint(path)

    assert loaded[0].pi_returncode is None
    assert loaded[0].pi_timed_out is False
    assert loaded[0].diff == record.diff


def test_checkpoint_round_trips_timeout_flags(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    result = replace(
        _sample_result(),
        grade=replace(_sample_result().grade, timed_out=True),
        pi_returncode=None,
        pi_timed_out=True,
    )

    append_checkpoint(path, result)

    assert load_checkpoint(path) == [result]


def test_checkpoint_round_trips_run_conditions(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    conditions = RunConditions(
        model="model",
        pi_command=("pi", "--mode", "json", "<task-spec>"),
        pi_version="0.82.0",
        task_spec_sha256="abc",
        harness_revision="def",
        run_timeout=600,
        grade_timeout=30,
        extension_digests=("abc123",),
    )
    result = replace(_sample_result(), conditions=conditions)

    append_checkpoint(path, result)

    assert load_checkpoint(path) == [result]


def test_a_checkpoint_predating_extension_digests_still_loads(tmp_path):
    # Four real evidence checkpoints predate this field. A record that
    # cannot be *read* cannot be recomputed -- and telemetry.py's
    # docstring makes recomputability the reason raw stdout is retained
    # at all. The sentinel keeps them readable while guaranteeing
    # run_batch refuses to resume them: no SHA-256 equals it.
    path = tmp_path / "checkpoint.jsonl"
    record = json.loads(json.dumps(asdict(replace(
        _sample_result(),
        conditions=RunConditions(
            model="model",
            pi_command=("pi",),
            pi_version="0.82.0",
            task_spec_sha256="abc",
            harness_revision="def",
            run_timeout=600,
            grade_timeout=30,
            extension_digests=("unused",),
        ),
    ))))
    del record["conditions"]["extension_digests"]
    path.write_text(json.dumps(record) + "\n")

    loaded = load_checkpoint(path)

    assert loaded[0].conditions is not None
    assert loaded[0].conditions.extension_digests == ("<pre-cycle1>",)
