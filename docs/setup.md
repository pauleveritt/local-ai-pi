# Setting up your environment

Getting from a fresh machine to a green test run, then to a real model run.

The good news: **most of this project's tests need nothing but Python.**
Cycles 1–10 were deliberately built so the grading engine is provable
against fixtures with no model in the loop. You can contribute
meaningfully before you ever start a model server.

So this guide is in two parts. Part 1 gets you running tests and reading
code. Part 2 gets you running a real model, which you only need when you're
working on something that invokes one.

## Part 1 — Enough to contribute

### uv

We use [uv](https://docs.astral.sh/uv/) for everything: Python versions,
dependencies, running commands. You don't need a system Python or a
hand-managed virtualenv.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### The project

```bash
git clone <repo-url>
cd local-ai-pi
uv sync
```

`uv sync` reads `pyproject.toml` and `uv.lock`, fetches **Python 3.14**
(pinned; the project uses 3.14-only syntax), and installs dependencies into
`.venv/`. You never activate it by hand — prefix commands with `uv run`.

### Verify

```bash
uv run pytest
```

Expect all tests to pass, with **one skipped**. That skip is the
integration test that needs `pi` and a live model server — skipping is the
correct result until you finish Part 2. If it *fails* rather than skips,
something is wrong; say so.

### Quality gates

Two more tools, both run in review:

```bash
uv run ruff check .        # lint
uv run ruff format --diff  # formatting (check only)
uv run pyrefly check       # type checking
```

Run these before you push. They're fast.

That's it for Part 1. You can now read the code, run the suite, and work on
any cycle that doesn't invoke a model.

## Part 2 — Running a real model

Needed only when you're working on something that actually invokes a model
— `harness/runner.py`, the batch cycles, or anything touching `pi`.

### Pi

[Pi](https://pi.dev) is the coding agent this project drives and extends.
Install it however you prefer (we use [Volta](https://volta.sh/) for the
Node toolchain); confirm with:

```bash
pi --version    # 0.82.0 or later
```

Two things to know about how we call it. We always run **non-interactive**
(`--print`), and we always run with **extensions, skills, prompt templates,
themes, and context files disabled** — the model gets the task spec and
nothing else. That isolation is deliberate: it's what makes one run
comparable to another. See `harness/runner.py` for the exact invocation.

### A local model server

We use [oMLX](https://github.com/olmo-tools/omlx) on Apple Silicon, serving
an OpenAI-compatible API on `127.0.0.1:8001`.

```bash
omlx start
```

The reference model is `omlx/gemma-4-12B-it-MLX-8bit`. Any
OpenAI-compatible server works — LM Studio, Ollama with its compat
endpoint, vLLM — but if you use a different one, **say so when you report
numbers.** Runs from different models aren't comparable, and the whole
point of the harness is producing numbers that mean something.

### Verify the server

```bash
uv run python -c "from harness.liveness import check_model_server_alive; check_model_server_alive(); print('alive')"
```

This is the harness's own liveness check (`harness/liveness.py`), so if it
passes, the harness agrees your server is up.

Two gotchas it exists to catch, both of which cost us real debugging time:

- **oMLX requires an `Authorization` header** — any non-empty value works;
  we send `not-needed`. Without it a perfectly healthy server returns 401
  and reads as down.
- **A different address** means passing `base_url=`. The default matches
  `BRIEF.md`; if yours differs, don't edit the default, pass the argument.

### Verify end to end

```bash
uv run pytest tests/test_runner.py -v
```

This invokes `pi` against a real model and grades the result. It takes a
minute or so. If it now *passes* rather than skips, your Part 2 setup is
complete.

## Editor notes

Nothing is required, but if you're configuring one: point it at
`.venv/bin/python`, and enable Ruff for both linting and formatting so
you're not fighting the quality gate on every commit.

## When something doesn't work

Check `BRIEF.md` first for the environment specifics it records (model
name, server address, Pi version) — it's the source of truth, and this
guide should agree with it. If it doesn't, `BRIEF.md` wins and the guide
is the bug.
