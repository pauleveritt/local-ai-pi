# Phase 5 cycle 6 — a loop-breaker that did not fire

**Date:** 2026-08-04
**Cycle:** phase 5 cycle 6 — the loop-breaker extension
**Model:** `omlx/gemma-4-12B-it-MLX-8bit` · **pi:** 0.83.0
**Suite:** `agentclinic-phase-1-user-story`

> **Publishes no number.** An n=6 pilot at `run_timeout=300`, not comparable
> with any n=16/600 s arm. Cycle 8 buys the comparable one.

> **Corrected 2026-08-04 by phase 5 cycle 9.** The delegated child in this
> arm was **not hermetic.** Pi's shipped subagent extension spawns the child
> without the parent's suppression flags, and user-scope resources load
> unconditionally, so the child loaded the operator's own
> `~/.pi/agent/extensions/` and packages -- including `rtk.ts`, which rewrites
> bash commands. Recorded child transcripts here show `ls -R` returning the
> output of `rtk ls -R`. The comparisons in this record stand, because the
> contamination was constant across the arms compared; what it means is that
> the orchestrated arm measured **this orchestrator plus the operator's
> toolbelt**, not the orchestrator alone. `RunConditions` gained
> `agent_dir_digest` in cycle 9 so this can never again be silent.

## The short version

The extension works — proven end to end on a live run — and **it never fired
in the pilot, because the loop it exists to break no longer happens.** Cycle
5's one-line prompt correction removed the behaviour. The breaker's value is
therefore established by *replay against evidence already recorded*, not by
fresh runs, and this record says so rather than dressing a quiet pilot up as a
result.

## What was built

`.pi/extensions/loop-breaker.ts`: a ring buffer of the last 20 tool calls,
keyed on tool name plus stably-serialised input, returning
`{ block: true, reason }` from `pi.on("tool_call")` when a key reaches 5
occurrences in that window. It appends a `loop_broken` entry, which
`RunTelemetry.custom_entries` already parses — so it is measurable with no
harness change at all.

**It counts repeats regardless of success.** That is the property the owner's
unmerged `pi-circuit-breaker` branch lacks — it tracks
`maxIdenticalFailingToolCalls`, and every one of cycle 4's 245 `ls -R` calls
succeeded. Here it is structural rather than a choice to defend: `tool_call`
fires *before* execution, so success is not knowable at that point.

It ships as a second improvement, `sdd-orchestrator-guarded`, carrying both
Pi's shipped subagent and our breaker. `Improvement.extensions` was already a
tuple, so this needed no composition machinery, and the unguarded improvement
survives as cycle 8's comparison.

## Evidence 1 — replay over five banked batches, zero model time

| batch | runs where it fires | calls prevented |
|---|---|---|
| cycle 2 bare (n=16) | 0/16 | 0 |
| cycle 2 sdd-orchestrator (n=16) | 0/16 | 0 |
| cycle 4 user-story bare (n=16) | 0/16 | 0 |
| **cycle 4 user-story sdd (n=16)** | **2/16** | **257** |
| cycle 5 pilot, corrected prompt (n=6) | 0/6 | 0 |

**Zero false positives across 55 healthy runs.** On cycle 4's run 1 — the 261
turn, 245×`ls -R` run — it first blocks at call 18 and prevents **239 of 261
calls**. On run 8 it blocks at call 32 and prevents 18.

The replay reimplements the policy in Python while the extension implements it
in TypeScript. **They can diverge and no test here would notice.** It is an
analysis of the rule, not a test of the shipped code; the rule is kept trivial
for that reason, and the live proof below is what covers the code.

## Evidence 2 — the mechanism, proven live

A breaker that never fires proves nothing about whether it works, and a
silently unloaded extension is a failure this project has already had once —
cycle 1 spent a live run discovering that `--extension` pointed at a directory
loads nothing, reports nothing, and still grades the run accepted.

So the mechanism was proven by forcing it: a copy with `THRESHOLD = 0` blocks
every call. That run produced **7 `loop_broken` entries for 7 tool calls**, with
payload `{"tool": "subagent", "repeats": 0, "blockedSoFar": 1}` on the first.
Load, hook, block, and entry are all confirmed.

*A first attempt used `THRESHOLD = 1` and proved nothing, because the run made
two **distinct** calls and never repeated one. Recorded because the weaker
probe looked like a test and was not.*

## Evidence 3 — the pilot, which is a quiet result

| | cycle 5 (unguarded) | cycle 6 (guarded) |
|---|---|---|
| accepted | 0/6 | 0/6 |
| timed out | 3/6 | 4/6 |
| tool calls, total | 13 | 12 |
| delegations | 5 | 5 |
| runs with a repeated identical call | 0/6 | 0/6 |
| worst single-command repetition | 1 | 1 |
| **`loop_broken` blocks** | — | **0** |
| wrote files | 5/6 | 5/6 |

The two arms are indistinguishable on every measure, and the breaker never
engaged. **This is the honest reading:** after cycle 5's correction the model
no longer loops on this configuration, so there is nothing for the guard to
catch. The one timeout of difference is n=6 noise, not a regression.

## Predictions, scored

| # | Prediction | Outcome |
|---|---|---|
| 1 | Replay trips on cycle 4's run 1 at or before call 10 | **FALSIFIED, narrowly.** First block at call 18 — the run's early calls were not yet all identical, so the 5-in-20 condition took longer to satisfy than assumed. |
| 2 | Replay trips on few or no cycle 5 runs | **CONFIRMED.** 0/6, and 0/32 across cycle 2's arms. |
| 3 | The live pilot shows no acceptance change | **CONFIRMED.** 0/6 both. |

## What this means for shipping it

Arguments to keep it, none of which depend on the pilot:

- It prevented 239 calls on real recorded evidence, and that failure cost a
  run its entire budget.
- Its cost is near zero: one extension load, a 20-element list, no model time,
  no false positive in 55 healthy runs.
- A prompt line asking a model not to repeat itself is a weaker guarantee than
  a mechanism that refuses. Cycle 5's fix is one model, one prompt, one
  workload — the guard does not care why the loop started.

The argument against, stated fairly: **on current evidence it is insurance
that has never been claimed on.** If the prompt correction holds across cycle
8's arm, the breaker will have no measured benefit in this project's own
numbers, and its case rests entirely on retrospective replay.

Both belong in the record. The phase's product goal — a Pi extension a
contributor can install — is served either way, and the failure it guards is
one the owner reports hitting for a month outside this harness.

## Evidence

`~/local-ai-pi-evidence/satyrn-phase5-cycle6-guarded-n6-t300.jsonl`, outside
version control, retaining full `pi_stdout`. The replay table regenerates from
`2026-08-04-phase5-cycle6-replay.py` over all five batches.
