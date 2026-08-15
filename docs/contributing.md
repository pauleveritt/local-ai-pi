# Contributing

Welcome. The most useful thing to know up front: **you can contribute
here without a GPU, a model server, or any of the research history.**
Most of this is ordinary Python with hermetic tests.

Start with [quick start](quickstart.md) for a green test run, then come back.
If a term stops you, try the [glossary](glossary.md) — it's short.

A rough order for a first hour:

1. `uv run pytest` — see it green (2 minutes)
2. Skim [deliver-candidate.md](engine/deliver-candidate.md) — one page, one path
3. Pick a [starter task](#three-starter-tasks) below

## Test commands

```bash
uv run pytest        # Python: harness, tools, guards' Python-side wiring
bun install && bun test   # TypeScript: extensions/implementer, extensions/guards
```

There is a third, smaller one. It replays recorded tool calls from real
runs through the loop breaker you would actually install:

```bash
node --experimental-strip-types tools/replay_guards.mjs tests/fixtures/guards/*.json
```

It needs no model, no server, and no `bun install` — the fixtures are
committed. `bun test` covers `extensions/guards/loop-breaker.ts`, the
`Guard` the implementer uses, and pins the shipped engine bundle
(`packages/engine/engine.ts`) against it. One policy, one shipped
artifact, deliberately
([deliver-candidate.md](engine/deliver-candidate.md#guards-still-in-the-extension-closure)).

`bun install` is only needed once (or after `package.json` changes) — it
pulls the one runtime dependency (`typebox`) into a gitignored
`node_modules/`. Skip it on a fresh clone and `orchestration.test.ts`
fails immediately with `Cannot find package "typebox"` — confirmed by
actually removing `node_modules` and running `bun test` before writing
this sentence, not assumed.

Both are the default, hermetic suites — no model server required. One
Python test is explicitly opt-in behind an environment variable
(`SATYRN_LIVE=1`); everything else either needs nothing live or mocks the
one live-only path.

Run a single file or test the normal way:

```bash
uv run pytest tests/test_typed_contract.py -k "supported_tasks"
bun test extensions/implementer/implementer.test.ts
```

## The model-optional boundary

You can read code, run the full default test suite, and make most changes
without ever starting a model server. You need one only when:

- exercising the [implementer](glossary.md#implementer)
  end to end (`tools/deliver_candidate.py --contract-task ...` against a
  real model), or
- running anything gated behind `SATYRN_LIVE=1`.

[`docs/model-setup.md`](model-setup.md) covers getting a local server running.
If you're working on [handoff packet](glossary.md#handoff-packet)
construction, [guard](glossary.md#guard) logic, the
[mutation engine](glossary.md#mutation-engine)'s TypeScript, or harness
plumbing, you almost certainly don't need Part 2 at all — the hermetic
test suites are the actual contract these pieces are built against.

## Repository conventions

- **Spec-driven development.** Every real feature has a committed design
  spec and implementation plan under `docs/superpowers/specs/` and
  `docs/superpowers/plans/` before the code — see
  [`docs/sdd.md`](sdd.md). Skim a couple before writing a large change; it's
  the fastest way to absorb how review here works.
- **Verify, don't assert.** A claim (a fix works, a test is non-vacuous, a
  refusal fires) gets demonstrated — stash the fix and show the new test
  fails first, or write the exploit and run it — not just stated. This
  project's own commit history is full of examples; `git log --oneline` on
  `harness/`, `extensions/`, or `tools/` for a sense of the pattern.
- **No machinery ahead of the contract it serves.** Build what a real task
  needs, not what might be needed later. Several ideas that would plausibly
  help sit deliberately unbuilt in `ROADMAP.md`'s Backlog.
- **Concept budget.** New jargon is a real cost. If a change needs a term a
  contributor doing this a few hours a week can't quickly absorb, prefer
  cutting the term over keeping it — see `ROADMAP.md`'s own concept-budget
  table for the standard this is held to. A term worth keeping is worth
  adding to the [glossary](glossary.md); a term no document uses should
  come back out of it.

## Three starter tasks

Each is real, currently true, and self-contained — no need to read
`ROADMAP.md` or the wider research record first.

1. **Add CLI argument-parsing tests for `tools/leak_probe.py`.** Its
   decision function `_majority` is covered (`tests/test_tool_decisions.py`),
   but `main()`'s argument handling is not — and that is where a
   mis-specified `--threshold` or a missing `--contract-dir` would surface.
   `tests/test_typed_contract.py`'s
   `test_the_cli_refuses_an_unsupported_task_cleanly_not_with_a_traceback`
   and `tests/test_run_cycle7_confirmatory_batch.py` show the pattern:
   exercise `argparse` validation and error paths with no live model call.

2. **Persist model transcripts and candidate diffs for a batch.** A known,
   documented harness gap: `harness/processes.py`'s `run_process()` captures
   the child's stdout/stderr only in memory, and `harness/workspace.py`'s
   `disposable_dir()` deletes each attempt's worktree unconditionally — so
   for the Cycle 7 batch, no raw transcript or candidate diff survives, only
   receipts. See the "What the bundle does not contain, and why" section of
   [`docs/superpowers/research/2026-08-11-phase7-cycle7-confirmatory-result.md`](superpowers/research/2026-08-11-phase7-cycle7-confirmatory-result.md).
   Making persistence opt-in (a flag on `deliver()`, writing under a
   caller-supplied directory before cleanup) would make future batches
   replayable.

3. **Add a repository policy check against newly-tracked oversized
   artifacts.** Nothing today stops a multi-megabyte transcript or binary
   from being tracked by accident. A `pytest` check (or a pre-commit hook)
   that fails on a newly tracked file above some size threshold outside an
   explicit allowlist would close a real, still-open gap from the
   2026-08-11 distribution brief's step 3.

   *Amended 2026-08-12. This item previously read "`workloads/svcs/screen/`
   is 106 MiB, tracked deliberately" and used that as its motivating
   example. That corpus is no longer tracked (see below), so the example is
   gone — but the gap it pointed at is not, which is why the item stays.*

## Why the screen corpus is not in your checkout

`workloads/svcs/screen/` — 570 files, 104.7 MiB of mechanism-screen output
— was tracked deliberately until **2026-08-12**, on the reasoning that
evidence a claim rests on should travel with the repository.

That reasoning was right about the evidence and wrong about the vehicle.
It made a first checkout 123 MiB, 95% of it a corpus no supported code
path reads, sitting between a new contributor and the 10 MiB that is
actually the project. Meanwhile a checksum-verified copy already existed
out of tree, and git history keeps every byte regardless.

So the corpus was removed from the working tree, not from the record:

```bash
git log --oneline -- workloads/svcs/screen/   # still there
git show <sha>:workloads/svcs/screen/<path>   # still readable
```

The out-of-tree bundle is named, located and checksummed in
[`evidence-index.md`](evidence-index.md). `.gitignore` now covers the
directory, because `tools/screen_workload.py` writes new batches there by
default and would otherwise re-commit the corpus a batch at a time.

`workloads/svcs/overnight/` (7.8 MiB) is **still tracked**, deliberately
and for a different reason: it has no out-of-tree copy, and 7.8 MiB does
not buy back enough to be worth the only-copy risk.
