"""Phase 5 cycle 1 — the improvement mechanism.

An *improvement* is a named, optional change to how a run is steered. The
harness has to record that a run had one applied, or a batch resumes a
checkpoint produced under different steering with nothing noticing. These
tests cover the recording, not the steering's effect.
"""

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
