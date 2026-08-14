# The eval system, end to end

You type a command; a batch of runs lands in a checkpoint; a summary reads
it back. This page is what sits between — module by module, in execution
order. [How to write an eval](writing-evals.md) is the authoring side; the
"why" is in [why evals?](why-evals.md).

## The entry point: `harness/cli.py`

Six subcommands — `one`, `batch`, `preflight`, `suites`, `improvements`,
`summarize` — are a **translation layer, not an engine**. The CLI resolves
names against the registries, checks liveness and the version pin, and
renders the engine's refusals as sentences with exit code 2 (`omlx start`,
`docs/setup.md`) instead of tracebacks. The engine (`run_suite`,
`run_batch`) is byte-identical whether driven by the CLI or by Python;
the CLI is deliberately thin.

## The registries: `harness/runner.py`

`SUITES` maps a short CLI name to a `Suite` (task spec, acceptance,
allowlist). `IMPROVEMENTS` maps a name to an improvement **factory** —
never a result, so `import harness.runner` succeeds on a machine without
Pi; resolving an improvement is the moment Pi is touched. Keys are
CLI-facing shorthands; a suite's `name` field is not recorded in run
conditions, so the shorthand cannot drift evidence.

## The run: `run_suite`

1. **Liveness** — `check_model_server_alive()` refuses before any call.
   A dead server otherwise lets Pi exit 0 with empty output and the
   harness record a result that looks like data.
2. **Workspace** — `prepare_workspace()` makes an empty git repository
   (initial commit included); an improvement's `seed_dir` is copied in
   *before* git-init, so seeded files land in the initial commit and never
   pollute the run diff.
3. **The Pi invocation** — `pi_command()` builds one hermetic call:
   `--print --mode json --no-session`, the model, explicit extensions,
   an optional `--append-system-prompt`, and the task spec's text as the
   prompt. `pi_env()` pins `PI_CODING_AGENT_DIR` to this repo's
   `pi-agent-dir/`, strips the harness venv from the child's PATH, and
   removes `SSH_AUTH_SOCK` — the model cannot reach the tooling that
   grades it or the network it wasn't given.
4. **The bounded process** — `run_process()` with a timeout.
5. **The diff** — everything is staged and diffed against the initial
   commit (a plain `git diff <commit>` would miss untracked files). A
   model-created nested git repo makes this fail loudly but the failure is
   recorded, not fatal.
6. **The grade** — see below.

## The grade: `harness/grading.py`

Grading is hermetic by construction: the allowlisted files and the
acceptance are **copied into a fresh directory**, pytest runs there with
the grading plugin loaded, and the verdict is read from the results file
the plugin's hooks write (`__DONE__` marker plus one `nodeid\toutcome`
line per test). The expected count is read from the acceptance's source
(`_test_count`); model-written config is refused before any of this. The
model can neither see its grader nor change what grades it.

## The conditions: `RunConditions`

Every field that could differ between runs is recorded per run: model, the
normalized Pi command, Pi version, digests of the task spec, acceptance,
and extensions, the harness revision, both timeouts, the improvement name
and digest, the allowlist, and the agent-dir digest. These are what make
two runs comparable — and what make a batch refuse to resume a checkpoint
whose conditions have moved. A commit mid-batch, an edited acceptance, a
different Pi: the harness stops rather than silently mixing evidence.

## The batch: `run_batch`

Pins the Pi version (`EXPECTED_PI_VERSION`), refuses a checkpoint whose
recorded conditions don't match this batch's, runs `preflight_model`
(one real model call) once, then loops: `run_suite`, verify conditions
didn't move, `append_checkpoint`. Sequential by design — one shared local
model has no isolation.

## The checkpoint: `harness/checkpoint.py`

JSONL, one run per line, append-only with truncation repair (a half-written
final line is discarded, never a rewrite that could lose earlier records).
`load_checkpoint` reads them back, with sentinels for fields older
checkpoints predate — old records stay readable even when no longer
resumable.

## The summary: `harness.cli summarize`

Reads one checkpoint and prints the conditions header, run count,
acceptance, and one line per rejected run naming its signal. It never
compares two checkpoints — comparison is deliberately manual.

## The model wiring

The model string `--model <provider>/<id>` resolves through Pi against
`models.json` in the pinned agent dir; the default is `DEFAULT_MODEL` in
`harness/pi_invocation.py`; liveness uses the recorded server defaults;
`SATYRN_PI_PACKAGE` overrides where Pi's package lives. See
[model-setup](model-setup.md) for the full story and its limits.

## What is deliberately absent

The manifest (the `Improvement` docstring parks it: "that is the cycle
that adds the manifest"), comparison automation, and any engine logic in
the CLI. The harness measures; the phase documents the rest.
