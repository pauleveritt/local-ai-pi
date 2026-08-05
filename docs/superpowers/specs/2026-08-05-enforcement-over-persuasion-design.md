# Enforcement over persuasion — the stopping condition

**Date:** 2026-08-05
**Status:** design — **substantially revised the same day, after review**
**Phase:** 6 candidate — the deep dive this project pivoted to Pi for

> **What the first draft got wrong.** It claimed the facts-only arm "builds
> correctly but never stops." A full recount of all eight withdrawn runs — the
> first draft sampled three — gives **7/8 grader-accepted, 6/8 run-accepted**,
> churn in only two runs, and the single grading failure caused by stopping
> **too early**. The diagnosis is refuted by its own evidence. The thesis about
> enforcement survives; the specific claim it was hung on does not. Sections
> below are rewritten rather than annotated: a reader following a superseded
> argument through footnotes is worse served than one reading the corrected one.

## The thesis

This project left OpenCode for Pi because Pi offers **machinery to control
operations** rather than prose to persuade a model with. Phase 5 then spent
four cycles writing prose.

| cycle | intervention | outcome |
|---|---|---|
| 5 | prompt: the call shape | worked |
| 5 | prompt: the workspace is empty | worked |
| 6 | **mechanism: the loop breaker** | built; idle until cycle 10 |
| 7 | prompt: the technology stack | worked |
| 8 | prompt: stop re-running a failing command | **failed, 3/3 predictions falsified** |

The prompt wins share a property cycle 8's loss lacks: they supplied a **fact
the model did not have**. Cycle 8 supplied a **rule of conduct**, and a 12B
model does not keep one. That is the persuasion ceiling, found empirically.

The loop breaker's idle cycles were **not** a weakness of the mechanism: the
parent had stopped looping and the child it could not reach was the one
looping (cycle 8's finding). Once cycle 9 delivered it to the child, it fired.

**It is now the only intervention that has demonstrably arrested a runaway.**
In all four churning runs across both arms, the thing that intervened was the
loop breaker — 10 and 2 refusals in cycle 10's children, 22 and 2 in the
withdrawn arm. All four runs were grader-accepted.

**The pivot's premise is correct and we have been under-using it.**

## What the model actually fails at, measured

| shape | evidence | closed by |
|---|---|---|
| **Exploration spiral** | 245 identical `ls -R` in one cycle-4 run | a *fact* (cycle 5); gone from every later arm |
| **Identical-call loop** | 77 identical `pytest` in one child; 178× `ls -F` | a *mechanism* (loop breaker), plus removing rtk (cycle 9) |
| **Revision churn** | 27× one template; 19× `app.py` in an orchestrated child | the loop breaker, partially |

**Corrected from the first draft**, which wrote row 2 as "83 of 103 child calls
one `pytest`". That is the *pre-correction* figure from cycle 8's design spec:
83 was three different pytest spellings, only 77 identical. Cycle 8's research
record already corrected it, and a project that publishes correction banners
must not re-cite a number it retracted.

### Churn is real, rarer than claimed, and does not separate the arms

Recount of all eight runs of the withdrawn facts-only arm:

| | facts-only (n=8, withdrawn) | orchestrated (n=16, cycle 10) |
|---|---|---|
| grader-accepted | **7/8** | 13/16 |
| run-accepted | **6/8** | 13/16 |
| runs with churn | **2** (27× and 7× one template) | **2** (19× and 10× `app.py`) |
| churning runs that passed | 2 of 2 | 2 of 2 |

Churn appears in **both** arms at comparable amplitude, and every churning run
in both was accepted. The handoff packet's Allowed Files / Validation / "report
and stop" — the definition of done the first draft credited — **does not
prevent churn either.** That settles the open question the first draft raised,
against the first draft.

The facts-only arm's one grading failure, run 4, made **three tool calls**,
announced it would create `app.py`, and halted with nothing written — the same
announce-and-halt shape as the bare arm. **Its failure was failing to start.**

## What this does to the orchestration claim

The first draft concluded "orchestration contributes termination, not
correctness." **That is unsupported.** At 7/8 against 13/16, once the two
technology facts are supplied, orchestration's measured contribution is
**indistinguishable from zero** — not termination, not correctness, neither.

n=8 cannot establish that it *is* zero. It comfortably refutes the claim that
it is specifically termination, because the arm without orchestration
terminated in seven of eight runs.

**The in-flight n=16 facts-only arm settles this, and this document should wait
for it.** If that arm lands near 13/16, phase 5's honest headline is that
**cycle 7's two sentences did nearly all the work** and the orchestrator is
scaffolding. That is a real result, and not the one the phase assumed.

## What Pi can actually enforce

Read from the v0.83.0 source at `/Users/pauleveritt/PycharmProjects/pi-v0.83.0`,
whose `packages/coding-agent/examples/extensions/subagent/index.ts` is
byte-identical to the installed package.

| hook | power |
|---|---|
| `tool_call` | **blocks** — `{block, reason}`; the block returns to the model as an error tool result and the loop continues |
| `tool_result` | **patches** `content`/`details`/`isError`/`usage`, and the patched value enters the next request |
| `message_end` | **replaces** the finalized message via `{message}` |
| `context` | rewrites or injects messages before a request |
| `pi.sendUserMessage` | injects steering as a user turn |
| `turn_end` | observes only; `ctx.abort()` is the lever |

`tool_result` patches are **model-visible**, not merely recorded — the patched
result becomes the `toolResult` message pushed into the live context. The
premise "a model ignores prompt text and believes tool output" holds
mechanically, not just rhetorically.

**Pi has no turn cap** at any level, and upstream closed #1898, #5248 and #6158
without shipping one. `shouldStopAfterTurn` and per-tool `terminate` exist in
agent-core but are unreachable from an extension in 0.83.0.

## Candidates

**1. A graceful turn budget — smallest, and it fixes the only measured loss.**
Past N turns, block every `tool_call` with a reason instructing the model to
summarize and stop. The run ends with a normal `stopReason` and its output is
salvaged.

This dominates `ctx.abort()`, now **confirmed** to yield `stopReason:
"aborted"`, which the shipped subagent classifies as a *failed* delegation
(`index.ts:182-184`) — converting a runaway into a lost result. The first draft
flagged this as unverified; it is verified, which is why abort is dropped
rather than ranked.

**2. A path-keyed churn breaker.** Generalize the loop breaker from *identical*
calls to *same-target* calls: N writes to one path in a window, regardless of
content. The current key includes arguments, which is why 26 of the 27
byte-identical template writes tripped it and the rest did not.

**3. The done-detector — demoted.** Watch for the model's own validation
command passing, patch that `tool_result` with a completion statement, then
block further `write`/`edit`. Three failure modes, the first disqualifying as a
motivating case:

- **It would never have fired in its own flagship run.** The 27×-template run
  ran `python -m pytest` once, at call 14 of 58: **`collected 0`, no tests
  ran** — the model never wrote a test file. All 44 churning calls came after.
  The first draft's "correct degradation" clause describes precisely the run
  the design was motivated by. It would have helped the *other* churn run,
  which reached `2 passed` and then churned 22 more calls.
- **Premature fire.** A model writing tests incrementally gets blocked at the
  first green pytest, possibly mid-build, turning a would-pass run into a fail.
- **Bypass and fragility.** Blocking `write`/`edit` does not block `bash`; an
  observed child created a test file with a `cat <<EOF >` heredoc. Validation
  is invoked four different ways across banked runs, so exact-string matching
  both misses and misfires.

**Both churning runs were graded accepted anyway**, so this detector would have
changed **zero grades** in all observed data. Its benefit is wall clock and
tokens — not the metric the comparison table uses.

Reordered from the first draft, which ranked the done-detector first on
intuition. The evidence ranks it last.

## What this must not become

One extension, one file, under ~150 lines, constants at the top — the loop
breaker's shape, which is documented, installed, and measured.

## How it gets measured

| arm | status |
|---|---|
| bare | **0/16** — a stopped-to-ask zero; the one run that built used Flask |
| facts-only | **7/8 withdrawn**; n=16 in flight |
| orchestrated | **13/16** |

**No new arm should run until the facts-only n=16 lands.** If orchestration's
contribution is near zero, the bar a mechanism must clear changes from "replace
the orchestrator" to "beat the facts alone" — a different and much harder
question.

Pre-registration comes with the cycle spec, not here.

## Settled before any code: the acceptance-command seam

### The contract is *nearly* public, not entirely

The first draft claimed the contract asserts nothing the task spec already
states. Refuted in three particulars:

- **`lang` exact match.** The contract requires `lang` to casefold to exactly
  `"en"`; the spec says "declared as English". `lang="en-US"` satisfies the
  prose and fails the contract.
- **Nav link text equality.** Link text must equal exactly `home` /
  `complaints` after normalization; "Back to Home" satisfies the prose and
  fails.
- **The `templates/` directory is an unstated layout contract.** The allowlist
  copies `app.py` and `templates` only, so HTML under `views/` passes locally
  and fails grading — while `stack.md` says template filenames are not
  prescribed and the contract's own docstring disclaims file layout.

None hurt an observed run. But "the only thing the contract adds is `from app
import app`" was false as written, and the third is a genuine hidden coupling
worth its own Backlog entry.

### The oracle argument stands, and it is the real reason

Running the harness's contract mid-run would give an arm a **perfect
done-signal no earlier arm had**. That is a capability, not an information
leak, and redacting failure text does not remove it — even one bit of "you are
done" is an advantage cycle 10 lacked. The leak framing is the dangerous one
precisely because it invites a fix that leaves the oracle intact.

### The decision, unchanged

**A detector must never touch the harness's acceptance file.** Its signal is
the model's own validation command. A structural guarantee backs it: `grade()`
copies allowlisted paths out to a fresh temp directory, so the acceptance file
is never in the workspace during a run.

One correction to the first draft's justification: it said the design gives the
arm "no capability the others lacked." **Enforced write-blocking is a
capability no other arm had** — that is the intervention under test, which is
fine, but the sentence contradicted the capability-not-information logic beside
it.

## Open questions

- Does revision churn cost anything measurable? In every observed case it was
  survivable. If it costs only wall clock, it may not deserve a mechanism at
  all — and this document should say so rather than build one.
- Is the `templates/` allowlist coupling worth fixing in the suite, given it
  contradicts the acceptance file's own docstring?
