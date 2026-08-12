# Contributing

Welcome. The useful thing to know up front: **you can contribute here
without a GPU, a model server, or any research background.** This is
ordinary Python with hermetic tests.

Start with [setup.md](setup.md) for a green test run, then come back.
If a term stops you, the [glossary](glossary.md) is short.

A rough first hour:

1. `uv run pytest` — see it green (2 minutes)
2. Skim [architecture.md](architecture.md) — one page, one path
3. Pick a [starter task](#starter-tasks)

## Test commands

```bash
uv run pytest             # Python
bun install && bun test   # TypeScript
node --experimental-strip-types tools/replay_guards.mjs tests/fixtures/guards/*.json
```

The third replays recorded tool calls from real runs through the loop
breaker you would install — no model, no server, no `bun install`. It is
the cheapest evidence here to reproduce. `bun test` covers the `Guard`
the bounded implementer uses; the replay covers
`.pi/extensions/loop-breaker.ts`, the standalone file `cp` installs.

Both suites are hermetic — no model server. One Python test is opt-in behind
`SATYRN_LIVE=1`; everything else needs nothing live.

Run one file the normal way:

```bash
uv run pytest tests/test_typed_contract.py -k supported_tasks
bun test extensions/orchestration/orchestration.test.ts
```

## The model-optional boundary

You need a model server only to exercise the
[bounded implementer](glossary.md#bounded-implementer) end to end, or for
anything behind `SATYRN_LIVE=1`. Work on the
[handoff contract](glossary.md#handoff-contract),
[guards](glossary.md#guard), the [mutation engine](glossary.md#mutation-engine),
or harness plumbing needs none of it — the hermetic suites are the real
contract those pieces are built against.

## Conventions

- **Verify, don't assert.** A claim gets demonstrated. Stash the fix and
  show the new test fails first; write the exploit and run it. Don't
  argue it.
- **Non-vacuity.** Ask of any test: *what else could make this pass?* A
  test that passes without testing its claim is this project's recurring
  hazard.
- **No machinery ahead of the contract it serves.** Build what a real
  task needs, not what might be needed later.
- **Concept budget.** New jargon is a real cost. If a change needs a term
  a few-hours-a-week contributor can't quickly absorb, prefer cutting the
  term. A term worth keeping belongs in the [glossary](glossary.md); one
  no document uses should come out of it.

## Starter tasks

Each is real, currently true, and self-contained.

1. **Give `harness/candidate.py` an option to keep the worktree.**
   `deliver()` discards each attempt's worktree unconditionally, so when
   a candidate is refused you cannot inspect what the model actually
   wrote — only the [receipt](glossary.md#receipt)'s summary. A
   `keep_workspace: Path | None` parameter, written before cleanup, would
   make refusals debuggable. `tests/test_candidate.py` shows the fixture
   pattern.

2. **Cover `tools/deliver_candidate.py`'s argument refusals.**
   Several combinations are rejected deliberately — `--cell` alongside
   `--model`/`--tools`/`--timeout`, `--validation` or `--writable`
   alongside `--contract-task`. Some are tested, not all. Each refusal
   exists because the combination silently produced a wrong result once.
   Follow the pattern in `tests/test_deliver_candidate.py`.

3. **Add a fifth task to the typed bridge.** `SUPPORTED_TASKS` in
   `harness/typed_contract.py` is deliberately four, and the CLI refuses
   the rest rather than guessing. Adding one means deciding what its
   contract should say — read `harness/typed_contract.py`'s docstring
   first; it explains why the boundary is where it is. This is the
   largest of the three and the one that most needs discussion before
   code.
