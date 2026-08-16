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
from dataclasses import dataclass
from pathlib import Path

import pytest

import harness.candidate as candidate_mod
import tools.deliver_candidate as deliver_candidate
from harness.cell_resolution import resolve_cell
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
    rc = deliver_candidate.main(
        [
            "--repo",
            str(tmp_path),
            "--task",
            "flask-extensions",
            "--contract-task",
            "flask-extensions",
            "--model",
            "omlx/gemma-4-12B-it-MLX-8bit",
            "--skip-server-check",
        ]
    )

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
    rc = deliver_candidate.main(
        [
            "--repo",
            str(tmp_path),
            "--task",
            "flask-extensions",
            "--contract-task",
            "flask-extensions",
            "--model",
            "omlx/gemma-4-12B-it-MLX-8bit",
            "--skip-server-check",
            "--receipt",
            str(receipt_path),
        ]
    )

    assert rc == 0
    payload = json.loads(receipt_path.read_text())
    manifest = load_manifest(TASKS_DIR / "flask-extensions")
    assert payload["task_oracle_command_unverified"] == list(manifest.oracle_command)
    # The stub outcome came from the preservation-gated call, not this note.
    assert payload["outcome"] == "candidate-created"


def test_an_explicit_validation_is_refused_alongside_contract_task(
    monkeypatch, tmp_path
):
    """The override used to be allowed, and it was a live footgun.

    A contract states, in the text handed to the child, which command the
    parent will run. `--validation` made that statement false with no
    signal -- the child is then judged against a gate it was never shown.
    It cost a real diagnosis once: a driver hardcoding `--validation`
    alongside `--contract-task` shadowed the corrected default and
    produced a false 0/4 on flask-extensions (2026-08-11).

    This test replaces one that asserted the opposite
    (`test_an_explicit_validation_still_overrides_the_contract_task_default`).
    The old behavior was deliberate, so the reversal is deliberate too:
    one contract, one source of truth.
    """

    def unreachable(*args, **kwargs):
        raise AssertionError("deliver() must not run; the CLI should refuse first")

    monkeypatch.setattr(deliver_candidate, "deliver", unreachable)

    with pytest.raises(SystemExit):
        deliver_candidate.main(
            [
                "--repo",
                str(tmp_path),
                "--task",
                "flask-extensions",
                "--contract-task",
                "flask-extensions",
                "--model",
                "omlx/gemma-4-12B-it-MLX-8bit",
                "--skip-server-check",
                "--validation",
                "echo explicit",
            ]
        )


def test_an_explicit_writable_is_refused_alongside_contract_task(monkeypatch, tmp_path):
    """Same one-source-of-truth rule for the outer scope glob."""

    def unreachable(*args, **kwargs):
        raise AssertionError("deliver() must not run; the CLI should refuse first")

    monkeypatch.setattr(deliver_candidate, "deliver", unreachable)

    with pytest.raises(SystemExit):
        deliver_candidate.main(
            [
                "--repo",
                str(tmp_path),
                "--task",
                "flask-extensions",
                "--contract-task",
                "flask-extensions",
                "--model",
                "omlx/gemma-4-12B-it-MLX-8bit",
                "--skip-server-check",
                "--writable",
                "src/**",
            ]
        )


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
        deliver_candidate.main(
            [
                "--repo",
                str(tmp_path),
                "--task",
                "flask-extensions",
                "--contract-task",
                "flask-extensions",
                "--cell",
                "workloads/svcs/cells/gemma12b-implementer-v1.toml",
                "--skip-server-check",
                "--timeout",
                "60",
            ]
        )


def test_implementer_extension_closure_lists_every_same_repo_import():
    # Confirmed by reading every `import` line in the chain (see the
    # constant's own comment), not by trusting this list to stay in sync
    # on its own. This test is the tripwire for that drift: it re-derives
    # the closure from the actual import graph and fails if the constant
    # and the source disagree.
    import re

    root = deliver_candidate._EXTENSIONS_ROOT
    seen = {deliver_candidate.IMPLEMENTER_EXTENSION}
    frontier = [deliver_candidate.IMPLEMENTER_EXTENSION]
    while frontier:
        current = frontier.pop()
        for match in re.finditer(r'from "(\.[^"]+)"', current.read_text()):
            relative = match.group(1)
            if not relative.startswith((".", "..")):
                continue
            candidate = (current.parent / relative).resolve().with_suffix(".ts")
            if candidate.is_relative_to(root) and candidate not in seen:
                seen.add(candidate)
                frontier.append(candidate)

    assert seen == set(deliver_candidate.IMPLEMENTER_EXTENSION_CLOSURE)


def test_cell_digest_changes_if_a_dependency_file_changes(tmp_path, monkeypatch):
    # The bug this whole fix closes: extensions_sha256 used to hash only
    # implementer.ts's own bytes, so an edit to a file it imports (e.g.
    # mutation-engine.ts) changed this arm's real behavior without
    # changing the digest verify() checks. Proven here by editing a copy
    # of the closure with one dependency file's content changed, and
    # asserting the resolved digest differs from the real one.
    real_extensions = deliver_candidate.IMPLEMENTER_EXTENSION_CLOSURE
    unmodified = resolve_cell(
        "omlx/gemma-4-12B-it-MLX-8bit", "read,write,edit", real_extensions, 900.0
    )["extensions_sha256"]

    shadow_root = tmp_path / "extensions"
    shadow_root.mkdir()
    (shadow_root / "implementer").mkdir()
    (shadow_root / "guards").mkdir()
    shadowed = []
    for path in real_extensions:
        relative = path.relative_to(deliver_candidate._EXTENSIONS_ROOT)
        shadow_path = shadow_root / relative
        shadow_path.write_bytes(path.read_bytes())
        shadowed.append(shadow_path)
    # Touch exactly one dependency, not the entry point itself.
    dependency = shadow_root / "implementer" / "mutation-engine.ts"
    dependency.write_text(dependency.read_text() + "\n// a change nobody asked for\n")

    modified = resolve_cell(
        "omlx/gemma-4-12B-it-MLX-8bit", "read,write,edit", tuple(shadowed), 900.0
    )["extensions_sha256"]

    assert modified != unmodified


def test_cell_records_the_full_closure_not_just_the_entry_point():
    declared = deliver_candidate.cell_module.load_cell(
        Path("workloads/svcs/cells/gemma12b-implementer-v1.toml")
    )
    names = declared.pinned["extensions"].split(",")
    assert names == [p.name for p in deliver_candidate.IMPLEMENTER_EXTENSION_CLOSURE]
    assert len(names) > 1, "a single-file digest is exactly the bug this closes"


def test_task_source_flag_reaches_the_contract_and_the_receipt(monkeypatch, tmp_path):
    # The pre-registered comparison's two arms need to be tellable apart
    # after the fact, pooled across many separate CLI invocations -- the
    # receipt is where that has to land.
    captured = {}

    def fake_deliver(repo, task_id, prompt, run_model, validation, **kwargs):
        captured["prompt"] = prompt
        return _StubReceipt()

    monkeypatch.setattr(deliver_candidate, "deliver", fake_deliver)

    receipt_path = tmp_path / "receipt.json"
    rc = deliver_candidate.main(
        [
            "--repo",
            str(tmp_path),
            "--task",
            "flask-extensions",
            "--contract-task",
            "flask-extensions",
            "--task-source",
            "brief",
            "--model",
            "omlx/gemma-4-12B-it-MLX-8bit",
            "--skip-server-check",
            "--receipt",
            str(receipt_path),
        ]
    )

    assert rc == 0
    manifest = load_manifest(TASKS_DIR / "flask-extensions")
    assert manifest.brief_path.read_text().strip() in captured["prompt"]
    payload = json.loads(receipt_path.read_text())
    assert payload["task_source"] == "brief"


def test_task_source_defaults_to_locating_contract(monkeypatch, tmp_path):
    receipt_path = tmp_path / "receipt.json"

    def fake_deliver(repo, task_id, prompt, run_model, validation, **kwargs):
        return _StubReceipt()

    monkeypatch.setattr(deliver_candidate, "deliver", fake_deliver)

    deliver_candidate.main(
        [
            "--repo",
            str(tmp_path),
            "--task",
            "flask-extensions",
            "--contract-task",
            "flask-extensions",
            "--model",
            "omlx/gemma-4-12B-it-MLX-8bit",
            "--skip-server-check",
            "--receipt",
            str(receipt_path),
        ]
    )

    assert json.loads(receipt_path.read_text())["task_source"] == "locating-contract"


def test_task_source_without_contract_task_is_refused(tmp_path):
    contract_file = tmp_path / "contract.md"
    contract_file.write_text(
        "---\nwritableFiles: [a/b.py]\nvalidation: echo ok\n---\ndo the thing\n"
    )
    with pytest.raises(SystemExit):
        deliver_candidate.main(
            [
                "--repo",
                str(tmp_path),
                "--task",
                "flask-extensions",
                "--contract",
                str(contract_file),
                "--model",
                "omlx/gemma-4-12B-it-MLX-8bit",
                "--skip-server-check",
                "--task-source",
                "brief",
            ]
        )
