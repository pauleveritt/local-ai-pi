# The engine

**One Pi extension — one file — that steers a small local model while
you work.** Not a planner, not a turn cap, not the orchestrator this
project also builds. It is the everyday layer: it watches tool calls and refuses
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
in `docs/engine/loop-breaker.md` and `docs/engine/architecture.md`.

## How you use it

The engine is one thing — everyday steering — and in this repository it
is already installed: `.pi/extensions/engine.ts` and `orchestrator.ts`
are project-local, and Pi loads them once you trust the project.
`/implement` is available in any session here, with no setup.

**Everyday steering.** For every session everywhere — including delegated
children, where a small model's runaway usually happens — copy the two
files to user scope:

```bash
mkdir -p ~/.pi/agent/extensions
cp .pi/extensions/engine.ts .pi/extensions/orchestrator.ts ~/.pi/agent/extensions/
```

That copy is the whole install — each file imports nothing local, so a
`cp` is complete. User scope is the point: Pi loads user-scope
extensions unconditionally, in every session, and in delegated children; a
project-local file guards the parent and leaves the child unguarded.

The loop breaker remembers the last `WINDOW` (20) calls and refuses the
next identical one once it has seen `THRESHOLD` (5) of them in that
window; a blocked call never enters the window, so a model that keeps
retrying stays blocked rather than sliding the repeats out of view.
Preserve-symbols governs `edit` alone, on purpose: it compares an edit's
old text against its new text, and leaves `write` and shell heredocs
alone, because the one run that recovered did so by rewriting a file
wholesale — blocking that escape hatch would have converted the only
success into a failure.

Only want guard #1? `docs/engine/loop-breaker.md` installs it alone, with the
same user-scope reasoning.

**A companion tool, not part of the engine.** The project also ships an
orchestrator (`deliver_candidate`) — a non-interactive CLI that pre-chews
a task into a handoff packet and drives the implementer, the bounded
worker, to make one reviewable attempt against your repository in a
throwaway worktree, checked with a command you declare. It is for a
deliberate, non-session moment, not something you reach for mid-session.
See `docs/engine/deliver-candidate.md`; the one-liner is in the README.

## What it is not

Not a planner. The typed-contract bridge under the orchestrator is scoped
to exactly four tasks and refuses the rest at the command line rather than
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
measured the **guards** — everyday steering, not the orchestrator — twice,
on the two suites: on the pre-chewed `agentclinic-phase-1` both arms hit
ceiling (6/6) with the guards never firing; on the harder
`agentclinic-phase-1-user-story` both arms hit the floor (0/6) — the bare
path provokes non-engagement, one turn and zero tool calls per run — and
the guards never fired there either. The composed pipeline's 13/16 on the
harder suite does not credit the guards: the effect lives in the pipeline.
It is written up in `docs/engine/shootout.md`; `docs/evidence-index.md`
lists the claims and writes down, claim by claim, what is confirmatory and
what is only pilot.

## Where to go next

- Install it and use it: [using the engine](usage.md) has the quick
  start, or `docs/engine/setup.md` has the setup.
- Set up a local model — server, model string, tuning, wiring it into Pi:
  `docs/model-setup.md`.
- Understand the problems and the architecture:
  `docs/engine/architecture.md`.
- The pilot shootout, and what it does and does not establish:
  `docs/engine/shootout.md`.
- The loop breaker alone, with tuning and the subagent gotcha:
  `docs/engine/loop-breaker.md`.
- The orchestrator path, end to end: `docs/engine/deliver-candidate.md`.
- Look up a term: `docs/glossary.md`.
- Check what backs a claim: `docs/evidence-index.md`.
