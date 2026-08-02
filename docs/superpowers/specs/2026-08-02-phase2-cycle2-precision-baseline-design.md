# Phase 2, Cycle 2 — Precision baseline: how many runs do you actually need

**Phase:** 2 — Measurement we can trust, cheaply enough to repeat
**Status:** design, awaiting plan

## Why this cycle

Cycle 1 built the instrument. This cycle answers the question that decides
whether the instrument is *usable*: how many runs does a claim need before
it's evidence rather than noise?

That question became urgent, not abstract, once two facts were measured
against the preserved n=16 checkpoint rather than assumed:

**Duration is real, and it is not general.** Per-run span, computed from
the delta between each run's first and last message-creation timestamp in
its captured `pi_stdout` (a lower bound — see the "Deliberate exclusions"
note on why this is a floor, not a true wall-clock figure):

| | min | median | max | total (n=16) |
|---|---|---|---|---|
| span (s) | 35.2 | 44.6 | 69.0 | 756.1 |

At the median, n=100 is **~74 minutes of model time alone** — before Pi
startup, workspace provisioning, or grading. This is specific to
`omlx/gemma-4-12B-it-MLX-8bit` on the owner's Apple Silicon Mac via MLX; it
does not generalize to a different model, quantization, or machine, and the
project has collaborators on lower-powered equipment who need to run **full
batches for their own claims** — not sanity-check a handful of runs, produce
their own measured results. A number this large, unqualified, would make
the engine owner-only in practice.

**`context_processed` is almost entirely explained by turn count.** Grouped
by turn count, the spread is ≤3.2%; across all 16 runs it is 2.25×. And
`tool_calls == turns - 1` in every one of the 16 runs, exactly. The one real
random variable is *how many turns the model takes*, observed as
6×9, 8×2, 9×3, 11×2 — nine of sixteen runs at the floor.

So the actual question — "how many runs to trust a number" — has a concrete
target: how many runs pin down the mean turn count (and, following from it,
`context_processed`) to a stated precision.

**Is n=16 itself enough to answer that? Tested, not assumed — and the
answer is no.** Three checks against the preserved data:

1. A leave-one-out jackknife on the mean turn count: dropping any single
   one of the 16 runs swings the mean between 7.20 and 7.53 — a 0.33-turn
   spread from removing one observation, against precision targets in the
   0.25–0.5 turn range this cycle considers below. The estimate is fragile
   to individual points already in hand.
2. Splitting the sample (first 8 runs vs. all 16) gives deceptively close
   bootstrap half-widths — but both subsets draw from the identical four
   observed values {6, 8, 9, 11}. Agreement between two samples that share
   the same support says nothing about whether that support is complete.
3. The decisive check: adding one *hypothetical* run at 20 turns (not
   implausible — the observed max already nearly doubled, from the floor
   of 6 to 11) to the 16-run sample **nearly doubles** the bootstrap
   half-width, at n=16 (0.844→1.625) and even at n=64 (0.438→0.828). No
   amount of resampling from 16 points protects against a tail those 16
   points haven't shown yet.

**Consequence: this cycle extends the baseline before trusting any
recommendation.** `harness/runner.py`'s `run_batch()` (cycle 14) already
does exactly this operation, unmodified. Owner-selected target: 32
additional real runs, bringing the combined sample to n=48.

**The extension writes to a *new* checkpoint, not literally onto the
preserved one — by design, not workaround.** `run_batch()` refuses when any
existing record's `conditions` don't exactly match the current ones, and
they don't: the preserved checkpoint's `harness_revision` is `ddc03b3`,
current HEAD is downstream of it, and the recorded `pi_command` embeds an
absolute path through `.worktrees/restructure/` that no longer resolves the
same way from this checkout. That refusal is cycle 13's batch-comparability
contract working correctly, not a bug to route around.

Verified before treating the two batches as comparable anyway: the only
`harness/` diff between `ddc03b3` and HEAD is (a) the pi-exit-veto
correction to `RunResult.accepted` and (b) a role-check guard added to
`_has_assistant_content`, used only by `preflight_model`. Neither touches
`_pi_command`, `_conditions`, or `run_agentclinic_phase1`'s invocation
logic. The extension file's content is confirmed byte-identical at both
the old worktree path and the current one (it has exactly one commit in
its history, cycle 8, never modified since). The task spec's SHA-256 is
unchanged. So the two checkpoints differ only in a git-revision string and
a recording artifact of which worktree ran them — not in what was actually
asked of the model — and the research record combines their turn-count and
`context_processed` data with this reasoning stated explicitly, rather than
silently.

## What this cycle is not

- **Not new *machinery*.** The 32-run extension uses `run_batch()` exactly
  as cycle 14 built it — no code changes to `runner.py`, `checkpoint.py`, or
  the batch. Extending the baseline is real model time, not a new
  mechanism.
- **Not a power analysis comparing two conditions.** There is only one
  condition on record — the existing AgentClinic Phase 1 task under fixed
  conditions. This cycle answers "how precisely can we pin down a mean from
  n runs," not "how many runs to detect a difference between condition A and
  B." That question is Backlog (the orchestration-cost experiment) and needs
  its own baseline-in-each-arm design when it's scheduled.
- **Not wall-clock instrumentation.** No new field on `RunTelemetry`, no
  timing code added to `harness/runner.py`. A contributor who wants their
  own real wall-clock figure can already get one by timing a single call to
  `run_agentclinic_phase1()` — one line, no new code. See "Deliberate
  exclusions."
- **Not cycle 3.** What (if anything) happens with the recommended n — a
  full batch, a cheaper task slice, adaptive stopping — is deliberately
  undecided until this cycle's evidence exists to decide it.

## Interface

```python
# harness/precision.py

def bootstrap_ci_halfwidth(
    sample: Sequence[float],
    n: int,
    confidence: float = 0.95,
    resamples: int = 10_000,
    seed: int | None = None,
) -> float:
    """Estimated half-width of a `confidence` CI on the mean of `n` future
    draws from the population `sample` was drawn from.

    Bootstrap: draw `n` values with replacement from `sample`, take the
    mean; repeat `resamples` times; return half the width of the central
    `confidence` interval of the resulting distribution of means.
    """


def minimum_n_for_precision(
    sample: Sequence[float],
    target_halfwidth: float,
    confidence: float = 0.95,
    resamples: int = 10_000,
    max_n: int = 1000,
    seed: int | None = None,
) -> int | None:
    """Smallest n <= max_n whose bootstrap_ci_halfwidth(sample, n, ...) is
    <= target_halfwidth. None if max_n is reached without satisfying it.

    Assumes bootstrap_ci_halfwidth is non-increasing in n (verified by
    test, not just assumed) and searches accordingly: doubling to find an
    n that satisfies the target, then binary search between the last
    failing n and the first succeeding one. A linear scan from n=1 would
    be correct but slow at max_n in the hundreds.
    """


def leave_one_out_spread(sample: Sequence[float]) -> float:
    """max - min of the sample mean recomputed with each single element
    dropped in turn. A stability diagnostic, not a CI: a sample whose mean
    swings a lot when any one point is removed is fragile evidence,
    independent of what any bootstrap half-width reports about it.
    """
```

All three functions are pure, stdlib-only (`random`, `statistics`), and
generic over any numeric sample — not specific to turn counts. The research
record (see below) applies them to the combined turn-count sample and the
combined `context_processed` sample (16 preserved + 32 extended = 48 each).

## Methodology, and its honest limits

**Why bootstrap, not a classical formula.** The observed turn-count sample
is small (n=16), discrete, and visibly not normal (6×9, 8×2, 9×3, 11×2 —
a spike at the floor, not a bell curve). A classical `n = (z·σ/E)²` formula
would silently assume normality this data doesn't have. The bootstrap makes
no distributional assumption beyond "future runs are drawn from the same
population this sample represents."

**What "precision," not "power," means here.** This cycle asks how tightly
n runs can pin down *one* mean — not how many runs are needed to detect a
difference between two conditions (that needs a two-arm design and doesn't
exist yet; see "What this cycle is not"). A rough translation for the
research record: to reliably distinguish a future condition whose true mean
differs by D, a half-width comfortably under D/2 is a reasonable target —
stated as a documented judgment call, not a derived fact, when the research
record picks concrete thresholds.

**The limitation the bootstrap does not remove, stated plainly.** Resampling
with replacement from only 16 unique turn-count values cannot produce a
value outside {6, 8, 9, 11}. For n far larger than 16, this understates the
true sampling variability somewhat — a known property of the bootstrap with
small original samples, not a bug in the implementation. The research record
must state this rather than present a recommended n as exact.

**External validity, stated plainly.** The turn-count relationship is
measured from one task (AgentClinic Phase 1) and one model
(`omlx/gemma-4-12B-it-MLX-8bit`) — n=48 after this cycle's extension, up
from 16. Whether it holds for a different task or model is unmeasured, not
assumed.

**The stability check is a required step, not a footnote.** Before the
research record reports any recommended n, it reports
`leave_one_out_spread` on the n=48 combined sample and states plainly
whether it has tightened relative to the n=16 figure (0.33 turns). If it
hasn't tightened meaningfully, the honest conclusion is that n=48 *also*
isn't enough to trust a recommendation, and the research record says so
rather than reporting a number anyway.

## Applying it to real data

`docs/superpowers/research/2026-08-02-phase2-cycle2-precision-baseline.md`
(new) records, reproducibly:

- The per-run table (turns, tool calls, `context_processed`, span) for all
  48 runs (16 preserved + 32 extended) — recomputed from both checkpoints by
  a committed script reference, not retyped by hand.
- The stability check: `leave_one_out_spread` on the n=48 combined sample,
  compared plainly against the n=16 figure (0.33 turns) that motivated the
  extension.
- `minimum_n_for_precision` applied to turn counts and to `context_processed`,
  at 95% confidence, for three candidate target half-widths: 1.0 turn (a
  coarse, cheap baseline), 0.5 turns (distinguishes a one-turn shift with
  reasonable margin, per the D/2 rule of thumb above), and 0.25 turns (tight
  enough to distinguish a half-turn shift). Three rows, not a sweep — enough
  to show the shape of the cost/precision tradeoff without inventing a
  report format.
- The recommendation expressed **in runs, not minutes** — the number a
  contributor on any hardware can use, paired with the one-line timing
  command from "Deliberate exclusions" so they compute their own real-world
  budget from their own machine.
- Both raw checkpoints' durable locations and checksums, mirroring cycle
  16's evidence-record pattern. The original n=16 checkpoint
  (`docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md`
  named `/tmp/satyrn-cycle14-checkpoint-v2.jsonl` as its source, noting
  `/tmp` is transient) has since been copied, checksum-verified before and
  after, to `~/local-ai-pi-evidence/satyrn-cycle14-checkpoint-v2.jsonl`.
  The extension's 32 runs land at
  `~/local-ai-pi-evidence/satyrn-phase2-cycle2-extension-n32.jsonl` from
  the start — never `/tmp`.
- Any operational finding from actually running the extension batch (for
  example, environment drift the liveness check catches) belongs here as
  an operational note, not in this spec.

## A dependency worth naming

This cycle's real fixture is 48 numbers (turn count, `context_processed`),
not the megabytes of raw `pi_stdout` those numbers were computed from — a
smaller, safely-committable derivative of cycle 1's fixture pattern. But the
*research record's* claims about the real batches (the per-run table, the
provenance) remain traceable only as long as both raw checkpoints survive
somewhere. Neither lives in `/tmp`, but neither is archived anywhere
durable-by-design either (no backup policy, single copy each). If either is
lost, the 48-number fixture below remains provable forever; the research
record's narrative around it would not be independently re-verifiable.

## Deliberate exclusions

| Excluded | Why |
|---|---|
| Wall-clock instrumentation in `harness/runner.py` | No new field, no new code: `import time; start = time.monotonic(); run_agentclinic_phase1(); print(time.monotonic() - start)` gets a contributor their own real wall-clock figure for one run, on their own hardware, today. Building dedicated tooling for something one line already does would be machinery ahead of its contract — and it would touch the run/batch machinery cycle 1 deliberately left untouched, for no gain over the one-liner. |
| Two-arm power analysis | No second condition exists yet. Revisit when the orchestration-cost experiment (Backlog) or any other comparison is actually scheduled. |
| A parametric (non-bootstrap) model of turn count | Would need to assume a distribution shape this data doesn't visibly have (Poisson-like floor-spike, not normal). The bootstrap avoids the assumption at the cost of the small-sample understatement noted above — an honest trade, not a free one. |
| Deciding cycle 3 | This cycle produces the number; what to do with it — run a full batch, build a cheaper task slice, adaptive stopping — is Backlog until this evidence exists. |

## Testing

**Synthetic, with known ground truth — TDD, not vacuity.**

- A zero-variance sample (`[5.0] * 20`): `bootstrap_ci_halfwidth` must be
  `0.0` at any `n`, and `minimum_n_for_precision` must return the smallest
  allowed n for any positive target — not merely "doesn't raise."
- Half-width must be **verified non-increasing in `n`** on a synthetic
  sample with real spread (not assumed — this is the property
  `minimum_n_for_precision`'s search strategy depends on).
- **Self-consistency, the non-vacuity pin for the search function:** the n
  `minimum_n_for_precision` returns must itself satisfy
  `bootstrap_ci_halfwidth(sample, n, ...) <= target_halfwidth` when checked
  directly — not just "returned an int." A search bug that returns the
  wrong n would pass a test that only checked the return type.
- **Unreachable target returns `None` specifically**, asserted with
  `is None` — a search that silently returned `max_n` instead would also
  "not raise," and would be wrong in exactly the way that matters, mirroring
  cycle 1's named non-vacuity trap.
- Determinism: same `seed` produces the same result, so the test suite isn't
  flaky and results are reproducible in the research record.
- **`leave_one_out_spread`:** `0.0` on a constant sample; a hand-computed
  small example (3–4 values worked out by hand) pinned as a regression
  value, not just "returns a float."
- **Real data, as a small committed fixture** —
  `tests/fixtures/phase1-n48-telemetry-summary.json`: the 48 `(turns,
  context_processed)` pairs derived from the two combined checkpoints (16
  preserved + 32 extended), with provenance recorded in
  `tests/fixtures/README.md` alongside the existing `pi-run-0.82.0.jsonl`
  entry. Small and safe to commit, unlike the raw streams — this is derived
  numbers, not model output. Tests apply `minimum_n_for_precision` and
  `leave_one_out_spread` to this real fixture and assert the result is a
  concrete, previously-computed value (a regression pin on the actual
  finding), not just "returns without error."

## Concept budget

No new project-specific term. "Bootstrap," "confidence interval," and
"half-width" are standard statistical vocabulary a contributor with any
quantitative background already carries — not jargon this project is
coining, in the sense the budget exists to track (compare `seam` or
`hermetic`, which name project-specific concepts with no standard meaning
outside it). "Precision baseline" is used descriptively in this doc's title
and is not treated as a defined term requiring a table row.

## Non-goals recap

No new machinery — the baseline extension runs unmodified `run_batch()`, no
new `RunTelemetry` field, no wall-clock instrumentation, no two-arm
comparison, no decision about cycle 3. This cycle produces one small pure
module, its tests, thirty-two additional real runs, and a research record
applying the module to the combined batch.
