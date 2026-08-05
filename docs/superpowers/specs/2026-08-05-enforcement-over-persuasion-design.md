# Enforcement over persuasion — the stopping condition

**Date:** 2026-08-05
**Status:** design
**Phase:** 6 candidate — the deep dive this project pivoted to Pi for

## The thesis, and the reason it needs stating

This project left OpenCode for Pi because Pi offers **machinery to control
operations** rather than prose to persuade a model with. Phase 5 then spent
four cycles writing prose.

| cycle | intervention | outcome |
|---|---|---|
| 5 | prompt: the call shape | worked |
| 5 | prompt: the workspace is empty | worked |
| 6 | **mechanism: the loop breaker** | built; did not fire for two cycles |
| 7 | prompt: the technology stack | worked |
| 8 | prompt: stop re-running a failing command | **failed, 3/3 predictions falsified** |

The prompt wins share a property cycle 8's loss lacks: they supplied a **fact
the model did not have**. Cycle 8 supplied a **rule of conduct**, and a 12B
model does not keep one. That is the persuasion ceiling, found empirically and
at a cycle's cost.

Meanwhile the one mechanism we built is the only thing that has ever *stopped*
a runaway: in cycle 11's withdrawn arm it refused **22 calls in a single run
that still passed**, and in cycle 10 it refused 12 across two runs, both of
which passed.

**The pivot's premise is correct and we have been under-using it.**

## What the model actually fails at, measured

Three distinct runaway shapes, all recorded, all with different causes:

| shape | evidence | closed by |
|---|---|---|
| **Exploration spiral** | 245 identical `ls -R` in one 261-turn run | a *fact* (cycle 5); gone from every later arm |
| **Identical-call loop** | 83 of 103 child calls one `pytest`; 178× `ls -F` | a *mechanism* (loop breaker) — and by removing rtk (cycle 9) |
| **Revision churn** | same base template written **27 times**; one `<nav>` edited 7× | **nothing yet** |

The third is the subject. It is not a failure to build — two of the first
three control-arm runs were **graded accepted**. It is a failure to *stop*.

**The diagnosis is concrete.** The orchestrated arm's handoff packet carries
Allowed Files, Acceptance Strings, **Validation**, and the implementer's
"once validation passes, report and stop." That is a definition of done. The
control arm has the same two technology facts and no definition of done, and
a user-story roadmap has no terminal condition — there is always another nav
link to polish.

So orchestration's measured contribution is **termination, not correctness**.
That is a weaker claim than phase 5 assumed and the exact claim `BRIEF.md`
says this project exists to test.

## What Pi can actually enforce

Read from the v0.83.0 source at
`/Users/pauleveritt/PycharmProjects/pi-v0.83.0`, whose
`packages/coding-agent/examples/extensions/subagent/index.ts` is byte-identical
to the installed package — so the source below is the source that produced
every measurement we have banked.

`packages/coding-agent/docs/extensions.md` documents 33 events. Four matter
here, and two of them do more than observe:

| hook | power | use |
|---|---|---|
| `tool_call` | **blocks** — `{block, reason}` before execution | what the loop breaker uses today |
| `tool_result` | **patches** `content`, `details`, `isError`, `usage` | put a fact in the channel the model trusts |
| `message_end` | **replaces** the finalized message via `{ message }` | strongest and most invasive |
| `turn_end` | observes `turnIndex`, `message`, `toolResults` | counting, with `ctx.abort()` as the lever |

`tool_result` is the one this project has never used and the one that fits the
thesis best. **A model ignores system-prompt instructions and believes tool
output.** Appending "validation passed — the task is complete, report and
stop" to the *actual pytest output* is not persuasion in a prompt; it is a
fact delivered where facts arrive.

**Pi has no turn cap** at any level — no CLI flag, settings key, or agent
frontmatter — and upstream closed the request for one (#1898, #5248, #6158).
Whatever we build, we build.

## Candidates, cheapest first

**1. The done-detector.** An extension that knows the run's acceptance command,
runs it after any tool call that wrote a file, and on success patches the next
`tool_result` with an unambiguous completion statement — then blocks further
`write`/`edit` calls with a reason naming the passing tests.

This is the direct answer to the measured failure. It converts "definition of
done" from prompt text the orchestrator supplies into a mechanism the harness
enforces, and it works for a bare model with no orchestration at all — which,
if it holds, means the orchestrator is *replaceable by a much smaller thing*.

**2. A revision-churn breaker.** Generalize the loop breaker from *identical*
calls to *same-target* calls: N writes to one path within a window, regardless
of content. The current `callKey` includes arguments, so a rewrite with
different bytes is invisible to it — yet 22 refusals fired in that run anyway,
meaning many rewrites were byte-identical. A path-keyed rule would have caught
the rest.

**3. A turn cap.** ~20 lines counting `turn_end` and calling `ctx.abort()`.
The backstop, not the fix. **Unverified and load-bearing:** `ctx.abort()` is
reported to yield `stopReason: "aborted"`, which the shipped subagent
classifies as a *failed* delegation — converting a runaway into a lost result
rather than a salvaged one. Check before building.

Ranked this way because 1 addresses the cause, 2 addresses the symptom, and 3
only bounds the damage.

## What this must not become

The trap `BRIEF.md` names is machinery about orchestration outgrowing anyone's
head. A done-detector that grows a rules engine, a policy language, or a
scheduler has failed regardless of its numbers. **The target is one extension,
one file, under ~150 lines, with constants at the top** — the loop breaker's
shape, which is now documented, installed, and measured.

## How it gets measured

The comparison is already built and half-banked, all n=16 at 600 s, hermetic:

| arm | status |
|---|---|
| bare | **0/16** — a stopped-to-ask zero |
| tech-stack-only (both facts) | pending |
| orchestrated | **13/16** |

The new arm is **bare + facts + done-detector, no orchestration**. If it
approaches 13/16, orchestration's benefit is reproducible by an extension a
user can install in one file, which is the phase's installable promise
arriving somewhere it was not expected.

**Pre-registration comes with the cycle spec, not here.** This document names
the question; a cycle that pre-registers its predictions before running is the
discipline that caught cycle 8.

## Open questions, honestly flagged

- Does `ctx.abort()` produce a salvageable result or a failed delegation?
  Unverified, and candidate 3 depends on it.
- Can the harness supply the acceptance command to an extension without
  leaking the grading contract into the workload? The suite's acceptance file
  is harness-owned and the model must not read it. A done-detector that runs
  it needs a seam that does not become a channel — this is the design risk of
  candidate 1 and should be settled before any code.
- Is revision churn present in the *orchestrated* arm at lower amplitude, or
  absent? Recomputable from banked checkpoints, and it decides whether
  candidate 2 is a general win or a control-arm artifact.
