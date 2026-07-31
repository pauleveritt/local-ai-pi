# Checkpoint Recording Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `append_checkpoint`/`load_checkpoint`, a pair of standalone
functions that persist completed `RunResult`s to a JSONL file, one line
per run, tolerant of a truncated final line.

**Architecture:** One new module, `harness/checkpoint.py`, with two
functions and no state of its own — every call takes an explicit `path`.
`RunResult`/`GradeResult` are frozen dataclasses of only
`str`/`int`/`bool`/`tuple` fields, so `dataclasses.asdict()` plus
`json.dumps` on write, and `json.loads` plus keyword-unpacking on read,
round-trip them exactly (with `GradeResult.refused_config` cast back from
`list` to `tuple`).

**Tech Stack:** Python 3.14 stdlib (`json`, `dataclasses`, `pathlib`).
pytest 8.3.4.

## Global Constraints

- `append_checkpoint(path: Path, result: RunResult) -> None` and
  `load_checkpoint(path: Path) -> list[RunResult]` are the exact
  signatures — `path` has no default on either function.
- No batch loop, no telemetry fields, no configurable format. This cycle
  is exactly these two functions.
- Truncation tolerance is scoped precisely: only the **last** line of the
  file may fail to parse without raising. Any other line failing to
  parse is a raise, not a silent drop.

---

## File Structure

```
harness/
  checkpoint.py          # CREATE: append_checkpoint(), load_checkpoint()
tests/
  test_checkpoint.py      # CREATE: round-trip, order, and truncation tests
```

---

### Task 1: `append_checkpoint` / `load_checkpoint` — round-trip

**Files:**
- Create: `harness/checkpoint.py`
- Create: `tests/test_checkpoint.py`

**Interfaces:**
- Consumes: `harness.runner.RunResult` (fields: `diff: str, grade:
  GradeResult, pi_stdout: str, pi_stderr: str`); `harness.grading.GradeResult`
  (fields: `accepted: bool, tests_executed: int, tests_expected: int,
  returncode: int | None, stdout: str, stderr: str, refused_config: tuple[str, ...]`).
- Produces: `harness.checkpoint.append_checkpoint(path: Path, result:
  RunResult) -> None`; `harness.checkpoint.load_checkpoint(path: Path)
  -> list[RunResult]`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_checkpoint.py`:

```python
from pathlib import Path

from harness.checkpoint import append_checkpoint, load_checkpoint
from harness.grading import GradeResult
from harness.runner import RunResult


def _sample_result(accepted: bool = True) -> RunResult:
    return RunResult(
        diff="diff --git a/app.py b/app.py\n+x = 1\n",
        grade=GradeResult(
            accepted=accepted,
            tests_executed=4,
            tests_expected=4,
            returncode=0,
            stdout="4 passed\n",
            stderr="",
            refused_config=(),
        ),
        pi_stdout="I created app.py.\n",
        pi_stderr="",
    )


def test_append_then_load_round_trips_a_single_record(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    result = _sample_result()

    append_checkpoint(path, result)
    loaded = load_checkpoint(path)

    assert loaded == [result]


def test_load_checkpoint_returns_records_in_append_order(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    first = _sample_result(accepted=True)
    second = _sample_result(accepted=False)

    append_checkpoint(path, first)
    append_checkpoint(path, second)
    loaded = load_checkpoint(path)

    assert loaded == [first, second]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_checkpoint.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.checkpoint'`

- [ ] **Step 3: Write the implementation**

Create `harness/checkpoint.py`:

```python
import json
from dataclasses import asdict
from pathlib import Path

from harness.grading import GradeResult
from harness.runner import RunResult


def append_checkpoint(path: Path, result: RunResult) -> None:
    with path.open("a") as f:
        f.write(json.dumps(asdict(result)) + "\n")


def load_checkpoint(path: Path) -> list[RunResult]:
    if not path.is_file():
        return []

    results = []
    for line in path.read_text().splitlines():
        data = json.loads(line)
        grade_data = data["grade"]
        grade_data["refused_config"] = tuple(grade_data["refused_config"])
        results.append(
            RunResult(
                diff=data["diff"],
                grade=GradeResult(**grade_data),
                pi_stdout=data["pi_stdout"],
                pi_stderr=data["pi_stderr"],
            )
        )
    return results
```

This version has no truncation handling yet — a corrupted line of any
kind, including the last, raises `json.JSONDecodeError` uncaught. That's
intentional: Task 2 adds truncation tolerance via its own failing test,
against this as the starting point.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_checkpoint.py -v`
Expected: PASS, 2 passed

- [ ] **Step 5: Commit**

```bash
git add harness/checkpoint.py tests/test_checkpoint.py
git commit -m "feat(checkpoint): append_checkpoint/load_checkpoint round-trip a RunResult"
```

---

### Task 2: Truncation tolerance, precisely scoped

**Files:**
- Modify: `harness/checkpoint.py`
- Modify: `tests/test_checkpoint.py`

**Interfaces:**
- Consumes: `_sample_result()` from Task 1 — no changes to its signature.
- Produces: no new public names; `load_checkpoint`'s behavior on
  malformed input changes.

- [ ] **Step 1: Write the failing test — tolerate a truncated final line**

Add to `tests/test_checkpoint.py`:

```python
def test_load_checkpoint_drops_a_truncated_final_line(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    complete = _sample_result()
    append_checkpoint(path, complete)

    with path.open("a") as f:
        f.write('{"diff": "partial, process died mid-writ')

    loaded = load_checkpoint(path)

    assert loaded == [complete]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_checkpoint.py::test_load_checkpoint_drops_a_truncated_final_line -v`
Expected: FAIL — `json.decoder.JSONDecodeError` propagates uncaught, from
Task 1's implementation having no try/except around `json.loads`.

- [ ] **Step 3: Write the non-vacuity control test, also failing**

This is the control that proves the fix is scoped to *only* the last
line, not "swallow any bad line." First, update the imports at the top
of `tests/test_checkpoint.py` to:

```python
import json

import pytest

from harness.checkpoint import append_checkpoint, load_checkpoint
from harness.grading import GradeResult
from harness.runner import RunResult
```

Then add to `tests/test_checkpoint.py`:

```python
def test_load_checkpoint_raises_on_a_corrupted_non_final_line(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    path.write_text(
        '{"diff": "corrupted, not the last lin\n'
        + json.dumps(
            {
                "diff": _sample_result().diff,
                "grade": {
                    "accepted": True,
                    "tests_executed": 4,
                    "tests_expected": 4,
                    "returncode": 0,
                    "stdout": "4 passed\n",
                    "stderr": "",
                    "refused_config": [],
                },
                "pi_stdout": _sample_result().pi_stdout,
                "pi_stderr": "",
            }
        )
        + "\n"
    )

    with pytest.raises(json.JSONDecodeError):
        load_checkpoint(path)
```

Run: `uv run pytest tests/test_checkpoint.py::test_load_checkpoint_raises_on_a_corrupted_non_final_line -v`
Expected: PASS already — Task 1's implementation has no truncation
handling at all, so it already raises on any bad line, including this
one. This step exists to pin that expectation with an explicit test
*before* Task 2's Step 4 changes the code, so Task 2's fix can't
accidentally start swallowing this case too.

- [ ] **Step 4: Implement truncation tolerance for the last line only**

Replace `load_checkpoint` in `harness/checkpoint.py`:

```python
def load_checkpoint(path: Path) -> list[RunResult]:
    if not path.is_file():
        return []

    lines = path.read_text().splitlines()
    results = []
    for i, line in enumerate(lines):
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            if i == len(lines) - 1:
                break
            raise
        grade_data = data["grade"]
        grade_data["refused_config"] = tuple(grade_data["refused_config"])
        results.append(
            RunResult(
                diff=data["diff"],
                grade=GradeResult(**grade_data),
                pi_stdout=data["pi_stdout"],
                pi_stderr=data["pi_stderr"],
            )
        )
    return results
```

- [ ] **Step 5: Run both new tests to verify they pass**

Run: `uv run pytest tests/test_checkpoint.py -v`
Expected: PASS, 4 passed (all tests in the file: the two from Task 1,
plus the two added in this task).

- [ ] **Step 6: Run the whole suite to confirm no regressions**

Run: `uv run pytest -q`
Expected: all previously-passing tests still pass, plus 4 new ones —
`test_runner.py`'s live-model test runs for real or skips cleanly
depending on the machine, as in every prior cycle.

- [ ] **Step 7: Commit**

```bash
git add harness/checkpoint.py tests/test_checkpoint.py
git commit -m "feat(checkpoint): tolerate a truncated final line, raise on any other corruption"
```

---

## Plan Self-Review Notes

- **Spec coverage:** module location and function signatures — Task 1
  Step 3. JSONL format, `asdict`/keyword-unpacking round-trip, tuple
  cast on `refused_config` — Task 1 Step 3. Resume-by-position semantics
  (no run-index field) — implicit in the round-trip and ordering tests,
  Task 1 Step 1; nothing in either task adds an index field. Truncation
  tolerance scoped to the last line only, with its non-vacuity control —
  Task 2. Non-goals (batch loop, telemetry, configurability) — untouched
  by both tasks.
- **Type consistency:** `append_checkpoint(path: Path, result: RunResult)
  -> None` and `load_checkpoint(path: Path) -> list[RunResult]` match the
  spec's Interface section exactly across both tasks; `RunResult` and
  `GradeResult` field names used in `_sample_result()` and the
  implementation match `harness/runner.py` and `harness/grading.py`'s
  actual dataclasses (verified against both files directly while writing
  this plan).
- **No placeholders:** every step shows complete, runnable code and an
  exact command with an expected result.
