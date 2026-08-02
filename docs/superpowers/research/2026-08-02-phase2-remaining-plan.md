# Phase 2 — plan for the remainder

Written 2026-08-02, after cycles 1 and 2 closed. This is a **planning
analysis awaiting owner review**, not an approved design.

> **Corrected the same day, before owner review.** The first version of
> this document recommended *closing* the "cheaper task slice" candidate,
> on the argument that per-run cost was dominated by ~23s of fixed
> overhead and a shorter task would therefore buy only ~1.4×. **That
> argument was wrong, and the measurement it proposed is what disproved
> it.** The ~23s figure was the *intercept of a regression with R² = 0.30*
> — a fitting artifact from a narrow x-range with large scatter, not
> measured overhead. Directly measured, the per-run floor is **1.6
> seconds**, about 3% of a run. Cost is therefore dominated by the work
> itself, and a cheaper slice is a *strong* lever, not a weak one. The
> recommendation below is reversed accordingly; the original reasoning is
> preserved in "The error, and what it cost" at the end, because how it
> failed is more instructive than the corrected number.

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

## The cost floor, measured

`ROADMAP.md` states Phase 2's direction as making measurement affordable —
"a slice small enough that n=100 is practical." Whether that is achievable
turns entirely on how much of a run is irreducible overhead versus actual
work. **That has now been measured directly** (2026-08-02, `omlx`
gemma-4-12B-it-MLX-8bit, owner's machine):

| Measurement | Median | Detail |
|---|---|---|
| Trivial single-turn probe — workspace, `git init`, Pi startup, one tiny model call | **1.6s** | 3 probes: 1.5 / 1.5 / 1.6s; a 4th verification run at 1.87s returned rc=0 with 5.2 KB of real JSONL, so this is a genuine invocation, not a fast failure |
| Full AgentClinic Phase 1 run, end to end | **45.0s** | n=5, range 38.6–52.0s, all accepted |
| — of which in-stream span | 37.4s | the interval every prior timing number in this project used |
| — of which outside the stream | 7.6s (**17%**) | Pi startup, workspace provisioning, grading, final generation tail |

Three conclusions, in order of importance:

1. **The per-run floor is negligible: 1.6s, about 3% of a run.** Roughly
   43 of the 45 seconds is the model doing the task — approximately 440
   context-tokens/sec against the n=48 mean `context_processed` of 19,097.
2. **Therefore a cheaper task slice is a strong lever, not a weak one.**
   Cost scales with work done, bounded below by 1.6s. Cutting
   `context_processed` to a third would put a run near ~16s and n=100 near
   **27 minutes** (~2.8× cheaper); cutting it to a fifth approaches ~10s
   and ~17 minutes (~4.4×). These are proportional estimates anchored on
   two measured points, not regression extrapolations — see the caveat
   below.
3. **The prior 77-minute n=100 estimate was very nearly right, by luck.**
   Measured end-to-end cost gives **75 minutes**, because the
   outside-the-stream gap (17%) is modest. The in-stream span was a decent
   proxy for total cost even though nobody had checked.

**The caveat that matters.** Neither turn count nor `context_processed`
predicts span well within the observed range — both regressions give
R² ≈ 0.30, with ~9.7s of residual scatter. Run-to-run noise (server state,
cache warmth, contention) dominates at this resolution. So the
proportional estimates above should be read as *order-of-magnitude*, and
**no linear fit over the 6–12 turn range should be extrapolated toward
zero** — doing exactly that is what produced the error this document was
corrected for.

## Recommended cycle 3 — design a cheaper slice, and prove it still measures something

The floor measurement above (the work this document originally proposed as
cycle 3) is **done**; it took ~6 minutes and is reported here. What it
unblocks is the candidate it was meant to adjudicate.

**What cycle 3 should do.** Design a smaller task — its own task spec,
fixture pair, and acceptance suite, following cycle 1's precedent — chosen
to cut `context_processed` substantially while *keeping the agentic tool
loop*, since turn count is the variable being measured.

**The risk that must be designed against, and proven.** A task small
enough to be cheap may be small enough to have no variance — if every run
takes exactly 2 turns, there is no distribution left to characterize, and
the precision machinery from cycle 2 measures nothing. **The cycle is not
done until it shows the cheaper slice still produces a spread of turn
counts**, compared against the n=48 baseline's spread (6–12 turns,
`leave_one_out_spread` 0.128). A cheap task with a degenerate distribution
is a failed cycle, not a cheaper one, and it should say so rather than
report a small number.

**Scope discipline.** This is a real build — new task spec, new fixtures,
new suite — so it is the largest cycle in Phase 2 so far. It is justified
only because the floor measurement shows the payoff is real (~2.8–4.4×)
and because affordability for lower-powered collaborators is a stated hard
constraint, not a nice-to-have.

## Deliberately not recommended

| Candidate | Why not |
|---|---|
| Adaptive stopping | Optimizes the count of runs. With no live claim naming a precision target, a stopping rule has nothing to stop at. Machinery ahead of its contract. Revisit if and when a claim is scheduled. |
| Topping up to n=56 (8 runs, ~6 min) | Cheap enough to be tempting, which is the whole problem. ±0.5-turn precision is not *needed* by any claim currently on the table; buying it because it is affordable is exactly the reasoning `BRIEF.md` warns against. Trivial to do later if a claim ever requires it — and if cycle 3 changes the slice, this baseline would need redoing anyway. |
| Reducing fixed overhead | At 1.6s and 3% of a run, there is nothing here worth optimizing. Closed on measurement. |
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

1. **Is a cheaper slice worth building at ~2.8–4.4×?** It is a real build
   (task spec, fixture pair, acceptance suite) against a real payoff, with
   a real risk of producing a degenerate distribution. The alternative is
   accepting 75 minutes per n=100 on the owner's machine — and
   proportionally worse for the lower-powered collaborators who were the
   reason affordability became a goal.
2. **Is there a claim you want to make** that needs tighter than ±1.0-turn
   precision? If not, the n=56 and n=237 rows are informational only, and
   further precision work is machinery ahead of its contract.
3. **Does Phase 2 end instead?** If the answer to (2) is "no claim yet,"
   stopping here is defensible: the instrument exists, its precision is
   characterized, and its cost is now measured. Letting the next suite
   author's real need reopen it is the `BRIEF.md`-consistent choice.

## The error, and what it cost

The first version of this document is worth preserving as a cautionary
case, because it failed in a way this project explicitly guards against.

The reasoning was: regress in-stream span on turn count, read the
intercept (22.9s) as fixed overhead, conclude that a shorter task can only
recover the marginal 3.2s/turn, and therefore close the cheaper-slice
candidate as a weak lever worth ~1.4×.

Three things went wrong, compounding:

1. **An unvalidated model was used to make a decision.** R² = 0.30 was
   stated in the document — and then the fit was used anyway to compute a
   specific 1.4× figure. Naming a caveat is not the same as heeding it.
2. **A regression intercept was read as a physical quantity.** Fitting a
   line to a narrow range (6–12 turns) with ~9.7s of scatter and then
   extrapolating to zero is unsound; the resulting intercept described
   nothing real. Measured, the floor is 1.6s, off by a factor of 14.
3. **The conclusion ran ahead of the measurement that would have tested
   it.** The same document proposed measuring the floor *and* pre-declared
   what closing the candidate would mean — reaching a verdict while
   explicitly noting the deciding evidence did not yet exist.

The measurement cost about six minutes. The correction arrived before the
owner acted on it, which is the only reason this is a cautionary note and
not a wasted cycle spent building the wrong thing — or worse, *not*
building the right one.
