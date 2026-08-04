# Phase 5 cycle 8 — the prompt did not hold the child

**Date:** 2026-08-04
**Cycle:** phase 5 cycle 8 — the runaway child
**Model:** `omlx/gemma-4-12B-it-MLX-8bit` · **pi:** 0.83.0
**Suite:** `agentclinic-phase-1-user-story`

> **Publishes no number.** n=6 at `run_timeout=300`, not comparable with any
> n=16/600 s arm.

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

## The result: a negative one

| pilot | run-accepted | grader-accepted | timeouts | worst repeated command | runs repeating a command ≥5× |
|---|---|---|---|---|---|
| cycle 7 — tech stack | 4/6 | 5/6 | 2/6 | 93 | 2/6 |
| **cycle 8 — + stop rule** | **4/6** | **4/6** | **2/6** | **178** | **3/6** |

The correction added to `implementer.md` — *if validation fails twice with the
same output, stop re-running it; once it passes, report and stop* — **did not
reduce the child's repetition.** By every column it is level or worse.

| # | run-accepted | grader-accepted | timed out | child steps | child tool calls | worst repeat | that command |
|---|---|---|---|---|---|---|---|
| 1 | True | True | False | 222 | 110 | 83 | `ls -R` |
| 2 | True | True | False | 18 | 8 | 1 | — |
| 3 | False | False | True | 365 | 182 | **178** | `ls -F` |
| 4 | False | False | True | 281 | 140 | 68 | `ls -R` |
| 5 | True | True | False | 24 | 11 | 1 | — |
| 6 | True | True | False | 30 | 14 | 2 | — |

## Why it failed, and it is not that the model ignored the instruction

**The cycle aimed at the wrong loop.** The diagnosis read one timed-out run —
77 identical `pytest` calls — and generalized it to "the child re-runs
validation forever." Re-reading the *other* cycle-7 timeout with the instrument
built for this cycle shows it repeated **`ls -d templates` 93 times**. It was
never predominantly a validation loop.

Cycle 8's pilot makes that unambiguous. Every repeated command in it is an
**exploration** command — `ls -R`, `ls -F`. The stop rule names validation, so
the runs it could have helped are not the runs that failed.

**This is the operator's month-old `ls -R` problem, relocated.** Cycle 5 killed
exactly this behaviour in the *parent* — 245 repetitions down to 1 — with one
sentence stating that the workspace is empty. The implementer prompt never got
that sentence. It says "do not explore the repository," which is an instruction
to refrain, not a fact that removes the reason to look.

## The generalization that is now paid for

Cycle 6 argued a mechanism beats a prompt. Cycle 8 argued the opposite for one
case, on the grounds that the mechanism could not be delivered and the two
previous prompt corrections had worked. **The bet lost.**

The distinction the two prompt successes share, and this one lacks: they
supplied a **fact the model did not have** — the call shape, the framework, the
empty workspace. Cycle 8 supplied a **rule of conduct**. On a 12B model, facts
land and rules of conduct do not. That is the transferable lesson, and it is
worth more than the cycle cost.

## Predictions, scored

| # | Prediction | Outcome |
|---|---|---|
| 1 | The child's repeated-command count falls sharply | **FALSIFIED.** Worst repeat 93 → 178; runs repeating ≥5× went 2 → 3. |
| 2 | Timeouts fall below 2/6 | **FALSIFIED**, and unscored anyway: 2/6, unchanged. |
| 3 | Grader-accepted does not fall | **FALSIFIED**, weakly. 5/6 → 4/6 is one run at n=6, well inside noise; recorded as a miss rather than as damage. |

Three for three against. The pre-registration did its job.

## Contention, measured rather than assumed

Aggregate output-token throughput over each pilot, computed identically for
both from message timestamps:

| pilot | throughput |
|---|---|
| cycle 7 | 9.28 tok/s |
| cycle 8 | 7.09 tok/s |

Cycle 8's machine was **~24% slower** — partly this session's own doing, since a
research agent ran on the same host during the pilot. (These figures use a
different method from the 17.46 tok/s in cycle 7's record and are not comparable
with it; the two *here* are comparable with each other, which is what the
comparison needs.)

So the timeout column is confounded in cycle 8's disfavour, exactly as cycle
7's was in its favour. Neither is claimed. **The repetition counts are not
confounded** — a slower machine gives a child fewer opportunities to repeat a
command, not more, so 93 → 178 survives the caveat and if anything understates.

## What this cycle actually bought

A negative result, an instrument, and — through the research it prompted —
something considerably larger than the cycle was scoped for. See cycle 9: **the
child has never been hermetic.** Every child in every orchestrated arm loaded
the operator's own Pi extensions, including one that rewrites bash commands.
The evidence is in this pilot's own transcripts.

That finding outranks the runaway child, and it arrived because a cheap fix
failed and forced a proper look at how the child is launched.

## Evidence

`~/local-ai-pi-evidence/satyrn-phase5-cycle8-childfix-n6-t300.jsonl`, outside
version control, retaining full `pi_stdout`. Every figure recomputes with
`docs/superpowers/research/2026-08-04-phase5-cycle8-child-analysis.py`.

## What stays

The `implementer.md` correction is **kept**, not reverted. It is true, it is
cheap, and one run in this pilot did reach validation and stop. It is simply
not load-bearing, and no later record should cite it as the reason for anything.
