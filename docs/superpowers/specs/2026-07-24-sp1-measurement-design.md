# SP1 — Part II (Measurement) Design

**Date**: 2026-07-24
**Status**: approved in brainstorming
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
- **Phase-agnostic.** The harness runs one phase or chains N with the same
  machinery. The baseline starts with Phase 1; multi-phase runs use the same
  code path.
- **n=8 statistical runs per data point.** Same phase, same model, independent
  workspace per run. Aggregate to success rate, mean/median/stddev of turns,
  tokens, and wall time.

## Architecture

```
harness/
  telemetry.py       # Parse pi --mode json JSONL → structured events
  workspace.py       # Provision disposable git-tracked workspace
  session.py         # Run one pi subprocess, capture stdout + diff + pytest
  runner.py          # n=8 loop, aggregation, report generation
  conftest.py        # Shared fixtures (pi binary, model config, app source)
tests/
  test_telemetry.py  # Unit: parse real and edge-case JSONL
  test_workspace.py  # Unit: git init, pristine commit, diff baseline
  test_session.py    # Integration: run pi against one phase (needs pi + model)
  test_runner.py     # Unit: aggregation with mock sessions
```

### `telemetry.py`

Parse the `pi --mode json` stdout stream line-by-line. Collect:
- User prompt(s)
- Tool calls (name, args, result, isError)
- Turn boundaries
- Token usage from `message_end` events (input, output, cache read/write)
- `appendEntry` evidence events

Return a `RunTelemetry` struct. Under 60 lines. The reader is unit-tested
against a recorded fixture JSONL (one real Pi run captured once).

### `workspace.py`

`prepare_workspace(app_dir)` copies the AgentClinic app into a disposable temp
directory, excludes `.venv`/`__pycache__`, runs `git init` + pristine commit.
Returns the workspace path.

`capture_diff(workspace)` runs `git diff` and `git status --porcelain -uall -z`,
returns changed files + full diff, excluding harness scaffolding and
Python/pytest build artifacts (`__pycache__`, `.pytest_cache`, `.pyc`).

Direct adaptation of Tainie's `_prepare_workspace` but simpler — no tool wiring,
no subagent config, no symlinks.

### `session.py`

`run_session(workspace, phase_prompt, model, timeout)` spawns
`pi --mode json -p "<prompt>" --model lmstudio/gemma-4-12b-it-mlx` via
`subprocess.Popen` (stream stdout), tees JSONL to
`research/sessions/<run-id>.jsonl`, waits for exit, runs `capture_diff` +
`uv run pytest`, returns `SessionResult`:

```python
@dataclass
class SessionResult:
    run_id: str
    outcome: str            # "exited" | "timeout" | "unreachable"
    returncode: int | None
    telemetry: RunTelemetry
    changed_files: list[str]
    diff: str
    tests_pass: bool
    wall_time_s: float
    artifact_path: str      # path to the session JSONL
```

Handles timeout via `subprocess.TimeoutExpired` — kills the subprocess, captures
partial stdout, sets `outcome: "timeout"`.

### `runner.py`

`run_baseline(phase, n=8)` calls `run_session` n times sequentially (each with
a fresh workspace), aggregates results into a `BaselineReport`: success rate,
mean/median/stddev of turns, tokens, tool calls, and wall time, plus a per-run
summary table. Writes the dated report to
`docs/superpowers/research/YYYY-MM-DD-baseline-phase-1.md`.

The runner uses a `--keep-workspaces` env var (default off) — when set, failed
workspaces are left in place for debugging. Mirrors Tainie's
`TAINIE_EVAL_KEEP_WORKSPACES`.

### `conftest.py`

Pytest fixtures for:
- `pi_binary` — `shutil.which("pi")`, skips if not on PATH
- `model` — `"lmstudio/gemma-4-12b-it-mlx"`
- `app_source` — path to `examples/agentclinic`
- `phase1_prompt` — the Phase 1 text from `examples/agentclinic/specs/roadmap.md`

## Evidence convention

The research report includes a markdown table citing each run's session file.
The Pi JSONL is the ground truth (auditable, replayable); the table is a
summary:

```
| Run | Outcome  | Turns | Tokens In | Tokens Out | Wall Time | Artifact |
|-----|----------|-------|-----------|------------|-----------|----------|
| 1   | exited   | 14    | 8.2K      | 3.1K       | 47s       | sessions/run-1.jsonl |
| 2   | timeout  | —     | —         | —          | 300s      | sessions/run-2.jsonl |
| ... |          |       |           |            |           |          |
|     | **Agg**  | μ=12  | μ=7.8K    | μ=2.9K     | μ=52s     |          |
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
AgentClinic app ──copy──▶ temp workspace ──pi --mode json──▶ JSONL + exit code
                                                                    │
                              git diff + git status ◀───────────────┤
                              uv run pytest       ◀───────────────┤
                                                                    ▼
                                                           SessionResult
                                                                    │
                                                     (n=8)          ▼
                                                           BaselineReport
                                                                    │
                                                                    ▼
                                              docs/superpowers/research/
                                              YYYY-MM-DD-baseline-phase-1.md
```

## Error handling

| Condition | Behavior |
|-----------|----------|
| Pi not on PATH | `pytest.skip` or clear error message |
| Model not reachable | Timeout, recorded as `outcome: "unreachable"` |
| Subprocess timeout | Kill, capture partial stdout, `outcome: "timeout"` |
| Pytest failure | `tests_pass: false`, included in report (this *is* the smoking gun) |
| Workspace cleanup | `try/finally` teardown; keep on failure via env var |

## Chapter outline

1. **"The Telemetry Reader"** — Parse `pi --mode json` stdout. Teaches the
   JSONL event schema, `message_end` token accounting, and `appendEntry`.
   End-to-end: the reader against a captured fixture produces a legible summary.

2. **"The Eval Session"** — Provision workspace, run pi headless, capture diff
   + pytest. Teaches disposable workspaces, `git diff` as a change signal, and
   acceptance tests as an oracle. End-to-end: one session against Phase 1
   produces a `SessionResult`.

3. **"The Smoking Gun"** — Run n=8 against Phase 1 with no steering, produce
   the baseline report. Teaches statistical aggregation, SLM variance, and the
   evidence convention. End-to-end: a dated report in `research/` that the rest
   of the course cites.

## Testing strategy

| Layer | Scope | Fixture | Gate |
|-------|-------|---------|------|
| `test_telemetry.py` | Unit: parse recorded JSONL | One real Pi run captured once | Always runs |
| `test_workspace.py` | Unit: git init, diff, exclusions | No model, no Pi | Always runs |
| `test_session.py` | Integration: live pi + model | Real `pi` on PATH | Gated by `PI_AVAILABLE` marker |
| `test_runner.py` | Unit: mock sessions → report | Pre-baked `SessionResult` values | Always runs |

## Out of scope

- The orchestrator/subagent mechanism (SP2 / Part III)
- Any guardrail/steering extension (SP3 / Part IV)
- n=8 across multiple phases (can be added later, same machinery)
- Model comparison (SP3 territory)
- A general-purpose "eval framework" — this is a course harness, not a product

## Source material

- Tainie eval driver: `~/projects/t-strings/tainie/src/tainie/eval/driver.py`
  (disposable workspace, subprocess driver, diff capture pattern)
- Tainie eval live: `~/projects/t-strings/tainie/src/tainie/eval/live.py`
  (`SessionResult`, `disposition` reducer)
- Tainie eval ledger: `~/projects/t-strings/tainie/src/tainie/eval/ledger.py`
  (GREEN/YELLOW/RED tiers)
- Tainie Pi verify spike:
  `~/projects/t-strings/tainie/docs/superpowers/specs/2026-07-12-pi-verify-spike-design.md`
  (Pi telemetry parsing, `--mode json` stream, runner/resume pattern)
