# The loop breaker

A small Pi extension that refuses a tool call the model has already made,
unchanged, several times in a row.

It exists because of one recorded run: **261 turns, of which 245 were the
identical command `ls -R`**, each returning nothing because the workspace was
genuinely empty. The model never concluded it should create files. It was
still going when the harness killed it.

That is not an exotic failure. On a small local model it is the common one.

## What it does

On every tool call, the extension builds a stable key from the tool name and
its arguments, and remembers the last `WINDOW` calls. If the same key has
already appeared `THRESHOLD` times in that window, the call is **blocked
before it executes** and the model is told why:

> You have already run this exact bash call 5 times in a row and the result
> will not change. Do not repeat it. Use what you already know and take the
> next concrete action — if you were looking for files and found none, create
> them.

The model receives that as the tool's result and carries on. Nothing is
killed, and no turn budget is consumed by the refusal.

**It counts repeats whether or not the call succeeded.** All 245 of those
`ls -R` calls succeeded. A breaker that only counts *failing* repeats would
not have fired once — and `tool_call` fires before execution, so success is
not knowable at the point the decision is made.

## What it is worth, measured

Live, in a 16-run batch: it fired in two runs, refusing **12 calls**, and
**both of those runs still passed their acceptance tests**. One of them had
repeated a single call 14 times and finished correctly after being steered
out of it.

That is the whole case for it. It is insurance that mostly does nothing, and
the runs where it does something are runs you would otherwise have lost.

> **Correction, 2026-08-10.** This section previously led with "zero false
> positives across 55 healthy runs", from a replay over five banked batches.
> That replay keyed on `tool_execution_start` events, which include calls
> that never reach `beforeToolCall` — Pi validates tool arguments first and
> raises above the hook. The hook therefore sees a *compressed* subsequence
> of what was replayed, in which identical calls sit closer together, so a
> window that stayed under threshold in replay can cross it live. The replay
> errs optimistic and **does not bound the live false-positive rate**; the
> figure is withdrawn. The 16-run live result above was measured through the
> hook itself and stands unchanged. The "239 of 261" figure is withdrawn for
> the same reason.

## Installing it

The loop breaker ships **inside the engine** — `packages/engine/engine.ts`
bundles both guards, and the engine is the install ([using the engine](usage.md)
is the quick start). There is no standalone loop-breaker install; the guard
comes with the engine, either in a checkout (`.pi/extensions/` loads it with
zero install) or via the pi package.

Pi loads user-scope extensions unconditionally. Project-scope extensions are
**trust-gated**: an interactive session will ask, and a non-interactive one
(`-p`, `--mode json`) skips them unless you pass `--approve` or have already
recorded a trust decision for that directory.

To load it explicitly for a single run, pass the **file** — not its
directory, which fails silently:

```bash
pi --extension ./packages/engine/engine.ts "your prompt"
```

## The thing that will surprise you: subagents

If you delegate work to a subagent, **the child does not load your project's
extensions.** It loads your *user-scope* ones.

Pi's shipped subagent extension spawns the child as `pi --mode json -p
--no-session [...]`, and project resources in the child are trust-gated with
no stored decision to consult. So a loop breaker in `.pi/extensions/` guards
the parent and leaves the child unguarded — and on a small model the child is
where the runaway usually is.

**Put it in `~/.pi/agent/extensions/` if you use subagents at all.** That is
the only route that reaches them.

We learned this the expensive way: a whole development cycle was spent
concluding that a guard could not be delivered to a delegated child, before
the user-scope route was tried.

## Tuning

Two constants at the top of the file:

| constant | default | meaning |
|---|---|---|
| `WINDOW` | 20 | how many recent calls are remembered; older ones stop counting |
| `THRESHOLD` | 5 | identical calls within that window before the next is refused |

The defaults are deliberately forgiving. Five identical calls is well past
anything a working model does by accident, and a 20-call window means a
legitimately repeated command — running the same test after each of several
edits — falls out of memory before it trips.

Lower `THRESHOLD` if your model spirals faster than it recovers. Raise
`WINDOW` if it interleaves a long repeated sequence rather than repeating
back-to-back.

Setting `THRESHOLD` to 0 blocks every call, which is only useful for checking
that the extension is loaded at all — which, given the subagent behaviour
above, is a thing worth checking.

## What it is not

It is not a turn cap. Pi has none — not as a CLI flag, a settings key, or
agent frontmatter — and upstream has declined to add one, pointing users at
extensions. This is one such extension, and it addresses looping specifically:
a model doing genuine, varied work for a very long time is untouched by it.
