"""The concept budget is a table, and a broken table stops being read.

Phase 5 cycle 13. `BRIEF.md` makes this budget a cost against a 5-10 h/wk
volunteer's ability to hold the design in mind, so it is load-bearing
documentation rather than decoration. A row with the wrong cell count
renders as prose in a Markdown viewer and the term silently stops appearing
in the table anyone actually reads.

**What is deliberately not tested here.** Phase 5 let the budget fall twelve
cycles behind -- its newest entry read "phase 5 cycle 1" while cycles 2-13
ran, and seven terms entered the published records without being weighed.
The obvious guard is to require the newest entry to keep pace with the
newest closed cycle. That is not written, because not every cycle should
introduce a term, and a test demanding one would create pressure to invent
vocabulary to satisfy it -- which is the exact cost the budget exists to
push back on. The lapse is recorded in `ROADMAP.md` as a lapse. Keeping the
budget current is a discipline, and mechanizing it here would corrupt what
it measures.
"""

from harness import runner

ROADMAP = runner.REPO_ROOT / "ROADMAP.md"


def _budget_rows() -> list[list[str]]:
    text = ROADMAP.read_text()
    start = text.find("## Concept budget")
    assert start != -1, "ROADMAP.md has no concept budget"
    end = text.find("\n## ", start + 10)
    section = text[start:end if end != -1 else len(text)]

    rows = []
    for line in section.splitlines():
        if not line.startswith("| ") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if cells and cells[0] == "Term":
            continue
        rows.append(cells)
    return rows


def test_every_budget_row_has_a_term_a_meaning_and_a_provenance():
    rows = _budget_rows()

    assert len(rows) > 20, "budget looks truncated"
    for cells in rows:
        assert len(cells) == 3, f"malformed row: {cells}"
        term, meaning, introduced = cells
        assert term, f"row with no term: {cells}"
        assert meaning, f"`{term}` has no meaning"
        assert introduced, f"`{term}` does not say where it was introduced"


def test_no_term_is_budgeted_twice():
    """A term spent twice is a term nobody is tracking. Redefinitions are
    recorded inside the existing row -- `suite` and `task spec` both carry
    theirs -- rather than by adding a second one.
    """
    terms = [cells[0] for cells in _budget_rows()]

    duplicates = {term for term in terms if terms.count(term) > 1}
    assert not duplicates, f"budgeted more than once: {sorted(duplicates)}"


def test_the_phase_5_vocabulary_the_published_records_rely_on_is_budgeted():
    """These seven were used in published research records before being
    weighed. Pinning them stops the backfill from being quietly reverted,
    which is the cheap way for a late entry to become no entry.
    """
    terms = {cells[0] for cells in _budget_rows()}

    for term in (
        "arm",
        "delegation",
        "delegated child",
        "loop breaker",
        "agent dir",
        "runaway",
        "churn",
    ):
        assert term in terms, f"`{term}` is used in the records but not budgeted"


def test_runaway_and_churn_are_distinguished_not_synonyms():
    """They looked like one concept for four cycles. The loop breaker keys
    on arguments, so it catches the first and mostly misses the second --
    collapsing them back together would let the phase claim a guard for a
    problem it does not address.
    """
    budget = {cells[0]: cells[1] for cells in _budget_rows()}

    assert "identical" in budget["runaway"]
    assert "same target" in budget["churn"]
    assert "Not a runaway" in budget["churn"]
