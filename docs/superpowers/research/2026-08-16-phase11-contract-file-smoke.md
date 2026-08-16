# Phase 11 contract-file smoke test

**n=1, a wiring check, not a rate.**

**Date:** 2026-08-16
**`pi --version`:** 0.84.1
**Model:** `omlx/gemma-4-12B-it-MLX-8bit`
**Task:** `async-cm-enter` (`workloads/svcs/tasks/async-cm-enter`), against a
clean `svcs` checkout materialized at `base_sha`
`25d8a0b3ff5fdaa47648802088ef99becde27e6d`.

The question this checks is only whether the path works end to end: a
contract authored through the `write-handoff-contract` skill's
instructions, consumed by `deliver_candidate.py --contract`, driving the
implementer child, judged, and reported — and separately, that a bad
contract refuses before any model call. It claims nothing about outcome
rates; the reference `async-cm-enter` contract's 8/8 belongs to the
spike, not to this run.

## The contract used

Written by reading `src/svcs/_core.py` at the materialized base tree, not
copied from `workloads/svcs/contracts/locating/async-cm-enter.md`.

````markdown
---
writableFiles: [src/svcs/_core.py]
readableFiles: [src/svcs/**, tests/**]
validation: pytest -q -p no:cacheprovider
knownFacts:
  - "svcs targets Python 3.14."
---
# Enter async context managers returned by async factories in aget()

`Container.aget()` (`src/svcs/_core.py`) resolves each service through
`self._lookup(svc_type)`, which returns `(cached, svc, name, enter)`. When
the registered factory is an async function, `rs.factory(...)` returns a
coroutine object, not yet awaited.

In `aget()`'s per-service loop there are three branches, in order:

```
if enter and isinstance(svc, AbstractAsyncContextManager):
    self._on_close.append((name, svc))
    svc = await svc.__aenter__()
elif enter and isinstance(svc, AbstractContextManager):
    self._on_close.append((name, svc))
    svc = svc.__enter__()
elif isawaitable(svc):
    svc = await svc
```

The first branch only catches a factory that returns an async context
manager *directly*, without needing an await. The third branch awaits an
async factory's coroutine but never checks whether the value it produces
is itself an async context manager -- so a factory shaped like
`async def factory(): return some_acm` is awaited, never entered, and its
`_on_close` cleanup never runs.

Change the third branch. After `svc = await svc`, if `enter` is true and
the resulting `svc` is an instance of `AbstractAsyncContextManager`,
append `(name, svc)` to `self._on_close` and rebind `svc` to
`await svc.__aenter__()`.

Leave the first two branches and `Container.get()` unchanged.
````

## The live run

```
uv run python -m tools.deliver_candidate \
    --repo <svcs-checkout> --task smoke-async-cm \
    --contract /tmp/smoke-async-cm-enter.md \
    --model omlx/gemma-4-12B-it-MLX-8bit \
    --receipt /tmp/smoke-receipt.json
```

Ran with the cohort's frozen dependency environment
(`workloads/svcs/env`, `ensure_cohort_env`) on `PATH` and the worktree's
`src/` on `PYTHONPATH`, so `pytest` inside the candidate worktree could
actually import `svcs` and its dependencies — the same shape the batch
driver (`tools/run_cycle7_confirmatory_batch.py`) sets up, applied here
by hand since the CLI itself has no `--validation-env` flag.

| Field | Value |
|---|---|
| receipt `outcome` | `discarded` |
| `refusal` | "candidate changed nothing" |
| `child_exit` | 0 |
| `child_timed_out` | `false` |
| wall-clock (`child`) | 22.6s |
| wall-clock (`total`) | 22.8s |
| exit code | 1 |

The child ran to completion, wrote nothing, and the receipt says so
plainly — no silent zero, no misclassification as an infrastructure
failure (the model server answered; this is a model outcome, not a setup
one). This is a valid, judged wiring-check result: exit 1 with a reason
is one of the two outcomes the plan calls passing. It says nothing about
whether a different attempt, a different day, or the skill's own
practice with harder prompts would score differently — that measurement
is explicitly Phase 14's, not this smoke test's.

## The refusal check

```
printf -- '---\nwritableFiles: [src/svcs/_core.py]\nvalidation: pytest -q\n---\nEdit `src/svcs/container.py`.\n' > /tmp/bad-contract.md
uv run python -m tools.deliver_candidate \
    --repo <svcs-checkout> --task smoke-refusal \
    --contract /tmp/bad-contract.md \
    --model omlx/gemma-4-12B-it-MLX-8bit
```

| Field | Value |
|---|---|
| exit code | 2 |
| message | `refused: the contract names src/svcs/container.py -- neither in the base tree nor in writableFiles, so it can be neither read nor created` |
| duration | 0.109s |

Well under a second, because AC-1 held: no model call was made before the
refusal.

## Conclusion

The path works end to end: a contract authored by hand-following the
skill's instructions against a real tree, refused correctly when it
names an impossible path (2, no model call), and driven through to a
judged outcome when it is well-formed (1, `discarded`, machinery behaved
even though this particular attempt wrote nothing). n=1. Not a rate.
