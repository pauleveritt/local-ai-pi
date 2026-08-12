# Contributing

Start with [`docs/setup.md`](setup.md) to get a green test run on a fresh
machine — most of this project needs nothing but Python. This page is what
comes after that: the test commands you'll actually use, the model-optional
boundary, repository conventions, and three starter tasks small enough to
finish without reading the research history.

## Test commands

```bash
uv run pytest        # Python: harness, tools, guards' Python-side wiring
bun install && bun test   # TypeScript: extensions/orchestration, extensions/guards
```

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
bun test extensions/orchestration/orchestration.test.ts
```

## The model-optional boundary

You can read code, run the full default test suite, and make most changes
without ever starting a model server. You need one only when:

- exercising the bounded implementer end to end (`tools/deliver_candidate.py
  --contract-task ...` against a real model), or
- running anything gated behind `SATYRN_LIVE=1`.

[`docs/setup.md`](setup.md)'s Part 2 covers getting a local server running.
If you're working on typed-contract construction, guard logic, the mutation
engine's TypeScript, or harness plumbing, you almost certainly don't need
Part 2 at all — the hermetic test suites are the actual contract these
pieces are built against.

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
  table for the standard this is held to.

## Three starter tasks

Each is real, currently true, and self-contained — no need to read
`ROADMAP.md` or the wider research record first.

1. **Add CLI argument-parsing tests for `tools/leak_probe.py`.** It has no
   dedicated test file today. `tests/test_typed_contract.py`'s
   `test_the_cli_refuses_an_unsupported_task_cleanly_not_with_a_traceback`
   and `tests/test_run_cycle7_confirmatory_batch.py` show the pattern this
   project uses for that: exercise `main()`'s `argparse` validation and
   error paths without a live model call.

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
   artifacts.** `workloads/svcs/screen/` is 106 MiB, tracked deliberately;
   nothing today stops a *new* multi-megabyte transcript or binary from
   being added the same way by accident. A `pytest` check (or a pre-commit
   hook) that fails on a newly tracked file above some size threshold
   outside an explicit allowlist would close a real, still-open gap from
   the 2026-08-11 distribution brief's step 3.
