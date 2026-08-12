# Setting up

Two parts. Part 1 gets you a green test run and needs nothing but
Python — most contributions never need Part 2.

## Part 1 — enough to contribute

### uv

[uv](https://docs.astral.sh/uv/) handles Python versions, dependencies,
and running commands. No system Python, no hand-managed virtualenv.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### The project

```bash
uv sync
uv run pytest
```

`uv sync` fetches **Python 3.14** (pinned; the code uses 3.14-only
syntax) and installs into `.venv/`. Never activate it by hand — prefix
with `uv run`.

Expect all tests to pass, with a couple skipped. The skips are the
live-model tests; skipping is correct until Part 2. A *failure* is
different — say so.

### TypeScript

```bash
bun install && bun test
```

`bun install` is needed once. It pulls one dependency (`typebox`); skip
it and `orchestration.test.ts` fails with `Cannot find package
"typebox"`.

### Quality gates

```bash
uv run ruff check .          # lint
uv run ruff format --check . # formatting
uv run pyrefly check         # types
```

All three are green on a clean checkout and are expected to stay that
way. Run them before you push.

That's Part 1. You can now read the code, run both suites, and work on
anything that doesn't invoke a model.

## Part 2 — running a real model

Needed only to exercise the [bounded implementer](glossary.md#bounded-implementer)
end to end.

### Pi

[Pi](https://pi.dev) is the coding agent this project drives and extends.

```bash
pi --version    # 0.84.1 is what the recorded evidence used
```

The version is **recorded, not enforced**, on this path — `harness/cell.py`
deliberately keeps it out of what a [cell](glossary.md#cell) pins, because
it moves for legitimate reasons. Your run's version lands in the
[receipt](glossary.md#receipt). A different Pi is not refused; it is
simply not the one the published numbers came from.

### A model server

Any OpenAI-compatible server. The recorded evidence used
[oMLX](https://github.com/olmo-tools/omlx) on Apple Silicon serving
`gemma-4-12B-it-MLX-8bit` at `127.0.0.1:8001`.

```bash
uv run python -c "from harness.liveness import check_model_server_alive; check_model_server_alive(); print('alive')"
```

Two gotchas this check exists to catch: oMLX needs an `Authorization`
header (any non-empty value — we send `not-needed`), and a different
address means passing `base_url=` rather than editing the default.

### Point Pi at your own models

`deliver_candidate` defaults to your `~/.pi/agent`, so your own model
names resolve. Pass `--agent-dir pi-agent-dir/` to use this
repository's pinned configuration instead — that is what reproduces a
measured run, and the [cell](glossary.md#cell) records whichever you used.

## Editor notes

Point it at `.venv/bin/python` and enable Ruff for lint and format, so
you're not fighting the gate on every commit.
