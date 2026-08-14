# Agent Engine

**Can a small local model do real Python work — and how would you know?**

A 12B model running on your own machine is not the "godbox" experience.
You don't hand it a vague prompt and let it reason its way out. The work
is small, routine, and much more like engineering — which makes the
interesting question not *is it magic* but *did that technique actually
help?*

This project's answer is to measure, carefully, and to write down what
the measurement does **not** show.

Agent Engine is two parts:

- A Pi extension to help steer small models by tackling their common problems
- An eval harness, to find those problems and see if you tackled them

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
cp .pi/extensions/engine.ts .pi/extensions/orchestrator.ts ~/.pi/agent/extensions/
```

Those two files are the whole install: the engine (the guards) and the
orchestrator's `/implement` command. Pi loads user-scope extensions
unconditionally, so both are active in every session — including
delegated children, where a small model's runaway usually happens. Put the
files in user scope, not a project's `.pi/extensions/`, if you delegate at
all: a child loads user-scope extensions but not project ones. (Only want
guard #1? [loop-breaker.md](docs/engine/loop-breaker.md) installs the loop breaker
alone.)

The other face is the orchestrator: the explicit front you invoke. In a
Pi session with the two-file install, that front is `/implement <task>` —
it writes your task to a prompt file and shells out to the CLI below,
which is also the direct path from a checkout. It pre-chews a task into a
handoff packet and drives the implementer — the bounded worker — through
one attempt. It runs a model once against your repo in a throwaway git
worktree, checks the result with a command you declare, and leaves either
a git ref you can review or a receipt explaining why not — your working
tree is never written to:

```bash
uv sync
uv run python -m tools.deliver_candidate \
  --repo . --task add-iter \
  --prompt-file docs/engine/example-brief.md \
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

## Run an eval

The harness that produced the evidence below is driven by a small command —
suites and improvements by name, not Python constants:

```bash
uv run python -m harness.cli one --suite duration
uv run python -m harness.cli batch --suite duration --improvement tech-stack-only
```

`one` runs a single attempt; `batch` runs attempts until the checkpoint
holds `--target` of them (default 16). `suites` and `improvements` list
what exists, `preflight` checks the model server and the pinned Pi version,
and `summarize <checkpoint.jsonl>` reads a checkpoint without comparing
anything — comparison stays manual. `--help` is the documentation.

Both need Pi and a model server running — [setup.md](docs/setup.md) Part 2
gets you there, and `preflight` is the fast readiness check.

What a run, batch, improvement, and checkpoint are — and the three things
that will bite you — is in [evals.md](docs/evals/index.md).

## What the evidence actually says

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

## What's still experimental

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
| Understand the one supported path, end to end | [deliver-candidate.md](docs/engine/deliver-candidate.md) |
| Get set up properly | [setup.md](docs/setup.md) |
| Run an eval | [evals.md](docs/evals/index.md) |
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
extensions/    the implementer, mutation engine, and guards (Pi extensions)
tools/         CLI entry points — deliver_candidate is the one to start with
tests/         Python tests, hermetic unless explicitly opted in
workloads/     the task cohort, manifests, cells, and recorded evidence
docs/          architecture, setup, contributing, glossary, evidence
```
