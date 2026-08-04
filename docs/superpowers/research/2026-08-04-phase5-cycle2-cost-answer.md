# Phase 5 cycle 2 — what the orchestration cost

**Date:** 2026-08-04
**Cycle:** phase 5 cycle 2 — the cost answer
**Model:** `omlx/gemma-4-12B-it-MLX-8bit` · **pi:** 0.83.0 · **n:** 16 per arm,
sequential, owner's machine
**Suite:** `agentclinic-phase-1` (detailed roadmap) for both arms

Every table below is emitted by
[`2026-08-04-phase5-cycle2-recompute.py`](2026-08-04-phase5-cycle2-recompute.py),
committed beside this file, run against the two raw checkpoints in
`~/local-ai-pi-evidence/` (outside version control). Do not hand-edit the
numbers.

## The short version

The orchestrated arm was **cheaper per turn and more expensive in context, and
less reliable** — 12/16 accepted against the bare arm's 16/16, with three
runs timing out where the bare arm had none. Two of those three timeouts had
already produced a *correct, grader-accepted* solution and hung anyway.

## Predictions, scored

Pre-registered in cycle 1's spec before the mechanism existed. Their source
series carries a `PENDING RULE 8 REVIEW` banner, so it supplied predictions,
never results.

| # | Prediction | Outcome |
|---|---|---|
| 1 | Both arms accept 16/16 | **FALSIFIED.** Bare 16/16, orchestrated 12/16. |
| 2 | Orchestrated `context_processed` is higher | **REPLICATED.** 1.15× median. |
| 3 | Delegation occurs on 16/16 orchestrated runs | **REPLICATED.** 16/16 successful, 0 failed. |

Prediction 1 came from the prior project's detailed-roadmap orchestrated arm
scoring 16/16. **That number did not replicate here.** This is n=16 against
n=16 on the same suite, model, and Pi version, but a different orchestrator
prompt, a different implementer specialist, and a different harness — so this
is evidence that our configuration is less reliable, not that the prior
measurement was wrong.

## Aggregates

| | bare | sdd-orchestrator |
|---|---|---|
| accepted | **16/16** | **12/16** |
| timed out | 0/16 | **3/16** |
| tool errors, total | 0 | 3 (all in one run) |
| runs with ≥1 successful delegation | 0/16 | 16/16 |
| runs with a failed delegation | 0 | 0 |
| max concurrent `subagent` calls, any run | 0 | **1** |
| turns — median (min–max) | 7 (7–10) | 6 (2–14) |
| `context_processed` — median (min–max) | 16,298 (16,189–26,058) | 18,680 (5,015–101,475) |
| `output_tokens` — median (min–max) | 965 (907–1,119) | 660 (432–2,243) |

Ratios, orchestrated ÷ bare: **turns 0.86×, `context_processed` 1.15×,
`output_tokens` 0.69×.**

Three orchestrated runs timed out, so their telemetry counts are lower bounds
(`complete=False`). Recomputing over complete runs only (n=13) gives turns
0.86×, context 1.15×, output 0.69× — **identical to two decimal places.** The
cost result does not depend on how the truncated runs are treated.

## The cost answer

On this workload the orchestrator **emits less and reads more**. It writes a
compact handoff packet and delegates instead of iterating, so its own output
drops by about a third and it takes one fewer turn; but the packet plus the
child's context pushes total context processed up ~15%.

So "does getting an orchestrator to write handoff packets cost more than doing
the work itself?" has a **two-sided answer on this workload**: more context,
less generation. Which one is expensive depends on what is scarce — on a local
single-threaded server, generation is usually the bottleneck, which makes the
orchestrated arm look *cheaper* on the resource that actually hurts.

That is not a recommendation. See reliability, below.

## Reliability, which is the more interesting result

| Run | What happened |
|---|---|
| 11 | **Timed out after thrashing.** 14 turns, 3 tool errors, 101,475 context — 6× the bare median. Solution broken: 4 acceptance tests failed with `TypeError`. |
| 12 | **Timed out after the delegation returned cleanly.** The `subagent` call ended, and the parent never produced another `turn_end`. Solution correct — the grader accepted it, 4/4. |
| 13 | **Timed out inside the delegation.** The `subagent` call never ended; the last event is a `tool_execution_update` on it. Solution correct — the grader accepted it, 4/4. |
| 14 | **Exited cleanly (rc 0) with a wrong solution.** One acceptance test failed: `test_home_extends_the_shared_layout`. |

Three distinct hang shapes — thrash-then-hang, parent-hangs-after-child-returns,
and child-never-returns — and **zero hangs in the bare arm**.

Runs 12 and 13 deserve emphasis: the work was *done and correct*, and the run
still failed. It failed on Phase 1 cycle 15's exit veto, which refuses to
certify a run whose Pi exited nonzero. That rule is doing its job — a hung
process is not a successful run — but it means orchestration cost two
otherwise-good runs purely by failing to terminate.

**Variance is the other story.** Bare `context_processed` spans 16,189–26,058,
a factor of 1.6. Orchestrated spans 5,015–101,475, a factor of **20**. The
bare arm is remarkably uniform — 13 of 16 runs took exactly 7 turns. The
orchestrated arm is not.

## The observation that decides a Backlog gate

**Maximum concurrent `subagent` calls was 1 in every one of the 16 runs.** The
shipped extension never put more than one child on the single-threaded server.

The Backlog gates building our own ~150-line subagent tool on "a measured run
shows the shipped extension contaminating or losing a measurement." On the
parallelism criterion, **the gate has not fired** and the shipped extension
stays. Nothing here argues for owning that code.

Concurrency is computed by walking `tool_execution_start`/`tool_execution_end`
pairs by `toolCallId` in stream order, not by counting calls per turn — which
would not distinguish two sequential delegations from two simultaneous ones.

## What this does *not* say

**It says nothing about keeping a small model on track**, which is the phase's
long-term goal. That question needs a workload where the bare arm thrashes,
and this one does not: bare was 16/16 with zero tool errors, no incomplete
runs, and 2 runs showing a single repeated tool call each. There is no
baseline thrash for an orchestrator to reduce. The three orchestrated hangs
are evidence that delegation *introduced* instability here — not evidence
about whether it prevents instability elsewhere.

That direction of result is consistent with the prior project's
repeat-spiral incident, which traced 4 of 16 hangs in a delegated batch to a
single cause. Consistent, not confirming: different root causes, and that
record is not citable.

**It is one configuration, not orchestration in general.** A different
orchestrator prompt or implementer specialist could plausibly close the 12/16
gap. Cycle 2 deliberately did no tuning; tuning is cycle 4+, under fresh
pre-registration.

## Method notes

Per-run wall clock ranged roughly 80–150 s across chunks; the bare arm took
about 30 minutes total. Batches ran in resumable chunks against one checkpoint
each. In-stream span understates true elapsed time by a median 7.6 s per run
(see the Backlog's wall-clock entry), so these figures are indicative only and
no wall-clock claim is made.

No commit landed in the batch's working directory between the first run and
the last, by agreement with the owner: `_conditions` re-reads `HEAD` per run,
so a commit would have aborted the batch and stranded the checkpoint.

Checkpoints:
`~/local-ai-pi-evidence/satyrn-phase5-cycle2-bare-n16.jsonl` and
`~/local-ai-pi-evidence/satyrn-phase5-cycle2-sdd-orchestrator-n16.jsonl`.
Raw, outside Git, retaining full `pi_stdout` — so every number here is
recomputable, and so are metrics nobody has written yet.

## Per-run tables

### bare — n=16

| # | accepted | turns | tool calls | tool errors | context_processed | subagent ok | subagent failed | max concurrent |
|---|---|---|---|---|---|---|---|---|
| 1 | True | 7 | 6 | 0 | 16300 | 0 | 0 | 0 |
| 2 | True | 7 | 6 | 0 | 16343 | 0 | 0 | 0 |
| 3 | True | 7 | 6 | 0 | 16338 | 0 | 0 | 0 |
| 4 | True | 7 | 6 | 0 | 16297 | 0 | 0 | 0 |
| 5 | True | 7 | 6 | 0 | 16293 | 0 | 0 | 0 |
| 6 | True | 7 | 6 | 0 | 16274 | 0 | 0 | 0 |
| 7 | True | 7 | 6 | 0 | 16189 | 0 | 0 | 0 |
| 8 | True | 7 | 6 | 0 | 16388 | 0 | 0 | 0 |
| 9 | True | 7 | 6 | 0 | 16265 | 0 | 0 | 0 |
| 10 | True | 9 | 8 | 0 | 21869 | 0 | 0 | 0 |
| 11 | True | 7 | 6 | 0 | 16323 | 0 | 0 | 0 |
| 12 | True | 10 | 9 | 0 | 26058 | 0 | 0 | 0 |
| 13 | True | 7 | 6 | 0 | 16334 | 0 | 0 | 0 |
| 14 | True | 7 | 6 | 0 | 16281 | 0 | 0 | 0 |
| 15 | True | 7 | 6 | 0 | 16274 | 0 | 0 | 0 |
| 16 | True | 7 | 6 | 0 | 16215 | 0 | 0 | 0 |

### sdd-orchestrator — n=16

| # | accepted | turns | tool calls | tool errors | context_processed | subagent ok | subagent failed | max concurrent |
|---|---|---|---|---|---|---|---|---|
| 1 | True | 6 | 5 | 0 | 18553 | 1 | 0 | 1 |
| 2 | True | 6 | 5 | 0 | 18911 | 1 | 0 | 1 |
| 3 | True | 6 | 5 | 0 | 18807 | 1 | 0 | 1 |
| 4 | True | 9 | 8 | 0 | 38609 | 3 | 0 | 1 |
| 5 | True | 5 | 4 | 0 | 15770 | 1 | 0 | 1 |
| 6 | True | 3 | 2 | 0 | 8582 | 1 | 0 | 1 |
| 7 | True | 7 | 6 | 0 | 23729 | 1 | 0 | 1 |
| 8 | True | 2 | 1 | 0 | 5996 | 1 | 0 | 1 |
| 9 | True | 3 | 2 | 0 | 8405 | 1 | 0 | 1 |
| 10 | True | 9 | 8 | 0 | 32558 | 3 | 0 | 1 |
| 11 | False | 14 | 14 | 3 | 101475 | 1 | 0 | 1 |
| 12 | False | 3 | 3 | 0 | 8055 | 2 | 0 | 1 |
| 13 | False | 2 | 3 | 0 | 5015 | 1 | 0 | 1 |
| 14 | False | 7 | 6 | 0 | 22514 | 1 | 0 | 1 |
| 15 | True | 9 | 8 | 0 | 31888 | 2 | 0 | 1 |
| 16 | True | 3 | 2 | 0 | 8653 | 1 | 0 | 1 |
