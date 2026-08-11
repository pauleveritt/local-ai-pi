"""tools/deliver_candidate.py's --contract-task wiring.

Deterministic: `deliver()` and the model-server check are stubbed, so no
worktree is created and no Pi process is spawned. What's under test is
argument resolution -- specifically the fix for a real defect a review
found: --contract-task's default --validation used to be the manifest's
*oracle* command, run unoverlaid against the plain worktree (no clone to
overlay the hidden target test files onto), which is a weaker, silently
mislabelled check. It must default to the same preservation command the
contract itself tells the child the parent will run.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import pytest

import harness.candidate as candidate_mod
import tools.deliver_candidate as deliver_candidate
from harness.typed_contract import _effective_preservation_command
from harness.workload import load_manifest

TASKS_DIR = Path(__file__).resolve().parents[1] / "workloads" / "svcs" / "tasks"


@dataclass(frozen=True)
class _StubReceipt:
    """Just enough of `Receipt` for main()'s printing and payload() paths."""

    outcome: str = "candidate-created"
    candidate_ref: str = "refs/satyrn/candidates/stub"
    candidate_commit: str = "deadbeef"
    changed_paths: tuple = ()
    refusal: str = ""
    child_exit: int | None = 0
    child_timed_out: bool = False
    out_of_scope: tuple = ()
    validation_tail: str = ""

    def payload(self) -> dict:
        return {"outcome": self.outcome}


def test_contract_task_defaults_validation_to_the_preservation_command_not_the_oracle(
    monkeypatch, tmp_path, capsys
):
    captured = {}

    def fake_deliver(repo, task_id, prompt, run_model, validation, **kwargs):
        captured["validation"] = validation
        return _StubReceipt()

    monkeypatch.setattr(candidate_mod, "deliver", fake_deliver)
    monkeypatch.setattr(deliver_candidate, "deliver", fake_deliver)

    # A repo path is required by argparse but never touched -- deliver()
    # is stubbed above, so preflight() never runs against it.
    rc = deliver_candidate.main([
        "--repo", str(tmp_path),
        "--task", "flask-extensions",
        "--contract-task", "flask-extensions",
        "--model", "omlx/gemma-4-12B-it-MLX-8bit",
        "--skip-server-check",
    ])

    assert rc == 0
    manifest = load_manifest(TASKS_DIR / "flask-extensions")
    assert captured["validation"] == _effective_preservation_command(manifest)
    assert captured["validation"] != manifest.oracle_command


def test_the_oracle_command_reaches_the_receipt_only_as_an_unverified_note(
    monkeypatch, tmp_path
):
    def fake_deliver(repo, task_id, prompt, run_model, validation, **kwargs):
        return _StubReceipt()

    monkeypatch.setattr(deliver_candidate, "deliver", fake_deliver)

    receipt_path = tmp_path / "receipt.json"
    rc = deliver_candidate.main([
        "--repo", str(tmp_path),
        "--task", "flask-extensions",
        "--contract-task", "flask-extensions",
        "--model", "omlx/gemma-4-12B-it-MLX-8bit",
        "--skip-server-check",
        "--receipt", str(receipt_path),
    ])

    assert rc == 0
    payload = json.loads(receipt_path.read_text())
    manifest = load_manifest(TASKS_DIR / "flask-extensions")
    assert payload["task_oracle_command_unverified"] == list(manifest.oracle_command)
    # The stub outcome came from the preservation-gated call, not this note.
    assert payload["outcome"] == "candidate-created"


def test_an_explicit_validation_still_overrides_the_contract_task_default(monkeypatch, tmp_path):
    captured = {}

    def fake_deliver(repo, task_id, prompt, run_model, validation, **kwargs):
        captured["validation"] = validation
        return _StubReceipt()

    monkeypatch.setattr(deliver_candidate, "deliver", fake_deliver)

    rc = deliver_candidate.main([
        "--repo", str(tmp_path),
        "--task", "flask-extensions",
        "--contract-task", "flask-extensions",
        "--model", "omlx/gemma-4-12B-it-MLX-8bit",
        "--skip-server-check",
        "--validation", "echo explicit",
    ])

    assert rc == 0
    assert captured["validation"] == ("echo", "explicit")


def test_cell_refuses_an_explicit_timeout_alongside_it(tmp_path, monkeypatch):
    # --cell's own help text claims --model/--tools/--timeout are all
    # refused alongside it, "so there is exactly one source of truth for
    # the arm" -- the code used to check only --model/--tools. The refusal
    # must happen before the cell is even loaded, independent of whatever
    # workloads/svcs/cells/*.toml happens to verify against live
    # pi-agent-dir/models.json right now -- load_cell raising proves this
    # test isn't accidentally passing because of an unrelated CellMismatch.
    def fail_if_reached(*args, **kwargs):
        raise AssertionError("--cell should have been refused before loading it")

    monkeypatch.setattr(deliver_candidate.cell_module, "load_cell", fail_if_reached)

    with pytest.raises(SystemExit):
        deliver_candidate.main([
            "--repo", str(tmp_path),
            "--task", "flask-extensions",
            "--contract-task", "flask-extensions",
            "--cell", "workloads/svcs/cells/gemma12b-implementer-v1.toml",
            "--skip-server-check",
            "--timeout", "60",
        ])
