"""harness/typed_contract.py: the smoke-only bridge from a manifest + a
locating contract to a `HandoffContract` and file baselines.

Deterministic, no model calls -- see the module docstring for what this
is and is not.
"""

import hashlib

import pytest

import harness.typed_contract as typed_contract
from harness.typed_contract import (
    TypedContractError,
    build_typed_handoff,
    strip_authoring_narration,
)


def test_strips_leading_authoring_narration_up_to_the_first_separator():
    raw = "Now I have a clear picture. Here is the contract:\n\n---\n\n# Contract: Title\n\nBody.\n"
    assert strip_authoring_narration(raw) == "# Contract: Title\n\nBody."


def test_leaves_text_alone_when_there_is_no_separator():
    assert strip_authoring_narration("# Contract: Title\n\nBody.") == "# Contract: Title\n\nBody."


@pytest.mark.parametrize(
    "task_id", ["flask-extensions", "stringified-annotations", "local-pings", "autowire"]
)
def test_builds_a_valid_handoff_for_every_smoke_task(tmp_path, task_id):
    # A bare worktree stand-in: the exact writable target absent, which is
    # a legitimate baseline state (the engine treats it as a create).
    handoff = build_typed_handoff(task_id, tmp_path)

    assert handoff.contract["task"].startswith("#"), "narration must be stripped"
    assert handoff.contract["writableFiles"], "every smoke task must resolve to an exact path"
    for entry in handoff.contract["writableFiles"]:
        assert "*" not in entry["path"]
    assert handoff.contract["validation"]
    assert handoff.oracle_command[0] == "pytest"
    assert handoff.writable_glob


def test_reads_a_real_baseline_from_the_worktree(tmp_path):
    target = tmp_path / "src" / "svcs"
    target.mkdir(parents=True)
    content = b"def f():\n    return 1\n"
    (target / "flask.py").write_bytes(content)

    handoff = build_typed_handoff("flask-extensions", tmp_path)

    assert len(handoff.baselines) == 1
    baseline = handoff.baselines[0]
    assert baseline["path"] == "src/svcs/flask.py"
    assert baseline["state"] == "present"
    assert baseline["sha256"] == hashlib.sha256(content).hexdigest()
    assert baseline["lineEnding"] == "LF"


def test_an_absent_writable_target_is_a_legitimate_absent_baseline(tmp_path):
    handoff = build_typed_handoff("stringified-annotations", tmp_path)
    assert handoff.baselines == [{"path": "src/svcs/_core.py", "state": "absent"}]


def test_autowire_falls_back_to_its_named_override_since_its_manifest_is_a_glob(tmp_path):
    handoff = build_typed_handoff("autowire", tmp_path)
    # Two paths, not one: the real target diff also touches __init__.py
    # (a 3-line export addition) -- without it the oracle's own
    # `from svcs import autowire, aautowire` is unsatisfiable no matter
    # what the new module contains.
    assert handoff.contract["writableFiles"] == [
        {"path": "src/svcs/_autowire.py"},
        {"path": "src/svcs/__init__.py"},
    ]


def test_refuses_a_task_with_no_locating_contract(tmp_path, monkeypatch):
    monkeypatch.setattr(typed_contract, "LOCATING_CONTRACTS_DIR", tmp_path / "empty")
    with pytest.raises(TypedContractError):
        build_typed_handoff("flask-extensions", tmp_path)


def test_flask_extensions_validation_deselects_the_two_nodes_its_own_target_diff_flips(tmp_path):
    # A real bug this closes: the preservation suite runs unmodified at
    # base, and flask-extensions' base test_flask.py directly asserts the
    # *old* behavior (app.config) in these two tests -- so a genuinely
    # correct fix (confirmed against the model's actual diff: all six
    # locations changed exactly as specified) was guaranteed to fail them,
    # every time, regardless of correctness. Verified live: 0/6 across two
    # pilot rounds, all six locations correct, both failures always these
    # same two node IDs -- which are exactly manifest.rejection_failing_nodes.
    handoff = build_typed_handoff("flask-extensions", tmp_path)
    validation = handoff.contract["validation"]
    assert "--deselect tests/integrations/test_flask.py::TestInitApp::test_implicit_registry" in validation
    assert "--deselect tests/integrations/test_flask.py::TestInitApp::test_explicit_registry" in validation


def test_deselecting_a_node_absent_at_base_is_a_harmless_no_op(tmp_path):
    # stringified-annotations and local-pings' rejection_failing_nodes name
    # parametrized/added tests that don't exist in the base tree at all
    # (their target diffs add coverage rather than flip an assertion) --
    # pytest's --deselect on an uncollected node id is a silent no-op, not
    # an error, so applying the same deselect logic to every task is safe.
    handoff = build_typed_handoff("stringified-annotations", tmp_path)
    assert "--deselect" in handoff.contract["validation"]
