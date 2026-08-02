# Telemetry Reader Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `harness/telemetry.py`, exposing `read_telemetry(pi_stdout: str) -> RunTelemetry` — a pure function that derives turn, tool-call, and token measurements from the `pi --mode json` JSONL text `RunResult.pi_stdout` already captures.

**Architecture:** One new module, one pure function, no I/O and no dependencies on other `harness` modules. It reads a string and returns two frozen dataclasses. `runner.py`, `checkpoint.py`, and the batch are untouched, and nothing consumes the result yet — that is deliberate (see the spec's "What this cycle is not"). Proof is anchored to a real captured stream, `tests/fixtures/pi-run-0.82.0.jsonl`, with small synthetic strings built inline only for the three cases real data cannot reach.

**Tech Stack:** Python 3.14, stdlib only (`json`, `dataclasses`). pytest 8.3.4, ruff, pyrefly.

**Spec:** [`docs/superpowers/specs/2026-08-02-phase2-cycle1-telemetry-reader-design.md`](../specs/2026-08-02-phase2-cycle1-telemetry-reader-design.md)

## Global Constraints

- **Zero changes to `harness/runner.py`, `harness/checkpoint.py`, or the batch.** This cycle adds one module and its tests. Nothing consumes `RunTelemetry`.
- **A turn is one `turn_end` event.** Load-bearing; recorded in the module docstring. Any future change to it invalidates comparison against every number this instrument produces.
- **Token usage is read from `turn_end` only.** `message_end` events also carry `message.usage` in this stream (6 of 12 of them). Summing both would exactly double the totals. The fixture assertions in Task 1 catch that.
- **Malformed lines are skipped, never raised** — matching the truncation tolerance `harness/checkpoint.py` already established.
- **`complete` is `True` only when both hold:** the stream contains an `agent_end` event, *and* every `tool_execution_start` has a matching `tool_execution_end`.
- **Deliberate exclusions stay excluded.** No `totalTokens` field, no separate `reasoning` field, no tool-call `args`/`result`, no wall time, no cost, no parent/child attribution. The spec's "Deliberate exclusions" table is not a backlog.
- **Quality gates:** `uv run pytest tests/ && uv run ruff check . && uv run pyrefly check` must pass at every commit. (See "A note on the bare `pytest` gate" at the end — `uv run pytest` without `tests/` fails on pre-existing local state unrelated to this cycle.)

## File Structure

| File | Responsibility |
|---|---|
| `harness/telemetry.py` (create) | `ToolCall`, `RunTelemetry`, `read_telemetry`. The whole cycle. |
| `tests/test_telemetry.py` (create) | Fixture-anchored proof plus the three synthetic cases. |
| `ROADMAP.md` (modify) | Phase 2 row, Phase 2 cycle table, four concept-budget terms. |
| `docs/superpowers/index.md` (modify) | Phase 2 section; spec and plan into the hidden toctrees. |

## Verified Facts About the Fixture

Every number below was reproduced by running against `tests/fixtures/pi-run-0.82.0.jsonl` before this plan was written. Do not re-derive them; do verify them by making the tests pass.

- 123 lines, all valid JSON, trailing newline, no blank lines.
- Event types present: `message_update` (72), `message_start` (12), `message_end` (12), `turn_start` (6), `turn_end` (6), `tool_execution_start` (5), `tool_execution_end` (5), `session` (1), `agent_start` (1), `tool_execution_update` (1), `agent_end` (1), `agent_settled` (1).
- The stream ends `message_end`, `turn_end`, `agent_end`, `agent_settled`.
- `turn_end` shape: `{"type": "turn_end", "message": {..., "usage": {"input": int, "output": int, "cacheRead": int, "cacheWrite": int, "reasoning": int, "totalTokens": int, "cost": {...}}, ...}, "toolResults": [...]}`.
- Per-turn `input`: 1751, 1778, 1115, 1344, 480, 600 — non-monotonic, so usage is per-turn and not cumulative.
- Totals: input 7,068 / output 933 / cacheRead 6,144 / cacheWrite 0 / reasoning 0. `context_processed` = 13,212.
- `tool_execution_start` shape: `{"type": ..., "toolCallId": str, "toolName": str, "args": {...}}`. Start order: `bash`, `write`, `write`, `write`, `write`.
- `tool_execution_end` shape: `{"type": ..., "toolCallId": str, "toolName": str, "result": {...}, "isError": bool}`. All 5 `isError` values are real Python `bool` `False` — **not** the string the pre-restructure 0.81.1 reader expected.
- `tool_execution_update` also carries `toolCallId` and `toolName`. It must not be counted as a start or an end.
- `reasoning` is 0 in every `turn_end`, so the fixture cannot prove the reasoning fold. Task 2 does that with a synthetic stream.

---

### Task 1: `read_telemetry` over a healthy run

Everything the real fixture can prove: turn counting, tool-call correlation by `toolCallId`, token summing from `turn_end`, and the `agent_end` half of `complete`.

**Files:**
- Create: `harness/telemetry.py`
- Test: `tests/test_telemetry.py`

**Interfaces:**
- Consumes: nothing. This module imports only `json` and `dataclasses`.
- Produces: `ToolCall(name: str, is_error: bool | None)`; `RunTelemetry(turns: int, tool_calls: tuple[ToolCall, ...], input_tokens: int, output_tokens: int, cache_read_tokens: int, cache_write_tokens: int, complete: bool)` with a `context_processed: int` property; `read_telemetry(pi_stdout: str) -> RunTelemetry`. Both dataclasses are `frozen=True`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_telemetry.py`:

```python
from pathlib import Path

from harness.telemetry import ToolCall, read_telemetry

FIXTURE = Path(__file__).parent / "fixtures" / "pi-run-0.82.0.jsonl"


def _real_run() -> str:
    return FIXTURE.read_text()


def test_counts_one_turn_per_turn_end_event():
    assert read_telemetry(_real_run()).turns == 6


def test_sums_token_usage_across_turn_end_events():
    # Also the double-count guard: `message_end` carries `message.usage`
    # too, on 6 of this stream's 12 message_end events. A reader that
    # summed both event types would report exactly twice these numbers.
    telemetry = read_telemetry(_real_run())
    assert telemetry.input_tokens == 7068
    assert telemetry.output_tokens == 933
    assert telemetry.cache_read_tokens == 6144
    assert telemetry.cache_write_tokens == 0


def test_context_processed_sums_input_and_both_cache_fields():
    assert read_telemetry(_real_run()).context_processed == 13212


def test_pairs_tool_starts_with_their_ends_in_start_order():
    assert read_telemetry(_real_run()).tool_calls == (
        ToolCall(name="bash", is_error=False),
        ToolCall(name="write", is_error=False),
        ToolCall(name="write", is_error=False),
        ToolCall(name="write", is_error=False),
        ToolCall(name="write", is_error=False),
    )


def test_a_healthy_run_is_complete():
    assert read_telemetry(_real_run()).complete is True
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run pytest tests/test_telemetry.py -v
```

Expected: 5 errors, `ModuleNotFoundError: No module named 'harness.telemetry'`.

- [ ] **Step 3: Write the implementation**

Create `harness/telemetry.py`:

```python
"""Structured measurements derived from one Pi run's captured stdout.

**A turn is one `turn_end` event.** This definition is load-bearing and
must not drift: any change to it invalidates comparison against every
number this instrument has produced. A prior effort counted assistant
messages in one lesson and a session-level field in another, producing 45
turns versus 6 for comparable work, and poisoned the trend it was
measuring.

**When `complete` is `False`, every count here is a lower bound.** A run
killed mid-flight loses the tokens of its unfinished turn entirely, and
leaves tool calls whose outcome is unknown rather than successful.

This is a derived, recomputable view and never load-bearing storage — but
only because checkpoints retain raw `pi_stdout`. Trimming stdout from
checkpoint records would make every telemetry number ever computed
unreproducible.
"""

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCall:
    name: str
    is_error: bool | None  # None = started but never finished


@dataclass(frozen=True)
class RunTelemetry:
    turns: int
    tool_calls: tuple[ToolCall, ...]
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    complete: bool  # the run finished normally; counts are lower bounds if False

    @property
    def context_processed(self) -> int:
        return self.input_tokens + self.cache_read_tokens + self.cache_write_tokens


def read_telemetry(pi_stdout: str) -> RunTelemetry:
    turns = 0
    input_tokens = 0
    output_tokens = 0
    cache_read_tokens = 0
    cache_write_tokens = 0
    started: dict[str, str] = {}  # toolCallId -> toolName, in start order
    ended: dict[str, bool | None] = {}  # toolCallId -> isError
    agent_ended = False

    for line in pi_stdout.splitlines():
        event = json.loads(line)
        match event.get("type"):
            case "turn_end":
                turns += 1
                # Usage is per-turn, not cumulative -- verified across all
                # 16 runs of the real batch, where per-turn input is
                # non-monotonic. Reading only the final event would
                # undercount badly.
                usage = event.get("message", {}).get("usage", {})
                input_tokens += usage.get("input", 0)
                output_tokens += usage.get("output", 0)
                cache_read_tokens += usage.get("cacheRead", 0)
                cache_write_tokens += usage.get("cacheWrite", 0)
            case "tool_execution_start":
                started[event["toolCallId"]] = event["toolName"]
            case "tool_execution_end":
                ended[event["toolCallId"]] = event.get("isError")
            case "agent_end":
                agent_ended = True

    tool_calls = tuple(
        ToolCall(name=name, is_error=ended.get(call_id))
        for call_id, name in started.items()
    )

    return RunTelemetry(
        turns=turns,
        tool_calls=tool_calls,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
        complete=agent_ended,
    )
```

Three things this deliberately does *not* yet do, each driven by a failing test in Task 2 rather than written on faith: skip malformed lines, fold `reasoning` into `output_tokens`, and require matched tool calls for `complete`. The fixture provides no evidence for any of them — all 123 lines parse, `reasoning` is 0 throughout, and all 5 tool calls match.

Note `started` is a plain `dict`, which preserves insertion order — that is what gives `tool_calls` its start order.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
uv run pytest tests/test_telemetry.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Run the full gates**

```bash
uv run pytest tests/ && uv run ruff check . && uv run pyrefly check
```

Expected: 78 passed, 1 skipped; ruff `All checks passed!`; pyrefly `0 errors`.

- [ ] **Step 6: Commit**

```bash
git add harness/telemetry.py tests/test_telemetry.py
git commit -m "feat(telemetry): read turns, tool calls, and tokens from a healthy pi run"
```

---

### Task 2: What the real fixture cannot reach

Three behaviors the captured stream has no instance of, each proven with a small synthetic string built inline. This is where the spec's non-vacuity requirement bites: an incomplete run must report `is_error is None` and `complete is False` *specifically*, because a reader that silently dropped unmatched starts would also "not raise" and would be wrong in exactly the way that matters.

**Files:**
- Modify: `harness/telemetry.py`
- Test: `tests/test_telemetry.py`

**Interfaces:**
- Consumes: `ToolCall`, `RunTelemetry`, `read_telemetry` from Task 1 — signatures unchanged.
- Produces: no new names. Behavior only.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_telemetry.py`:

```python
def test_a_malformed_final_line_is_skipped_not_raised():
    # A process killed mid-write leaves a partial final line, exactly as
    # harness/checkpoint.py already tolerates.
    stream = (
        '{"type": "turn_end", "message": {"usage": '
        '{"input": 10, "output": 2, "cacheRead": 0, "cacheWrite": 0, "reasoning": 0}}}\n'
        '{"type": "agent_end"}\n'
        '{"type": "turn_en'
    )
    telemetry = read_telemetry(stream)
    assert telemetry.turns == 1
    assert telemetry.input_tokens == 10


def test_a_tool_start_with_no_end_is_unknown_not_successful():
    # agent_end IS present here, so `complete is False` is driven purely
    # by the unmatched start -- not by a missing end-of-agent marker.
    stream = (
        '{"type": "tool_execution_start", "toolCallId": "call_1", "toolName": "bash"}\n'
        '{"type": "tool_execution_end", "toolCallId": "call_1", '
        '"toolName": "bash", "isError": false}\n'
        '{"type": "tool_execution_start", "toolCallId": "call_2", "toolName": "write"}\n'
        '{"type": "agent_end"}\n'
    )
    telemetry = read_telemetry(stream)
    assert telemetry.tool_calls == (
        ToolCall(name="bash", is_error=False),
        ToolCall(name="write", is_error=None),
    )
    assert telemetry.tool_calls[1].is_error is None
    assert telemetry.complete is False


def test_a_stream_truncated_before_any_turn_end_reports_zero_not_an_error():
    stream = (
        '{"type": "session", "version": "0.82.0"}\n'
        '{"type": "agent_start"}\n'
        '{"type": "turn_start"}\n'
        '{"type": "message_start", "message": {"role": "assistant"}}\n'
    )
    telemetry = read_telemetry(stream)
    assert telemetry.turns == 0
    assert telemetry.tool_calls == ()
    assert telemetry.input_tokens == 0
    assert telemetry.output_tokens == 0
    assert telemetry.cache_read_tokens == 0
    assert telemetry.cache_write_tokens == 0
    assert telemetry.context_processed == 0
    assert telemetry.complete is False


def test_reasoning_tokens_are_folded_into_output_tokens():
    # gemma-4-12B emits 0 reasoning tokens, so the real fixture cannot
    # prove this. The fold exists so a future reasoning-capable model's
    # generated tokens cannot vanish silently.
    stream = (
        '{"type": "turn_end", "message": {"usage": '
        '{"input": 10, "output": 5, "cacheRead": 0, "cacheWrite": 0, "reasoning": 7}}}\n'
        '{"type": "agent_end"}\n'
    )
    assert read_telemetry(stream).output_tokens == 12
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
uv run pytest tests/test_telemetry.py -v
```

Expected: 3 of the 4 new tests fail, for these distinct reasons —

- `test_a_malformed_final_line_is_skipped_not_raised` — `json.decoder.JSONDecodeError`.
- `test_a_tool_start_with_no_end_is_unknown_not_successful` — `assert True is False` on the `complete` line. The `is_error is None` assertion above it already passes; it is a pin on the spec's named non-vacuity trap, not a driver of new code, and should not be removed for that reason.
- `test_reasoning_tokens_are_folded_into_output_tokens` — `assert 5 == 12`.

`test_a_stream_truncated_before_any_turn_end_reports_zero_not_an_error` passes already: with no `agent_end`, `complete` is `False` under Task 1's implementation too. It stays as a regression pin on the zero-count path.

- [ ] **Step 3: Skip malformed lines**

In `harness/telemetry.py`, replace the bare parse inside the loop:

```python
        event = json.loads(line)
```

with:

```python
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            # A process killed mid-write leaves a partial final line.
            # Tolerated, as harness/checkpoint.py already tolerates one.
            continue
```

- [ ] **Step 4: Fold reasoning into output tokens**

In the `case "turn_end":` block, replace:

```python
                output_tokens += usage.get("output", 0)
```

with:

```python
                # Reasoning tokens are generated output. Folding them in
                # rather than giving them their own field means a future
                # reasoning-capable model's tokens cannot vanish
                # silently, and no assertion has to fire to prevent it.
                output_tokens += usage.get("output", 0) + usage.get("reasoning", 0)
```

- [ ] **Step 5: Require matched tool calls for `complete`**

Replace:

```python
        complete=agent_ended,
```

with:

```python
        complete=agent_ended and started.keys() <= ended.keys(),
```

`started.keys() <= ended.keys()` is a subset test: every started call has an end recorded. It is checked against `ended`'s keys rather than its values so that a matched call carrying no `isError` field still counts as complete, while an unmatched one never does.

- [ ] **Step 6: Run the tests to verify they pass**

```bash
uv run pytest tests/test_telemetry.py -v
```

Expected: 9 passed.

- [ ] **Step 7: Run the full gates**

```bash
uv run pytest tests/ && uv run ruff check . && uv run pyrefly check
```

Expected: 82 passed, 1 skipped; ruff `All checks passed!`; pyrefly `0 errors`.

- [ ] **Step 8: Commit**

```bash
git add harness/telemetry.py tests/test_telemetry.py
git commit -m "feat(telemetry): tolerate malformed lines and report incomplete runs honestly"
```

---

### Task 3: Cycle close — roadmap, concept budget, and docs wiring

**Files:**
- Modify: `ROADMAP.md`
- Modify: `docs/superpowers/index.md`

**Interfaces:**
- Consumes: the finished `harness/telemetry.py` from Tasks 1–2.
- Produces: nothing code depends on.

- [ ] **Step 1: Add the four concept-budget terms**

In `ROADMAP.md`, in the "Concept budget" table, append these four rows after the `process group` row (the last row of the table):

```markdown
| telemetry | structured measurements derived from a run's captured output (`harness/telemetry.py`); a recomputable view, never storage | phase 2 cycle 1 |
| turn | one `turn_end` event in Pi's JSON stream — borrowed from Pi's vocabulary, not coined. Pinned: any redefinition invalidates every number already produced | phase 2 cycle 1 |
| tool call | one tool Pi invoked during a run, correlated start-to-end by `toolCallId` — borrowed from Pi's vocabulary, not coined | phase 2 cycle 1 |
| context processed | `input + cacheRead + cacheWrite` — a cumulative *workload* measure, not a context-window size, and not latency or cost. Adopted from the prior effort's metrics report rather than invented, so its numbers stay comparable | phase 2 cycle 1 |
```

- [ ] **Step 2: Add the Phase 2 row to the phases table**

In `ROADMAP.md`, in the "Phases" table, append after the Phase 1 row:

```markdown
| 2 | Measure the cost of orchestration | Instrument a run, then test whether an orchestrator writing handoff packets costs more than doing the work itself | in progress |
```

- [ ] **Step 3: Add the Phase 2 cycle table**

In `ROADMAP.md`, immediately after the "Post-Phase 1 corrective cycles" table (after the cycle 18 row, before the "**Why this order.**" paragraph), insert:

```markdown
### Phase 2 feature cycles

| Cycle | Summary | Spec | Plan | State |
|-------|---------|------|------|-------|
| 1 | Telemetry reader — `harness/telemetry.py`'s `read_telemetry()` derives turns, tool calls, and token counts from the JSONL `RunResult.pi_stdout` already captures. A pure function over a string: `runner.py`, `checkpoint.py`, and the batch are untouched, and nothing consumes the result yet. Proven against a real captured pi 0.82.0 stream, because the schema drifts across pi versions — the pre-restructure reader's 0.81.1 beliefs (no usage in `--mode json`; `isError` a string) are both false in 0.82.0. Three cases real data cannot reach are proven with inline synthetic streams. | [spec](docs/superpowers/specs/2026-08-02-phase2-cycle1-telemetry-reader-design.md) | [plan](docs/superpowers/plans/2026-08-02-phase2-cycle1-telemetry-reader.md) | Done |
```

- [ ] **Step 4: Record why Phase 2 opens here**

In `ROADMAP.md`'s "Now" section, replace this paragraph:

```markdown
**Phase 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine.** One
run, hermetically graded, recorded to a checkpoint; then n=16 reproducing
~15/16. The engine's first job is to reproduce a number we already trust, not
to discover one — see `BRIEF.md` for why. Everything else waits.
```

with this pair of paragraphs, leaving the superseded-framing note that follows untouched:

```markdown
**Phase 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine.
Complete.** One run, hermetically graded, recorded to a checkpoint; then
n=16 reproducing ~15/16 — the supervised batch accepted 16/16. The engine's
first job was to reproduce a number we already trust, not to discover one —
see `BRIEF.md` for why.

**Phase 2 — Measure the cost of orchestration.** Phase 1 measured whether
generated code can be *trusted*; it says nothing about speed, cost, or
effort. The Backlog gated telemetry on "a suite author naming a claim they
need those measurements to support," and cycle 1 satisfies that gate rather
than waiving it. The claim: *getting an orchestrator to write handoff
packets for an implementer may consume more tokens than the orchestrator
simply doing the work itself.* Step 1 builds the instrument; step 2 brings
back a hello-world Pi extension teaching lifecycle events and
`appendEntry`; step 3 begins incremental orchestrator work, where the
instrument answers the claim.
```

- [ ] **Step 5: Update the Backlog telemetry entry**

In `ROADMAP.md`'s Backlog, replace the telemetry bullet:

```markdown
- Telemetry (Phase 2): aggregate model/session measurements only after a
  suite author has named a claim they need those measurements to support.
  Phase 1 records accept/reject evidence and complete Pi output, but does not
  infer token, tool, or context-window metrics from it.
```

with:

```markdown
- Telemetry — **gate satisfied; promoted to Phase 2 cycle 1.** The gate was
  "only after a suite author has named a claim they need those measurements
  to support," and the handoff-packet cost claim named one. What remains
  deferred is everything past the reader itself: wall time, cost,
  parent/child attribution, and any aggregation or report format. Each is
  listed with its reason and a path back in the cycle 1 spec's "Deliberate
  exclusions" table — that table is a record of decisions, not a backlog to
  work through.
```

- [ ] **Step 6: Add Phase 2 to the docs development record**

In `docs/superpowers/index.md`, insert a new section immediately before `## Withdrawn` (currently line 55):

```markdown
## Phase 2 — Measure the cost of orchestration

Phase 1 asked whether generated code can be trusted. Phase 2 asks what it
costs. Cycle 1 builds the instrument and wires it to nothing — the same
instrument-before-experiment order Phase 1 used when it built the entire
grading apparatus before a model ran once.

| # | Cycle | Spec | Plan |
|---|---|---|---|
| 1 | Telemetry reader | [spec](specs/2026-08-02-phase2-cycle1-telemetry-reader-design.md) | [plan](plans/2026-08-02-phase2-cycle1-telemetry-reader.md) |

```

- [ ] **Step 7: Wire both documents into the hidden toctrees**

This is required, not cosmetic: `.github/workflows` builds the site with `sphinx-build -W`, so a document in no toctree fails the Pages deploy on push to `main`. The committed spec is currently in no toctree and already breaks that build — Step 8 verifies the fix.

In `docs/superpowers/index.md`, in the Specs toctree, append after `specs/2026-08-01-post-phase1-pages-publication-design`:

```
specs/2026-08-02-phase2-cycle1-telemetry-reader-design
```

In the Plans toctree, append after `plans/2026-08-01-post-phase1-pages-publication`:

```
plans/2026-08-02-phase2-cycle1-telemetry-reader
```

- [ ] **Step 8: Verify the strict docs build is warning-free**

```bash
uv run --group docs sphinx-build -W -b html docs docs/_build/html
```

Expected: `build succeeded.` — no `toc.not_included` warning. Before this task it reported `1 warning (with warnings treated as errors)` for the unwired spec.

- [ ] **Step 9: Run the full gates one last time**

```bash
uv run pytest tests/ && uv run ruff check . && uv run pyrefly check
```

Expected: 82 passed, 1 skipped; ruff `All checks passed!`; pyrefly `0 errors`.

- [ ] **Step 10: Commit**

```bash
git add ROADMAP.md docs/superpowers/index.md
git commit -m "docs(phase2-cycle1): close the telemetry reader cycle"
```

---

## A note on the bare `pytest` gate

`uv run pytest` without a path argument currently fails on this checkout with 29 collection errors — every one of them from `.worktrees/oracle-repair/`, the git-ignored linked worktree holding the pre-restructure project. `pyproject.toml`'s `norecursedirs` excludes `examples/agentclinic` and `docs/_build` but not `.worktrees`, and cycle 17 deliberately kept that worktree as local state.

This is pre-existing and unrelated to this cycle: the committed suite is green (`uv run pytest tests/` → 73 passed, 1 skipped before this plan's tasks). Every gate command in this plan therefore says `uv run pytest tests/`. Widening `norecursedirs` would fix the bare command in one line, but that is the owner's call and outside this cycle's scope — flagged, not taken.

**Resolved after the fact, by the owner's decision.** The owner took the one-line fix once it was flagged: `.worktrees` joined `examples/agentclinic` and `docs/_build` in `norecursedirs`. Bare `uv run pytest` now collects the same set as `uv run pytest tests/` — 82 passed, 1 skipped — so the gate commands in this plan and the one in `BRIEF.md` no longer disagree. The `tests/`-qualified commands above are left as written, since that is what was actually run at each step.
