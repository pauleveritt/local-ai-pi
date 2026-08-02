# Phase 2, Cycle 4 — Claim discipline: four checks and a table gate

**Phase:** 2 — Measurement we can trust, cheaply enough to repeat
**Status:** design, awaiting plan

## Why this cycle

Cycle 3 piloted three questions against its own record and reported what they
caught. This cycle turns that pilot into something that survives the session
that invented it.

**The corpus.** This session produced six errors in derived prose. None was
caught by any test in the repository, because no test looks at prose.

| # | Error | Class | Caught by |
|---|---|---|---|
| 1 | An R² = 0.30 regression intercept read as "23s of fixed overhead", then used to compute a 1.4× recommendation. Measured, the floor is 1.6s — off by a factor of 14. | An unvalidated model drove a decision | Direct measurement, ~6 minutes |
| 2 | The n=48 median **in-stream span**, 46.1s, offered as the reference for an instruction that told contributors to time **end-to-end** `run_agentclinic_phase1()` — ~16% apart, in the direction that under-budgets a batch. | Unit mismatch | Fable's review |
| 3 | "500 not reachable within 1000 runs", published as a finding. It was a bug in `minimum_n_for_precision`'s search, which never tested `max_n` itself. | A defect published as a result | Fable's review |
| 4 | A precision table computed from the n=16 sample, whose support was missing turn values 10 and 12. | Extrapolation past the observed support | The n=32 extension that revealed them |
| 5 | The 48-run baseline's tool totals given as `bash` 207 / `write` 129 — 129 being *this* batch's write count copied into the old batch's column, and 207 corresponding to nothing in either dataset. The real figures are `bash` 137 / `write` 199. A claim was then built on the error ("the `write` count is *identical*, 129 in both"), true only because the same number had been written into both cells. | A number that was never measured | Recomputing before commit |
| 6 | The paragraph confessing error 5 **misreported error 5**, giving the bad draft's figures as `bash` 207 / `write` 199 and calling them "inverted" — 199 is the correct old value, not the draft's, and nothing was inverted. | A number written from memory rather than from the source | Writing this spec, one day later |

**What the pilot showed.** Questions 1 and 2 both bit. Question 3 was quiet.
Errors 5 and 6 slipped all three, and they are the worst of the six, because
reasoning about a fabricated number produces confident, internally coherent
prose. The three questions interrogate what a number *means*; none asks whether
it was ever *measured*.

**Error 6 deserves its own sentence.** A paragraph written specifically to
confess a fabricated number contained a fabricated number, because it was
written from memory of the draft rather than from the draft. It survived the
three questions, an adversarial read, a full gate run, and publication to a
live Pages site. If the discipline this cycle designs cannot account for that
case, it is not worth having — and no reasoning check can, which is why §1–3
below exist.

**Why prose and not only a checklist.** The concept-budget episode recorded in
`ROADMAP.md` is this project's own demonstration that an unenforced rule
drifts: the budget existed, and terms still entered in prose without being
checked against it, because the check ran against code and not against
writing. A checklist alone would repeat that. So this cycle pairs the
checklist with one thing a test enforces.

## The change

### 1. A committed recompute output beside each record

Each research record whose claims come from a recompute script commits that
script's stdout alongside it:

```
docs/superpowers/research/
  2026-08-02-phase2-cycle3-clean-baseline.md
  2026-08-02-phase2-cycle3-recompute-summary.py     (exists)
  2026-08-02-phase2-cycle3-recompute-output.txt     (new)
```

The naming rule is mechanical: `<stem>-recompute-output.txt` beside
`<stem>-recompute-summary.py`. The output is small — 54 lines for cycle 2, 48
for cycle 3 — while the raw checkpoints it derives from are 8.7 MB and stay
outside Git. That asymmetry is the whole reason this works on a fresh clone.

### 2. `tests/test_research_records.py`

For every `docs/superpowers/research/*.md` containing a per-run table:

1. Require a sibling `*-recompute-output.txt`. **A missing file is a failure,
   not a skip** — otherwise a record opts out of the gate by omission, which
   is the same hole as an unenforced checklist.
2. Parse the record's table rows and the script output's per-run lines.
3. Assert they agree: the same set of run numbers, and equal values in every
   column, `span` included.

Records with no per-run table — cycle 1's fixture results, the n=16 evidence
record, the Phase 2 planning analysis — are not gated, because there is no
table to gate. That exemption is by document *shape*, not by an allowlist a
future author can quietly add to.

No model, no server, no raw checkpoints: the fixture-only pattern cycles 3–7
established, for the same reason.

### 3. The non-vacuity pin

A gate that only ever sees matching data proves nothing. Two parsers that both
return an empty dict agree perfectly.

The suite therefore includes a synthetic record-and-output pair, written
inline, differing by **one digit in one cell**, and asserts the comparison
**fails** on it. This is the test that has to be written first and seen to
fail for the stated reason; the passing backfill below is not evidence the
check works.

### 4. Backfill cycles 2 and 3

Regenerate both outputs from the raw checkpoints and commit them.

**Already verified before this spec was written:** cycle 2's 48 rows and cycle
3's 32 rows each match their script's output exactly, in all compared columns.
So the backfill is expected to pass, and **the record must say the audit found
nothing** rather than presenting a clean result as though the gate had earned
its keep on the first day. One passing audit is one data point.

### 5. The four checks, in `docs/sdd.md`

A new section on the published how-we-work page — the right home, because this
is a rule about how records get written, and that page is what a volunteer
reads to learn the loop.

1. **Am I extrapolating outside the observed range?**
2. **What exactly does this number measure — in the same units as whatever I
   am comparing it to?**
3. **Could a new sample contain a value mine never showed?**
4. **Did this number come from a command whose output I can point to, or did I
   write it down?**

Each is stated with the error from the corpus that motivates it, because a
checklist without its casualty list is exactly the kind of prose that drifts.

Question 3 is kept despite catching nothing in its only pilot. It guards error
4, which cost a 32-run extension to discover, and cycle 3's support-coverage
diagnostic exists because of it. Retiring a guard because the one time it ran
it found nothing is the same reasoning as reading a quiet final quarter as
coverage — which this project has already rejected in writing.

**The section must state what the gate does not cover.** Item 4 is mechanized
for table rows only. Prose figures — rates, differences, percentages — remain a
human check, and errors 5 and 6 were both prose. A reader who sees a green test
suite and concludes their derived paragraph is verified would be making this
cycle's own mistake.

## Deliberate exclusions

| Excluded | Why |
|---|---|
| Gating prose figures | Legitimately derived numbers (rates, ratios, differences) have no line in any script output to match. A gate that fires on all of them would be turned off within a cycle. |
| Gating `ROADMAP.md` rows and `docs/superpowers/index.md` | They restate figures the record already establishes, in prose form no script emits. They inherit the record's verification. |
| Gating `BRIEF.md`, `docs/setup.md` | Their numbers are environmental facts — ports, versions — with no recompute script behind them. The gate would be almost entirely exceptions. |
| Running recompute scripts in CI | The raw checkpoints are outside Git, so the run would skip on every fresh clone and in CI — silently absent exactly where it would matter. Committing the output instead moves the evidence to where the test can reach it. |
| Requiring every numeral in a record to appear in committed output | Would fire on dates, versions, and every derived figure. Too noisy to survive a real record. |
| Changing the adversarial-review step | Fable's review caught errors 2 and 3 and stays exactly as it is. This cycle adds a check that runs earlier and cheaper, not a replacement. |
| Any `harness/` change | This is `tests/` and `docs/` only. Phase 2 has not touched the run machinery and does not start here. |

## Concept budget

No new terms expected. "Claim", "check", and "gate" are used in their ordinary
senses and name no mechanism a contributor must hold in mind; the artifacts
have literal names (`tests/test_research_records.py`, `*-recompute-output.txt`).

The budget check runs **at close, against the prose actually written**, per the
correction cycle 2's episode demands and cycle 3 first honoured. If a term
turns out to be doing mechanism work, it gets added to the table with an honest
note rather than quietly kept.

## Testing

**The failing test first.** The synthetic one-digit-off pair from §3, seen to
fail before the comparison logic exists, then seen to pass once it does.

**Shape coverage, not just value coverage.** Separate synthetic cases for: a
record whose table has a row the output lacks; an output with a row the table
lacks; and a record with a table but no sibling output file. Each must fail.
Value equality alone would let a parser that silently drops rows pass.

**Backfill as real data.** Cycles 2 and 3's committed outputs exercise the gate
against two genuine records, 80 rows between them — the same split cycles 2 and
3 used, where synthetic cases carry the non-vacuity weight and real data proves
the thing works on the actual artifacts.

**Gates unchanged:** `uv run pytest tests/ && uv run ruff check . && uv run
pyrefly check`, plus strict Sphinx.

## Non-goals recap

No harness changes, no gate on prose or roadmap rows, no new concepts, no
change to adversarial review, and no claim that one passing audit proves the
discipline works. This cycle writes down what the six errors taught, enforces
the one part of it a test can reach, and is explicit about the part it cannot.
