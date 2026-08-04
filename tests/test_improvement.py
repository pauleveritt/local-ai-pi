"""Phase 5 cycle 1 — the improvement mechanism.

An *improvement* is a named, optional change to how a run is steered. The
harness has to record that a run had one applied, or a batch resumes a
checkpoint produced under different steering with nothing noticing. These
tests cover the recording, not the steering's effect.
"""

from pathlib import Path
from types import SimpleNamespace

import harness.runner as runner
from harness.runner import Suite


def _stub_subprocess(monkeypatch):
    """`_conditions` shells out for the harness revision and Pi's version.

    Both are irrelevant here and one of them requires Pi installed, so the
    tests below stub them rather than skipping without Pi.
    """
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda command, **kwargs: SimpleNamespace(stdout="stub\n"),
    )
    monkeypatch.setattr(runner, "_path_digest", lambda path: "digest")


def _suite(tmp_path, allowlist=("thing.py",)) -> Suite:
    spec = tmp_path / "spec.md"
    spec.write_text("build a thing")
    acceptance = tmp_path / "test_acceptance.py"
    acceptance.write_text("def test_one(): assert True\n")
    return Suite("s", spec, acceptance, allowlist)


def test_uncommitted_acceptance_edit_changes_conditions(tmp_path, monkeypatch):
    """`harness_revision` is `git rev-parse HEAD`, so an *uncommitted* edit
    to an acceptance file sails past it. Without `acceptance_sha256` a batch
    resumes a checkpoint graded under a different contract."""
    _stub_subprocess(monkeypatch)
    suite = _suite(tmp_path)

    before = runner._conditions(suite, "model", ["pi", "prompt"], 600)
    suite.acceptance.write_text("def test_one(): assert False\n")
    after = runner._conditions(suite, "model", ["pi", "prompt"], 600)

    assert before.acceptance_sha256 != after.acceptance_sha256
    assert before != after


def test_changing_the_allowlist_changes_conditions(tmp_path, monkeypatch):
    """Two suites differing only in which model-written paths get copied
    out and graded must not share conditions."""
    _stub_subprocess(monkeypatch)
    narrow_suite = _suite(tmp_path, allowlist=("thing.py",))
    wide_suite = Suite(
        "s", narrow_suite.task_spec, narrow_suite.acceptance, ("thing.py", "templates")
    )

    narrow = runner._conditions(narrow_suite, "model", ["pi", "p"], 600)
    wide = runner._conditions(wide_suite, "model", ["pi", "p"], 600)

    assert narrow.source_allowlist != wide.source_allowlist
    assert narrow != wide


def test_conditions_without_an_improvement_say_so(tmp_path, monkeypatch):
    """A run with no improvement records that explicitly, so a reader of a
    checkpoint line never has to infer it from an absent field -- and so no
    real improvement name can collide with the pre-phase-5 sentinel."""
    _stub_subprocess(monkeypatch)

    conditions = runner._conditions(_suite(tmp_path), "model", ["pi", "prompt"], 600)

    assert conditions.improvement_name == "none"
    assert conditions.improvement_digest == "<none>"


def _tree(root, marker="name: implementer\n"):
    (root / "agents").mkdir(parents=True)
    (root / "index.ts").write_text("export const x = 1\n")
    (root / "agents" / "implementer.md").write_text(marker)
    return root


def test_tree_digest_changes_on_any_nested_file(tmp_path):
    """A digest that only saw top-level files would let an edit deep in
    Pi's shipped subagent tree pass unnoticed -- and its specialists live
    exactly one level down, in `agents/`."""
    tree = _tree(tmp_path / "ext")

    before = runner._path_digest(tree)
    (tree / "agents" / "implementer.md").write_text("name: implementer!\n")
    after = runner._path_digest(tree)

    assert before != after


def test_tree_digest_ignores_the_trees_own_path(tmp_path):
    """Pi's shipped extension sits at a different absolute path on every
    contributor's machine and moves on every upgrade. A path-sensitive
    digest would report drift that is not there, and `run_batch` would
    refuse to resume a checkpoint that is in fact still valid."""
    first = _tree(tmp_path / "a" / "ext")
    second = _tree(tmp_path / "b" / "ext")

    assert runner._path_digest(first) == runner._path_digest(second)


def test_tree_digest_sorts_rather_than_trusting_iteration_order(tmp_path, monkeypatch):
    """Filesystem iteration order is not guaranteed, and the same
    extension must digest identically on two machines.

    This perturbs `rglob` directly instead of building two trees in
    different creation orders. **The creation-order version was written
    first and was vacuous**: `rglob` returned both trees' entries in the
    same order anyway, so removing `sorted()` left it green. It was
    replaced rather than kept, because a test that cannot fail is worse
    than no test -- it reports coverage that is not there.
    """
    tree = tmp_path / "ext"
    tree.mkdir()
    for name in ("one.ts", "two.ts", "three.ts"):
        (tree / name).write_text(name)

    natural = runner._path_digest(tree)

    real_rglob = Path.rglob
    monkeypatch.setattr(
        Path, "rglob", lambda self, pattern: reversed(list(real_rglob(self, pattern)))
    )

    assert runner._path_digest(tree) == natural


def test_tree_digest_notices_a_file_moving_within_the_tree(tmp_path):
    """Contents alone are not enough: two trees holding the same bytes at
    different paths are different extensions. Hashing the concatenated
    file digests without their names would call them equal."""
    first = tmp_path / "a"
    second = tmp_path / "b"
    (first / "agents").mkdir(parents=True)
    (second / "prompts").mkdir(parents=True)
    (first / "agents" / "one.md").write_text("body\n")
    (second / "prompts" / "one.md").write_text("body\n")

    assert runner._path_digest(first) != runner._path_digest(second)
