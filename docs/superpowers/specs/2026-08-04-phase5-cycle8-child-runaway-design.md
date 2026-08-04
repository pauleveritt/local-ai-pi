# Phase 5 cycle 8 — the runaway child

**Date:** 2026-08-04
**Status:** design
**Phase:** 5 — the improvement loop

## Purpose

The last known cause of a *correct* solution failing its run. Cycles 5–7
closed the parameter defect, the exploration spiral, and the framework
mistake; the user-story suite now reaches 5/6 grader-accepted. What still
costs runs is the delegated child running until the harness kills it.

The phase's target is a **useful baseline orchestrator**, and one that solves
the task but does not terminate is not that.

## What the child is actually doing — measured

Both timed-out runs in cycle 7's pilot were killed with the child still going,
`stopReason: "toolUse"`, at **98 and 103 turns**, producing 9–10 MB of stdout.

Extracting the child's own tool calls from the parent's
`tool_execution_update` payload for one of them:

| count | command |
|---|---|
| **77** | `python3 -m pytest tests/test_app.py` |
| 4 | `python -m pytest tests/test_app.py` |
| 2 | `pytest tests/test_app.py` |
| 2 | writing `tests/test_app.py` |
| rest | `ls`, `mkdir`, `pip list` |

**103 bash calls, 83 of them the same test command.** This is not a hang and
not a stall. It is the same repeated-identical-call loop the loop-breaker was
built for — running in the one process the loop-breaker cannot see.

That is why the breaker never fired in cycles 6 and 7: **the parent does not
loop; the child does.**

## Why the obvious fix does not work

The child is spawned by Pi's shipped subagent extension as
`pi --mode json -p --no-session [--model] [--tools] [--append-system-prompt]`
— **no `--no-extensions`**, which suggested it would pick up a project-local
extension seeded into the workspace, exactly as `.pi/agents/` already reaches
it.

It does not. Verified 2026-08-04 with a probe extension that appends an entry
on `agent_start`: a child-style invocation with the extension in
`cwd/.pi/extensions/` produced **no entry, and adding `--approve` changed
nothing.** Agents are discovered from cwd; extensions are not. That asymmetry
is now a Backlog deep-dive item — the third extension-loading surprise this
project has paid for.

So the guard cannot be delivered to the child without controlling the child's
arguments, and those belong to the shipped extension.

## What this cycle does instead, and why that order

**A prompt correction to the implementer specialist**, not a mechanism.

`improvements/sdd-orchestrator/seed/.pi/agents/implementer.md` currently says
"Run validation before you report completion" and nothing about what to do
when validation fails. The child obeys it literally and forever.

The correction: if the validation command fails twice with the same output,
stop re-running it — change the code or report the failure with what it
printed. Report and stop once it passes.

**Why prompt-first here**, given cycle 6 argued a mechanism beats a prompt:
the mechanism is not available, the two previous prompt corrections both
worked (parameters, and the exploration spiral), and this is the cheapest
thing that could work. If it fails, the alternative is well-defined and its
gate is now met — see below.

## The Backlog gate this evidence fires

The Backlog holds "our own minimal subagent tool — gated on evidence, not
preference," to be adopted when "a measured run shows the shipped extension
contaminating or losing a measurement."

**That gate is now met.** Two runs of six lost their result to a child the
shipped extension spawned with arguments we cannot influence, and the guard we
already built cannot reach it. Our own tool would spawn the child with
`--extension` pointing at the loop-breaker, which is the whole difference.

This cycle does not build it. It tries the cheap fix first and records that
the expensive one is now justified rather than merely wanted.

## Pre-registered predictions

1. **The child's repeated-test-command count falls sharply** — no child runs
   the same validation command dozens of times.
2. **Timeouts fall below cycle 7's 2/6.** Weak: n=6 cannot resolve small
   differences, and cycle 7's own timeout comparison was unscored for
   contention.
3. **Grader-accepted does not fall.** The correction must not cost
   correctness by making the child give up early.

## Verification

1. Static assertion: the specialist names the stop condition.
2. One smoke run: child turn count and repeated-command count, read from the
   parent's payload.
3. n=6 pilot at `run_timeout=300`, uncontended.

## Out of scope

- Building our own subagent tool. Gated, justified, and not this cycle.
- Turn caps and watchdogs generally.
- The n=16 arm, which follows immediately after this cycle.
