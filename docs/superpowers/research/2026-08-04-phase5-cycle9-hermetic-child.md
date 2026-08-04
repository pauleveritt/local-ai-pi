# Phase 5 cycle 9 — the contamination was the pathology

**Date:** 2026-08-04
**Cycle:** phase 5 cycle 9 — the hermetic child
**Model:** `omlx/gemma-4-12B-it-MLX-8bit` · **pi:** 0.83.0
**Suite:** `agentclinic-phase-1-user-story`

> **Publishes no number.** n=6 at `run_timeout=300`, not comparable with any
> n=16/600 s arm. The comparable arm follows.

## The result

| pilot | run-accepted | grader-accepted | timeouts | worst repeated command | runs repeating ≥5× |
|---|---|---|---|---|---|
| cycle 7 — tech stack | 4/6 | 5/6 | 2/6 | 93 | 2/6 |
| cycle 8 — + stop rule | 4/6 | 4/6 | 2/6 | 178 | 3/6 |
| **cycle 9 — hermetic child** | **5/6** | **5/6** | **0/6** | **5** | **1/6** |

**Every run terminated on its own.** All six report `stopReason: "stop"`;
cycles 7 and 8 killed two apiece with the child still calling tools. The single
failure is a genuine one — a run that finished and did not satisfy the grader —
not a hang.

| # | run-accepted | grader-accepted | child steps | child tool calls | blocked | worst repeat |
|---|---|---|---|---|---|---|
| 1 | True | True | 22 | 10 | 0 | 1 |
| 2 | True | True | 16 | 7 | 0 | 1 |
| 3 | True | True | 22 | 10 | 0 | 1 |
| 4 | False | False | 44 | 21 | 0 | 5 |
| 5 | True | True | 20 | 9 | 0 | 1 |
| 6 | True | True | 22 | 10 | 0 | 2 |

## The finding: removing the contamination removed the runaway

The change was **not** a guard that caught the loop. The loop-breaker refused
**zero** calls. The repetition simply stopped happening: worst repeated command
across a pilot went **178 → 5**, and the median run now repeats nothing at all.

The intervention was to stop the child loading the operator's personal Pi
resources — chiefly `rtk.ts`, which rewrites the child's bash commands. So the
most economical account of three cycles of runaway children is that **the
rewriter was causing them.**

The supporting measurements point the same way:

| pilot | median run stdout | max run stdout | median total context | max total context |
|---|---|---|---|---|
| cycle 7 | 0.90 MB | 10.96 MB | 118,840 | 141,297 |
| cycle 8 | 9.63 MB | 25.59 MB | 70,780 | **2,808,164** |
| **cycle 9** | **0.49 MB** | **1.20 MB** | **37,839** | **90,963** |

A 20× drop in transcript size and a 31× drop in peak context. `rtk ls -R`
returns a flattened, size-annotated listing of everything beneath the cwd —
including the whole of `.git` — where plain `ls -R` in an empty workspace
returns almost nothing. The child was reading a large, unhelpful answer,
learning nothing, and asking again.

**This is a claim about a mechanism, made from n=6.** It is consistent with
every measurement taken, and it is the account this record will defend, but the
comparable arm is what would establish it.

## Contention: the usual caveat, pointing the other way this time

| pilot | throughput |
|---|---|
| cycle 7 | 9.28 tok/s |
| cycle 8 | 7.09 tok/s |
| **cycle 9** | **22.80 tok/s** |

Cycle 9 measured 2.5× cycle 7's throughput, which by the standard applied in
cycles 7 and 8 would make its timeout column uninterpretable.

**Here that reading is probably backwards.** Throughput is output tokens per
second of wall clock, and generation speed falls as context grows. A run whose
child is re-reading a megabyte-scale directory listing carries an enormous
context and generates slowly *because of the pathology*. Cycle 8's peak context
was 2.8M tokens against cycle 9's 91k. So low throughput in cycles 7–8 is at
least partly an **effect** of the thing this cycle removed, not evidence of a
busier machine.

Both readings are recorded because they cannot be separated with this data. The
machine was also genuinely quieter than during cycle 8's pilot, which ran
alongside a research agent on the same host.

What survives either reading: **the repetition counts.** A faster machine gives
a child *more* opportunity to repeat a command inside a fixed 300 s window, not
less. 178 → 5 cannot be explained by speed.

## Predictions, scored

| # | Prediction | Outcome |
|---|---|---|
| 1 | The child's bash commands stop being rewritten | **CONFIRMED.** No rtk-shaped output in any child transcript, checked by pattern across all six runs plus the smoke. |
| 2 | The loop-breaker fires in the child | **FALSIFIED, in the best available way.** Zero refusals — because there was nothing left to refuse. The guard's *delivery* was proven separately (below); its *necessity* was not. |
| 3 | Timeouts fall | **CONFIRMED** as a count, 2/6 → 0/6, and left **unscored** as a claim, for the contention reasons above. |
| 4 | Grader-accepted does not fall | **CONFIRMED.** 4/6 → 5/6. |

Prediction 2 is the interesting miss. The cycle was designed around delivering a
guard to the child, and the guard turned out to be unnecessary once the thing it
was guarding against was removed. That is a better outcome than the one
predicted, and it is still a falsified prediction.

## The guard does reach the child, proven separately

Zero refusals is ambiguous on its own — loaded and unneeded looks identical to
never loaded, and cycle 8 was burned by exactly that class of reading. So it was
tested directly: a **threshold-0** copy of the loop-breaker in the harness agent
dir, one live run, and the child's **first** tool result is the refusal text.

**The guard loads in the child.** Cycle 8 concluded this was impossible; it had
probed the project-local `.pi/extensions/` route, which is genuinely
trust-gated shut, and never tried the user-scope route, which is open
unconditionally.

## An instrument limit this exposed

While every child call was being refused, the parent's stream reported
`loop_broken: 0`. The child appends those entries in its own session and the
subagent extension never surfaces them. **A child-side block is observable only
as the refusal text arriving back as a child tool result**, which is what the
analysis script now counts. Anyone reading `loop_broken` counts as evidence
about the child would be reading a number that cannot rise.

## Evidence

`~/local-ai-pi-evidence/satyrn-phase5-cycle9-hermetic-n6-t300.jsonl`, outside
version control, retaining full `pi_stdout`. Recompute with
`docs/superpowers/research/2026-08-04-phase5-cycle8-child-analysis.py`.
