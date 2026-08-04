# Phase 5 cycle 6 — the loop-breaker extension

**Date:** 2026-08-04
**Status:** design
**Phase:** 5 — the improvement loop

## Purpose

Stop a small local model repeating the same tool call forever. This is the
phase's **installable artifact** — the first thing this project produces that
a contributor could load into their own Pi and benefit from without adopting
the harness.

The failure is measured, not hypothetical: one cycle-4 run executed 261 turns
of which **245 were the identical `ls -R`**, each returning `(no output)`,
writing nothing. The owner reports recursive listing has been near the top of
their problems for a month.

## Why an extension, and why ours

Pi ships **nothing** for this: no `--max-turns`, no loop detection, no
tool-call budget. Upstream has declined to add one and pointed users at
extensions — issue #1898 (*"this can be solved by an extension"*), #5248, and
#6158, which reports this exact scenario on a small quantized local model.

The one implementation in the owner's own checkout, on the unmerged
`pi-circuit-breaker` branch, tracks `maxIdenticalFailingToolCalls` and
**explicitly excludes repeated successful calls**. Every one of our 245
`ls -R` calls *succeeded*. It would not have fired.

`pi.on("tool_call")` returning `{ block: true, reason }` is documented in
installed 0.83.0 (`docs/extensions.md:70-73, 765, 770-781`) and verified
present in `dist/core/agent-session.js`. That hook fires **before execution**,
so a detector on it cannot know whether the call would have succeeded — which
makes success-agnosticism a property of the mechanism rather than a decision
to defend.

## The policy

A ring buffer of the last **20** tool calls. Key: `toolName` plus a
stably-serialised copy of the call's input. When a key's count within that
window reaches **5**, block it.

The blocked call returns a `reason` that steers rather than merely refusing —
it names the repetition, states that the result will not change, and tells the
model to act on what it already has. A bare refusal invites the model to retry
a sixth time.

Numbers are the shape used by `@mjasnikovs/pi-task`'s `loop-detector.ts`
(window 20, threshold 5), adopted as a starting point rather than derived.
Five is well below 245 and well above the 1 repetition that cycle 5's pilot
still showed, so it should not fire on healthy runs.

## How it becomes measurable

The extension calls `pi.appendEntry("loop_broken", …)` on each block.
`RunTelemetry.custom_entries` already parses `entry_appended`, so **no harness
change is needed** to count blocks per run. Phase 3 cycle 1's finding applies:
entries must be appended after print mode subscribes, so this happens inside
the `tool_call` handler, well after `agent_start`.

## How it composes

`Improvement.extensions` is already a tuple, so a new improvement,
`sdd-orchestrator-guarded`, carries **both** Pi's shipped subagent `index.ts`
and our `loop-breaker.ts`, with the same seed and prompt as
`sdd-orchestrator`. This honours the phase's binding rule — a run has exactly
one improvement or none — without inventing composition machinery.

The unguarded `sdd-orchestrator` stays, because cycle 8 needs it as the
comparison.

## Verification

1. **Offline replay** over the four banked batches: for each recorded run,
   apply the policy to its `tool_execution_start` sequence and report where it
   would first have tripped. Zero model time, real data. This answers *"would
   it have stopped run 1 at call 5 instead of 245?"*
   **Stated limitation:** the replay reimplements the policy in Python; the
   extension implements it in TypeScript. They can diverge. The replay is an
   *analysis of the rule*, not a test of the shipped code, and the live smoke
   is what proves the code. The rule is kept trivially small for exactly this
   reason.
2. **Live smoke**: one run with the guarded improvement, asserting at least
   one `loop_broken` entry appears in telemetry when a loop occurs — or that
   none appears and the run behaves normally, which is also informative.
3. **n=6 pilot at `run_timeout=300`**, now expressible through `run_batch`
   thanks to the corrective. Never published.

## Pre-registered predictions

1. **Replay trips on cycle 4's run 1 at or before call 10**, having seen 5
   identical `ls -R` calls inside a 20-call window.
2. **Replay trips on few or no cycle 5 pilot runs**, whose worst repetition
   was 1 — if it fires there, the threshold is too tight.
3. **The live pilot shows no acceptance change.** Blocking a loop does not
   supply the missing facts; that is cycle 7.

## Out of scope

- Turn caps, tool-call budgets, and stream-inactivity watchdogs. Each is a
  separate mechanism with its own claim, and the community packages that
  implement them are a Backlog entry, not this cycle.
- Any change to `harness/`, the orchestrator prompt, or the suites.
- Publishing a number. Cycle 8.
