"""The contract arm's admission gate, tested offline against fixtures.

No automated coverage existed for this gate before tonight -- only live
CLI checks against real drafts. That gap is what let a design review
find the hash-binding hole in the first place: nothing here proved a
stale probe result couldn't pass a rewritten draft.
"""

from pathlib import Path

from harness.reconstruction import contract_hash
from tools.screen_workload import contract_admission


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_a_clean_current_draft_is_admitted(tmp_path: Path) -> None:
    drafts, probes = tmp_path / "drafts", tmp_path / "probes"
    _write(drafts / "t.md", "the contract")
    _write(
        probes / "t.json",
        f'{{"leaked": [], "contract_sha256": "{contract_hash("the contract")}"}}',
    )
    assert contract_admission(["t"], drafts, probes) == ""


def test_a_leaking_draft_is_refused_by_name(tmp_path: Path) -> None:
    drafts, probes = tmp_path / "drafts", tmp_path / "probes"
    _write(drafts / "t.md", "the contract")
    _write(
        probes / "t.json",
        f'{{"leaked": ["_services.values"], "contract_sha256": "{contract_hash("the contract")}"}}',
    )
    refusal = contract_admission(["t"], drafts, probes)
    assert "disclose the fix" in refusal
    assert "t" in refusal


def test_a_missing_probe_result_is_refused_not_treated_as_clean(tmp_path: Path) -> None:
    drafts, probes = tmp_path / "drafts", tmp_path / "probes"
    _write(drafts / "t.md", "the contract")
    refusal = contract_admission(["t"], drafts, probes)
    assert "no leak-probe result" in refusal


def test_a_rewritten_draft_invalidates_its_old_probe_result(tmp_path: Path) -> None:
    """The hash-binding fix. Without it this is the exact hole a re-authoring
    loop that overwrites drafts in place would fall into: a clean verdict for
    attempt 1 silently blessing attempt 2's different bytes."""
    drafts, probes = tmp_path / "drafts", tmp_path / "probes"
    _write(drafts / "t.md", "attempt 1, clean")
    _write(
        probes / "t.json",
        f'{{"leaked": [], "contract_sha256": "{contract_hash("attempt 1, clean")}"}}',
    )
    assert contract_admission(["t"], drafts, probes) == ""

    _write(drafts / "t.md", "attempt 2, never probed")
    refusal = contract_admission(["t"], drafts, probes)
    assert "changed since their leak-probe result" in refusal
    assert "t" in refusal


def test_a_task_with_no_draft_is_silently_skipped(tmp_path: Path) -> None:
    """Not every cohort task has a contract; the gate only judges what's there."""
    drafts, probes = tmp_path / "drafts", tmp_path / "probes"
    assert contract_admission(["never-drafted"], drafts, probes) == ""


def test_mixed_tasks_report_every_problem_not_just_the_first(tmp_path: Path) -> None:
    drafts, probes = tmp_path / "drafts", tmp_path / "probes"
    _write(drafts / "admitted.md", "ok")
    _write(
        probes / "admitted.json",
        f'{{"leaked": [], "contract_sha256": "{contract_hash("ok")}"}}',
    )
    _write(drafts / "leaking.md", "bad")
    _write(
        probes / "leaking.json",
        f'{{"leaked": ["x"], "contract_sha256": "{contract_hash("bad")}"}}',
    )
    _write(drafts / "unmeasured.md", "new")

    refusal = contract_admission(["admitted", "leaking", "unmeasured"], drafts, probes)
    paragraphs = refusal.split("\n\n")
    assert len(paragraphs) == 2, "exactly leaking + unmeasured, no stale section"
    assert any("disclose the fix" in p and "leaking" in p for p in paragraphs)
    assert any("no leak-probe result" in p and "unmeasured" in p for p in paragraphs)
    assert not any("admitted" in p for p in paragraphs), (
        "the clean task must not appear as a problem"
    )
