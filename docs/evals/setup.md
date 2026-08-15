# Evals setup

The in-depth setup for running the eval harness. The terse version is
[quick start](../quickstart.md); the model story behind it is
[model setup](../model-setup.md); the concepts are in
[running evals](index.md).

## Pi

Install Pi however you prefer (this project uses Volta). The harness pins
**Pi 0.84.1** (`EXPECTED_PI_VERSION` in `harness/runner.py`): a batch
refuses to run on any other version, so batches from different
contributors stay comparable. If yours differs, either install **Pi
0.84.1**, or bump the pin and re-check this page, which names the version
twice, and the docs that cite Pi by file and line. A single `one` run
does not pin — exploring is never blocked — but `batch` and `preflight`
will tell you when the version is wrong.

The version check is a deliberate red suite: `test_the_pinned_version_is_
the_installed_version` fails when your Pi is a different version, so a
silent upgrade turns the tests red rather than drifting evidence.

## The model server

The harness needs an OpenAI-compatible model server up before any run —
oMLX on Apple Silicon, serving `127.0.0.1:8001`, started with `omlx
start`. The server's deep story — install, the API-key quirk, the
paged/tiered KV cache — is in [model setup](../model-setup.md); the two
gotchas that cost real debugging time:

- **oMLX requires an `Authorization` header** — any non-empty value
  works; the harness sends `not-needed`. Without it a perfectly healthy
  server returns 401 and reads as down.
- **A different address means a code change, not a flag.** The eval
  CLI's liveness check hardcodes `127.0.0.1:8001` — there is no
  `--server` on `one`/`batch`. A server on another port is refused
  before any call. (The engine's `/implement` path drives the same
  server but is not bound to the eval CLI's check.)

## The model string, for evals

`--model <provider>/<id>` — default `omlx/gemma-4-12B-it-MLX-8bit`
(`DEFAULT_MODEL` in `harness/pi_invocation.py`). The harness pins
`PI_CODING_AGENT_DIR=pi-agent-dir/`, so the string must resolve in
`pi-agent-dir/models.json` — the part before the slash is a provider key,
the part after is a model entry under it. Registering a provider or model,
and the limits on pointing at a different server, are in
[model setup](../model-setup.md).

## Verify the server

```bash
uv run python -c "from harness.liveness import check_model_server_alive; check_model_server_alive(); print('alive')"
```

## Verify end to end

```bash
SATYRN_LIVE=1 uv run pytest tests/test_runner.py -v
```

This invokes `pi` against a real model and grades the result — it takes a
minute or so, and without `SATYRN_LIVE=1` it deliberately skips. The
faster smoke path is the CLI:

```bash
uv run python -m harness.cli preflight
uv run python -m harness.cli one --suite duration
```

`preflight` reports the server and the pinned Pi version and says what to
fix if either is wrong; `one --suite duration` runs the smallest suite
once. The eval-specific limits above — the fixed server address, the
pinned registry — are why `preflight`'s advice points here.
