# Phase 11 contract-file smoke test

**n=1, a wiring check, not a rate.**

**Date:** 2026-08-16
**`pi --version`:** 0.84.1
**Model:** `omlx/gemma-4-12B-it-MLX-8bit`
**Task:** `async-cm-enter` (`workloads/svcs/tasks/async-cm-enter`), against a
clean `svcs` checkout materialized at `base_sha`
`25d8a0b3ff5fdaa47648802088ef99becde27e6d`.

Revised after an independent deep review (a Fable-model agent, given full
repo access) found real bugs in the first pass of this work — see
**Review and fixes** below. This is the run against the fixed code; the
original contract used a glob (`readableFiles: [src/svcs/**, tests/**]`)
that the fix now correctly refuses, so it could not be reused as-is.

The question this checks is only whether the path works end to end: a
contract authored through the `write-handoff-contract` skill's
instructions, consumed by `deliver_candidate.py --contract`, driving the
implementer child, judged, and reported — and separately, that a bad
contract refuses before any model call. It claims nothing about outcome
rates; the reference `async-cm-enter` contract's 8/8 belongs to the
spike, not to this run.

## Review and fixes

Before this run, an independent agent (Fable model, full repo read
access, asked to adversarially trace the diff by hand rather than skim)
reviewed the six-commit branch. Two findings changed this smoke test:

1. **`writableFiles`/`readableFiles` globs silently do nothing.** The
   engine's `normalizeContractPath` (`extensions/implementer/handoff-contract.ts`)
   drops any path containing `*`. The original skill example and this
   smoke test's own first contract both used
   `readableFiles: [src/svcs/**, tests/**]` — that parsed and linted
   cleanly, then left the implementer able to read nothing outside
   `writableFiles`, silently. `harness/contract_file.py` now refuses
   globs (and absolute paths and `..`-escapes) at parse time, before any
   model call. The skill's example and this contract were rewritten to
   name files exactly.
2. **A markdown thematic break in the body silently truncated the task.**
   `_split_front_matter`'s substring split treated *any* standalone
   `---` line as a second closing delimiter and discarded everything
   after it — with no error, in a format whose whole premise is "the
   body is the task." Fixed with a delimiter regex anchored to line
   boundaries; twelve new regression tests cover this and the other
   findings (glob rejection, absolute/`..` paths, a closing line with
   trailing text, dotfile-rooted lint paths, digit extensions, missing
   `--contract` override guards, and the prompt-rendering gap below).

A third finding surfaced only by actually running `/implement` through a
live `pi` session rather than calling `deliver_candidate.py` directly —
see **The `/implement` command itself**.

## The contract used

Written by reading `src/svcs/_core.py` at the materialized base tree, not
copied from `workloads/svcs/contracts/locating/async-cm-enter.md`.

````markdown
---
writableFiles: [src/svcs/_core.py]
readableFiles: [src/svcs/__init__.py, tests/test_container.py]
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

## The live run (via `deliver_candidate.py --contract`)

```
uv run python -m tools.deliver_candidate \
    --repo <svcs-checkout> --task smoke-async-cm-v2 \
    --contract /tmp/smoke-async-cm-enter.md \
    --model omlx/gemma-4-12B-it-MLX-8bit \
    --receipt /tmp/smoke-receipt-v2.json
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
| wall-clock (`child`) | 19.3s |
| wall-clock (`total`) | 19.5s |
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
    --repo <svcs-checkout> --task smoke-refusal-v2 \
    --contract /tmp/bad-contract.md \
    --model omlx/gemma-4-12B-it-MLX-8bit
```

| Field | Value |
|---|---|
| exit code | 2 |
| message | `refused: the contract names src/svcs/container.py -- neither in the base tree nor in writableFiles, so it can be neither read nor created` |
| duration | 0.111s |

Well under a second, because AC-1 held: no model call was made before the
refusal.

## The `/implement` command itself

Everything above drives `deliver_candidate.py` directly. It does not
exercise `packages/engine/orchestrator.ts` — the actual TypeScript command
`/implement` registers on a `pi` session, which is what a contributor
actually types. That needed a real `pi` invocation:

```
pi --no-extensions -e packages/engine/orchestrator.ts --no-session \
    -p "/implement /tmp/contract.md"
```

**First attempt crashed.** The handler spawned the delivery subprocess
and returned without awaiting it. In `--print` (non-interactive) mode,
`pi`'s session tears down as soon as the handler's promise settles; the
still-running child's `stdout`/`stderr` callbacks then fired against a
torn-down session and crashed the process with `Error: This extension ctx
is stale after session replacement or reload.` — reproduced twice. Fixed
by wrapping the spawn in a promise the handler awaits, resolving on the
child's `close` (or `error`) event, so every `ctx.ui.notify` call happens
while the session is still live.

**Two invocation-shape findings, not code bugs, surfaced getting a clean
run:**

- `/implement`'s `--repo` and the subprocess's `cwd` are both `ctx.cwd` —
  unchanged from before this phase. `/implement` is meant to run *from
  inside* the repository it will modify (dogfooding this engine on
  itself), not pointed at an arbitrary external target the way the
  svcs harness workload is. Pointing it at the svcs checkout produced a
  fast, silent no-op (`uv run` there resolved svcs's own `pyproject.toml`,
  not this project's `tools` package) rather than a crash or a clear
  error — worth a future paper cut, out of scope for this phase.
- `deliver()` creates its candidate worktree at `<repo>/.git/satyrn-worktrees/…`,
  which assumes `.git` is a real directory. Run from inside *this
  project's own* linked worktree (`.worktrees/phase11-contract-file`,
  where `.git` is a plain gitlink file), `git worktree add` failed with
  `Not a directory`. Pre-existing `harness/candidate.py` behavior,
  untouched by this phase — worked around here with a throwaway
  `git clone --local` of the branch into an ordinary checkout.

**The corrected run**, from inside that clone (a real checkout of this
branch, `.git` a real directory), against a trivial one-line
contract asking the implementer to create a new file:

| Field | Value |
|---|---|
| wall-clock | 13s |
| `pi` exit code | 0 (no crash) |
| candidate ref created | no (`refs/satyrn/`, `git branch -a`, and `git worktree list` all clean afterward) |
| working tree touched | no (`deliver()` never writes outside its own worktree/refs) |

`ctx.ui.notify` produces no visible output in `--print` mode (no TTY to
render a toast to) — the absence of printed text is expected, not a
second bug. The load-bearing evidence is what didn't happen: no crash,
and no residue left behind by either the crashed first attempt or the
fixed second one, confirmed by inspecting refs and worktrees directly
rather than trusting console output.

## Conclusion

The path works end to end at both layers: `deliver_candidate.py
--contract` (a contract authored by hand-following the skill's
instructions against a real tree, refused correctly when it names an
impossible path, driven through to a judged outcome when well-formed) and
the actual `/implement` command a contributor types, which crashed on
first contact with non-interactive `pi` and now doesn't. n=1 on the model
outcome. Not a rate. The review-and-fix cycle this smoke test triggered
is the more durable result: two silent-failure classes (truncated task
bodies, neutered glob paths) and one process-lifecycle crash, all fixed
before anyone hit them for real.
