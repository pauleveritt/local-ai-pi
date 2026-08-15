# Quick Start

From zero to: tests green, a model running, the engine steering a Pi
session, and one eval run. Each step is terse here and has an in-depth
page. [What is Agent Engine?](what-is.md) is the context for any of it.

```{admonition} Note
:class: info

These docs and this project are still too big. I'm working on slimming it
down. If you get lost, need the big picture, have a question, want to
find something... ask your agent. The repo has tons of specs and
material. The answers are in there, it's just too big to find on your
own.
```

## 0. The environment

```bash
uv sync          # Python 3.14, dependencies
uv run pytest    # expect a handful of skips — the live tests need a model
```

The quality gates before you push: `uv run ruff check .`, `uv run ruff
format --diff`, `uv run pyrefly check`. More in [contributing](contributing.md).

## 1. A local model

You need a model server (oMLX) serving a model Pi can resolve. The one
thing you type is the model string, `--model <provider>/<id>`. The whole
story — install, acquisition, tuning, wiring — is [model setup](model-setup.md).

## 2. The engine, in a Pi session

**If you're working in this repository, you already have it.** The engine
is project-local here — `.pi/extensions/engine.ts` and `orchestrator.ts`
— and Pi loads project-local extensions once you trust the project, so
`/implement` is already available. Skip the install.

(To carry the engine into *every* session, everywhere — and into
delegated children, where a small model's runaway usually happens — copy
the two files to user scope:

```bash
mkdir -p ~/.pi/agent/extensions
cp .pi/extensions/engine.ts .pi/extensions/orchestrator.ts ~/.pi/agent/extensions/
```

If Pi is already running, `/reload` picks them up.)

Then, in the repository you're working on, type:

```
/implement add a hello() function to duration.py
```

The orchestrator chews that into a handoff packet and drives the bounded
implementer against the current repo — a throwaway worktree, pytest
validation, your session's model — leaving a ref. Review it, then discard
it:

```bash
git show refs/satyrn/candidates/<task-slug>
git update-ref -d refs/satyrn/candidates/<task-slug>
```

That is the whole engine: in this repo it is already there, elsewhere it
is one install — then use Pi normally, and `/implement` when you want a
bounded attempt. The full setup is [engine setup](engine/setup.md);
the ways to use it are [using the engine](engine/usage.md).

## 3. Run an eval

```bash
uv run python -m harness.cli preflight
uv run python -m harness.cli one --suite duration
uv run python -m harness.cli batch --suite duration
```

`preflight` checks the server and the pinned Pi version; `one` runs a
single attempt; `batch` fills a checkpoint. The full setup is [evals
setup](evals/setup.md); the concepts are in [running evals](evals/index.md).

## After that

[Contributing](contributing.md) has the conventions and starter tasks;
[the glossary](glossary.md) defines the vocabulary.
