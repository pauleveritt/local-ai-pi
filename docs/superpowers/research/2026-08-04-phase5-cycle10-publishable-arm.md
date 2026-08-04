# Phase 5 cycle 10 — the number the phase publishes

**Date:** 2026-08-04
**Cycle:** phase 5 cycle 10 — one publishable arm
**Model:** `omlx/gemma-4-12B-it-MLX-8bit` · **pi:** 0.83.0
**Suite:** `agentclinic-phase-1-user-story` · **n:** 16 at `run_timeout=600`

This is the one comparable arm the phase publishes. Same suite, same n, same
timeout as cycle 4's — the arm that scored zero.

## The result

| arm | run-accepted | grader-accepted | timeouts |
|---|---|---|---|
| cycle 4 — as-shipped orchestrator | **0/16** | **0/16** | 6/16 |
| **cycle 10 — corrected, guarded, stacked, hermetic** | **13/16** | **13/16** | **1/16** |

Fifteen of sixteen runs terminated on their own.

## Why the credit is not the machine

| arm | aggregate throughput |
|---|---|
| cycle 4 | 12.24 tok/s |
| cycle 10 | **10.27 tok/s** |

**Cycle 10's machine was ~16% slower.** Every previous pilot in this phase had
to leave its timeout comparison unscored because the faster machine could
explain it. This one cannot: the arm improved while running slower.

| | cycle 4 | cycle 10 |
|---|---|---|
| median total turns | 30 | **14** |
| max total turns | 261 | **42** |
| median run transcript | 2.65 MB | **0.50 MB** |
| max run transcript | 71.88 MB | **5.66 MB** |
| median total context | 119,204 | **39,760** |
| max total context | 1,814,481 | **674,945** |

Half the turns, a fifth of the transcript, a third of the context.

## What separates the two arms

Four changes, each measured in its own cycle before landing here:

1. **Cycle 5 — the call shape.** `orchestrator.md` never named the `subagent`
   tool's `agent` parameter, so calls were rejected as `"Invalid parameters"`
   and no child ran. Rejections went to zero.
2. **Cycle 5 — the empty workspace, stated as a fact.** The parent's `ls -R`
   spiral went 245 repetitions to 1.
3. **Cycle 7 — the technology stack.** The model was writing Flask, a WSGI
   framework, against an ASGI test client; naming FastAPI and `app.py` took the
   suite off the floor for the first time.
4. **Cycle 9 — the hermetic child.** The delegated child had been loading the
   operator's personal Pi extensions, including one that rewrites bash
   commands. Removing them removed the runaway.

Cycle 8's contribution was a **falsified** prediction and the investigation it
forced. Cycle 6's loop-breaker contributed insurance that finally paid out —
see below.

## The loop-breaker fired, in the child, and both runs still passed

**12 child tool calls refused across runs 1 and 3.** Both runs are
grader-accepted and run-accepted.

This is the first time the guard has fired in a live run in this project's
history, and it is the cleanest possible demonstration of what it is for: run 1
repeated one call 14 times and still finished correctly, because the refusals
steered it out. Cycle 9's prediction 2 — *the loop-breaker fires in the child* —
was falsified at n=6 and is **confirmed at n=16.**

It also confirms cycle 9's separate finding that the guard reaches the child at
all, this time from live evidence rather than a threshold-0 probe.

## The three failures, named

| # | what happened |
|---|---|
| 2 | finished cleanly, did not satisfy the grader |
| 8 | the only timeout; the child itself stopped normally |
| 15 | finished cleanly, did not satisfy the grader |

Two honest wrong answers and one parent-side timeout. **No run in this arm was
killed with a child still calling tools** — the failure mode that dominated
cycles 2, 4, 7 and 8 is absent.

## What this arm does and does not claim

**It claims:** on this suite, this model, and this harness, the corrected,
guarded, stack-informed, hermetic orchestrator reaches 13/16 where the
as-shipped orchestrator reached 0/16, at equal n and equal timeout, on a
slower machine.

**It does not claim** a comparison against bare Pi on this suite. Cycle 4's bare
arm also scored 0/16, but it scored it by *stopping to ask a human what to do*
in all sixteen runs — a floor produced by a different behaviour, and one that
the cycle 7 tech-stack fact would likely also move. A bare arm rerun under
these conditions is the obvious next measurement and is not in this record.

**It does not claim** the cost comparison from cycle 2 still holds. That arm's
child was contaminated, and its ratios are now lower bounds.

## Evidence

`~/local-ai-pi-evidence/satyrn-phase5-cycle10-hermetic-n16-t600.jsonl`, outside
version control, retaining full `pi_stdout`. Recompute with
`docs/superpowers/research/2026-08-04-phase5-cycle8-child-analysis.py`.
