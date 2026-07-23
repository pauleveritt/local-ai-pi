# SP1 — Part II (Measurement) Design

**Date**: 2026-07-24
**Status**: approved in brainstorming, revised after deep review
**Parent**: [course-design](2026-07-23-course-design.md) Part II

## Purpose

Build the measurement harness for the course: a telemetry reader, a disposable
eval session, and an n=8 statistical baseline run against the AgentClinic app
with an unsteered SLM. This Part is load-bearing — Parts III and IV cannot be
evaluated without the harness and baseline it produces.

The harness itself is a teaching vehicle, built incrementally across three
chapters, not delivered as finished infrastructure.

## Non-negotiable constraints

- **Built-in Pi only.** The harness drives the `pi` binary on `PATH` via
  `subprocess` — no fork, no patch, no internal API.
- **Evidence-gated.** The baseline report is a dated artifact in
  `docs/superpowers/research/`, not a prose claim. Every number cites its
  session JSONL.
- **Python, stdlib+pytest.** `subprocess` for `pi`, `pytest` for the n=8 loop,
  `tempfile` for workspaces. No framework dependencies.
- **Phase-agnostic.** The harness runs any phase with the same machinery by
  extracting a phase's prompt from the roadmap. The baseline starts with Phase
  1; if Phase 1 does not produce a failure, the harness moves to Phase 2 or 3
  for the smoking-gun report. Multi-phase chaining (accumulating workspace
  across phases in one pi invocation) is deferred to a later sub-project; the
  harness runs single phases independently.
- **n=8 statistical runs per data point.** Same phase, same model, independent
  workspace per run. Aggregate to success rate, mean/median/stddev of turns,
  tokens, and wall time. Runs are sequential to avoid single-model contention on
  LM Studio; wall time budget is ~30–50 minutes for n=8 (each run may take up
  to 300s before timeout).
- **Headless pi is isolated from global configuration.** No RTK, Superpowers,
  skills, prompt templates, themes, or context files — only the extensions and
  configuration intentionally placed by the harness. Achieved via pi CLI flags
  (see "Pi invocation" below).

## Architecture

```
harness/
  telemetry.py       # Parse pi --mode json JSONL → structured events
  workspace.py       # Provision disposable git-tracked workspace
  session.py         # Run one pi subprocess, capture stdout + diff + pytest
  runner.py          # n=8 loop, aggregation, report generation
tests/
  conftest.py        # Shared fixtures (pi binary, model config, app source)
  fixtures/          # Captured artifacts for deterministic unit tests
    sample-session.jsonl   # One real Pi run, regenerated manually
  test_telemetry.py  # Unit: parse real and edge-case JSONL
  test_workspace.py  # Unit: git init, pristine commit, diff baseline
  test_session.py    # Integration: run pi against one phase (needs pi + model)
  test_runner.py     # Unit: aggregation with mock sessions
```

`pytest` discovers `harness/` modules via `[tool.pytest.ini_options]` in the
root `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

### Pre-implementation: schema capture (R0)

Before writing `telemetry.py`, capture one real `pi --mode json` session to
run-confirm the event schema. This is a deliberate guard against the
documented-but-wrong trap: the Tainie Pi spike's plan discovered that
documented event names diverge from reality, so the exact event types, field
names, and token-usage shapes must be extracted from a real capture, not
assumed.

**Deliverable:** `tests/fixtures/sample-session.jsonl` — a real pi run
(one prompt, one phase, Gemma on LM Studio), committed to the repo as a
frozen test fixture. Regenerated manually when Pi's event schema changes.

### `telemetry.py`

Parse the `pi --mode json` stdout stream line-by-line. Collect:
- User prompt(s)
- Tool calls (name, args, result, isError)
- Turn boundaries
- Token usage from `message_end` events (fields confirmed from the captured
  fixture, not documented expectations)
- `appendEntry` evidence events (written by the hello-world extension)

Return a `RunTelemetry` dataclass. A focused, small module.

Unit-tested against `tests/fixtures/sample-session.jsonl` (always runs, no
model needed). Edge cases: empty stream, malformed lines, missing fields.

Event type strings and field names are extracted from the captured fixture,
not hard-coded from documentation. The module's docstring records which Pi
version produced the fixture.

### `workspace.py`

`prepare_workspace(app_dir)` copies the AgentClinic app into a disposable temp
directory, excludes `.venv`/`__pycache__`, runs `git init` + pristine commit.
Returns the workspace path **and the pristine commit hash**.

A workspace is spec-only (the `examples/agentclinic/` directory contains only
`specs/` — no app code, no `pyproject.toml`). The harness stamps a `pyproject.toml`
with the dependencies from `examples/agentclinic/specs/tech-stack.md` into the
workspace before the pristine commit. This is what makes `uv run pytest`
runnable after the SLM writes the app:

```toml
[project]
name = "agentclinic"
version = "0.1.0"
requires-python = ">=3.14,<3.15"
dependencies = [
    "fastapi[standard]==0.115.10",
    "uvicorn==0.51.0",
    "pytest==8.3.4",
]
```

After stamping `pyproject.toml`, `prepare_workspace` runs `uv sync` in the
workspace to install dependencies, then `git add -A` + pristine commit. The
`.venv/` is excluded from the pristine commit (it's in `.gitignore` not yet
existing; the commit must explicitly exclude it). Dependencies are re-resolved
per workspace (no cached lockfile) — fastapi/starlette/uvicorn/pytest resolve
quickly and the course values simplicity over lockfile purity for the harness.

`capture_diff(workspace, pristine_hash)` runs `git diff <pristine_hash>` and
`git status --porcelain -uall -z`, returns changed files + full diff, excluding
harness scaffolding and Python/pytest build artifacts. Union of both commands
so edits the model committed (`git add`/`git commit`, possible via bash) are
still visible via `git diff <pristine_hash>`.

Direct adaptation of Tainie's `_prepare_workspace` but simpler — no tool wiring,
no subagent config, no symlinks. Adds the `pyproject.toml` stamp + `uv sync`
step Tainie did not need (its apps were pre-built).

### `session.py`

`run_session(workspace, phase_prompt, model, timeout)`:

**Pi invocation (isolation):**
```
pi --mode json --print --no-session \
   --model lmstudio/gemma-4-12b-it-mlx \
   --no-extensions --extension .pi/extensions/hello-world.ts \
   --no-skills --no-prompt-templates --no-themes --no-context-files \
   --approve \
   -- "<phase_prompt>"
```

The `--no-*` flags strip global configuration (RTK, Superpowers, skills).
`--extension` explicitly whitelists only the hello-world extension (needed for
`appendEntry` evidence events). `--approve` trusts the project-local extension
file in headless mode. `--no-session` prevents Pi from writing its own session
file; the harness captures stdout as the sole artifact. `--print` (same as
`-p`) is non-interactive mode.

**Subprocess mechanics:**

Uses `subprocess.Popen` with `stdin=subprocess.DEVNULL` to avoid the
never-EOF stdin hang documented in KICKOFF. Streams stdout line-by-line,
teeing each line to `research/sessions/<run-id>.jsonl` (the durable artifact)
while accumulating events in memory for `RunTelemetry`.

Sets `stdin=subprocess.DEVNULL`. Passes the prompt as a positional argument
(preceded by `--` to prevent flag parsing issues) rather than via stdin, so
the prompt content is cleanly separated from the stdin close.

**Post-run:**

After the subprocess exits, runs `capture_diff(workspace, pristine_hash)` +
`uv run pytest -q`, returns `SessionResult`:

```python
@dataclass
class SessionResult:
    run_id: str
    outcome: str            # "exited" | "timeout"
    returncode: int | None
    telemetry: RunTelemetry
    changed_files: list[str]
    diff: str
    tests_pass: bool
    wall_time_s: float
    artifact_path: str      # path to the session JSONL
```

Handles timeout via `subprocess.TimeoutExpired` — kills the subprocess,
captures whatever stdout accumulated, sets `outcome: "timeout"`.

**Startup-hang detection:** If the subprocess exits with a timeout and
produced zero JSONL lines (no sessionID-equivalent), retry up to 3 times
before recording `outcome: "timeout"`. An empty-stdout timeout is a
transient launch failure (Tainie's `F-OPENCODE-STARTUP-HANG`), not a
measurement. A run that produced at least one event before timing out is
not retried — that is a real measurement, even if truncated.

**"Success" per run:** A run is successful when `outcome == "exited"` and
`tests_pass == True` and `len(changed_files) > 0`. Timeouts and null-action
runs (zero changed files, tests pass vacuously) are not success. This is
the definition `runner.py` uses for success rate.

### `runner.py`

`run_baseline(phase_prompt, n=8)` calls `run_session` n times sequentially
(each with a fresh workspace), aggregates results into a `BaselineReport`:
success rate, mean/median/stddev of turns, tokens, tool calls, and wall time,
plus a per-run summary table. Writes the dated report to
`docs/superpowers/research/YYYY-MM-DD-baseline-phase-1.md`.

The runner uses a `PI_EVAL_KEEP_WORKSPACES` env var (default unset) — when set
to any non-empty value, failed workspaces are left in place for debugging.
Mirrors Tainie's `TAINIE_EVAL_KEEP_WORKSPACES`.

**Phase escalation:** If Phase 1 succeeds (majority of n=8 are successful),
the runner notes this in the Phase 1 report and proceeds to baseline Phase 2
or Phase 3 until a failure surface appears. The smoking-gun report is the
first phase that shows consistent failure. This prevents the course premise
from resting on a phase that might be too simple for the SLM to fail.

### `tests/conftest.py`

Pytest fixtures for:
- `pi_binary` — `shutil.which("pi")`, skips if not on PATH
- `model` — `"lmstudio/gemma-4-12b-it-mlx"`
- `app_source` — path to `examples/agentclinic`
- `phase1_prompt` — verbatim Phase 1 section from `examples/agentclinic/specs/roadmap.md`

The phase prompt fixture extracts the `## Phase N — ...` section from the
roadmap. The extraction is trivial: find the markdown header, take all lines
until the next `## Phase` or EOF. The prompt handed to pi is the verbatim
checklist text — no reformulation or wrapping. This matches the course
design's intent: "the existing overly-detailed, implementation-heavy roadmap"
serves as the baseline workload.

## Evidence convention

The research report includes a markdown table citing each run's session file.
The Pi JSONL is the ground truth (auditable, replayable); the table is a
summary:

```
| Run | Outcome  | Success | Turns | Tokens In | Tokens Out | Wall Time | Artifact |
|-----|----------|---------|-------|-----------|------------|-----------|----------|
| 1   | exited   | ✅       | 14    | 8.2K      | 3.1K       | 47s       | sessions/run-1.jsonl |
| 2   | timeout  | ❌       | —     | —         | —          | 300s      | sessions/run-2.jsonl |
| ... |          |         |       |           |            |           |          |
|     | **Agg**  | 3/8     | μ=12  | μ=7.8K    | μ=2.9K     | μ=52s     |          |
```

Claims carry evidence tiers per the [evidence policy](../policies/evidence.md):
- **GREEN** — deterministic, artifact-backed (e.g., "3 of 8 runs passed
  `pytest`" with session files cited)
- **YELLOW** — real but noisy (e.g., "mean turns: 14 ± 6", with sample size
  noted)
- **RED** — estimated, never presented as a result

No separate `LedgerEntry` type system — the JSONL is the artifact, the table is
the presentation.

## Data flow

```
AgentClinic app ──copy──▶ temp workspace ──pi --mode json -p --no-session──▶ JSONL + exit code
      │                        │         (stdin=DEVNULL, isolated flags)           │
      │                  pyproject.toml stamp                                      │
      │                  uv sync                                                  │
      │                  git init + pristine commit                                │
      │                                                                           │
      │                    git diff <pristine> + git status ◀─────────────────────┤
      │                    uv run pytest                 ◀─────────────────────┤
      │                                                                           ▼
      │                                                                   SessionResult
      │                                                                            │
      └── specs/roadmap.md (phase prompt)                              (n=8)          ▼
                                                                             BaselineReport
                                                                                    │
                                                                                    ▼
                                                                  docs/superpowers/research/
                                                                  YYYY-MM-DD-baseline-phase-N.md
```

## Error handling

| Condition | Behavior |
|-----------|----------|
| Pi not on PATH | `pytest.skip` or clear error message |
| Subprocess timeout (zero output) | Retry up to 3×; still empty → `outcome: "timeout"` |
| Subprocess timeout (partial output) | Keep partial stdout, `outcome: "timeout"` |
| Pytest failure in workspace | `tests_pass: false`, included in report |
| Workspace cleanup | `try/finally` teardown; keep on failure via `PI_EVAL_KEEP_WORKSPACES` |
| SLM commits via git | Diffed against pristine commit hash, so committed changes are visible |

## Chapter outline

1. **"The Telemetry Reader"** — Parse `pi --mode json` stdout. Teaches the
   JSONL event schema, `message_end` token accounting, and `appendEntry`.
   End-to-end: the reader against `sample-session.jsonl` produces a legible
   summary. The chapter opens by capturing the fixture live so the reader
   runs pi once and sees the raw event stream.

2. **"The Eval Session"** — Provision workspace, stamp `pyproject.toml`, run
   pi headless with isolation flags, capture diff + pytest. Teaches disposable
   workspaces, `git diff <pristine>` as a change signal, and acceptance tests
   as an oracle. End-to-end: one session against Phase 1 produces a
   `SessionResult`.

3. **"The Smoking Gun"** — Run n=8 against a phase with no steering, produce
   the baseline report. Teaches statistical aggregation, SLM variance, and
   the evidence convention. End-to-end: a dated report in `research/` that
   the rest of the course cites. If Phase 1 passes consistently, escalate to
   Phase 2 or 3 for the failure visible in the report.

## Testing strategy

| Layer | Scope | Fixture | Gate |
|-------|-------|---------|------|
| `test_telemetry.py` | Unit: parse recorded JSONL | `tests/fixtures/sample-session.jsonl` | Always runs |
| `test_workspace.py` | Unit: git init, diff, exclusions, pyproject stamp | No model, no Pi | Always runs |
| `test_session.py` | Integration: live pi + model | Real `pi` on PATH | Gated by `PI_AVAILABLE` marker |
| `test_runner.py` | Unit: mock sessions → report | Pre-baked `SessionResult` values | Always runs |

## Out of scope

- The orchestrator/subagent mechanism (SP2 / Part III)
- Any guardrail/steering extension (SP3 / Part IV)
- Multi-phase chaining (accumulating workspace across phases in one pi
  invocation) — deferred to a later sub-project; the harness runs single
  phases independently
- Model comparison (SP3 territory)
- A general-purpose "eval framework" — this is a course harness, not a product

## Source material

- Tainie eval driver: `~/projects/t-strings/tainie/src/tainie/eval/driver.py`
  (disposable workspace, subprocess driver, diff capture pattern, startup-hang retry)
- Tainie eval live: `~/projects/t-strings/tainie/src/tainie/eval/live.py`
  (`SessionResult`, `disposition` reducer)
- Tainie eval ledger: `~/projects/t-strings/tainie/src/tainie/eval/ledger.py`
  (GREEN/YELLOW/RED tiers)
- Tainie Pi verify spike:
  `~/projects/t-strings/tainie/docs/superpowers/specs/2026-07-12-pi-verify-spike-design.md`
  (Pi telemetry parsing, `--mode json` stream, runner/resume pattern, R0 schema capture)
