# Phase 2, Cycle 3 — Honest environment, clean baseline

**Phase:** 2 — Measurement we can trust, cheaply enough to repeat
**Status:** design, awaiting plan

## Why this cycle

Cycles 1 and 2 built an instrument and characterized its precision. This
cycle fixes what that instrument turned out to be measuring.

**The finding.** Across the 48-run baseline, turn count — the quantity
cycle 2 called "the one real random variable" — is almost entirely
explained by tool errors:

```
errors = -3.79 + 0.643 × turns     R² = 0.952
```

Every one of the **65 errored tool calls** is environment friction, in two
families:

| Family | Count | What happens |
|---|---|---|
| Dependency install | 43 | `pip install fastapi uvicorn jinja2 pytest httpx` → `pip: command not found`; `python3 -m pip install …` → `No module named pip`. The dependencies are *already importable* (cycle 8 established this deliberately) and the uv venv has no `pip`. |
| Test import | 22 | `pytest tests/test_app.py` → `ModuleNotFoundError: No module named 'app'`. A bare `pytest` puts the test file's directory on `sys.path`, not the project root. |

**Why this is not a cosmetic problem.** All **20 of 20** zero-error
baseline runs have a byte-identical shape: `mkdir -p templates tests`
followed by four `write` calls, and **no test run at all**. The runs that
avoided the friction avoided it by skipping verification. Stated plainly:

> The trusted 16/16 was produced in an environment that punished
> verification and rewarded skipping it.

**Measured effect of stating the environment.** Sixteen exploratory runs
against a variant spec (12 by the author, 4 independently raw-captured
during review) produced **0 errors, 16/16 accepted**, and the model ran
`python -m pytest` successfully. Against the baseline zero-error rate of
20/48, sixteen consecutive clean runs has probability ≈ 8.3 × 10⁻⁷, and
the longest zero-error streak anywhere in the 48 baseline runs is 6. The
effect is mechanism-backed, not a lucky streak.

**This is a teaching artifact, which changes the scope.** `docs/` is
published and framed as a teaching record. Phase 1's cycles 2 and 11 are
titled *workspace provisioning* and *corrective hardening*, and what they
provisioned was a **git repository**, not a working environment — cycle
11's controlled environment covers the *pytest grading child* only, while
`runner.py` passes `env=None` so Pi inherits the ambient environment. A
contributor copying that pattern inherits the same trap. So this cycle
corrects the Phase 1 record too, not only Phase 2's.

## What this cycle is not

- **Not a cheaper task slice.** That recommendation has now been withdrawn
  twice. Its motivation was 75 minutes per n=100, but the friction finding
  attacks the *n*, not the per-run cost: a defensible clean claim needs
  roughly 30–48 runs, not 100+. The per-run saving from an honest
  environment is only ~1.12×, and the measured floor (1.6s, ~3% of a run)
  caps what any task redesign could recover.
- **Not a change to `runner.py`, `workspace.py`, `checkpoint.py`, or the
  batch.** Phase 2 has deliberately never touched the run machinery, and
  does not start here.
- **Not a re-claim of Phase 1's result.** Nothing here asserts 16/16 under
  new conditions. Phase 1's record stands, with a correction noting the
  environment it was produced in.
- **Not cycle 4.** The discipline for preventing the recurring
  derived-prose error class is its own cycle; this one only *pilots* the
  check and records what it found.

## The change

### 1. Amend the task spec

Append to `examples/agentclinic/specs/roadmap.md`:

```markdown
## Environment

- FastAPI, Jinja2, pytest, and httpx are already installed. Do not install
  anything.
- A bare `pytest` does not put the project root on `sys.path`, so importing
  `app` from a test will fail. Run tests with `python -m pytest`, which adds
  the working directory.
```

Two lines, ~40 tokens. The second states the environment *fact* and then
the working command, so it reads as description rather than incantation.

**Why `python -m pytest` and not `uv run …`.** Measured in a fresh
workspace under the environment Pi actually inherits: bare `pytest` fails
with `ModuleNotFoundError` (reproducing the 22 real failures); `python -m
pytest` passes; `uv run python -m pytest` also passes. `uv run` is rejected
because the workspace has no `pyproject.toml`, so it succeeds only by
falling back to the ambient environment — incidental behavior that should
not be baked into a model-facing document — and it additionally assumes
`uv` is on the model's PATH. The load-bearing element is `-m`.

### 2. Add `RunTelemetry.tool_errors`

```python
@property
def tool_errors(self) -> int:
    """Count of tool calls that finished and reported an error.

    Counts `is_error is True` only. `None` means *unknown* -- a start with
    no matching end -- not a failure, and `complete` already declares every
    count a lower bound when that happens.
    """
    return sum(1 for call in self.tool_calls if call.is_error)
```

A derived property over existing data, the same shape as
`context_processed`. No new storage, no schema change. Its named consumer
is this cycle's research record, which reports error rate.

**Error *text* is deliberately excluded.** Classification of the two
families required the full payload — truncation does not work, because the
classifying line sits at line 1 of 4 for the `pip` family but around line
14 of 23 for the test-import family. Retaining it would be affordable
(~34 KB across 48 runs) but it is unbounded in principle, and raw
`pi_stdout` already retains everything. That is cycle 1's stated principle
and it held: today's classification was done from raw stdout successfully.
Promote the text only if failure-mode classification becomes routine, with
a named consumer.

### 3. Run a clean baseline

`run_batch()` unmodified, **n = 32**, into a fresh checkpoint outside git.
The existing conditions mechanism prevents mixing with the old checkpoints:
`task_spec_sha256` changes, so `run_batch` refuses to extend them, which is
correct.

**Why 32 and not 12.** The sixteen exploratory runs are evidence that
motivated this change; they are *not* the baseline. Cycle 2's n=16 sample
missed turn values 10 and 12, and this session's 12-run clean sample missed
a 10-turn run that the 16th draw revealed — the same mistake twice. n=32
matches the extension batch that corrected it. Cost ≈ 25 minutes.

**Support-coverage diagnostic, reported not assumed.** The record must
state whether any *new* distinct turn value appeared in the final quarter
of the batch. If one did, the support is not covered and the record says
so rather than publishing a precision table as if it were.

### 4. Research record

`docs/superpowers/research/2026-08-02-phase2-cycle3-clean-baseline.md`,
following cycle 2's pattern: raw checkpoint path and checksum, conditions,
per-run table, aggregates, and a recompute script.

It must report:

- error rate (expected ~0; **if it is not near zero the fix failed** and
  the record says so)
- turn distribution and the support-coverage diagnostic above
- `minimum_n_for_precision` **with** the support-incompleteness caveat
  cycle 2's spec already wrote — and, if the distribution proves too thin
  for the bootstrap to be meaningful, a plain statement to that effect plus
  a binomial rate of longer-than-modal runs instead

### 5. Correct two records

**Cycle 2's research record** gets a third dated correction block: its turn
variance was ~95% environment friction, its 20 six-turn runs never ran a
test, and a pointer to this cycle's record. Its per-run table and checksums
are untouched — they are the raw material this cycle depended on.

**Phase 1's teaching record** gets a note where it describes workspace
provisioning: what was provisioned is a git repository, and the model's own
working environment was never in any Phase 1 cycle's scope. The n=16
evidence record notes the environment its result was produced under. The
result itself is not restated or re-litigated.

### 6. Pilot the cycle 4 check

Apply three questions to every quantitative claim in this cycle's record,
and record whether they caught anything:

1. Am I extrapolating outside the observed range?
2. What exactly does this number measure — the same units as whatever I am
   comparing it to?
3. Could a new sample contain a value mine never showed?

These come from the four derived-prose errors this session produced, none
of which any test caught. Cycle 4 designs the discipline; this cycle
supplies the evidence for whether it is worth having.

## Deliberate exclusions

| Excluded | Why |
|---|---|
| `PYTHONPATH` in `runner.py` | Addresses only the 22 test-import errors. The 43 install errors are the model *deciding* to install; no environment variable prevents a decision. |
| Giving the venv a working `pip` | Installs would then *succeed*, spending turns and context on pointless work — worse for measurement than erroring. |
| A workspace `conftest.py` | On cycle 5's refusal list; the grader cannot distinguish harness authorship from model authorship. |
| Error text on `ToolCall` | Raw stdout retains it; truncation cannot classify; no routine consumer. |
| Cheaper task slice | Withdrawn twice; see "What this cycle is not". |
| Re-running Phase 1 under new conditions | Phase 1 is complete and its record cites its own spec hash. |

## Concept budget

No new terms. `tool_errors` aggregates two already-budgeted terms (*tool
call*, and `is_error` within it). "Environment" is used in its ordinary
sense and is not a defined mechanism.

## Testing

**`tool_errors`, synthetic, with the non-vacuity pin the semantics
require:** a stream mixing `is_error` `True`, `False`, and an unmatched
start must yield a count of the `True` values only — asserting the
unmatched call is *excluded* specifically, since counting it would be the
plausible wrong implementation.

**Against committed real data.** `tests/fixtures/phase1-n48-telemetry-summary.json`
holds only `turns` and `context_processed`, so it cannot pin error counts,
and extending it would change a checksum already recorded in
`tests/fixtures/README.md`. The available real-data pin is the committed
single-run stream `tests/fixtures/pi-run-0.82.0.jsonl`: `tool_errors == 0`
across its 5 tool calls, matching what the fixture README already states
("all matched, none errored"). That is a weak pin on its own — zero — which
is exactly why the synthetic mixed-outcome test above carries the
non-vacuity weight.

The 65-across-48-runs figure belongs to the **research record**, recomputed
by its committed script from the raw checkpoints, not to a repo test: the
raw checkpoints live outside git, so a test asserting it could not run on a
fresh clone. Stating that boundary is deliberate — it is the same split
cycle 2 used, where the fixture pins what a test can verify and the script
reproduces what only the raw data can show.

**Gates unchanged:** `uv run pytest tests/ && uv run ruff check . && uv run
pyrefly check`, plus strict Sphinx.

## Non-goals recap

No run-machinery changes, no cheaper slice, no new concepts, no re-claim of
Phase 1's number, and no design of the cycle 4 discipline. This cycle makes
the environment honest, measures what that does, and corrects the records
that taught otherwise.
