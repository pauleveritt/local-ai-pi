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

> **CORRECTED 2026-08-04, same day, before any downstream use.** The first
> version of this record counted only the **parent's** tokens and concluded
> the orchestrated arm was *cheaper* — 1.15× context, 0.69× output. That was
> wrong, and wrong in the flattering direction. Pi's shipped subagent
> extension surfaces the child's usage in the parent's `tool_execution_end`
> under `details.results[].usage`, and `harness/telemetry.py` parses the
> parent's own events only. The child does most of the work: counting it
> turns 1.15× into **8.11×**. Every figure below is the corrected one, and
> the parent-only column is retained so the size of the error stays visible.
> The prompt for the recheck was the owner asking whether machine contention
> explained the result; it did not, but looking answered a question nobody
> had asked.

## The short version

Orchestration on this workload cost **8× the context, 2.5× the output, and 3×
the turns**, and was **less reliable** — 12/16 accepted against the bare arm's
16/16, with three runs timing out where the bare arm had none. Two of those
three timeouts had already produced a *correct, grader-accepted* solution and
hung anyway.

The handoff-packet claim is **confirmed, emphatically**, on this workload.

## Predictions, scored

Pre-registered in cycle 1's spec before the mechanism existed. Their source
series carries a `PENDING RULE 8 REVIEW` banner, so it supplied predictions,
never results.

| # | Prediction | Outcome |
|---|---|---|
| 1 | Both arms accept 16/16 | **FALSIFIED.** Bare 16/16, orchestrated 12/16. |
| 2 | Orchestrated `context_processed` is higher | **REPLICATED, and by far more than expected.** 8.11× median once the child is counted (1.15× parent-only). |
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
| **total** turns — median (min–max) | 7 (7–10) | **22 (2–137)** |
| **total** `context_processed` | 16,298 (16,189–26,058) | **132,218 (5,015–3,802,853)** |
| **total** `output_tokens` | 965 (907–1,119) | **2,399 (432–13,142)** |
| parent-only `context_processed` | 16,298 | 18,680 |

Ratios, orchestrated ÷ bare: **total turns 3.14×, total `context_processed`
8.11×, total `output_tokens` 2.49×.** Parent-only context is 1.15×, which is
what the uncorrected version of this record reported as the whole answer.

## The cost answer

**The orchestrator is not doing the work; the child is, and the child is
expensive.** The parent looks frugal in isolation — 6 turns against the bare
arm's 7, and a third less output — because it writes a packet and hands off.
Behind that packet the implementer child ran a median of **16 turns** and
processed a median of **~113,000 additional tokens**.

So "does getting an orchestrator to write handoff packets cost more than doing
the work itself?" — on this workload, **yes, by roughly 8× in context and 2.5×
in generation.** The claim that justified building `harness/telemetry.py` is
confirmed, and the answer is not close.

The tail is worse than the median. Run 4's child took **128 turns and 3.76M
context**; run 11's took 60 turns and 1.35M. A bare run never exceeded 26,058
total. Delegation did not merely add overhead, it added a heavy tail that the
bare arm does not have.

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

**Variance is the other story.** Bare total `context_processed` spans
16,189–26,058, a factor of 1.6. Orchestrated spans 5,015–3,802,853, a factor
of **759**. The bare arm is remarkably uniform — 13 of 16 runs took exactly 7
turns. The orchestrated arm is not remotely.

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

## Was the machine just busy?

The owner asked whether another workload running on the machine explained
this. It does not, and checking is what surfaced the error corrected above.

Generation throughput, from `message.timestamp` spans in the retained
streams: **bare 12.61 tokens/second aggregate, orchestrated 17.83.** The
orchestrated arm was *faster* per token generated, not slower. Parent-only
throughput looks like a collapse — 14.9 down to 4.7 tokens/second median —
but that is the same artifact as the cost error: the span includes the
child's generation time while the numerator excluded the child's tokens.

So contention is ruled out for the cost result. It is not fully ruled out for
the three timeouts, which are wall-clock events against a fixed 600 s budget
and would be sensitive to a slower machine. But a run that needs 8× the
context and 3× the turns has far less headroom inside that budget regardless
of load, and the two arms ran back-to-back on the same machine within 100
minutes. Recorded as a residual uncertainty rather than dismissed.

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

| # | accepted | parent turns | child turns | total turns | parent ctx | child ctx | total ctx | total output | subagent ok | failed | max concurrent |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | True | 7 | 0 | 7 | 16300 | 0 | 16300 | 931 | 0 | 0 | 0 |
| 2 | True | 7 | 0 | 7 | 16343 | 0 | 16343 | 998 | 0 | 0 | 0 |
| 3 | True | 7 | 0 | 7 | 16338 | 0 | 16338 | 982 | 0 | 0 | 0 |
| 4 | True | 7 | 0 | 7 | 16297 | 0 | 16297 | 939 | 0 | 0 | 0 |
| 5 | True | 7 | 0 | 7 | 16293 | 0 | 16293 | 966 | 0 | 0 | 0 |
| 6 | True | 7 | 0 | 7 | 16274 | 0 | 16274 | 935 | 0 | 0 | 0 |
| 7 | True | 7 | 0 | 7 | 16189 | 0 | 16189 | 957 | 0 | 0 | 0 |
| 8 | True | 7 | 0 | 7 | 16388 | 0 | 16388 | 995 | 0 | 0 | 0 |
| 9 | True | 7 | 0 | 7 | 16265 | 0 | 16265 | 907 | 0 | 0 | 0 |
| 10 | True | 9 | 0 | 9 | 21869 | 0 | 21869 | 1110 | 0 | 0 | 0 |
| 11 | True | 7 | 0 | 7 | 16323 | 0 | 16323 | 944 | 0 | 0 | 0 |
| 12 | True | 10 | 0 | 10 | 26058 | 0 | 26058 | 1119 | 0 | 0 | 0 |
| 13 | True | 7 | 0 | 7 | 16334 | 0 | 16334 | 1000 | 0 | 0 | 0 |
| 14 | True | 7 | 0 | 7 | 16281 | 0 | 16281 | 943 | 0 | 0 | 0 |
| 15 | True | 7 | 0 | 7 | 16274 | 0 | 16274 | 998 | 0 | 0 | 0 |
| 16 | True | 7 | 0 | 7 | 16215 | 0 | 16215 | 964 | 0 | 0 | 0 |

### sdd-orchestrator — n=16

| # | accepted | parent turns | child turns | total turns | parent ctx | child ctx | total ctx | total output | subagent ok | failed | max concurrent |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | True | 6 | 29 | 35 | 18553 | 197011 | 215564 | 2506 | 1 | 0 | 1 |
| 2 | True | 6 | 15 | 21 | 18911 | 90260 | 109171 | 1857 | 1 | 0 | 1 |
| 3 | True | 6 | 10 | 16 | 18807 | 55600 | 74407 | 1728 | 1 | 0 | 1 |
| 4 | True | 9 | 128 | 137 | 38609 | 3764244 | 3802853 | 6290 | 3 | 0 | 1 |
| 5 | True | 5 | 15 | 20 | 15770 | 92782 | 108552 | 2082 | 1 | 0 | 1 |
| 6 | True | 3 | 15 | 18 | 8582 | 93445 | 102027 | 2318 | 1 | 0 | 1 |
| 7 | True | 7 | 13 | 20 | 23729 | 79270 | 102999 | 1917 | 1 | 0 | 1 |
| 8 | True | 2 | 19 | 21 | 5996 | 128338 | 134334 | 2262 | 1 | 0 | 1 |
| 9 | True | 3 | 20 | 23 | 8405 | 143692 | 152097 | 2188 | 1 | 0 | 1 |
| 10 | True | 9 | 68 | 77 | 32558 | 1046170 | 1078728 | 7976 | 3 | 0 | 1 |
| 11 | False | 14 | 60 | 74 | 101475 | 1350331 | 1451806 | 8578 | 1 | 0 | 1 |
| 12 | False | 3 | 34 | 37 | 8055 | 270458 | 278513 | 13142 | 2 | 0 | 1 |
| 13 | False | 2 | 0 | 2 | 5015 | 0 | 5015 | 432 | 1 | 0 | 1 |
| 14 | False | 7 | 35 | 42 | 22514 | 296563 | 319077 | 3367 | 1 | 0 | 1 |
| 15 | True | 9 | 16 | 25 | 31888 | 98213 | 130101 | 2480 | 2 | 0 | 1 |
| 16 | True | 3 | 17 | 20 | 8653 | 110545 | 119198 | 3361 | 1 | 0 | 1 |
