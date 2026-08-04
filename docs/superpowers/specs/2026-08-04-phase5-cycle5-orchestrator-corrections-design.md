# Phase 5 cycle 5 — correct the orchestrator's instructions

**Date:** 2026-08-04
**Status:** design
**Phase:** 5 — the improvement loop

## Purpose

Two defects in `improvements/sdd-orchestrator/orchestrator.md` account for
most of the orchestrator's observed failures. Both are prompt lines. This is a
**correction to a demonstrably broken artifact, not a lever** — tuning from a
broken baseline measures the wrong thing, which is why it precedes cycle 7.

**Claims no publishable number.** One smoke run and an n=6 pilot at
`run_timeout=300`, neither comparable with the n=16/600 s arms.

## Defect 1 — the prompt never states the tool's call shape

Pi's shipped subagent tool takes flat parameters and infers the mode from
which are present (`examples/extensions/subagent/index.ts:448-500`, installed
0.83.0):

```
hasSingle = Boolean(params.agent && params.task)
modeCount = hasChain + hasTasks + hasSingle
if (modeCount !== 1) -> "Invalid parameters. Provide exactly one mode."
```

**Verified from the banked streams**: every rejected call in this project sent
`{agentScope, task}` and **omitted `agent`**. Four occurrences — cycle 2 runs
10, 13, 15 and cycle 4 run 14 — each producing no child at all. Run 13's
*only* completed call was such a rejection, so it delegated nothing.

`orchestrator.md` currently says "delegate it to the `implementer` specialist
using the `subagent` tool". It names the specialist in prose and never says
which parameter carries it. The correction states the call shape literally:
`agent: "implementer"`, `task: <the packet text>`, `agentScope: "both"`.

An earlier reading of this defect guessed the model was passing a `packet`
object, on the strength of cycle 1's spike. The streams say otherwise. Both
readings implied the same fix, but the record should say what was measured.

**Why this is invisible to every check we have:** the rejection is returned as
a *non-error* `tool_execution_end` with an empty `results[]`, so nothing keyed
on `isError` can see it. `harness/telemetry.py` already gets this right by
counting delegations only when child usage comes back; the corrected recompute
script now agrees.

## Defect 2 — the prompt never says the workspace is empty

The most economical account of both cycle 4 arms:

- **Bare**, 16/16 runs: exactly one turn, no tool calls, nothing written. Each
  read the spec, restated it accurately, and asked a human which file to start
  with. There is no human in a headless run.
- **Orchestrated**, run 1: 261 turns, of which **245 were the identical
  `ls -R`**, each returning `(no output)` because the workspace genuinely was
  empty. It never concluded that it should create files.

Both behaviours are consistent with a model that believes it is joining an
existing project. The correction states that the workspace is empty, that no
files exist yet, and that everything must be created.

**It must not name a framework, module, or file path.** That is cycle 7's
lever, and leaking it here would destroy the experiment the user-story suite
exists to run — the same reasoning that shaped that suite's environment note.

## What gets changed

`improvements/sdd-orchestrator/orchestrator.md` only. The implementer
specialist is untouched: it never calls the tool, and no evidence implicates
it.

Changing the file changes `improvement_digest`, so no existing checkpoint
resumes. That is correct and expected — these are different run conditions.

## Verification, cheapest first

1. **Static assertions**, no model. The prompt must name `agent`, `task`, and
   `agentScope`; must contain the literal `implementer`; must state the
   workspace is empty; and must **not** contain framework or module names.
   The parameter names are read from the shipped tool's own `SubagentParams`
   schema rather than hardcoded, so the test fails if Pi renames them instead
   of rotting quietly.
2. **One smoke run** on the user-story suite at `timeout=300`, asserting a
   delegation completes with real child usage.
3. **n=6 pilot**, `run_timeout=300`, orchestrated, user-story suite.

## Pre-registered predictions

Written before the smoke run.

1. **Parameter rejections fall to zero.** A call carrying `agent` cannot
   produce `modeCount == 0`.
2. **More runs write files than cycle 4's 11/16.** Stated as a direction, not
   a threshold: n=6 cannot resolve a small difference.
3. **Acceptance stays at or near zero.** The two missing facts — the module
   name and the framework — are untouched by this cycle, and cycle 4 showed
   runs that built plausible apps still failing on them.

A pilot that shows rejections gone and acceptance still zero is a **success
for this cycle**: it isolates the remaining failure to the facts cycle 7
supplies.

## Out of scope

- The loop-breaker extension (cycle 6). Run 1's 245 repetitions are not
  addressed here, and the pilot may well show another.
- The tech-stack lever (cycle 7).
- Any n=16 arm (cycle 8), any change under `harness/`, and any change to the
  implementer specialist or the packet's four sections.
