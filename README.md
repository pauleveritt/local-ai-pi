# Agent Engine

**Can a small local model do real Python work — and how would you know?**

A 12B model running on your own machine is not the "godbox" experience.
You don't hand it a vague prompt and let it reason its way out. The work
is small, routine, and much more like engineering — which makes the
interesting question not *is it magic* but *did that technique actually
help?*

This project's answer is to measure, carefully, and to write down what
the measurement does **not** show.

## The engine

One Pi extension — a single file — that steers a small local model during
everyday sessions. It bundles two guards: the **loop breaker**, which
refuses a tool call the model has already made unchanged several times in
a row, and **preserve-symbols**, which refuses an edit that deletes a
public symbol (a function, class, or route) without replacing it. It is
not a planner and not a turn cap; varied work is untouched.

Minimal install:

```bash
mkdir -p ~/.pi/agent/extensions
cp .pi/extensions/engine.ts ~/.pi/agent/extensions/
```

That copy is the whole install. Pi loads user-scope extensions
unconditionally, so the guards are active in every session — including
delegated children, where a small model's runaway usually happens. Put the
file in user scope, not a project's `.pi/extensions/`, if you delegate at
all: a child loads user-scope extensions but not project ones. (Only want
guard #1? [loop-breaker.md](docs/loop-breaker.md) installs the loop breaker
alone.)

The other face is the bounded executor, run from a checkout. It runs a
model once against your repo in a throwaway git worktree, checks the result
with a command you declare, and leaves either a git ref you can review or a
receipt explaining why not — your working tree is never written to:

```bash
uv sync
uv run python -m tools.deliver_candidate \
  --repo . --task add-iter \
  --prompt-file docs/example-brief.md \
  --validation "pytest -q" --writable "src/**" \
  --model your-provider/your-model
```

Success prints a ref you can review with ordinary git:

```bash
git show refs/satyrn/candidates/add-iter
```

More, including what the engine is and isn't:
[docs/engine/index.md](docs/engine/index.md).

## Setup (applies to the engine and the evals)

[uv](https://docs.astral.sh/uv/) manages everything — the Python version,
the dependencies, and the commands. `uv sync` sets up the project; prefix
every command with `uv run`.

The quality gates are four commands you run before pushing: `uv run ruff
check .`, `uv run ruff format --diff`, `uv run pyrefly check`, and
`uv run pytest`.

A real model run needs a local server. We use
[oMLX](https://github.com/olmo-tools/omlx) on Apple Silicon — `omlx start`
— and if your server is not at the default address, pass `base_url=` to
point at it rather than editing the default.

The long form, with the gotchas and how to verify the server is actually
up: [docs/setup.md](docs/setup.md).

## The evals

The measurement side runs three suites — `agentclinic-phase-1`,
`agentclinic-phase-1-user-story`, and `duration` — that grade a small local
model against real tasks and decide hermetically whether it succeeded.
Which claim rests on which suite is written down, claim by claim, in
[docs/evidence-index.md](docs/evidence-index.md).

Running one today goes through the harness in
[docs/setup.md](docs/setup.md). A single command for it is the planned
entry point of a later phase, and is not documented here until it exists.

## The evidence

### What the evidence actually says

One pre-registered comparison, 64 attempts, run 2026-08-11: does giving
the model a complete [locating contract](docs/glossary.md#locating-contract)
beat a short [brief](docs/glossary.md#brief)?

**On one task of four, clearly yes** (8/8 versus 3/8). On two, both arms
were already at ceiling. On the fourth, both were at the floor — the
contract got the model to a *safe* answer every time and a *correct* one
never.

That last one is the honest headline: locating information solves
locating problems. It does not make a model capable of something it
can't do.

Full numbers, intervals, and what they don't establish:
[the result](docs/superpowers/research/2026-08-11-phase7-cycle7-confirmatory-result.md).
Every claim's evidence category — [pilot](docs/glossary.md#pilot) versus
[confirmatory](docs/glossary.md#confirmatory) — is indexed in
[evidence-index.md](docs/evidence-index.md).

### What's still experimental

The typed-contract path is scoped to exactly four tasks and refuses the
rest at the command line rather than guessing. It's a tested bridge, not
a planner.

And the fourth task above sits at a genuine capability ceiling. That's a
real limit, not a harness bug — we checked, because a similar-looking
result once turned out to be our own validation gate rejecting correct
answers.

## Where to go next

| You want to… | Read |
|---|---|
| Understand the engine — what it is and isn't | [engine/index.md](docs/engine/index.md) |
| Understand the one supported path, end to end | [architecture.md](docs/architecture.md) |
| Get set up properly | [setup.md](docs/setup.md) |
| Contribute — commands, conventions, starter tasks | [contributing.md](docs/contributing.md) |
| Look up a term | [glossary.md](docs/glossary.md) |
| Check what backs a claim | [evidence-index.md](docs/evidence-index.md) |
| Read the full research history | [ROADMAP.md](ROADMAP.md), [BRIEF.md](BRIEF.md), [the design record](docs/superpowers/index.md) — all historical |

## How this project works

Every feature gets a committed design spec and implementation plan
before the code, so you can read *why* something looks the way it does —
see [sdd.md](docs/sdd.md). Four habits shape review, and
[contributing.md](docs/contributing.md) covers them; the shortest
version is **verify, don't assert**: claims here get demonstrated, not
argued.

## Layout

```
harness/       the typed-contract bridge, candidate lifecycle, cell verification
extensions/    the bounded implementer, mutation engine, and guards (Pi extensions)
tools/         CLI entry points — deliver_candidate is the one to start with
tests/         Python tests, hermetic unless explicitly opted in
workloads/     the task cohort, manifests, cells, and recorded evidence
docs/          architecture, setup, contributing, glossary, evidence
```
