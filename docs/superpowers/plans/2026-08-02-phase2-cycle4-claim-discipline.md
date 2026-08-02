# Phase 2, Cycle 4 — Claim discipline: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a research record's per-run table impossible to publish unless
it matches a committed recompute output, and write down the four checks that
cover what no test can reach.

**Architecture:** One new test module, `tests/test_research_records.py`, holding
two string parsers and a comparison function. The file-level gate walks
`docs/superpowers/research/*.md`; the synthetic tests call the same functions
with inline strings, so the non-vacuity cases need no fixture files. Records
name their own output file, so the test never guesses at filename stems. No
`harness/` change; `tests/` and `docs/` only.

**Tech Stack:** Python 3.14, pytest 8.3.4, ruff, pyrefly, Sphinx (strict, `-W`).

## Global Constraints

- **`tests/` and `docs/` only.** No change to `harness/`, the run machinery, or
  the adversarial-review step.
- **The gate must run on a fresh clone.** No raw checkpoints, no model, no
  server. The committed output is the evidence; the 8.7 MB of checkpoints stay
  outside Git.
- **A record with a table and no output file is a failure, not a skip.** A
  record must not be able to opt out of the gate by omission.
- **The non-vacuity tests are written and seen to fail first.** The backfill
  passing is not evidence the gate works — two broken parsers agree perfectly.
- **No new concept-budget terms expected**; the check runs at close against the
  prose actually written, not against this plan.
- **Gates, before every commit:** `uv run pytest tests/ && uv run ruff check . &&
  uv run pyrefly check`, plus `uv run --group docs sphinx-build -W -b html docs
  docs/_build/html`.

**Starting state:** worktree `.worktrees/phase2-cycle4` on branch
`phase2-cycle4`, HEAD `1b5fab7`, tree clean, baseline green (101 tests).

**The raw checkpoints Task 2 needs** (present on the owner's machine, outside
Git):

| Record | Checkpoints |
|---|---|
| Cycle 2 | `~/local-ai-pi-evidence/satyrn-cycle14-checkpoint-v2.jsonl`, `~/local-ai-pi-evidence/satyrn-phase2-cycle2-extension-n32.jsonl` |
| Cycle 3 | `~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-part1-n13.jsonl`, `~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-part2-n19.jsonl` |

---

### Task 1: The gate, proven against synthetic failures first

**Files:**
- Create: `tests/test_research_records.py`

**Interfaces:**
- Consumes: nothing from the project. Pure string functions plus `pathlib`.
- Produces, for Task 2 and any later record:
  - `parse_record_table(text: str) -> dict[int, tuple[str, ...]]`
  - `parse_output_rows(text: str) -> dict[int, tuple[str, ...]]`
  - `compare_record_to_output(record_text: str, output_text: str) -> list[str]`
    — returns a list of human-readable mismatch descriptions; empty means agree.
  - `OUTPUT_REFERENCE: re.Pattern` — finds `<name>-recompute-output.txt`
    mentions inside a record.

**The two formats being parsed.** Both already exist in the repository; the
parsers are written to them, not the other way round.

A record's per-run table row:

```
| 1 | 7 | 6 | 0 | 16237 | 28.0 |
```

Six cells: run, turns, tools, err, ctx, span.

A recompute script's per-run line (cycle 2's and cycle 3's formats differ in
spacing and trailing fields, and the parser must accept both):

```
 1: turns= 6 tools= 5 (bashx1,writex4  ) errors=0 ctx= 13212 span=35.2s complete=True
 1: turns= 7 tools= 6 (bashx2,writex4     ) errors=0 ctx= 16237 span=  28.0s complete=True accepted=True tested=True
```

- [ ] **Step 1: Write the failing tests**

Create `tests/test_research_records.py`:

```python
"""A research record's per-run table must match its recompute script's
committed output.

The raw checkpoints these records derive from live outside Git (8.7 MB, see
each record's "Raw checkpoints" table), so no test can recompute them. What
is committed is the script's *output* -- small enough to live in the
repository, and enough to prove the record's table was transcribed from a
real command rather than written down.

This gates the table only. Prose figures -- rates, differences, percentages
-- are legitimately derived and have no line to match. See docs/sdd.md,
"Checking a quantitative claim", for the part of the discipline no test can
reach.
"""

import re
from pathlib import Path

import pytest

RESEARCH = Path(__file__).resolve().parents[1] / "docs" / "superpowers" / "research"

# A record names its own output file. Deriving the name from the record's
# stem would not work -- "...cycle3-clean-baseline.md" sits beside
# "...cycle3-recompute-output.txt" -- and a guessing rule would be one more
# thing to get quietly wrong.
OUTPUT_REFERENCE = re.compile(r"([0-9A-Za-z.\-]+-recompute-output\.txt)")

# Accepts both scripts' spacing, and ignores their trailing fields.
_OUTPUT_ROW = re.compile(
    r"^\s*(\d+): turns=\s*(\d+) tools=\s*(\d+) \([^)]*\) "
    r"errors=(\d+) ctx=\s*(\d+) span=\s*([\d.]+)s"
)


def parse_record_table(text: str) -> dict[int, tuple[str, ...]]:
    """Per-run rows of a record's markdown table, keyed by run number.

    Values stay strings: comparing "28.0" to "28.0" avoids float equality,
    and the record and the output are both rendered to one decimal place.
    """
    rows: dict[int, tuple[str, ...]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 6 or not cells[0].isdigit():
            continue
        rows[int(cells[0])] = tuple(cells[1:])
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
    record = parse_record_table(record_text)
    output = parse_output_rows(output_text)
    problems = []
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
            problems.append(
                f"run {run}: record {record[run]} != output {output[run]}"
            )
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
    assert parse_record_table(other_tables) == {}


# --- The gate itself, over the committed records.


def _gated_records() -> list[Path]:
    return sorted(
        path for path in RESEARCH.glob("*.md") if parse_record_table(path.read_text())
    )


def test_at_least_two_records_are_gated():
    # Without this, a parser regression that stops recognising tables would
    # make every parametrised case below vanish and the suite still pass.
    assert len(_gated_records()) >= 2


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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_research_records.py -v`

Expected: the synthetic tests **pass** (the functions are defined in the same
file), and the two gate tests **fail** — `test_at_least_two_records_are_gated`
passes but `test_a_records_table_matches_its_committed_output` fails for both
records with "must name exactly one `*-recompute-output.txt` file; found []".

That failure is the point: the gate is real and the records do not yet satisfy
it. Task 2 makes them satisfy it.

If instead the parametrised test does not appear at all, the record parser is
broken — fix that before continuing, because a silently empty parametrisation
is exactly the hole `test_at_least_two_records_are_gated` guards.

- [ ] **Step 3: Confirm the synthetic pins fail when they should**

Temporarily break `compare_record_to_output` by making it `return []`
unconditionally, then run:

Run: `uv run pytest tests/test_research_records.py -k "altered or only_in or empty_side" -v`

Expected: all four of those tests FAIL. Restore the real body and re-run;
expected: all pass.

This step exists because a comparison function that always reports success
would otherwise sail through every synthetic case, and the whole module would
be decoration.

- [ ] **Step 4: Commit**

```bash
git add tests/test_research_records.py
git commit -m "test(phase2-cycle4): gate a record's per-run table on committed output

Fails today for both records, by design: neither names an output file
yet. The synthetic pins carry the non-vacuity weight -- an altered
digit, a row on either side alone, and the empty-vs-empty case that a
pair of broken parsers would otherwise pass."
```

---

### Task 2: Backfill cycles 2 and 3

**Files:**
- Create: `docs/superpowers/research/2026-08-02-phase2-cycle2-recompute-output.txt`
- Create: `docs/superpowers/research/2026-08-02-phase2-cycle3-recompute-output.txt`
- Modify: `docs/superpowers/research/2026-08-02-phase2-cycle2-precision-baseline.md`
- Modify: `docs/superpowers/research/2026-08-02-phase2-cycle3-clean-baseline.md`

**Interfaces:**
- Consumes: `compare_record_to_output` and `OUTPUT_REFERENCE` from Task 1; the
  four raw checkpoints listed in Global Constraints.
- Produces: two committed outputs and two records that name them. After this
  task the gate is green.

- [ ] **Step 1: Regenerate both outputs**

```bash
PYTHONPATH=. uv run python \
  docs/superpowers/research/2026-08-02-phase2-cycle2-recompute-summary.py \
  ~/local-ai-pi-evidence/satyrn-cycle14-checkpoint-v2.jsonl \
  ~/local-ai-pi-evidence/satyrn-phase2-cycle2-extension-n32.jsonl \
  > docs/superpowers/research/2026-08-02-phase2-cycle2-recompute-output.txt
```

```bash
PYTHONPATH=. uv run python \
  docs/superpowers/research/2026-08-02-phase2-cycle3-recompute-summary.py \
  ~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-part1-n13.jsonl \
  ~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-part2-n19.jsonl \
  > docs/superpowers/research/2026-08-02-phase2-cycle3-recompute-output.txt
```

Verify: `wc -l docs/superpowers/research/*-recompute-output.txt`
Expected: 54 lines for cycle 2, 48 for cycle 3.

If either command fails because a checkpoint is missing, **stop**. Do not
hand-write an output file — a fabricated output would defeat the entire cycle
and would be error 5 with extra steps.

- [ ] **Step 2: Have each record name its output**

In `2026-08-02-phase2-cycle2-precision-baseline.md`, replace:

```markdown
Recomputed by `2026-08-02-phase2-cycle2-recompute-summary.py`, alongside
this file.
```

with:

```markdown
Recomputed by `2026-08-02-phase2-cycle2-recompute-summary.py`, alongside this
file. Its output is committed as
`2026-08-02-phase2-cycle2-recompute-output.txt`, and
`tests/test_research_records.py` asserts the per-run table below matches it
row for row — see `docs/sdd.md`, "Checking a quantitative claim".
```

In `2026-08-02-phase2-cycle3-clean-baseline.md`, replace:

```markdown
Recomputed by `2026-08-02-phase2-cycle3-recompute-summary.py`, alongside this
file.
```

with:

```markdown
Recomputed by `2026-08-02-phase2-cycle3-recompute-summary.py`, alongside this
file. Its output is committed as
`2026-08-02-phase2-cycle3-recompute-output.txt`, and
`tests/test_research_records.py` asserts the per-run table below matches it
row for row — see `docs/sdd.md`, "Checking a quantitative claim".
```

- [ ] **Step 3: Run the gate against real data**

Run: `uv run pytest tests/test_research_records.py -v`

Expected: every test passes, and the parametrised gate shows two ids —
`2026-08-02-phase2-cycle2-precision-baseline` and
`2026-08-02-phase2-cycle3-clean-baseline`.

**If a mismatch is reported, that is a finding, not an obstacle.** It means a
published table disagrees with its own script. Do not edit the output file to
match the record. Investigate which side is wrong, fix the record, and record
what was found — the audit turning something up is a better outcome for this
cycle than a clean pass.

- [ ] **Step 4: Run the gates**

```bash
uv run pytest tests/ && uv run ruff check . && uv run pyrefly check
```

Expected: all pass. Ruff does not lint `.txt`; pyrefly covers `harness` and
`tests`, so the new test module is type-checked.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/research/
git commit -m "docs(phase2-cycle4): backfill committed recompute outputs

Both published tables -- 48 rows and 32 -- match their scripts exactly.
The audit found nothing, which is one data point and not evidence the
gate has earned its keep."
```

---

### Task 3: The four checks, in `docs/sdd.md`

**Files:**
- Modify: `docs/sdd.md` (new section after "The loop")

**Interfaces:**
- Consumes: the corpus from the design spec.
- Produces: the section `tests/test_research_records.py` and both records
  point at by name, "Checking a quantitative claim". **The heading text is
  load-bearing** — three files cite it.

- [ ] **Step 1: Add the section**

Insert after the "The loop" section in `docs/sdd.md`, before "Feature cycles
and phases":

````markdown
## Checking a quantitative claim

Research records carry numbers, and numbers are where this project has been
wrong most often. Six times in a single day, in prose that no test looked at:

| Error | What went wrong | Caught by |
|---|---|---|
| A regression intercept read as "23s of fixed overhead" | R² was 0.30; the fit was stated as unreliable and then used anyway. Measured, the floor is 1.6s — off by a factor of 14. | Measuring it, six minutes |
| A 46.1s median offered as a budgeting reference | It was *in-stream* span, next to an instruction to time an *end-to-end* call — about 16% apart, in the direction that under-budgets. | Adversarial review |
| "500 not reachable within 1000 runs" | A search bug published as a finding. | Adversarial review |
| A precision table built on 16 runs | The sample's support was missing two turn values that 32 more runs revealed. | Running the extra runs |
| Tool totals of `bash` 207 / `write` 129 | Never measured. 129 was another batch's figure copied across; 207 matched nothing at all. | Recomputing before commit |
| The paragraph confessing the previous row | It misreported the very numbers it was confessing, having been written from memory of the draft rather than from the draft. | Writing the next cycle's spec |

Before publishing a number, ask:

1. **Am I extrapolating outside the observed range?** Fitting a line to a
   narrow range and reading its intercept is the classic case. So is a
   bootstrap over a sample that is mostly one value.
2. **What exactly does this number measure — in the same units as whatever I
   am comparing it to?** Two counts over different denominators are not
   comparable. Neither are two durations that start and stop at different
   points. And a number can be *correct* while measuring the wrong thing: a
   zero error rate looked like success until it turned out the runs with no
   errors were the runs that never tested anything.
3. **Could a new sample contain a value mine never showed?** A quiet tail is
   not coverage. The 16-run sample's last quarter introduced nothing new, and
   two unseen values surfaced immediately afterwards.
4. **Did this number come from a command whose output I can point to, or did
   I write it down?** The last two rows of the table above are this question
   going unasked. Memory is not a source.

**What is enforced, and what is not.** Question 4 is mechanised for one thing
only: a record's per-run table is diffed against its script's committed output
by `tests/test_research_records.py`. Everything else on this page is a human
check. Both of the fabricated numbers above were in *prose*, not in a table,
so the test would not have caught either. A green suite means the table was
transcribed correctly. It says nothing about the paragraph underneath it.

**Why the output is committed and the data is not.** The raw checkpoints are
millions of bytes of model output and stay outside the repository; a script's
output is a few dozen lines. Committing the small artifact is what lets the
check run on a fresh clone, where the data will never exist.
````

- [ ] **Step 2: Verify the heading matches every citation**

Run:

```bash
grep -rn "Checking a quantitative claim" docs/ tests/ | grep -v _build
```

Expected: four hits — the heading itself in `docs/sdd.md`, the two records
from Task 2, and the module docstring in `tests/test_research_records.py`. A
missing hit means a citation drifted from the heading.

- [ ] **Step 3: Build the docs**

```bash
uv run --group docs sphinx-build -W -b html docs docs/_build/html
```

Expected: builds. A warning that the cycle 4 spec and plan are not in any
toctree is expected here and resolved in Task 4.

- [ ] **Step 4: Commit**

```bash
git add docs/sdd.md
git commit -m "docs(phase2-cycle4): four checks for a quantitative claim

Carries its casualty list. A checklist without one is the kind of prose
that drifts -- which is what the concept budget already demonstrated."
```

---

### Task 4: Close the cycle

**Files:**
- Modify: `ROADMAP.md` (Phase 2 table; concept-budget note)
- Modify: `docs/superpowers/index.md` (Phase 2 table, two toctrees)

**Interfaces:**
- Consumes: everything above. Produces a closed cycle.

Note there is no research record for this cycle, so nothing is added to the
Research list — the deliverable is a test and a docs section, not a
measurement.

- [ ] **Step 1: Add the roadmap row**

Append to the Phase 2 feature-cycle table in `ROADMAP.md`, directly after
cycle 3's row with no blank line between them:

```markdown
| 4 | Claim discipline — six derived-prose errors in one session, none reachable by any existing test. `tests/test_research_records.py` diffs each research record's per-run table against its recompute script's committed output, so a table cannot be published without a command behind it; `docs/sdd.md` gains "Checking a quantitative claim", four questions carrying the casualty list that motivates each. Cycles 2 and 3 backfilled: both tables matched, an audit that found nothing and says so. | [spec](docs/superpowers/specs/2026-08-02-phase2-cycle4-claim-discipline-design.md) | [plan](docs/superpowers/plans/2026-08-02-phase2-cycle4-claim-discipline.md) | Done |
```

Verify the table did not break:

```bash
grep -n -A1 "^| 3 | Honest environment" ROADMAP.md | cut -c1-60
```

Expected: the cycle 4 row on the immediately following line, not a blank.

- [ ] **Step 2: Run the concept-budget check at close**

Read this cycle's spec, the `docs/sdd.md` section, and the roadmap row, and
check every term against the budget table — against the prose actually
written, which is the correction cycle 2's episode demands.

Expected result: nothing spent. "Claim", "check", and "gate" are ordinary
English naming no mechanism; the artifacts have literal names. Record the
outcome in `ROADMAP.md` after cycle 3's budget note, in the same form:

```markdown
**Cycle 4 spent nothing.** "Claim", "check", and "gate" are used in their
ordinary senses; the two artifacts are named literally
(`tests/test_research_records.py`, `*-recompute-output.txt`). The check was
run at close against the spec, the `docs/sdd.md` section, and the roadmap row.
```

If the check does find a term, add it to the table with an honest note instead.

- [ ] **Step 3: Wire the docs index**

In `docs/superpowers/index.md`, add to the Phase 2 table:

```markdown
| 4 | Claim discipline | [spec](specs/2026-08-02-phase2-cycle4-claim-discipline-design.md) | [plan](plans/2026-08-02-phase2-cycle4-claim-discipline.md) |
```

Add to the Specs toctree, after `specs/2026-08-02-phase2-cycle3-honest-environment-design`:

```
specs/2026-08-02-phase2-cycle4-claim-discipline-design
```

Add to the Plans toctree, after `plans/2026-08-02-phase2-cycle3-honest-environment`:

```
plans/2026-08-02-phase2-cycle4-claim-discipline
```

Nothing is added to the Research toctree.

- [ ] **Step 4: Run every gate**

```bash
rm -rf docs/_build/html && uv run pytest tests/ && uv run ruff check . && \
uv run pyrefly check && \
uv run --group docs sphinx-build -W -b html docs docs/_build/html
```

Expected: all pass, and Sphinx reports **no warnings** — the clean build is
what proves the toctree wiring is complete.

- [ ] **Step 5: Commit**

```bash
git add ROADMAP.md docs/superpowers/index.md
git commit -m "docs(phase2-cycle4): close the cycle

Roadmap row, index and toctree wiring, and the concept-budget check run
at close against the prose."
```

- [ ] **Step 6: Report honestly**

State: whether the backfill audit found any mismatch (and say plainly if it
found none), that the gate covers tables and not prose, that two of the six
corpus errors would still slip it, and that the branch is `phase2-cycle4` and
unmerged.

Do not describe the discipline as proven. One passing audit is one data point,
and the spec says so.
