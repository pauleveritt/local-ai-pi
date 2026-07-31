import json

import pytest

from harness.checkpoint import append_checkpoint, load_checkpoint
from harness.grading import GradeResult
from harness.runner import RunResult


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
            }
        )
        + "\n"
    )

    with pytest.raises(json.JSONDecodeError):
        load_checkpoint(path)
