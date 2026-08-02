# Phase 2 — plan for the remainder

Written 2026-08-02, after cycles 1 and 2 closed. This is a **planning
analysis awaiting owner review**, not an approved design. It recommends
what cycle 3 should be, and — more importantly — argues that one of the
three candidates cycle 2 left open should be closed on evidence rather
than built.

## Where Phase 2 stands

| Cycle | Built | State |
|---|---|---|
| 1 | `harness/telemetry.py` — turns, tool calls, tokens from captured `pi_stdout` | Done |
| 2 | `harness/precision.py` + an n=48 real baseline; how many runs a claim needs | Done |

Cycle 2's answer, at 95% confidence, on 48 real runs:

| Precision target (turn count) | Runs needed | Status |
|---|---|---|
| ±1.0 turn | 14 | already satisfied by the 48 in hand |
| ±0.5 turns | 56 | 8 runs short |
| ±0.25 turns | 237 | far off |

Cycle 2 deliberately left cycle 3 undecided, naming three candidates:
**nothing needed**, **a cheaper task slice**, or **adaptive stopping**.

## A finding that changes the choice

`ROADMAP.md` states Phase 2's direction as making measurement affordable —
"a slice small enough that n=100 is practical." That framing assumes the
lever is *task size*: a task that finishes in fewer turns should cost
proportionally less, making n=100 affordable, especially for collaborators
on much lower-powered hardware who need full batches for their own claims.

**Measured against the 48 real runs, that assumption does not hold up.**
Regressing in-stream span on turn count:

```
span = 22.9s + 3.2s per turn     R² = 0.300     residual spread 9.7s
```

Two things follow, and the second matters more than the first:

1. **Turn count explains only ~30% of run-time variance.** The
   fit is weak enough that the "22.9s fixed + 3.2s marginal" split should
   not be quoted as a decomposition — but the weakness *is itself* the
   finding. Whatever dominates run time, it is mostly not the number of
   turns. Median span by turn count bears this out: 6 turns → 41.5s,
   12 turns → 57.8s. Doubling the work adds under 40% to the clock.
2. **Therefore a cheaper task slice is a weak lever on cost.** Taking the
   fit at face value (generously, given its R²), a hypothetical 3-turn
   task would run ~33s against the current ~46s median — about **1.4×
   cheaper**, turning a 77-minute n=100 into ~54 minutes. For a
   collaborator 5× slower, that is 6.4 hours becoming 4.5 hours. It does
   not convert an impractical batch into a practical one, and it costs a
   new task spec, a new fixture pair, and a new acceptance suite to find
   out.

**This is the argument for closing the "cheaper task slice" candidate on
evidence rather than building it.** It was the most attractive of the
three on its face; the data does not support it.

## The gap that should be closed first

Every timing number this project has — including the ones above — is the
**in-stream span**: the delta between the first and last `message_start`
timestamp inside `pi_stdout`. That interval excludes Pi process startup,
workspace provisioning and `git init`, the grading pytest subprocess, and
the final message's generation tail (nothing after the last
`message_start` carries a timestamp).

So the honest position is: **nobody has measured what a run actually
costs end to end.** The 77-minute figure for n=100 is a floor built from a
partial measurement, and the fixed-versus-marginal question that decides
whether *any* cost work is worth doing cannot be answered from it.

## Recommended cycle 3 — measure the real cost floor

Small, cheap, and it is the evidence that decides everything after it.

**What it does.** Time `run_agentclinic_phase1()` end to end — wall clock,
including startup, provisioning, and grading — across a handful of runs
(≈5). Separately time a trivial single-turn Pi invocation (the shape
`preflight_model()` already uses) to isolate the per-run floor that no
task redesign can get below.

**What it produces.** An honest cost model: what one run costs, what
fraction is irreducible, and therefore what n=100 really costs here — plus
the one-line recipe a collaborator runs to get the same number for their
own hardware, expressed in runs rather than minutes, exactly as cycle 2's
record does.

**Why this and not more precision work.** It needs ~5 minutes of model
time, no new machinery, and no new concepts. And it converts the central
open question from an assumption into a measurement.

**What it decides.**

- If per-run cost is dominated by fixed overhead → the cheaper-slice
  candidate is closed for good, and Phase 2's affordability goal is either
  met as well as it can be, or redirects to fixed overhead (model load,
  prefill, process startup) rather than task design.
- If end-to-end cost *does* scale with turns, contrary to the in-stream
  evidence → the cheaper slice becomes viable again and gets specced as
  cycle 4, with this measurement as its justification.

## Deliberately not recommended

| Candidate | Why not |
|---|---|
| Cheaper task slice, now | The evidence above argues against it. Revisit only if cycle 3 overturns the in-stream finding. |
| Adaptive stopping | Optimizes the count of runs. If cost is dominated by per-run fixed overhead, that is the wrong axis — and with no live claim needing a specific precision, a stopping rule has no target to stop at. Machinery ahead of its contract. |
| Topping up to n=56 (8 runs, ~6 min) | Cheap enough to be tempting, which is the whole problem. ±0.5-turn precision is not *needed* by any claim currently on the table; buying it because it is affordable is exactly the reasoning `BRIEF.md` warns against. Trivial to do later if a claim ever requires it. |
| Anything orchestrator-shaped | Explicitly deferred out of Phase 2 by owner decision, 2026-08-02. Unchanged. |

## The tension worth stating plainly

"How much precision do we need?" has no answer without a claim that needs
it — and the claim that motivated this whole line of work (whether an
orchestrator writing handoff packets costs more than doing the work
directly) is deferred to the Backlog.

That means **further precision work past cycle 3 risks being machinery
ahead of its contract**, the specific failure `BRIEF.md` names. Cycle 3 is
defensible because it closes a measurement gap in what already exists,
not because it anticipates a future need. What comes after it may honestly
be *nothing* until a suite author names a claim — and "Phase 2 is done"
is a legitimate outcome, not a failure to find more work.

## What needs the owner's decision

1. **Is closing the cheaper-slice candidate on this evidence acceptable**,
   or is the R²=0.30 fit too weak to retire it and worth confirming with
   the end-to-end measurement first? (Cycle 3 as scoped would confirm it
   either way.)
2. **Is there a claim you want to make** that needs tighter than ±1.0-turn
   precision? If not, the n=56 and n=237 rows are informational only, and
   Phase 2 may be closer to done than the roadmap implies.
3. **After cycle 3, does Phase 2 end?** If the answer to (2) is "no claim
   yet," the honest close is to stop here and let the next suite author's
   real need reopen it.
