---
name: write-handoff-contract
description: Use when the user wants to hand a coding task to the local bounded implementer via /implement — writes the handoff contract file that /implement consumes. Trigger on "write a contract", "hand this to the implementer", or before running /implement.
---

# Writing a handoff contract

`/implement <file>` runs a small local model against one task, confined to
the files you declare. It cannot plan and it cannot derive a change: handed
a concrete recipe it applies it near-perfectly, and handed a description of
a desired outcome it stalls or edits nothing. **You are the planner. The
contract is the recipe.**

## Before you write

Read the code. The contract's value is entirely in naming real
operations on real files, and every path you name is checked against the
tree before any model call.

## The file

````markdown
---
writableFiles: [src/svcs/_core.py]
readableFiles: [src/svcs/_registry.py, tests/test_container.py]
validation: pytest -q
knownFacts:
  - The app is ASGI, not WSGI.
---
# Enter async context managers in aget()

`Container.aget()` resolves a factory and returns the value. When the
factory returns an async context manager it must be entered.

In `aget()`, after `_lookup` returns `(cached, svc, rs)` and before the
`isawaitable(svc)` branch: if `svc` is an `AbstractAsyncContextManager`
and `rs.enter` is true, `await svc.__aenter__()`, append `(name, svc)` to
`self._on_close`, and rebind `svc` to the entered value.

Follow the pattern already in `get()`, which does the synchronous form.

Leave the `isawaitable` branch and all caching behaviour unchanged.
````

`writableFiles` and `validation` are required. Everything else is optional.

## The rule that decides whether this works

**Name the operation, not the intention.**

| Works (measured 8/8) | Fails (measured 0/8) |
|---|---|
| ``append `(name, svc)` to `self._on_close` `` | "register the resulting cleanup mechanism" |
| ``insert before the `isawaitable(svc)` branch`` | "place the guard appropriately" |
| ``follow the pattern in `get()` `` | "handle the async case similarly" |

The second column reads like a specification and produces runs where the
model emits the same no-op edit nine times and writes nothing at all.

## The rest

- **Bounds are declared, never implied.** A file the implementer must
  change goes in `writableFiles` even if the body names it. A file that
  does not exist yet is fine there — that is how you say "create this".
- **No globs, no `**`.** Name every file exactly, in both `writableFiles`
  and `readableFiles`. A glob parses but the implementer's own path
  normalizer drops it silently — you get a run that can write or read
  nothing, not a refusal.
- **Every backticked path must exist in the tree or be in
  `writableFiles`.** Otherwise `/implement` refuses before spending a
  model call, naming the path.
- **`knownFacts` is for what the tree cannot reveal** — a deployment
  detail, a runtime constraint. One sentence measured as well as a whole
  stack description; do not pad it.
- **Name what must not change.** The implementer is confined but not
  careful.
- **`validation` is what the parent runs to judge the result.** The
  implementer never runs it.

## Then

Save it (a scratch path is fine) and run `/implement <path>`. On refusal,
fix the contract — a refusal costs no model call and names its cause.
