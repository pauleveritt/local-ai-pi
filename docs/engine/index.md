# The engine

**One Pi extension — one file — that steers a small local model while
you work.** Not a planner, not a turn cap, not the executor this project
also builds. It is the everyday layer: it watches tool calls and refuses
the two failure modes that cost real runs, before they cost you a run.

## What it is

The engine is `.pi/extensions/engine.ts`. It bundles two guards, each a
small rule that inspects a tool call and may refuse it:

- **The loop breaker** refuses a tool call the model has already made,
  unchanged, several times in a row. A recorded run of this project
  spent 261 turns, 245 of them the identical `ls -R` against an empty
  directory, never concluding it should create files.
- **Preserve-symbols** refuses an `edit` that deletes a public symbol —
  a function, a class, or a route — without replacing it. The failure it
  was built from replaced an existing `/about` route instead of adding
  the requested `/contact` one, and three acceptance tests failed from
  that single deletion.

Each guard compares a call against itself and returns a decision. Neither
knows anything about your task; that is what lets them ship in one file
and steer any session. The details, and the measured case for each, are
in `docs/loop-breaker.md` and `docs/engine/architecture.md`.

## The two faces

You can use the engine two ways, and they are independent.

**Everyday steering.** Copy the one file into user scope:

```bash
mkdir -p ~/.pi/agent/extensions
cp .pi/extensions/engine.ts ~/.pi/agent/extensions/
```

That copy is the whole install — the file imports nothing local, so a
`cp` is complete. User scope is the point: Pi loads user-scope
extensions unconditionally, in every session, and — the reason it
matters here — in delegated children, where a small model's runaway
usually happens. A file in a project's `.pi/extensions/` guards the
parent and leaves the child unguarded.

The loop breaker remembers the last `WINDOW` (20) calls and refuses the
next identical one once it has seen `THRESHOLD` (5) of them in that
window; a blocked call never enters the window, so a model that keeps
retrying stays blocked rather than sliding the repeats out of view.
Preserve-symbols governs `edit` alone, on purpose: it compares an edit's
old text against its new text, and leaves `write` and shell heredocs
alone, because the one run that recovered did so by rewriting a file
wholesale — blocking that escape hatch would have converted the only
success into a failure.

Only want guard #1? `docs/loop-breaker.md` installs it alone, with the
same user-scope reasoning.

**The bounded executor.** Run from a checkout, it lets a model make one
attempt against your repository in a throwaway git worktree, checks the
result with a command you declare, and leaves either a ref you can review
or a receipt explaining why not. Your working tree is never written to.
The one-liner is in the README (`uv run python -m tools.deliver_candidate
...`); the full path, in execution order, is `docs/architecture.md`.

## What it is not

Not a planner. The typed-contract bridge under the executor is scoped to
exactly four tasks and refuses the rest at the command line rather than
guessing — a tested bridge, not a general contractor.

Not a godbox. It will not reason your way to a conclusion for you. It
steers: it names the repetition, states that the answer will not change,
and hands the model the next concrete action, instead of a bare "no"
that invites a sixth attempt.

Not a turn cap. Pi has none, and a model doing genuine, varied work for
a long time is untouched by these guards.

## The evidence in one paragraph

The loop breaker came out of that 261-turn run, and live, in a 16-run
batch, it fired in two runs — refusing 12 calls — and both still passed
their acceptance tests. Preserve-symbols came out of three of four runs
failing the same way on the `/about`-route deletion. The pilot shootout
for the executor side is `docs/evidence-index.md`, which also writes
down, claim by claim, what is confirmatory and what is only pilot.

## Where to go next

- Install it: `docs/setup.md` has the environment, or the README's
  engine section is the front door.
- Understand the problems and the architecture:
  `docs/engine/architecture.md`.
- The loop breaker alone, with tuning and the subagent gotcha:
  `docs/loop-breaker.md`.
- The executor path, end to end: `docs/architecture.md`.
- Look up a term: `docs/glossary.md`.
- Check what backs a claim: `docs/evidence-index.md`.
