"""replicate.py's command construction and failure handling, offline.

The command builder is the one place an unattended caller's cell
selection reaches the subprocess. `--probe` used to be hardcoded into
every invocation regardless of `--cell`, which meant a cell pinning the
exact envelope (envelope-cap.ts) failed `Cell.verify` on every single
attempt -- caught before this file existed, by a design review that
actually read the argv being built. These tests pin the fix and the
shapes that would silently regress it back.
"""

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.replicate import _command, main


def _args(**overrides) -> argparse.Namespace:
    base = dict(
        cohort=Path("workloads/svcs/cohort.toml"),
        model="omlx/gemma-4-12B-it-MLX-8bit",
        server="http://127.0.0.1:8001",
        tools="read,write",
        timeout="900",
        contract_draft_dir=None,
        probe_dir=None,
        probe=False,
        proposal_limit=False,
        guards=False,
        cell=Path("workloads/svcs/cells/gemma12b-envelope.toml"),
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def test_probe_flag_is_opt_in_not_forced() -> None:
    """The blocker: this used to be unconditional, killing every envelope cell."""
    command = _command(_args(probe=False), "registry-iter", Path("/out"))
    assert "--probe" not in command


def test_probe_flag_passes_through_when_requested() -> None:
    command = _command(_args(probe=True), "registry-iter", Path("/out"))
    assert "--probe" in command


def test_cell_is_always_forwarded() -> None:
    command = _command(_args(), "registry-iter", Path("/out"))
    assert "--cell" in command
    assert str(_args().cell) in command


def test_probe_dir_forwarded_when_set() -> None:
    command = _command(
        _args(probe_dir=Path("workloads/svcs/contracts/locating/probe")),
        "registry-iter",
        Path("/out"),
    )
    assert "--probe-dir" in command
    assert "workloads/svcs/contracts/locating/probe" in command


def test_probe_dir_omitted_when_unset() -> None:
    command = _command(_args(probe_dir=None), "registry-iter", Path("/out"))
    assert "--probe-dir" not in command


def _fake_run(returncode: int, writes_record: bool):
    """A subprocess.run stand-in that optionally writes the attempt record.

    `main()` decides infrastructure-death by whether the record landed,
    not by the subprocess's exit code -- `screen_workload` can exit
    nonzero for a properly graded rejection. Mirroring that here is what
    makes this test exercise the real decision.
    """

    def run(command, stdout=None, stderr=None):
        if writes_record:
            out_index = command.index("--out") + 1
            out_dir = Path(command[out_index])
            out_dir.mkdir(parents=True, exist_ok=True)
            task = command[command.index("--task") + 1]
            (out_dir / f"{task}.json").write_text(
                json.dumps({"outcome": "accepted", "gap_closed": 1.0})
            )

        class Result:
            pass

        result = Result()
        result.returncode = returncode
        return result

    return run


def test_consecutive_infrastructure_failures_abort_the_run(tmp_path) -> None:
    """A dead server must not burn the rest of the night recording FAILED.

    Three replicates in a row with no attempt record is the shape a dead
    model server or a broken cell produces -- distinct from a model that
    tried and was correctly rejected, which still writes a record.
    """
    with patch(
        "tools.replicate.subprocess.run", side_effect=_fake_run(1, writes_record=False)
    ):
        code = main(
            [
                "--cohort", "workloads/svcs/cohort.toml",
                "--model", "omlx/gemma-4-12B-it-MLX-8bit",
                "--task", "registry-iter",
                "--replicates", "6",
                "--out", str(tmp_path),
                "--max-consecutive-failures", "3",
            ]
        )
    assert code == 2
    # Aborted after 3, not after all 6 -- the remaining replicates for this
    # task were never attempted.
    assert not (tmp_path / "registry-iter__r4").exists()


def test_a_real_rejection_does_not_count_as_infrastructure_failure(tmp_path) -> None:
    """The record existing is what matters, not whether the arm accepted.

    A model can be correctly rejected six times in a row -- that is a
    result, not a reason to abort an unattended run.
    """
    with patch(
        "tools.replicate.subprocess.run", side_effect=_fake_run(1, writes_record=True)
    ):
        code = main(
            [
                "--cohort", "workloads/svcs/cohort.toml",
                "--model", "omlx/gemma-4-12B-it-MLX-8bit",
                "--task", "registry-iter",
                "--replicates", "3",
                "--out", str(tmp_path),
                "--max-consecutive-failures", "3",
            ]
        )
    assert code == 0
    assert (tmp_path / "registry-iter__r3" / "registry-iter.json").is_file()


def test_a_recovery_resets_the_consecutive_counter(tmp_path) -> None:
    """Two failures then a success then two more failures must not abort at 4.

    The counter tracks a *streak*, not a lifetime total -- an unattended
    run should tolerate an occasional infrastructure hiccup, only abort
    on a sustained one.
    """
    calls = {"n": 0}

    def run(command, stdout=None, stderr=None):
        calls["n"] += 1
        # Fail, fail, succeed, fail, fail -- never 3 in a row.
        writes = calls["n"] == 3
        return _fake_run(1, writes_record=writes)(command, stdout, stderr)

    with patch("tools.replicate.subprocess.run", side_effect=run):
        code = main(
            [
                "--cohort", "workloads/svcs/cohort.toml",
                "--model", "omlx/gemma-4-12B-it-MLX-8bit",
                "--task", "registry-iter",
                "--replicates", "5",
                "--out", str(tmp_path),
                "--max-consecutive-failures", "3",
            ]
        )
    assert code == 0
    assert calls["n"] == 5


def test_an_existing_record_is_skipped_and_resets_the_streak(tmp_path) -> None:
    """Resuming into a directory with prior work must not misread it as new failures."""
    existing = tmp_path / "registry-iter__r1"
    existing.mkdir(parents=True)
    (existing / "registry-iter.json").write_text(
        json.dumps({"outcome": "accepted", "gap_closed": 1.0})
    )
    with patch(
        "tools.replicate.subprocess.run", side_effect=_fake_run(0, writes_record=True)
    ) as mock_run:
        code = main(
            [
                "--cohort", "workloads/svcs/cohort.toml",
                "--model", "omlx/gemma-4-12B-it-MLX-8bit",
                "--task", "registry-iter",
                "--replicates", "2",
                "--out", str(tmp_path),
            ]
        )
    assert code == 0
    assert mock_run.call_count == 1, "r1 was present on disk and must not be re-run"
