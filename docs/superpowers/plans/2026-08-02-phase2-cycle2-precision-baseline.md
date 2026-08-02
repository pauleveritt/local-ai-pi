# Precision Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `harness/precision.py` — a pure bootstrap-precision module answering "how many runs does a claim need before it's evidence" — and apply it to a real, verified n=48 sample (16 preserved + 32 freshly run) to produce a committed research record with an honest, hardware-independent recommendation.

**Architecture:** One new module (`bootstrap_ci_halfwidth`, `minimum_n_for_precision`, `leave_one_out_spread`), proven first against synthetic samples with known ground truth (TDD), then applied to a small committed real-data fixture derived from two checkpoints already run. A small committed script recomputes the research record's per-run table from the raw checkpoints, so the record's claims are reproducible, not retyped by hand.

**Tech Stack:** Python 3.14, stdlib only (`random`, `statistics`). pytest, ruff, pyrefly, Sphinx (`-W`).

**Spec:** [`docs/superpowers/specs/2026-08-02-phase2-cycle2-precision-baseline-design.md`](../specs/2026-08-02-phase2-cycle2-precision-baseline-design.md) (approved, Fable-reviewed with 8 fixes already applied).

## Global Constraints

- **Zero changes to `harness/runner.py`, `harness/checkpoint.py`, or the batch.** The 32-run extension already happened using unmodified `run_batch()`; this plan adds one new module and documentation only.
- **`harness/precision.py` is pure and stdlib-only** — no dependency on `harness.telemetry` or any other project module. Generic over any numeric sample.
- **All three functions are proven synthetically first, with known ground truth — non-vacuity, not "doesn't raise."** Every synthetic test in this plan has a hand- or script-verified expected value; none asserts only that a call succeeded.
- **Real data is committed as small derived numbers, not raw `pi_stdout`.** The fixture is 48 `{"turns": int, "context_processed": int}` objects — kilobytes, not megabytes.
- **Quality gates, every task:** `uv run pytest tests/ && uv run ruff check . && uv run pyrefly check` (see cycle 1's plan for why `tests/` is qualified — `.worktrees/` is now excluded via `norecursedirs`, so the bare `uv run pytest` should also work, but `tests/` is used throughout this plan to match established habit).
- **Strict docs build must stay clean:** `uv run --group docs sphinx-build -W -b html docs docs/_build/html`.
- **Two raw checkpoints already exist, verified, outside git:**
  - `~/local-ai-pi-evidence/satyrn-cycle14-checkpoint-v2.jsonl` — 16 records, SHA-256 `ef0a7b9fc80b8c33fbe619ecf6fbef03edd98fad2209431b4af6febee1c26c8e`, `harness_revision` `ddc03b36329807088d1fc5875f38e6fcccc22bc6`.
  - `~/local-ai-pi-evidence/satyrn-phase2-cycle2-extension-n32.jsonl` — 32 records, SHA-256 `66acdc5a272a45a8e94e040594e7e6821597944ea686bb98cf39d098a07edcce`, `harness_revision` matching commit `99e07a9` (the "docs(phase2-cycle2): precision baseline design spec" commit) — verified non-behaviorally different from `ddc03b3` (see the spec's "Why this cycle").
  - All 48 runs: `accepted=True`, `returncode=0`, `timed_out=False`.

## File Structure

| File | Responsibility |
|---|---|
| `harness/precision.py` (create) | `bootstrap_ci_halfwidth`, `minimum_n_for_precision`, `leave_one_out_spread`. The whole statistical core. |
| `tests/test_precision.py` (create) | Synthetic ground-truth proof, then real-fixture regression pins. |
| `tests/fixtures/phase1-n48-telemetry-summary.json` (create) | The 48 real `(turns, context_processed)` pairs, checkpoint order. |
| `tests/fixtures/README.md` (modify) | Provenance entry for the new fixture. |
| `docs/superpowers/research/2026-08-02-phase2-cycle2-recompute-summary.py` (create) | Small script recomputing the per-run table from the two raw checkpoints. Not a test; a reproducibility aid the research record cites. |
| `docs/superpowers/research/2026-08-02-phase2-cycle2-precision-baseline.md` (create) | The research record: per-run table, stability findings, precision recommendation, provenance. |
| `ROADMAP.md` (modify) | Cycle 2 row in the Phase 2 feature cycles table. |
| `docs/superpowers/index.md` (modify) | Cycle 2 row in the Phase 2 development-record table; new research doc wired into the toctree. |

## Verified Facts, So the Plan's Numbers Aren't Re-Derived Mid-Task

Every number below was computed and independently sanity-checked before this plan was written. Steps that use them do not need to recompute anything — they exist to catch a regression, not to discover a value.

**Synthetic reference values** (all with `resamples=10_000`, the module's default):

- `bootstrap_ci_halfwidth([5.0]*20, n, seed=0)` is exactly `0.0` at `n` in `{1, 5, 20, 100}`.
- `minimum_n_for_precision([5.0]*20, target_halfwidth=0.1, seed=0)` is exactly `1`.
- `leave_one_out_spread([1, 2, 3, 4])` is exactly `1.0` (leave-one-out means: 3.0, 2.6̄, 2.3̄, 2.0 → spread 1.0).
- `leave_one_out_spread([5.0]*20)` is exactly `0.0`.
- For `sample = list(range(1, 21))` (1..20) and `seed=0`, `bootstrap_ci_halfwidth` at doublings 1, 2, 4, 8, 16, 32, 64 is: `9.5, 8.0, 5.5, 4.0, 2.8125, 1.984375, 1.421875` — strictly decreasing.
- `minimum_n_for_precision(list(range(1, 21)), target_halfwidth=2.0, seed=0)` is exactly `31`; `bootstrap_ci_halfwidth(list(range(1, 21)), 31, seed=0) == 2.0` exactly (the boundary), and at `n=30` it is `2.05` (> target, confirming 31 is the true minimum, not an off-by-one).
- `minimum_n_for_precision(list(range(1, 21)), target_halfwidth=0.5, max_n=4, seed=0)` is exactly `None` (halfwidths at n=1,2,4 are 9.5, 8.0, 5.5 — none reach 0.5, and doubling past `max_n=4` triggers the `None` return).

**Real n=48 reference values** (16 preserved + 32 extended, `resamples=10_000`, `seed=0`):

- Turn-count distribution: `{6: 20, 8: 9, 9: 7, 10: 4, 11: 7, 12: 1}`. Mean `8.0` exactly (up from `7.4375` at n=16).
- `context_processed`: min `12804`, max `31710`, mean `19097.208333333332`.
- `tool_calls == turns - 1` holds for all 48 runs, exactly.
- All 336 tool calls across 48 runs: `{bash: 137, write: 199}`. All 65 errors are `bash`; no `write` errors.
- `leave_one_out_spread(turns_16)` is `0.33333333333333304`; `leave_one_out_spread(turns_48)` is `0.12765957446808418` — a 61.7% reduction.
- `leave_one_out_spread(context_processed_48)` is `402.2553191489351`.
- `minimum_n_for_precision(turns_48, target_halfwidth=1.0, seed=0)` is `14`.
- `minimum_n_for_precision(turns_48, target_halfwidth=0.5, seed=0)` is `56`.
- `minimum_n_for_precision(turns_48, target_halfwidth=0.25, seed=0)` is `237`.
- `minimum_n_for_precision(context_processed_48, target_halfwidth=1500, seed=0)` is `64`.
- `minimum_n_for_precision(context_processed_48, target_halfwidth=1000, seed=0)` is `144`.
- `minimum_n_for_precision(context_processed_48, target_halfwidth=500, seed=0)` is `None` (unreachable within `max_n=1000`).
- Adding one hypothetical run at 20 turns to the n=48 sample: `bootstrap_ci_halfwidth` at n=16 goes `0.9375 → 1.28125` (×1.37); at n=48, `0.5416666666666665 → 0.7291666666666666` (×1.35) — versus roughly ×2 at n=16 alone. Improved, not eliminated.
- `context_processed` spread within each turn-count group, n=48 (was ≤3.2% at n=16, for the groups that existed then): 6 turns (n=20) 3.2%, 8 turns (n=9) 6.8%, 9 turns (n=7) 0.4%, 10 turns (n=4) 1.3%, 11 turns (n=7) 1.0%, 12 turns (n=1) — undefined (single value).

**Full 48-row table** (turns, tool calls by name, errors, `context_processed`, message-creation-timestamp span in seconds, `complete`) is reproduced by Task 3's script; the exact values are not retyped here to avoid a second hand-copied source of truth — Task 3 verifies the script's output against the summary above.

---

### Task 1: `harness/precision.py` — synthetic-proven core

**Files:**
- Create: `harness/precision.py`
- Test: `tests/test_precision.py`

**Interfaces:**
- Consumes: nothing. `random`, `statistics`, `collections.abc.Sequence` only.
- Produces: `bootstrap_ci_halfwidth(sample, n, confidence=0.95, resamples=10_000, seed=None) -> float`; `minimum_n_for_precision(sample, target_halfwidth, confidence=0.95, resamples=10_000, max_n=1000, seed=None) -> int | None`; `leave_one_out_spread(sample) -> float`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_precision.py`:

```python
from harness.precision import (
    bootstrap_ci_halfwidth,
    leave_one_out_spread,
    minimum_n_for_precision,
)

ZERO_VARIANCE = [5.0] * 20
SPREAD_1_TO_20 = list(range(1, 21))


def test_zero_variance_sample_has_zero_halfwidth_at_any_n():
    for n in (1, 5, 20, 100):
        assert bootstrap_ci_halfwidth(ZERO_VARIANCE, n, seed=0) == 0.0


def test_zero_variance_sample_needs_only_the_smallest_allowed_n():
    assert minimum_n_for_precision(ZERO_VARIANCE, target_halfwidth=0.1, seed=0) == 1


def test_halfwidth_decreases_across_doublings_on_a_spread_sample():
    # Not adjacent-n monotonicity (resampling noise can produce tiny local
    # upticks there) -- across doublings, the ~1/sqrt(n) trend dominates.
    halfwidths = [
        bootstrap_ci_halfwidth(SPREAD_1_TO_20, n, seed=0)
        for n in (1, 2, 4, 8, 16, 32, 64)
    ]
    assert halfwidths == [9.5, 8.0, 5.5, 4.0, 2.8125, 1.984375, 1.421875]
    assert halfwidths == sorted(halfwidths, reverse=True)


def test_minimum_n_self_consistency_the_returned_n_actually_satisfies_target():
    # The non-vacuity pin for the search: returning the wrong n would pass
    # a test that only checked the return type.
    n = minimum_n_for_precision(SPREAD_1_TO_20, target_halfwidth=2.0, seed=0)
    assert n == 31
    assert bootstrap_ci_halfwidth(SPREAD_1_TO_20, n, seed=0) == 2.0
    assert bootstrap_ci_halfwidth(SPREAD_1_TO_20, n - 1, seed=0) > 2.0


def test_unreachable_target_returns_none_specifically():
    # A search that silently returned max_n instead would also "not
    # raise," and would be wrong in exactly the way that matters.
    result = minimum_n_for_precision(
        SPREAD_1_TO_20, target_halfwidth=0.5, max_n=4, seed=0
    )
    assert result is None


def test_same_seed_produces_the_same_result():
    a = bootstrap_ci_halfwidth(SPREAD_1_TO_20, 10, seed=42)
    b = bootstrap_ci_halfwidth(SPREAD_1_TO_20, 10, seed=42)
    assert a == b == 3.55


def test_leave_one_out_spread_matches_a_hand_computed_example():
    # drop 1 -> mean(2,3,4)=3.0; drop 2 -> mean(1,3,4)=2.667;
    # drop 3 -> mean(1,2,4)=2.333; drop 4 -> mean(1,2,3)=2.0
    # spread = 3.0 - 2.0 = 1.0
    assert leave_one_out_spread([1, 2, 3, 4]) == 1.0


def test_leave_one_out_spread_is_zero_for_a_constant_sample():
    assert leave_one_out_spread(ZERO_VARIANCE) == 0.0
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run pytest tests/test_precision.py -v
```

Expected: 8 errors, `ModuleNotFoundError: No module named 'harness.precision'`.

- [ ] **Step 3: Write the implementation**

Create `harness/precision.py`:

```python
"""Precision analysis over a numeric sample: how many future draws are
needed to pin down the mean to a stated confidence-interval half-width.

Bootstrap-based, not a classical formula. The samples this module was
built to analyze are small, discrete, and visibly not normal -- a
floor-spike distribution, not a bell curve. The bootstrap makes no
distributional assumption beyond "future draws come from the same
population `sample` represents."

Resampling with replacement from a sample of size m cannot produce a
value the sample never contained. For n far larger than m, this
understates the true sampling variability -- a known property of the
bootstrap with a small original sample, not a bug here. Treat a
reported half-width as optimistic, not exact, once n approaches or
exceeds the original sample size by a large factor.
"""

import random
import statistics
from collections.abc import Sequence


def bootstrap_ci_halfwidth(
    sample: Sequence[float],
    n: int,
    confidence: float = 0.95,
    resamples: int = 10_000,
    seed: int | None = None,
) -> float:
    """Estimated half-width of a `confidence` CI on the mean of `n` future
    draws from the population `sample` was drawn from.

    Draws `n` values with replacement from `sample`, takes the mean;
    repeats `resamples` times; returns half the width of the central
    `confidence` interval of the resulting distribution of means.
    """
    rng = random.Random(seed)
    means = sorted(
        statistics.fmean(rng.choice(sample) for _ in range(n))
        for _ in range(resamples)
    )
    lo = int((1 - confidence) / 2 * resamples)
    hi = int((1 + confidence) / 2 * resamples) - 1
    return (means[hi] - means[lo]) / 2


def minimum_n_for_precision(
    sample: Sequence[float],
    target_halfwidth: float,
    confidence: float = 0.95,
    resamples: int = 10_000,
    max_n: int = 1000,
    seed: int | None = None,
) -> int | None:
    """Smallest n, 1 <= n <= max_n, whose bootstrap_ci_halfwidth(sample,
    n, ...) is <= target_halfwidth. None if max_n is reached without
    satisfying it.

    Searches by doubling from n=1 to find an n that satisfies the
    target, then binary search between the last failing n and the first
    succeeding one -- relies on bootstrap_ci_halfwidth's ~1/sqrt(n)
    trend, not strict monotonicity at every adjacent n (resampling
    noise can produce tiny local upticks there). The returned n is
    checked directly against the target inside the search, not merely
    inferred from it.
    """
    n = 1
    while bootstrap_ci_halfwidth(sample, n, confidence, resamples, seed) > target_halfwidth:
        n *= 2
        if n > max_n:
            return None
    lo, hi = n // 2, n
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if bootstrap_ci_halfwidth(sample, mid, confidence, resamples, seed) <= target_halfwidth:
            hi = mid
        else:
            lo = mid
    return hi


def leave_one_out_spread(sample: Sequence[float]) -> float:
    """max - min of the sample mean recomputed with each single element
    dropped in turn. A stability diagnostic, not a CI: a sample whose
    mean swings a lot when any one point is removed is fragile evidence,
    independent of what any bootstrap half-width reports about it.
    """
    sample = list(sample)
    means = [
        statistics.fmean(sample[:i] + sample[i + 1 :]) for i in range(len(sample))
    ]
    return max(means) - min(means)
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run pytest tests/test_precision.py -v
```

Expected: 8 passed.

- [ ] **Step 5: Run the full gates**

```bash
uv run pytest tests/ && uv run ruff check . && uv run pyrefly check
```

Expected: 92 passed, 1 skipped (84 from before this cycle + 8 new); ruff `All checks passed!`; pyrefly `0 errors`.

- [ ] **Step 6: Commit**

```bash
git add harness/precision.py tests/test_precision.py
git commit -m "feat(precision): bootstrap precision, minimum-n search, and a stability diagnostic"
```

---

### Task 2: Real fixture and regression pins against the n=48 batch

**Files:**
- Create: `tests/fixtures/phase1-n48-telemetry-summary.json`
- Modify: `tests/fixtures/README.md`
- Test: `tests/test_precision.py`

**Interfaces:**
- Consumes: `bootstrap_ci_halfwidth`, `minimum_n_for_precision`, `leave_one_out_spread` from Task 1 — signatures unchanged.
- Produces: no new names. A committed fixture and tests that pin real-data findings.

- [ ] **Step 1: Create the fixture**

Create `tests/fixtures/phase1-n48-telemetry-summary.json` with this exact content (48 objects, checkpoint order: the 16 preserved runs first, then the 32 extended runs):

```json
[
  {"turns": 6, "context_processed": 13212},
  {"turns": 9, "context_processed": 22188},
  {"turns": 11, "context_processed": 28557},
  {"turns": 6, "context_processed": 12884},
  {"turns": 8, "context_processed": 19501},
  {"turns": 6, "context_processed": 12894},
  {"turns": 8, "context_processed": 19419},
  {"turns": 6, "context_processed": 12896},
  {"turns": 9, "context_processed": 22224},
  {"turns": 11, "context_processed": 28830},
  {"turns": 6, "context_processed": 12896},
  {"turns": 6, "context_processed": 12990},
  {"turns": 6, "context_processed": 12948},
  {"turns": 6, "context_processed": 12804},
  {"turns": 6, "context_processed": 12918},
  {"turns": 9, "context_processed": 22205},
  {"turns": 10, "context_processed": 25084},
  {"turns": 8, "context_processed": 18317},
  {"turns": 6, "context_processed": 12982},
  {"turns": 12, "context_processed": 31710},
  {"turns": 6, "context_processed": 12862},
  {"turns": 8, "context_processed": 19377},
  {"turns": 9, "context_processed": 22279},
  {"turns": 8, "context_processed": 19591},
  {"turns": 9, "context_processed": 22239},
  {"turns": 11, "context_processed": 28639},
  {"turns": 10, "context_processed": 24998},
  {"turns": 11, "context_processed": 28635},
  {"turns": 8, "context_processed": 18587},
  {"turns": 10, "context_processed": 25091},
  {"turns": 6, "context_processed": 12850},
  {"turns": 6, "context_processed": 12862},
  {"turns": 6, "context_processed": 12868},
  {"turns": 6, "context_processed": 12908},
  {"turns": 6, "context_processed": 12912},
  {"turns": 6, "context_processed": 12934},
  {"turns": 10, "context_processed": 25322},
  {"turns": 8, "context_processed": 18316},
  {"turns": 6, "context_processed": 12950},
  {"turns": 6, "context_processed": 12858},
  {"turns": 9, "context_processed": 22228},
  {"turns": 8, "context_processed": 18349},
  {"turns": 9, "context_processed": 22206},
  {"turns": 11, "context_processed": 28690},
  {"turns": 11, "context_processed": 28849},
  {"turns": 6, "context_processed": 12874},
  {"turns": 8, "context_processed": 18316},
  {"turns": 11, "context_processed": 28617}
]
```

- [ ] **Step 2: Get the fixture's checksum**

```bash
shasum -a 256 tests/fixtures/phase1-n48-telemetry-summary.json
```

Expected: `140680ed8a16b57e29bcfbd795f520c3387f6d664789ba3c8f46b85806a8f0ad` if the file matches Step 1 exactly (2-space JSON indent, trailing newline). If it differs, the file's formatting drifted from what's specified above — fix the formatting rather than accepting a different checksum, since Step 3 records this exact value.

- [ ] **Step 3: Add fixture provenance to `tests/fixtures/README.md`**

Append after the existing `pi-run-0.82.0.jsonl` section (the file currently ends after its "What it cannot test" paragraph):

```markdown

## `phase1-n48-telemetry-summary.json`

48 `{"turns": int, "context_processed": int}` pairs — the derived
telemetry summary of every run in two real batches, not raw model
output. In checkpoint order: the 16 preserved runs from the supervised
n=16 batch, then 32 more run specifically to extend this baseline
(Phase 2 cycle 2).

**Provenance.** Computed via `harness.telemetry.read_telemetry` from:

- `~/local-ai-pi-evidence/satyrn-cycle14-checkpoint-v2.jsonl` (16 records,
  SHA-256 `ef0a7b9fc80b8c33fbe619ecf6fbef03edd98fad2209431b4af6febee1c26c8e`,
  the same checkpoint `pi-run-0.82.0.jsonl` above was extracted from).
- `~/local-ai-pi-evidence/satyrn-phase2-cycle2-extension-n32.jsonl` (32
  records, SHA-256
  `66acdc5a272a45a8e94e040594e7e6821597944ea686bb98cf39d098a07edcce`).

Both files are outside Git, per the same reasoning as the n=16 batch's raw
output (see `docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md`).
The full per-run detail (tool calls, errors, timing) and the reasoning for
treating the two checkpoints as one comparable batch are in
`docs/superpowers/research/2026-08-02-phase2-cycle2-precision-baseline.md`.

- Fixture SHA-256: `140680ed8a16b57e29bcfbd795f520c3387f6d664789ba3c8f46b85806a8f0ad`
- Turn-count distribution: 6×20, 8×9, 9×7, 10×4, 11×7, 12×1
- All 48 runs accepted, `returncode=0`, not timed out, `complete=True`
```

- [ ] **Step 4: Write the failing tests**

Append to `tests/test_precision.py`:

```python
import json
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "phase1-n48-telemetry-summary.json"


def _real_samples() -> tuple[list[int], list[int]]:
    records = json.loads(FIXTURE.read_text())
    turns = [r["turns"] for r in records]
    context_processed = [r["context_processed"] for r in records]
    return turns, context_processed


def test_real_fixture_has_48_records_and_the_expected_turn_distribution():
    turns, _ = _real_samples()
    assert len(turns) == 48
    from collections import Counter

    assert Counter(turns) == {6: 20, 8: 9, 9: 7, 10: 4, 11: 7, 12: 1}


def test_stability_tightened_from_n16_to_n48():
    # Non-vacuity: pins the *actual* finding that motivated running the
    # extension, not just "the function returns a float."
    turns, _ = _real_samples()
    turns_16 = turns[:16]
    assert leave_one_out_spread(turns_16) == 0.33333333333333304
    assert leave_one_out_spread(turns) == 0.12765957446808418


def test_context_processed_stability_at_n48():
    _, context_processed = _real_samples()
    assert leave_one_out_spread(context_processed) == 402.2553191489351


def test_minimum_n_for_turn_count_precision_at_n48():
    turns, _ = _real_samples()
    assert minimum_n_for_precision(turns, target_halfwidth=1.0, seed=0) == 14
    assert minimum_n_for_precision(turns, target_halfwidth=0.5, seed=0) == 56
    assert minimum_n_for_precision(turns, target_halfwidth=0.25, seed=0) == 237


def test_minimum_n_for_context_processed_precision_at_n48():
    _, context_processed = _real_samples()
    assert minimum_n_for_precision(context_processed, target_halfwidth=1500, seed=0) == 64
    assert minimum_n_for_precision(context_processed, target_halfwidth=1000, seed=0) == 144
    assert minimum_n_for_precision(context_processed, target_halfwidth=500, seed=0) is None
```

- [ ] **Step 5: Run the tests to verify they fail, then pass**

```bash
uv run pytest tests/test_precision.py -v
```

Expected first run: `FileNotFoundError` or similar on the fixture path if Step 1 wasn't done in this session, otherwise these 6 new tests should pass immediately since they pin already-verified real values — this step is a *regression pin*, not new-behavior TDD. If any assertion fails, the fixture content (Step 1) or the module (Task 1) has drifted from what was verified while writing this plan; do not adjust the expected values to match a wrong result without first re-deriving them independently.

Expected: 14 passed (8 from Task 1 + 6 new).

- [ ] **Step 6: Run the full gates**

```bash
uv run pytest tests/ && uv run ruff check . && uv run pyrefly check
```

Expected: 98 passed, 1 skipped; ruff clean; pyrefly 0 errors.

- [ ] **Step 7: Commit**

```bash
git add tests/fixtures/phase1-n48-telemetry-summary.json tests/fixtures/README.md tests/test_precision.py
git commit -m "test(precision): pin the n=48 stability and precision findings against a real fixture"
```

---

### Task 3: Research record and its recompute script

**Files:**
- Create: `docs/superpowers/research/2026-08-02-phase2-cycle2-recompute-summary.py`
- Create: `docs/superpowers/research/2026-08-02-phase2-cycle2-precision-baseline.md`
- Modify: `docs/superpowers/index.md`

**Interfaces:**
- Consumes: `harness.telemetry.read_telemetry` (existing); `harness.precision.*` from Tasks 1–2.
- Produces: nothing code depends on. A published record.

- [ ] **Step 1: Write the recompute script**

Create `docs/superpowers/research/2026-08-02-phase2-cycle2-recompute-summary.py`:

```python
"""Recompute this cycle's per-run table and aggregates from the two raw
checkpoints. Not a test -- a reproducibility aid the research record
cites, since its claims come from parsing pi_stdout via read_telemetry,
not from a trivial line count.

Usage (from the repo root, so `harness` is importable):
    PYTHONPATH=. uv run python \\
        docs/superpowers/research/2026-08-02-phase2-cycle2-recompute-summary.py \\
        ~/local-ai-pi-evidence/satyrn-cycle14-checkpoint-v2.jsonl \\
        ~/local-ai-pi-evidence/satyrn-phase2-cycle2-extension-n32.jsonl

The two raw checkpoints are outside Git (see tests/fixtures/README.md's
phase1-n48-telemetry-summary.json entry for their checksums); this script
cannot run without them.
"""

import json
import sys
from collections import Counter
from pathlib import Path

from harness.telemetry import read_telemetry


def message_span(pi_stdout: str) -> float | None:
    starts = []
    for line in pi_stdout.split("\n"):
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("type") == "message_start":
            ts = event.get("message", {}).get("timestamp")
            if ts is not None:
                starts.append(ts)
    if len(starts) < 2:
        return None
    return (max(starts) - min(starts)) / 1000.0


def load(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        tel = read_telemetry(data["pi_stdout"])
        rows.append(
            {
                "turns": tel.turns,
                "tool_calls": len(tel.tool_calls),
                "tool_names": Counter(tc.name for tc in tel.tool_calls),
                "errors": sum(1 for tc in tel.tool_calls if tc.is_error),
                "context_processed": tel.context_processed,
                "complete": tel.complete,
                "span": message_span(data["pi_stdout"]),
            }
        )
    return rows


def main(preserved_path: str, extension_path: str) -> None:
    rows = load(Path(preserved_path)) + load(Path(extension_path))
    for i, r in enumerate(rows, 1):
        tools = ",".join(f"{k}x{v}" for k, v in sorted(r["tool_names"].items()))
        print(
            f"{i:>2}: turns={r['turns']:>2} tools={r['tool_calls']:>2} ({tools:<14}) "
            f"errors={r['errors']} ctx={r['context_processed']:>6} "
            f"span={r['span']:.1f}s complete={r['complete']}"
        )
    turns = [r["turns"] for r in rows]
    ctx = [r["context_processed"] for r in rows]
    tools = sum((r["tool_names"] for r in rows), Counter())
    print()
    print("turn distribution:", dict(sorted(Counter(turns).items())))
    print("tool totals:", dict(tools))
    print("total errors:", sum(r["errors"] for r in rows))
    print("all complete:", all(r["complete"] for r in rows))
    print("context_processed min/max/mean:", min(ctx), max(ctx), sum(ctx) / len(ctx))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
```

- [ ] **Step 2: Run the script and verify its output matches the plan's verified facts**

```bash
PYTHONPATH=. uv run python \
  docs/superpowers/research/2026-08-02-phase2-cycle2-recompute-summary.py \
  ~/local-ai-pi-evidence/satyrn-cycle14-checkpoint-v2.jsonl \
  ~/local-ai-pi-evidence/satyrn-phase2-cycle2-extension-n32.jsonl
```

Expected: 48 rows; final summary lines showing `turn distribution: {6: 20, 8: 9, 9: 7, 10: 4, 11: 7, 12: 1}`, `tool totals: {'bash': 137, 'write': 199}`, `total errors: 65`, `all complete: True`, `context_processed min/max/mean: 12804 31710 19097.208333333332` — matching this plan's "Verified Facts" section exactly. If anything differs, stop: either a checkpoint file has changed since this plan was written, or the script has a bug — do not proceed to Step 3 with mismatched numbers.

- [ ] **Step 3: Write the research record**

Create `docs/superpowers/research/2026-08-02-phase2-cycle2-precision-baseline.md`:

```markdown
# Phase 2, Cycle 2 — Precision baseline

Verified 2026-08-02 against two checkpoints: the preserved n=16 supervised
batch, and 32 more runs executed specifically to extend it (see the
[design spec](../specs/2026-08-02-phase2-cycle2-precision-baseline-design.md)
for why the extension was necessary before trusting any recommendation).

## Raw checkpoints

| | Path | Records | SHA-256 |
|---|---|---|---|
| Preserved | `~/local-ai-pi-evidence/satyrn-cycle14-checkpoint-v2.jsonl` | 16 | `ef0a7b9fc80b8c33fbe619ecf6fbef03edd98fad2209431b4af6febee1c26c8e` |
| Extension | `~/local-ai-pi-evidence/satyrn-phase2-cycle2-extension-n32.jsonl` | 32 | `66acdc5a272a45a8e94e040594e7e6821597944ea686bb98cf39d098a07edcce` |

Neither lives in `/tmp` (the preserved one did, transiently, before being
copied out — see `docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md`).
Neither is committed to Git or archived elsewhere; this record and the
small derived fixture (`tests/fixtures/phase1-n48-telemetry-summary.json`)
are what survive if either is lost.

Recomputed by `2026-08-02-phase2-cycle2-recompute-summary.py`, alongside
this file.

## Why two checkpoints, treated as one batch

`run_batch()` refused to extend the preserved checkpoint directly — its
`conditions` (git revision, and an absolute extension path through
`.worktrees/restructure/`) no longer match the current checkout. Verified
before combining them anyway: the only `harness/` change between the
preserved checkpoint's revision and the extension's is the addition of
`harness/telemetry.py` (imported by nothing in `runner.py`) plus two
`runner.py` corrections (the pi-exit veto on `RunResult.accepted`, and a
role-check guard in `_has_assistant_content` used only by
`preflight_model`) — neither touches how `pi` is invoked. The extension
file is byte-identical at both paths. The task spec's SHA-256 is
unchanged. Full reasoning in the design spec.

## Conditions shared by all 48 records

| Field | Value |
|---|---|
| Model | `omlx/gemma-4-12B-it-MLX-8bit` |
| Pi version | `0.82.0` |
| Task-spec SHA-256 | `db17991e47b1b3dd5df18df08ff8939ed7924b81422a84cdb196dd0c51381c84` |
| Accepted | 48 of 48 |
| Pi return codes | all 0 |
| Timed out | none |
| `complete` (telemetry) | `True` for all 48 |

## Per-run table

Runs 1–16 are the preserved checkpoint; 17–48 are the extension. `tools`
is total tool calls (`turns - 1` in every row); `err` is how many of those
were `bash` errors (`write` never errored); `ctx` is `context_processed`;
`span` is seconds between the first and last `message_start` timestamp — a
lower bound on wall-clock, not a true duration (see `ROADMAP.md`'s Backlog
note on wall-clock timing).

| run | turns | tools | err | ctx | span(s) |
|---|---|---|---|---|---|
| 1 | 6 | 5 | 0 | 13212 | 35.2 |
| 2 | 9 | 8 | 2 | 22188 | 42.1 |
| 3 | 11 | 10 | 3 | 28557 | 53.1 |
| 4 | 6 | 5 | 0 | 12884 | 38.8 |
| 5 | 8 | 7 | 1 | 19501 | 51.4 |
| 6 | 6 | 5 | 0 | 12894 | 42.0 |
| 7 | 8 | 7 | 1 | 19419 | 49.5 |
| 8 | 6 | 5 | 0 | 12896 | 51.8 |
| 9 | 9 | 8 | 2 | 22224 | 59.7 |
| 10 | 11 | 10 | 3 | 28830 | 69.0 |
| 11 | 6 | 5 | 0 | 12896 | 41.8 |
| 12 | 6 | 5 | 0 | 12990 | 40.8 |
| 13 | 6 | 5 | 0 | 12948 | 39.6 |
| 14 | 6 | 5 | 0 | 12804 | 39.9 |
| 15 | 6 | 5 | 0 | 12918 | 47.1 |
| 16 | 9 | 8 | 2 | 22205 | 54.5 |
| 17 | 10 | 9 | 3 | 25084 | 45.1 |
| 18 | 8 | 7 | 2 | 18317 | 40.8 |
| 19 | 6 | 5 | 0 | 12982 | 41.2 |
| 20 | 12 | 11 | 4 | 31710 | 57.8 |
| 21 | 6 | 5 | 0 | 12862 | 44.1 |
| 22 | 8 | 7 | 1 | 19377 | 46.6 |
| 23 | 9 | 8 | 2 | 22279 | 67.8 |
| 24 | 8 | 7 | 1 | 19591 | 57.4 |
| 25 | 9 | 8 | 2 | 22239 | 61.9 |
| 26 | 11 | 10 | 3 | 28639 | 70.9 |
| 27 | 10 | 9 | 3 | 24998 | 58.2 |
| 28 | 11 | 10 | 3 | 28635 | 69.6 |
| 29 | 8 | 7 | 2 | 18587 | 50.3 |
| 30 | 10 | 9 | 3 | 25091 | 90.1 |
| 31 | 6 | 5 | 0 | 12850 | 39.8 |
| 32 | 6 | 5 | 0 | 12862 | 47.8 |
| 33 | 6 | 5 | 0 | 12868 | 67.8 |
| 34 | 6 | 5 | 0 | 12908 | 44.1 |
| 35 | 6 | 5 | 0 | 12912 | 43.9 |
| 36 | 6 | 5 | 0 | 12934 | 48.9 |
| 37 | 10 | 9 | 3 | 25322 | 45.5 |
| 38 | 8 | 7 | 2 | 18316 | 38.9 |
| 39 | 6 | 5 | 0 | 12950 | 35.6 |
| 40 | 6 | 5 | 0 | 12858 | 34.2 |
| 41 | 9 | 8 | 2 | 22228 | 40.1 |
| 42 | 8 | 7 | 2 | 18349 | 37.8 |
| 43 | 9 | 8 | 2 | 22206 | 40.0 |
| 44 | 11 | 10 | 3 | 28690 | 49.4 |
| 45 | 11 | 10 | 3 | 28849 | 50.1 |
| 46 | 6 | 5 | 0 | 12874 | 34.7 |
| 47 | 8 | 7 | 2 | 18316 | 38.2 |
| 48 | 11 | 10 | 3 | 28617 | 49.0 |

All 48 runs: `complete=True`. This table is real data, not retyped by
hand — it matches the recompute script's output exactly (Task 3 Step 2
verifies this).

## Aggregates

| Metric | n=16 (original) | n=48 (this cycle) |
|---|---|---|
| Mean turns | 7.4375 | 8.0 |
| Turn distribution | 6×9, 8×2, 9×3, 11×2 | 6×20, 8×9, 9×7, 10×4, 11×7, 12×1 |
| Distinct turn values | {6, 8, 9, 11} | {6, 8, 9, 10, 11, 12} |
| `tool_calls == turns - 1` | holds, all 16 | holds, all 48 |
| Tool errors | 14/103, all `bash` | 65/336, all `bash` |
| `context_processed` range | 12804–28830 | 12804–31710 |

**New turn-count values appeared: 10 and 12, neither seen in the original
16.** This is the concrete evidence that motivated the extension in the
first place — the n=16 sample's support was incomplete, not just noisy.

## Stability: did extending actually help?

| | n=16 | n=48 | change |
|---|---|---|---|
| `leave_one_out_spread` (turns) | 0.333 | 0.128 | −61.7% |
| Hypothetical +1 run at 20 turns, halfwidth ratio at n=16 | ×1.73 (0.938→1.625, unseeded estimate from the spec) | ×1.37 (seed=0) | improved |
| Hypothetical +1 run at 20 turns, halfwidth ratio at n=48/n=64 | — | ×1.35 (seed=0) | — |

The jackknife spread tightened substantially — a real, meaningful
improvement by the spec's own stated gate. The tail-sensitivity check also
improved: one hypothetical unseen run now moves the estimate by ~35%
rather than roughly doubling it.

**But read this alongside a second fact the spec's gate didn't explicitly
check: the mean itself moved by 0.5625 turns between n=16 and n=48** — larger
than two of the three candidate precision targets below (0.5 and 0.25).
The *estimate* got more stable; the *value it is converging toward* has
already moved by more than a 0.25-turn or 0.5-turn precision claim would
promise to resolve. This is not a contradiction of the tightening finding —
it is exactly what "n=16 was too thin" predicts — but it means: treat a
0.25-turn precision claim built from this n=48 sample with real skepticism
about whether even n=48 has converged, not just whether its own bootstrap
half-width looks small.

## How many runs do you need? (95% confidence, `seed=0`)

**Turn count:**

| Target half-width | Minimum n |
|---|---|
| 1.0 turn (coarse) | 14 |
| 0.5 turns | 56 |
| 0.25 turns (fine) | 237 |

**`context_processed`:**

| Target half-width | Minimum n |
|---|---|
| 1500 (coarse) | 64 |
| 1000 | 144 |
| 500 (fine) | not reachable within 1000 runs |

**Read in runs, not minutes, on purpose** — a contributor on any hardware
uses this table by timing one `run_agentclinic_phase1()` call on their own
machine (one line, no new tooling — see the design spec's "Deliberate
exclusions") and multiplying. On the owner's machine, the measured n=48
median span was **44.6 seconds** per run (min 34.2s, max 90.1s, total
2343.7s across all 48) — so n=56 is roughly 42 minutes of model time
there; elsewhere, it depends entirely on that machine's own one-run timing.

**n=48 already covers the coarsest target for both metrics.** It sits just
short of the middle turn-count target (56 vs. 48 in hand) and well short of
the finer ones. Whether closing that gap is worth another batch, versus
accepting a coarser precision target, versus a cheaper task slice, is
cycle 3's decision — not this cycle's (see the design spec, "Not cycle 3").

## Operational note: an environment drift the liveness check caught correctly

Running the extension batch hit two real failures before any run
succeeded, both caught by existing safeguards rather than producing a
silent bad result:

1. **The local `omlx` server wasn't running.** `preflight_model()` raised
   `ModelServerDown` before spending any batch time, per `BRIEF.md`'s
   explicit warning about this exact failure mode.
2. **After starting it, the server rejected requests with HTTP 401.**
   `~/.omlx/settings.json` had drifted to `"api_key": "evalkey"`,
   `"skip_api_key_verification": false` — no longer matching
   `harness/liveness.py`'s documented default (`"not-needed"`) or
   `BRIEF.md`'s stated environment. Resolved by resetting the server
   config back to `skip_api_key_verification: true` (the owner's choice,
   preferring to match the documented environment over changing harness
   code), verified via `curl` and then via `preflight_model()` itself
   before relaunching.

A third, unrelated failure came from this session's own process: a `git
commit` landed while the batch's first attempt was running in the
background. `run_batch()`'s `_conditions()` reads `git rev-parse HEAD`
live, so the commit invalidated every run still in flight —
`RuntimeError: run conditions changed during batch`, after 3 records had
already been appended under the pre-commit revision. Those 3 records were
discarded (not comparable to a fresh run under the new HEAD) and the
extension was relaunched cleanly, with no further commits until it
finished. Worth naming as an operational rule for any future batch: **do
not commit to the repository while a `run_batch()` call is in flight.**

## Verification method

Both checkpoints were parsed with `harness.telemetry.read_telemetry`
(already fixture-proven; see cycle 1) via the recompute script above, not
hand-aggregated. The precision analysis was performed with
`harness.precision` (this cycle), against the derived turn-count and
`context_processed` samples — both committed as
`tests/fixtures/phase1-n48-telemetry-summary.json` and pinned by
`tests/test_precision.py`.
```

- [ ] **Step 4: Wire the new research doc into the Sphinx toctree**

In `docs/superpowers/index.md`, find the Research section (a `## Research` heading with a bulleted list, followed by a hidden `{toctree}` block captioned "Research"). Add a bullet after the existing two:

```markdown
- [Phase 2 cycle 2 — precision baseline](research/2026-08-02-phase2-cycle2-precision-baseline.md)
```

And add the corresponding entry to the Research toctree block:

```
research/2026-08-02-phase2-cycle2-precision-baseline
```

The spec and plan documents are already wired into their toctrees (the
spec when it was committed; the plan immediately after it was written,
as part of finishing that writing-plans step — same discipline this
spec's own commit message named: "so the strict Pages build (-W) doesn't
regress the way cycle 1's did"). The Phase 2 development-record table's
cycle 2 row is added at cycle close, in Task 4, alongside `ROADMAP.md`'s
— not here, matching cycle 1's actual precedent (its docs/superpowers/index.md
row landed in the same commit as its `ROADMAP.md` row, not earlier).

- [ ] **Step 5: Verify the strict docs build**

```bash
uv run --group docs sphinx-build -W -b html docs docs/_build/html
```

Expected: `build succeeded.` — no `toc.not_included` warning for the new
research document.

- [ ] **Step 6: Run the full gates**

```bash
uv run pytest tests/ && uv run ruff check . && uv run pyrefly check
```

Expected: 98 passed, 1 skipped (no new tests this task); ruff clean; pyrefly 0 errors.

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/research/2026-08-02-phase2-cycle2-recompute-summary.py \
        docs/superpowers/research/2026-08-02-phase2-cycle2-precision-baseline.md \
        docs/superpowers/index.md
git commit -m "docs(phase2-cycle2): precision baseline research record"
```

---

### Task 4: Cycle close — `ROADMAP.md` and `docs/superpowers/index.md`

**Files:**
- Modify: `ROADMAP.md`
- Modify: `docs/superpowers/index.md`

**Interfaces:**
- Consumes: the finished module, fixture, and research record from Tasks 1–3.
- Produces: nothing code depends on.

- [ ] **Step 1: Add the cycle 2 row to `ROADMAP.md`**

In `ROADMAP.md`'s "Phase 2 feature cycles" table (added at cycle 1's close, currently holding only the cycle 1 row), append:

```markdown
| 2 | Precision baseline — `harness/precision.py` answers how many runs a claim needs before it's evidence: `bootstrap_ci_halfwidth`, `minimum_n_for_precision`, and a `leave_one_out_spread` stability diagnostic, proven against synthetic samples with known ground truth. Applied to a real n=48 sample (the preserved n=16 checkpoint plus 32 more runs executed specifically to extend it, after a jackknife check demonstrated n=16 wasn't yet trustworthy) — new turn-count values (10, 12) appeared that n=16 never showed, confirming the extension was necessary. Recommendation expressed in runs, not minutes, so it holds on any hardware. | [spec](docs/superpowers/specs/2026-08-02-phase2-cycle2-precision-baseline-design.md) | [plan](docs/superpowers/plans/2026-08-02-phase2-cycle2-precision-baseline.md) | Done |
```

- [ ] **Step 2: Add the matching row to `docs/superpowers/index.md`**

In the `## Phase 2` section's cycle table (the one with the cycle 1 "Telemetry reader" row — both the spec and plan links are already wired into their toctrees, from when each was written), append:

```markdown
| 2 | Precision baseline | [spec](specs/2026-08-02-phase2-cycle2-precision-baseline-design.md) | [plan](plans/2026-08-02-phase2-cycle2-precision-baseline.md) |
```

- [ ] **Step 3: No concept-budget change needed — confirm, don't skip**

The spec's own "Concept budget" section and Fable's review both concluded no new project-specific term is spent this cycle ("bootstrap," "confidence interval," "half-width" are standard vocabulary, not coined). Run a quick check that this judgment still holds after implementation — nothing in `harness/precision.py`'s actual public names (`bootstrap_ci_halfwidth`, `minimum_n_for_precision`, `leave_one_out_spread`) introduces a term beyond what the spec already named. No edit to the Concept budget table.

- [ ] **Step 4: Verify the strict docs build one more time**

```bash
uv run --group docs sphinx-build -W -b html docs docs/_build/html
```

Expected: `build succeeded.`

- [ ] **Step 5: Run the full gates one last time**

```bash
uv run pytest tests/ && uv run ruff check . && uv run pyrefly check
```

Expected: 98 passed, 1 skipped; ruff clean; pyrefly 0 errors.

- [ ] **Step 6: Commit**

```bash
git add ROADMAP.md docs/superpowers/index.md
git commit -m "docs(phase2-cycle2): close the precision baseline cycle"
```

## A note for the executor on git discipline during this plan

Nothing in this plan invokes `pi` or `run_batch()` — all real-batch work is already done and preserved outside the repo. The mid-session lesson recorded in Task 3's research record (don't commit while a batch runs) does not constrain this plan's own commits; it is recorded as an operational note for *future* cycles that run a live batch, not a rule this plan's tasks need to work around.
