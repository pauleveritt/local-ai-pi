# Setting up your environment

Getting from a fresh machine to a green test run, then to a real model run.

The good news: **most of this project's tests need nothing but Python.**
Cycles 1–7 and 9–11 were deliberately built so their grading and harness
behavior is provable against fixtures with no model in the loop. You can
contribute meaningfully before you ever start a model server.

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

Expect all tests to pass, with **a handful skipped**. Those skips are the
integration tests that need `pi` and a live model server — skipping is the
correct result until you finish Part 2. If one *fails* rather than skips,
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
pi --version    # 0.84.1
```

**Which paths actually enforce this, and which only record it** — worth
being precise, because the two halves of this repository differ:

- **The legacy duration-suite harness enforces it.** `EXPECTED_PI_VERSION`
  in `harness/runner.py`; `run_batch` refuses to run on any other version,
  so batches from different contributors stay comparable. A single
  `run_suite` does not check, so exploring is never blocked.
- **The bounded-implementer path does not.** `harness/cell.py` says so
  outright — a cell "carries the conditions that define an arm and nothing
  else: not the grading rule …, not the Pi version or `models.json` digest
  (which move for legitimate reasons and are recorded per attempt
  instead)." So `deliver_candidate.py` will run under any Pi your system
  has; the version it used is written into the receipt, not checked
  against a pin.

Do not read the first bullet as covering the second. A candidate produced
under a different Pi is not refused; it is recorded.

The test suite checks the pin for the path that has one.
`test_the_pinned_version_is_the_installed_version` in `tests/test_runner.py`
skips when `pi` is not on your PATH — you have done nothing wrong by not
installing it — and **fails** when your Pi is a different version. That
failure is deliberate: it turns a silent upgrade into a red suite.

So if yours differs, either install Pi `0.84.1`, or bump
`EXPECTED_PI_VERSION` and re-check the documentation that cites Pi — this
file, which names the version twice, and the chapters that cite Pi by file
and line. Neither survives an upgrade, and no test catches them.

The pin removes one variable, not the set: `RunConditions` records nothing
about the oMLX server's version or build, so two contributors on identically
pinned Pi still have an unrecorded difference between them.

Two things to know about how we call it. We always run **non-interactive**
(`--print`), and we disable Pi's ambient extensions, skills, prompt templates,
themes, and context files. We then load this repository's explicit
`.pi/extensions/hello-world.ts` extension. That deliberate, fixed input is
what makes one run comparable to another. See `harness/runner.py` for the
exact invocation.

### A local model server

We use [oMLX](https://github.com/olmo-tools/omlx) on Apple Silicon, serving
an OpenAI-compatible API on `127.0.0.1:8001`.

```bash
omlx start
```

The reference model is `omlx/gemma-4-12B-it-MLX-8bit`. Phase 1's runner is
configured for the recorded oMLX endpoint; another OpenAI-compatible server
is not yet a supported runner configuration. Do not compare numbers from a
different model or endpoint with the Phase 1 baseline.

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
SATYRN_LIVE=1 uv run pytest tests/test_runner.py -v
```

This explicitly opts into invoking `pi` against a real model and grading the
result. It takes a minute or so. A passing result is evidence that the live
path worked; without `SATYRN_LIVE=1`, the test deliberately skips.

## Editor notes

Nothing is required, but if you're configuring one: point it at
`.venv/bin/python`, and enable Ruff for both linting and formatting so
you're not fighting the quality gate on every commit.

## When something doesn't work

Check `BRIEF.md` first for the environment specifics it records (model
name, server address, Pi version) — it's the source of truth, and this
guide should agree with it. If it doesn't, `BRIEF.md` wins and the guide
is the bug.
