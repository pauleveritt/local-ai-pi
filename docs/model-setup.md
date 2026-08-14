# Model setup

The eval harness drives Pi, and Pi calls an OpenAI-compatible inference
server on your own machine. This page is that stack, the way this project
runs it: the server (oMLX), the model (Gemma 4 12B), how the model string
you type is resolved, what you can tune, and how to wire in your own model.
The short version of getting everything running is [setup.md](setup.md)
Part 2; this is the longer treatment of the model half.

## The model string — the one thing you type

Suites and improvements are addressed by name, and so is the model. Every
`one` and `batch` run takes `--model <string>`; the default is
`omlx/gemma-4-12B-it-MLX-8bit` (`DEFAULT_MODEL` in
`harness/pi_invocation.py`).

The string is **`<provider>/<model-id>`**, and both halves live in
`pi-agent-dir/models.json` — the part before the slash is a *provider* key
(which carries the server's `baseUrl` and `apiKey`), and the part after is
a *model entry* under that provider. Pi resolves the string against that
file; the harness pins `PI_CODING_AGENT_DIR=pi-agent-dir/` on every
invocation, so that file is the registry.

There is no CLI that lists models — `suites` and `improvements` list the
harness's registries, but models are Pi's registry. To find the strings
available on your machine, read `pi-agent-dir/models.json`.

## The server: oMLX

oMLX is an inference server for **Apple Silicon only** — it is built on
MLX, Apple's machine-learning framework, so it does not run on Windows,
Linux, or Intel Macs. It serves an OpenAI-compatible API on
`127.0.0.1:8001`.

Installation (Homebrew):

```bash
brew tap jundot/omlx https://github.com/jundot/omlx
brew install omlx
omlx start        # runs as a background service, auto-restarts on crash
```

From source (`pip install -e .` in a clone of
`github.com/jundot/omlx`) is the alternative; this machine's recorded
binary is `~/.omlx/bin/omlx` (BRIEF.md's practical-environment section).
`omlx stop` / `restart` / `diagnose` manage the service.

**Windows and Linux.** oMLX cannot run there. Options exist — ollama,
llama.cpp, LM Studio, vLLM — but the harness is pinned to the oMLX
endpoint, and *another OpenAI-compatible server is not yet a supported
runner configuration* (setup.md's own words). There is a concrete reason
beyond conservatism: the harness's liveness check hardcodes
`127.0.0.1:8001` and the eval CLI has no `--server` flag (the older
`deliver_candidate` tool has one, as precedent), so a server on any other
port reads as DOWN and `one`/`batch` refuse before Pi is ever invoked.
Supporting another server is a small, well-scoped change when someone
needs it; it is not this project's supported path yet.

**The API key.** oMLX requires an `Authorization` header but never checks
its value — a missing header makes a healthy server answer 401 and read as
down. The harness sends `not-needed` in two places: the liveness check
(`check_model_server_alive`'s `api_key` default in `harness/liveness.py`,
sent as a Bearer token) and the provider's `apiKey` in `models.json`
(what Pi sends on every call). If you ever point at a server that actually
validates keys, both places need the real key; for oMLX the value is
irrelevant as long as the header is present.

## The model: Gemma 4 12B IT

The pinned model is `gemma-4-12B-it-MLX-8bit` — Gemma 4 12B IT, in the
MLX 8-bit quantization (the id embeds the quantization). It is a small
local model: fast enough for iterative work, not a reasoning godbox, which
is the entire premise of the project.

Models are acquired through oMLX's HuggingFace integration — the menu-bar
app and admin dashboard wrap a downloader that searches Hugging Face,
filtering for MLX-quantized models and by system memory, and downloads the
one you pick. (The admin API behind it is `/api/hf/search` and
`/api/hf/download`.) The reference model arrives from Hugging Face as an
MLX quantized model.

Variants — other quantizations of the same family, other parameter sizes,
other model families — are discoverable through the same search. To use
one, two things are needed: get it into oMLX, and register it in
`models.json` (below). The harness itself has no other model-specific
coupling: the string is the whole interface.

## Tuning for our usage

There are two halves, and it is worth knowing which is which.

**Pi-side — `models.json`, per model entry.** These are the fields that
shape a run:

- `contextWindow` — 80000 for the reference model.
- `maxTokens` — 8192 in the committed file. Some workloads need more
  output budget; the phase-7 machinery temporarily raises it with
  `harness/model_config.py`'s `bumped_max_tokens` context manager, which
  restores the committed value even if the caller raises. Hand-editing the
  file, running, and hand-editing it back was the old practice — and a
  forgotten restore silently broke reproducibility, which is why the
  context manager exists.
- `reasoning` — false for the reference model; true for the DeepSeek entry
  in the same file.

**Server-side — oMLX.** The server does the heavy lifting: continuous
batching via a vLLM-style scheduler, a paged KV cache with prefix sharing
(repeated prefixes — like the harness's repeated tool-call envelopes —
don't re-evaluate), and a tiered cache that offloads to paged SSD when the
GPU cache fills. The exact knobs live in oMLX's menu-bar app and admin
dashboard, not in this repository's configuration.

## Wiring your own model into Pi

`pi-agent-dir/models.json` already demonstrates multi-provider
configuration: the `omlx` provider (baseUrl `http://127.0.0.1:8001/v1`,
apiKey `not-needed`, api `openai-completions`) with the Gemma and Qwen
entries, and a second provider, `dsflash`, pointing at a DeepSeek server on
port 8002. To add your own model:

1. Get it into oMLX through the HuggingFace downloader.
2. Add a model entry under a provider in `pi-agent-dir/models.json` —
   `id`, `name`, `reasoning`, `input`, `cost`, `contextWindow`,
   `maxTokens`.
3. Run with `--model <provider>/<id>`.

The rest of the environment wiring: `PI_CODING_AGENT_DIR` pins Pi to this
repo's `pi-agent-dir/`; `SATYRN_PI_PACKAGE` points at Pi's installed
package when the harness cannot locate it (`pi_package_root` in
`harness/runner.py` explains why the obvious lookups lie under volta); and
`EXPECTED_PI_VERSION` pins Pi 0.84.1 for batches so runs stay comparable.

The honest limit, restated: a different model on the reference server is a
one-entry edit. A different *server* — different port, different host, a
real API key — is not possible through the **eval** CLI without either
running it on `127.0.0.1:8001` or a small code change; the **engine** CLI
has `--server` and can point elsewhere today.

## Telling the eval and the engine about a new provider or model

Two consumers read the model registry, and they are configured
differently. This documents the existing seams — it builds no new
machinery.

**The registry.** Both paths resolve the model string through Pi, and Pi
reads `models.json` from the agent directory it is pointed at. The eval
pins `PI_CODING_AGENT_DIR=pi-agent-dir/` — the repo's committed registry.
The engine defaults to your own `~/.pi/agent` (`--agent-dir` overrides), so
its registry is personal unless you point it at the repo's.

**The eval (`one` / `batch`).** Three steps, all in
`pi-agent-dir/models.json`:

1. Add (or reuse) a provider block: `name`, `baseUrl` (the server's
   OpenAI-compatible root), `api`, `apiKey`, and a `models` list.
2. Add a model entry under it: `id`, `name`, `reasoning`, `input`, `cost`,
   `contextWindow`, `maxTokens`.
3. Run `--model <provider>/<id>` (or change `DEFAULT_MODEL` in
   `harness/pi_invocation.py`).

The eval's own liveness check still probes `127.0.0.1:8001` with no flag
to change it — a provider on another port is reachable by Pi but refused
by the CLI's liveness before any call. The `dsflash` provider in the
committed file (a DeepSeek server on port 8002) is a real example of a
second provider block.

**The engine (`deliver_candidate`).** Two forms:

- **Bare:** `--model <provider>/<id>` — the string must resolve in the
  `models.json` of the agent dir in use (default `~/.pi/agent/models.json`;
  `--agent-dir pi-agent-dir` to use the repo's). A different server
  address is `--server http://host:port` (the engine's liveness check
  honors it, and `--skip-server-check` exists for a server the machine
  cannot see). Pi's actual calls still go to the model entry's provider
  `baseUrl`.
- **Measured (a cell):** cells pin the arm's whole configuration and
  verify it before spending a call. `workloads/svcs/cells/*.toml` has a
  `[pinned]` section holding `model`, `base_url`, `max_tokens`,
  `context_window`, `tools`, `extensions`, `extensions_sha256`, and
  `wall_clock_seconds`; `verify()` refuses unless the live configuration
  matches ("Do not spend model calls until they agree"). So a new
  provider/model as a *measured* arm means a new cell pinning the new
  string and values, with the model registered in the agent dir's
  `models.json` — and any `maxTokens`/`contextWindow` the cell pins equal
  to that entry's fields (a mismatch fails `verify()`, not a run).

**Worked example — a second provider and a model on it.** A server on
`127.0.0.1:8003` serving `my-model`:

1. `models.json` gains a provider block, e.g.
   `"myprov": {"name": "My local server", "baseUrl":
   "http://127.0.0.1:8003/v1", "api": "openai-completions",
   "apiKey": "not-needed", "models": [{"id": "my-model", ...}]}`.
2. Eval: `uv run python -m harness.cli one --suite duration --model
   myprov/my-model` — on port 8003 the CLI's liveness refuses (port
   mismatch); serve it on 8001 and it runs.
3. Engine: `uv run python -m tools.deliver_candidate ... --model
   myprov/my-model --server http://127.0.0.1:8003` runs in bare form; a
   cell `myprov-my-model.toml` pins the string, `base_url`, and budgets
   for the measured form.
