# Phase 8 — An eval you can type, not one you paste

**Date:** 2026-08-13
**Status:** design — approved before any cycle
**Supersedes** the phase brief of the same date. This document is the
contract the five cycles implement; the brief was scratch paper and is
deleted once this is committed.

## Direction, one sentence

> Replace the harness's Python-only interface — module constants and
> factory functions — with a small, stdlib-only command,
> `uv run python -m harness.cli`, where suites and improvements are
> addressed by name, failures say what to fix, and `--help` is the
> documentation.

## Why this phase, and why now

Every published number in this project was produced by `run_suite` and
`run_batch` in `harness/runner.py`, and their only interface is Python:
`AGENTCLINIC_PHASE_1` and `AGENTCLINIC_PHASE_1_USER_STORY` are module
constants, `tech_stack_only()` and `sdd_orchestrator()` are factory
functions, and running anything means writing a `python -c` incantation
that reconstructs a `Path.home() / "evidence" / …` default. There is no
`--help`, no way to discover what suites or improvements exist, and a dead
model server or wrong Pi version surfaces as a raw traceback.

The machinery is done — the phase is about the entry point. `run_suite`
and `run_batch` stay exactly as they are; the CLI is a thin, discoverable
translation of what they already do. Comparison stays deliberately manual.

## What this phase is not

It is **not** a manifest and **not** a Makefile. The `Improvement`
docstring explicitly parks the manifest ("that is the cycle that adds the
manifest"); a parser, a schema, and an error path have no present caller.
The phase is the registry, not the manifest.

It is **not** comparison automation. `summarize` reads a checkpoint and
compares nothing; "one improvement at a time, comparison by hand" stays the
binding.

It adds **no dependency**. `argparse` ships with Python; nothing new goes
into `pyproject.toml`.

It does **not** touch the engine. No change to `run_suite`/`run_batch`
semantics beyond the two registry dicts added to `runner.py`; no change to
the phase 7 machinery or its branch.

## Decisions locked in brainstorming

Four decisions were made during brainstorming, each with a recorded
rationale so a later cycle does not quietly re-litigate them.

**D1 — Registry keys are short CLI names, not mirrors of `name`.**
`SUITES` is keyed `agentclinic-phase-1`, `user-story`, `duration`; the
user-story suite's real `name` is `agentclinic-phase-1-user-story` and is
not a valid key. This matches the brief and the ROADMAP ("keyed by short
name"), and "type, don't paste" is the point of the phase. The shorthand is
safe because `Suite.name` is **not** recorded in `RunConditions` — a
checkpoint distinguishes suites by `task_spec_sha256`,
`acceptance_sha256`, and `source_allowlist`, so a shorthand key causes zero
drift in recorded evidence. Improvement keys are the **exact** mirror of
`Improvement.name`, because `improvement_name` *is* recorded — the name a
user types is the name in the checkpoint. The asymmetry is justified, not
accidental. To keep the shorthand self-documenting, the registry carries a
comment and the `suites` subcommand prints each key beside its `Suite.name`.

**D2 — `one` checks the model server only, not the Pi version.**
`run_suite` deliberately does not pin Pi (setup.md: "A single `run_suite`
does not check, so exploring is never blocked"), and the CLI translates the
harness rather than extending it. The version pin stays where the harness
has it: `batch` (via `run_batch`'s existing `RuntimeError`) and the
`preflight` subcommand's report. This deviates from the brief's cycle-3
sentence ("`one` and `batch` run … the Pi-version check up front") on
purpose; the deviation is recorded here rather than silently absorbed.

**D3 — Exit codes follow the repo's established language.** `deliver_candidate`
already documents `0/1/2/3` and the README explains them; this CLI uses the
subset that applies:

- **0** — the command completed its purpose. For `one`, that includes a run
  the model *failed*: the verdict is printed data and the checkpoint is the
  record, so a failing model is not a broken command.
- **2** — refused before starting: unknown suite/improvement name, negative
  `--target`, model server down, wrong Pi version, checkpoint mismatch,
  missing summarize path. This is also argparse's native usage-error code,
  so `choices=` rejections and `parser.error` calls agree with it.
- **1** — unexpected error. The known failure classes are translated to
  messages; a genuine bug still tracebacks. Hiding a bug is worse than
  showing it.

**D4 — `summarize` prints a conditions header plus per-run rejections.**
`load_checkpoint` gives the records; the summary reads one checkpoint and
never compares two. The first record's `RunConditions` (model,
`improvement_name`, `pi_version`) head the output so two summaries can sit
side by side for the manual comparison the phase deliberately preserves.
Rejected runs get one line each, 1-indexed by position in the file, naming
the distinguishing signal.

## Section 1 — Name registries (`harness/runner.py`)

Cycle 1 adds two module-level dicts and frees a name:

- Rename the existing `IMPROVEMENTS` **Path** constant (`REPO_ROOT /
  "improvements"`) to `IMPROVEMENTS_DIR`. Four references, all inside
  `runner.py`; nothing else in the repo uses the name. The dict takes
  `IMPROVEMENTS`.
- `SUITES: dict[str, Suite]`, placed after the three `Suite` constants:

  ```python
  SUITES = {
      "agentclinic-phase-1": AGENTCLINIC_PHASE_1,
      "user-story": AGENTCLINIC_PHASE_1_USER_STORY,
      "duration": DURATION,
  }
  ```

  with a comment stating the shorthand policy (D1): keys are CLI-facing
  short names; `Suite.name` is not recorded in `RunConditions`, so the
  divergence is cosmetic by design.

- `IMPROVEMENTS: dict[str, Callable[[], Improvement]]`, placed after the
  four improvement factories, keyed by the exact `Improvement.name`s:

  ```python
  IMPROVEMENTS = {
      "tech-stack-only": tech_stack_only,
      "sdd-orchestrator": sdd_orchestrator,
      "sdd-orchestrator-guarded": sdd_orchestrator_guarded,
      "sdd-orchestrator-guarded-stack": sdd_orchestrator_guarded_stack,
  }
  ```

  Values are the **factories**, never their results. This is what makes
  `import harness.runner` succeed on a machine without Pi: the factories
  call `pi_package_root()`, and calling it at import time would break the
  constraint that the suite stays runnable for a contributor who has not
  installed Pi. The CLI resolves a name by invoking the factory, exactly as
  callers invoke `tech_stack_only()` today.

`Callable` comes from `collections.abc` (already the repo's style for
typing imports).

## Section 2 — The CLI (`harness/cli.py`)

A single module, argparse subparsers, `main(argv: Sequence[str] | None =
None) -> int` and `if __name__ == "__main__": sys.exit(main())` — the same
shape as `tools/deliver_candidate.py`, including the testable `main(argv)`
seam. Run as `uv run python -m harness.cli`.

Six subcommands:

```
one            --suite NAME [--improvement NAME] [--model M] [--timeout S]
batch          --suite NAME [--target N] [--improvement NAME] [--model M]
               [--checkpoint PATH] [--timeout S]
preflight      (no arguments; reports liveness and the Pi version pin — see Section 3)
suites         (no arguments)
improvements   (no arguments)
summarize      CHECKPOINT_PATH
```

- `--suite` and `--improvement` use `choices=` built from the registry
  keys, so an unknown name is argparse's clean "invalid choice" error
  (exit 2) and `--help` renders the full menu — `--help` is the
  documentation.
- `--model` defaults to `DEFAULT_MODEL`; `--timeout` to `600`; `--target`
  to `16` — the exact defaults `run_suite`/`run_batch` already carry.
- `--checkpoint` defaults to `~/evidence/<suite>-<date>.jsonl` where
  `<suite>` is the registry key and `<date>` is ISO `YYYY-MM-DD`.
  Short keys make short filenames — a second reason D1's shorthand pays.
- `one` runs a single `run_suite` and prints the verdict (accepted or not,
  with the grade signals that explain a rejection: `tests_executed` vs
  `tests_expected`, `returncode`, `refused_config`, `timed_out`). It does
  **not** write a checkpoint — checkpointing is `batch`'s job; `one` is for
  exploring and verifying.
- `batch` runs `run_batch` and prints one line per attempt plus a final
  summary naming the checkpoint path and the accepted count.
- `suites` prints the keys sorted, each with its `Suite.name` in
  parentheses (D1's self-documentation); `improvements` prints the keys
  sorted.

## Section 3 — Friendly preflight

`one` and `batch` call `check_model_server_alive()` up front and translate
`ModelServerDown` into a human sentence with the fix — "start the model
server with `omlx start` (see docs/setup.md)" — and exit 2. Without this,
a dead server surfaces as a traceback from inside `run_suite`.

`batch` additionally translates the two exceptions `run_batch` already
raises, as messages rather than tracebacks:

- the Pi-version `RuntimeError` (wrong `pi --version`) → the message plus
  "see docs/setup.md", exit 2;
- the checkpoint-mismatch `ValueError` ("checkpoint conditions do not match
  this batch") → the message as-is, exit 2.

`one` does **not** translate a version mismatch because it never checks
(D2). Unexpected exceptions are not caught: a bug should traceback.

The known exception classes are caught individually and explicitly; the
translation is a handful of `except` clauses in the dispatch, not a wrapper
that swallows everything.

**`preflight`** is the diagnostic form of the same checks. It runs
`check_model_server_alive()` and the version pin — installed `pi --version`
(via subprocess, as `runner._conditions` already does) compared against
`EXPECTED_PI_VERSION` — and prints one line per check with its verdict. All
pass: exit 0. Either fails: the same human fix sentence as `one`/`batch`
(`omlx start`; `docs/setup.md`) and exit 2. It makes no model call and
writes nothing — it is the cheap thing to run before starting a batch.

## Section 4 — `summarize`

`harness.cli summarize <checkpoint.jsonl>` reads the checkpoint via
`load_checkpoint` and prints, for a checkpoint with records:

```
file:       ~/evidence/duration-2026-08-13.jsonl
conditions: model=omlx/gemma-4-12B-it-MLX-8bit  improvement=none  pi=0.84.1
runs:       16
accepted:   12

rejected:
  2   refused_config=pyproject.toml
  5   timed_out
  9   returncode=1 (2/4 tests passed)
  12  refused_config=conftest.py
```

The `conditions` line comes from the first record's `RunConditions` —
model, `improvement_name`, `pi_version` — and is what lets a contributor
put two summaries side by side for the manual comparison. Each rejected
run's line names the distinguishing `GradeResult` signal, in priority
order: `refused_config`, `timed_out`, nonzero `returncode` (with
`tests_executed`/`tests_expected`), then `tests_executed <
tests_expected`. All-accepted checkpoints omit the `rejected:` block.

A missing path is a friendly error (exit 2 — almost certainly a typo); a
present-but-empty checkpoint prints `runs: 0` (exit 0 — `load_checkpoint`
returns `[]` for a missing file, which is the resume-empty contract for
`batch`, and `summarize` treats that as "nothing recorded yet", not an
error).

`summarize` never compares two checkpoints. That is deliberate and stated
in its help text.

## Section 5 — Documentation

- **README.md**: a short "run an eval" subsection with one-liners for
  `one` and `batch` (`uv run python -m harness.cli one --suite duration`,
  `… batch --suite duration --improvement tech-stack-only`), each pointing
  at `docs/evals.md` for the longer treatment.
- **docs/evals.md** (new): why measure, what a run / batch / improvement /
  checkpoint is, how to run each via the CLI, and the three things that
  will bite you, moved out of the roadmap and given room:
  - batches are single-threaded — the model server serializes children, so
    a batch is many sequential runs, not parallel;
  - a commit aborts a running batch — the run conditions guard refuses to
    resume a checkpoint whose recorded conditions moved;
  - no trustworthy wall-clock number exists — per-message durations are not
    recorded as start/end pairs, and the phase publishes no timing claim.

## Test strategy

Hermetic throughout; no live model, no Pi, no network. `tests/` conventions
apply (`tests/support.py`, `tests/conftest.py`, the `capsys` +
`monkeypatch` pattern from `tests/test_deliver_candidate.py`).

**`tests/test_registries.py`** (cycle 1):

- `SUITES` and `IMPROVEMENTS` have exactly the documented key sets (the
  contract is pinned, so an accidental key change fails a test).
- `SUITES` values are `Suite`s whose `task_spec`/`acceptance` exist and
  whose `source_allowlist` is non-empty (extends the existing
  `test_both_suites_point_at_files_that_exist` to all three).
- `IMPROVEMENTS` values are callables, never `Improvement` instances.
- Invoking each factory — with `pi_package_root` monkeypatched to a stub
  path, or `SATYRN_PI_PACKAGE` pointed at a stub — returns an `Improvement`
  whose `name` matches the key, whose `extensions` resolve under the stub
  (they are the only paths that come from `pi_package_root`), and whose
  `seed_dir`/`system_prompt` resolve under the repo's `IMPROVEMENTS_DIR`.
- **Laziness, proven**: with `pi_package_root` monkeypatched to raise,
  `importlib.reload(harness.runner)` succeeds (import never calls it), and
  invoking a factory raises — the registry holds lazy callables, not
  eager results.

**`tests/test_cli.py`** (cycles 2–4), driving `main(argv)` directly:

- `suites`/`improvements` print the sorted keys; `suites` shows
  key → `Suite.name`.
- Unknown `--suite`/`--improvement` and a negative `--target` are clean
  errors, exit 2, no traceback.
- `one` with `run_suite` monkeypatched prints the verdict; with
  `check_model_server_alive` monkeypatched to raise `ModelServerDown`, it
  prints the friendly sentence and exits 2.
- `batch` with `run_batch` monkeypatched prints per-attempt lines and the
  final summary; the default checkpoint path has the shape
  `~/evidence/<key>-<date>.jsonl`; a `RuntimeError` from `run_batch` (the
  version refusal) and a `ValueError` (the checkpoint mismatch) each render
  as a message with exit 2.
- `summarize` over a fixture checkpoint written as literal JSONL prints the
  section-4 shape; a missing path is a friendly error, exit 2.
- `--help` at top level lists all six subcommands (the "help is the
  documentation" contract).
- `preflight` with liveness and the version check stubbed passes prints a
  per-check verdict and exits 0; with either stubbed to fail it prints the
  fix sentence and exits 2.

## Constraints and norms

- **Stdlib only.** `argparse`; nothing added to `pyproject.toml`.
- **No machinery ahead of the contract.** No manifest, no Makefile/Justfile
  target, no comparison automation.
- **Quality gates:** `uv run ruff check .`, `uv run ruff format --diff`,
  `uv run pyrefly check` — all green before pushing.
- **Verify, don't assert.** The friendly-message behavior is tested against
  stubs, not claimed.
- **Working style:** branch `phase8-eval-cli` off `main`, worktree in
  `.worktrees/`, five tiny commits, one per cycle, test-first, messages in
  repo style (`feat(phase8): …`, `docs(phase8): …`). Phase 7's machinery is
  not touched.

## Definition of done

- `uv run pytest` green (live tests skip without Pi, as today).
- All three quality gates pass.
- A contributor can run `uv run python -m harness.cli --help` and get from
  zero to a batch with no reference to `harness/runner.py`.
- `docs/evals.md` exists and the README points at it.
