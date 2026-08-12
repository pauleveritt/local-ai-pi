"""A research record's per-run table must match its recompute script's
committed output.

The raw checkpoints these records derive from live outside Git (22,908,754
bytes across four files; see each record's "Raw checkpoints" table), so no
test can recompute them. What is committed is the script's *output* -- small
enough to live in the repository.

**What a green run does and does not mean.** It means the record's per-run
table agrees with the committed output. It does NOT prove that output came
from a real command: a hand-written .txt passes identically. The output's
authenticity rests on the checkpoint SHA-256s recorded in the record beside
it, and on whoever ran the script -- not on this test.

It also gates per-run tables only. Aggregate lines and derived prose figures
are not compared, and both fabricated numbers in the corpus that motivated
this test were outside a per-run table. See docs/sdd.md, "Checking a
quantitative claim".
"""

import re
from pathlib import Path

import pytest

RESEARCH = Path(__file__).resolve().parents[1] / "docs" / "superpowers" / "research"

# A record names its own output file. Deriving the name from the record's
# stem would not work -- "...cycle3-clean-baseline.md" sits beside
# "...cycle3-recompute-output.txt" -- and a guessing rule would be one more
# thing to get quietly wrong.
#
# Known brittleness, accepted: a record that mentions ANOTHER record's
# output filename -- quoting one as an example, say -- breaks its own gate,
# because exactly one reference is required. Likewise any future six-column
# table with a numeric first cell would be read as run data. Both are safe
# across all five records today. If you hit either, the fix is to change the
# record, not to loosen the check.
OUTPUT_REFERENCE = re.compile(r"([0-9A-Za-z.\-]+-recompute-output\.txt)")

# Accepts both scripts' spacing, and ignores their trailing fields.
_OUTPUT_ROW = re.compile(
    r"^\s*(\d+): turns=\s*(\d+) tools=\s*(\d+) \([^)]*\) "
    r"errors=(\d+) ctx=\s*(\d+) span=\s*([\d.]+)s"
)


def parse_record_table(text: str) -> list[tuple[int, tuple[str, ...]]]:
    """Per-run rows of a record's markdown table, in document order.

    A list, not a dict, on purpose. This project keeps superseded content in
    place -- "kept for the record" recurs throughout ROADMAP.md and both
    research records -- so a document can plausibly end up holding a
    withdrawn per-run table beside its replacement. A dict keyed by run
    number would silently let the last one win and never compare the first.
    Returning rows in order lets compare_record_to_output see the duplicate
    and fail.

    Values stay strings: comparing "28.0" to "28.0" avoids float equality,
    and the record and the output are both rendered to one decimal place.
    """
    rows: list[tuple[int, tuple[str, ...]]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 6 or not cells[0].isdigit():
            continue
        rows.append((int(cells[0]), tuple(cells[1:])))
    return rows


def parse_output_rows(text: str) -> dict[int, tuple[str, ...]]:
    """Per-run lines of a recompute script's stdout, keyed by run number."""
    rows: dict[int, tuple[str, ...]] = {}
    for line in text.splitlines():
        match = _OUTPUT_ROW.match(line)
        if match:
            rows[int(match.group(1))] = match.groups()[1:]
    return rows


def compare_record_to_output(record_text: str, output_text: str) -> list[str]:
    """Mismatches between a record's table and a script's output.

    Empty list means they agree. Reports missing and extra run numbers as
    well as differing values, so a parser that silently drops rows cannot
    pass by producing two small matching dicts.
    """
    ordered = parse_record_table(record_text)
    record = dict(ordered)
    output = parse_output_rows(output_text)
    problems = []
    seen: set[int] = set()
    for run, _ in ordered:
        if run in seen:
            problems.append(f"run {run} appears more than once in the record")
        seen.add(run)
    if not record:
        problems.append("no per-run rows parsed from the record")
    if not output:
        problems.append("no per-run rows parsed from the output")
    for run in sorted(set(record) - set(output)):
        problems.append(f"run {run} is in the record but not the output")
    for run in sorted(set(output) - set(record)):
        problems.append(f"run {run} is in the output but not the record")
    for run in sorted(set(record) & set(output)):
        if record[run] != output[run]:
            problems.append(f"run {run}: record {record[run]} != output {output[run]}")
    return problems


# --- Synthetic pins. These carry the non-vacuity weight, not the real
# --- records: two parsers that both return {} agree perfectly.

_GOOD_RECORD = """
| run | turns | tools | err | ctx | span(s) |
|---|---|---|---|---|---|
| 1 | 7 | 6 | 0 | 16237 | 28.0 |
| 2 | 9 | 8 | 0 | 23184 | 41.8 |
"""

_GOOD_OUTPUT = """\
 1: turns= 7 tools= 6 (bashx2,writex4  ) errors=0 ctx= 16237 span=28.0s complete=True
 2: turns= 9 tools= 8 (bashx3,writex5  ) errors=0 ctx= 23184 span=41.8s complete=True
"""


def test_a_matching_record_and_output_report_no_problems():
    assert compare_record_to_output(_GOOD_RECORD, _GOOD_OUTPUT) == []


def test_one_altered_digit_is_caught():
    # The case that matters: a transcription slip in a single cell. 16237
    # becomes 16238 and nothing else changes.
    altered = _GOOD_RECORD.replace("16237", "16238")
    assert altered != _GOOD_RECORD
    problems = compare_record_to_output(altered, _GOOD_OUTPUT)
    assert len(problems) == 1
    assert "run 1" in problems[0]


def test_a_row_only_in_the_record_is_caught():
    extra = _GOOD_RECORD + "| 3 | 12 | 11 | 0 | 31993 | 71.9 |\n"
    problems = compare_record_to_output(extra, _GOOD_OUTPUT)
    assert problems == ["run 3 is in the record but not the output"]


def test_a_row_only_in_the_output_is_caught():
    extra = _GOOD_OUTPUT + (
        " 3: turns=12 tools=11 (bashx5,writex6  ) errors=0 ctx= 31993 span=71.9s\n"
    )
    problems = compare_record_to_output(_GOOD_RECORD, extra)
    assert problems == ["run 3 is in the output but not the record"]


def test_an_empty_side_is_a_problem_not_a_pass():
    # Guards the failure mode this whole module exists to prevent: two
    # parsers that agree because neither found anything.
    assert compare_record_to_output("", "") != []
    assert compare_record_to_output(_GOOD_RECORD, "") != []
    assert compare_record_to_output("", _GOOD_OUTPUT) != []


def test_the_record_parser_ignores_tables_that_are_not_per_run_tables():
    # Records open with a raw-checkpoints table whose first cell is a word,
    # and a conditions table of two columns. Neither may be read as run data.
    other_tables = """
| | Path | Records | SHA-256 |
|---|---|---|---|
| Part 1 | `~/x.jsonl` | 13 | `cd11` |

| Field | Value |
|---|---|
| Pi version | 0.82.0 |
"""
    assert parse_record_table(other_tables) == []


def test_a_duplicated_run_number_is_caught():
    # The gate's most plausible defeat path. This project keeps superseded
    # content in place, so a record could hold a withdrawn per-run table
    # beside its corrected one. A dict-keyed parser would compare only the
    # last and pass.
    doubled = _GOOD_RECORD + "| 1 | 99 | 99 | 9 | 99999 | 9.9 |\n" + _GOOD_RECORD
    problems = compare_record_to_output(doubled, _GOOD_OUTPUT)
    assert any("more than once" in problem for problem in problems)


# --- The gate itself, over the committed records.


def _gated_records() -> list[Path]:
    return sorted(
        path for path in RESEARCH.glob("*.md") if parse_record_table(path.read_text())
    )


def test_at_least_two_records_are_gated():
    # Without this, a parser regression that stops recognising tables would
    # make every parametrised case below vanish and the suite still pass.
    assert len(_gated_records()) >= 2


def _records_naming_an_output_file() -> list[Path]:
    return sorted(
        path
        for path in RESEARCH.glob("*.md")
        if OUTPUT_REFERENCE.search(path.read_text())
    )


def test_a_record_naming_an_output_file_parses_a_nonempty_table():
    # _gated_records() finds records by successfully parsing a table -- so a
    # table whose shape changes (a seventh column, say) parses to zero rows
    # and silently drops out of the gate, while still naming its output file.
    # This inverts the search: start from the output-file reference, which
    # survives a shape change, and require a non-empty table behind it.
    for record in _records_naming_an_output_file():
        rows = parse_record_table(record.read_text())
        assert rows, (
            f"{record.name} names a *-recompute-output.txt file but its "
            f"per-run table parsed to zero rows -- check its column count"
        )


@pytest.mark.parametrize("record", _gated_records(), ids=lambda p: p.stem)
def test_a_records_table_matches_its_committed_output(record: Path):
    text = record.read_text()
    referenced = set(OUTPUT_REFERENCE.findall(text))
    assert len(referenced) == 1, (
        f"{record.name} has a per-run table, so it must name exactly one "
        f"*-recompute-output.txt file; found {sorted(referenced)}"
    )
    output_path = record.parent / referenced.pop()
    assert output_path.is_file(), f"{record.name} names a missing {output_path.name}"
    assert compare_record_to_output(text, output_path.read_text()) == []
