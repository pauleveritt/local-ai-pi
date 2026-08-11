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
    assert captured["validation"] == manifest.preservation_command
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

    deliver_candidate.main([
        "--repo", str(tmp_path),
        "--task", "flask-extensions",
        "--contract-task", "flask-extensions",
        "--model", "omlx/gemma-4-12B-it-MLX-8bit",
        "--skip-server-check",
        "--validation", "echo explicit",
    ])

    assert captured["validation"] == ("echo", "explicit")
