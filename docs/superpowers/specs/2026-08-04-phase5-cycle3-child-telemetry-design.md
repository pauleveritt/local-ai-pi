# Phase 5 cycle 3 — telemetry counts the delegated child

**Date:** 2026-08-04
**Status:** design
**Phase:** 5 — the improvement loop

## Purpose

`read_telemetry` parses the parent's own events, so a delegated run's `turns`
and `context_processed` omit the child entirely. On cycle 2's orchestrated arm
that omission was not a rounding error: it reported **1.15×** the bare arm's
context when the true figure was **8.11×**, and it reported orchestration as
*cheaper* when it is 2.5× more expensive in generation.

Cycle 2's research script was patched to work around this. That is the wrong
place. Every future orchestrated batch reads through `harness/telemetry.py`,
and a workaround living in one research file protects exactly one document.

**This cycle claims no number and runs no batch.** It is parsing data already
present in checkpoints we have.

## The data is already there

Pi's shipped subagent extension aggregates the child's `message_end` usage and
surfaces it in the parent's `tool_execution_end` result:

```
result.details.results[] -> { agent, exitCode, usage, model, stopReason, ... }
usage -> { input, output, cacheRead, cacheWrite, cost, contextTokens, turns }
```

So this is a parsing change, not new measurement, and it **recomputes
retroactively over every batch already recorded** — cycle 2's included —
because checkpoints retain raw `pi_stdout`. That property is why the fix is
cheap now and why deferring it would be a false economy.

## What gets added

A frozen `Delegation` record per successful child, mirroring the existing
`ToolCall` pattern, plus a tuple on `RunTelemetry`:

```python
@dataclass(frozen=True)
class Delegation:
    agent: str
    turns: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    exit_code: int | None
```

with derived properties for `child_turns`, `child_context_processed`,
`child_output_tokens`, and `total_*` counterparts.

**Existing fields keep their meaning exactly.** `turns` stays the count of the
parent's `turn_end` events; `context_processed` stays the parent's. Nothing
already published changes meaning — the new numbers arrive under new names.
This matters because `turn` is a **pinned** term: any redefinition invalidates
every number this instrument has produced.

## One definitional asymmetry, stated rather than hidden

The parent's `turns` is counted by this project, one per `turn_end` event.
The child's turn count is *reported by Pi's extension*, which derives it from
the child's own stream. Both are called turns and they are not measured the
same way. `Delegation.turns` therefore carries the child's own claim, and the
docstring says so. If the two ever need to be strictly comparable, the child's
raw stream is not in the parent's stdout and would have to be captured
separately — which is the deferred parent/child attribution work, still
deferred.

## Scope boundaries

- **Only successful delegations count.** A `tool_execution_end` with
  `isError: true` carries no usable usage; cycle 1 found one whose result was
  the string `"Tool subagent not found"`. Failed calls are not counted and not
  silently treated as zero-cost successes.
- **`contextTokens` is ignored.** It is a context-window size, not a workload
  measure. `context_processed` remains `input + cacheRead + cacheWrite`, the
  definition phase 2 cycle 1 pinned.
- **`cost` is ignored.** It reads 0 against a local server and would invite a
  cost claim this project has never made.
- **No grand-total field on `RunResult`,** and no change to `RunConditions`.
  Telemetry stays a derived, recomputable view.

## Verification

Mutation checks, each with a named test: drop the child's `cacheRead` from the
sum and watch the context test fail; count failed delegations and watch the
error-handling test fail; leave `total_turns` returning the parent's count and
watch the totals test fail.

The regression that motivates the cycle gets its own test: a fixture built
from a **real** cycle-2 orchestrated run, asserting `total_context_processed`
is several times `context_processed`. A synthetic fixture would pass while
the shape of Pi's payload drifted underneath it.

Cycle 2's recompute script drops its local `child_usage` helper and calls the
instrument instead, so the published table and the harness cannot diverge.

## What this does not do

It does not attribute cost *within* a delegation, does not capture the child's
raw stream, and does not change any recorded evidence — checkpoints are
untouched. It makes the existing evidence readable, which it was not.
