# Phase 1 Cycle 3: Verdict from a Hook-Written Results File Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Grade a suite run against a workspace by reading a file a pytest
plugin's own hooks write, not by trusting pytest's exit code, and return a
typed `GradeResult` verdict.

**Architecture:** Two new modules. `harness/grading_plugin.py` is a pytest
plugin that appends one line per real test outcome, plus a completion
marker, to a results file named by an environment variable. `harness/grading.py`
exports the `GradeResult` dataclass, a pure `_verdict` function that turns
results-file text plus an expected count and return code into a
`GradeResult` (testable with hand-crafted text, no subprocess needed), and
`grade()`, the orchestrator that copies the suite into a workspace, runs
pytest there with the plugin loaded, and calls `_verdict` on the outcome.
One test file, `tests/test_grading.py`, built up in three TDD increments
matching these three pieces.

**Tech Stack:** Python 3.14, pytest 8.3.4, standard library only
(`ast`/`os`/`subprocess`/`tempfile`/`dataclasses`).

## Global Constraints

- Python `>=3.14,<3.15` (from `pyproject.toml`).
- `pytest==8.3.4`, `fastapi[standard]==0.115.10`, `turbohtml==1.5.0` are
  the pinned dependencies already declared in `pyproject.toml` — do not
  add new dependencies for this cycle.
- `GradeResult` is a frozen dataclass with fields `accepted: bool`,
  `tests_executed: int`, `tests_expected: int`, `returncode: int`,
  `stdout: str`, `stderr: str`. The boolean field is named `accepted`, not
  `passed` — the grader's own accept/reject vocabulary, not pytest's.
- `grade(workspace: Path, suite: Path, timeout: int = 30) -> GradeResult`
  — `timeout` defaults to `30`.
- Accept iff: the `__DONE__` marker is present in the results file, AND
  `tests_executed == tests_expected`, AND `tests_expected > 0`, AND every
  recorded outcome is `passed`, AND the process return code is `0`. The
  return code is a one-way veto (nonzero always rejects; zero alone never
  accepts on its own).
- No separate grader directory, no pinned `pyproject.toml` copy, no source
  allowlist, no refusal of model-written config — all deferred to cycle 5.
  `grade()` runs pytest directly inside the workspace cycle 2's
  `prepare_workspace` already provisions.
- Invoke pytest as `[sys.executable, "-m", "pytest", ...]`, matching the
  precedent already established in `tests/test_workspace.py` — not
  `uv run pytest`.
- Single test file for this cycle: `tests/test_grading.py`.
- No changes to `examples/agentclinic/phase-1/{reference,broken,acceptance}`
  or to `harness/workspace.py` — all are read-only inputs here.

---

### Task 1: `harness/grading_plugin.py` — the pytest hook plugin

**Files:**
- Create: `harness/grading_plugin.py`
- Test: `tests/test_grading.py` (new file)

**Interfaces:**
- Produces: `RESULTS_ENV_VAR: str` (the environment variable name whose
  value is the results-file path), `DONE_SENTINEL: str` (the completion
  marker line, without its trailing newline), and two pytest hook
  functions, `pytest_runtest_logreport(report)` and
  `pytest_sessionfinish(session, exitstatus)`, registered as a pytest
  plugin when loaded via `-p harness.grading_plugin`. Task 2 imports
  `DONE_SENTINEL`; Task 3 imports both `DONE_SENTINEL` and
  `RESULTS_ENV_VAR`, and loads the module as a pytest plugin by name.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_grading.py
from types import SimpleNamespace

from harness.grading_plugin import (
    DONE_SENTINEL,
    RESULTS_ENV_VAR,
    pytest_runtest_logreport,
    pytest_sessionfinish,
)


def test_plugin_appends_outcome_line_on_call_phase(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    report = SimpleNamespace(when="call", outcome="passed", nodeid="test_call.py::test_alpha")
    pytest_runtest_logreport(report)

    assert results.read_text() == "test_call.py::test_alpha\tpassed\n"


def test_plugin_records_a_failed_call_phase(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    report = SimpleNamespace(when="call", outcome="failed", nodeid="test_call.py::test_beta")
    pytest_runtest_logreport(report)

    assert results.read_text() == "test_call.py::test_beta\tfailed\n"


def test_plugin_ignores_successful_setup_and_teardown(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    setup_report = SimpleNamespace(when="setup", outcome="passed", nodeid="test_setup_ok.py::test_gamma")
    teardown_report = SimpleNamespace(when="teardown", outcome="passed", nodeid="test_setup_ok.py::test_gamma")
    pytest_runtest_logreport(setup_report)
    pytest_runtest_logreport(teardown_report)

    assert not results.exists()


def test_plugin_records_a_setup_failure(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    report = SimpleNamespace(when="setup", outcome="failed", nodeid="test_setup_fail.py::test_delta")
    pytest_runtest_logreport(report)

    assert results.read_text() == "test_setup_fail.py::test_delta\tfailed\n"


def test_plugin_appends_done_sentinel_on_session_finish(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    pytest_sessionfinish(session=None, exitstatus=0)

    assert results.read_text() == f"{DONE_SENTINEL}\n"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_grading.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness.grading_plugin'`

- [ ] **Step 3: Write the plugin**

```python
# harness/grading_plugin.py
"""Pytest plugin: records verdict-relevant test outcomes via pytest's own
runtest hooks, and a completion marker, to a results file whose path is
given by an environment variable.

Reads real per-test hook events -- which only fire when pytest's own
runner actually executes a test -- rather than trusting captured
stdout/stderr text, which a model-imported module sharing this process
could write into directly.
"""
import os

RESULTS_ENV_VAR = "SATYRN_GRADE_RESULTS_PATH"
DONE_SENTINEL = "__DONE__"

_outcomes: dict[str, str] = {}


def pytest_runtest_logreport(report):
    if report.when == "call":
        _outcomes[report.nodeid] = report.outcome
    elif report.when in ("setup", "teardown") and report.outcome in ("failed", "error"):
        _outcomes.setdefault(report.nodeid, report.outcome)
    else:
        return
    _append(f"{report.nodeid}\t{_outcomes[report.nodeid]}\n")


def pytest_sessionfinish(session, exitstatus):
    _append(f"{DONE_SENTINEL}\n")


def _append(line: str) -> None:
    path = os.environ[RESULTS_ENV_VAR]
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, line.encode())
        os.fsync(fd)
    finally:
        os.close(fd)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_grading.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add harness/grading_plugin.py tests/test_grading.py
git commit -m "feat(grading): pytest plugin writes outcomes and a completion marker to a results file"
```

---

### Task 2: `GradeResult` and the pure verdict function

**Files:**
- Create: `harness/grading.py`
- Modify: `tests/test_grading.py`

**Interfaces:**
- Consumes: `DONE_SENTINEL` from `harness.grading_plugin` (Task 1).
- Produces: `GradeResult` (frozen dataclass: `accepted: bool`,
  `tests_executed: int`, `tests_expected: int`, `returncode: int`,
  `stdout: str`, `stderr: str`) and
  `_verdict(results_text: str, tests_expected: int, returncode: int, stdout: str, stderr: str) -> GradeResult`.
  Task 3 imports both `GradeResult` (as the return type of `grade()`) and
  calls `_verdict` directly.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_grading.py`:

```python
from harness.grading import _verdict


def test_verdict_accepts_when_all_conjuncts_hold():
    results_text = (
        "test_acceptance.py::test_a\tpassed\n"
        "test_acceptance.py::test_b\tpassed\n"
        "test_acceptance.py::test_c\tpassed\n"
        "test_acceptance.py::test_d\tpassed\n"
        "__DONE__\n"
    )

    result = _verdict(results_text, tests_expected=4, returncode=0, stdout="", stderr="")

    assert result.accepted is True
    assert result.tests_executed == 4
    assert result.tests_expected == 4


def test_verdict_rejects_when_done_sentinel_missing():
    results_text = (
        "test_acceptance.py::test_a\tpassed\n"
        "test_acceptance.py::test_b\tpassed\n"
        "test_acceptance.py::test_c\tpassed\n"
        "test_acceptance.py::test_d\tpassed\n"
    )

    result = _verdict(results_text, tests_expected=4, returncode=0, stdout="", stderr="")

    assert result.accepted is False


def test_verdict_rejects_a_partial_run():
    results_text = (
        "test_acceptance.py::test_a\tpassed\n"
        "test_acceptance.py::test_b\tpassed\n"
        "__DONE__\n"
    )

    result = _verdict(results_text, tests_expected=4, returncode=0, stdout="", stderr="")

    assert result.accepted is False
    assert result.tests_executed == 2
    assert result.tests_expected == 4


def test_verdict_rejects_when_an_outcome_failed():
    results_text = (
        "test_acceptance.py::test_a\tpassed\n"
        "test_acceptance.py::test_b\tfailed\n"
        "test_acceptance.py::test_c\tpassed\n"
        "test_acceptance.py::test_d\tpassed\n"
        "__DONE__\n"
    )

    result = _verdict(results_text, tests_expected=4, returncode=0, stdout="", stderr="")

    assert result.accepted is False


def test_verdict_rejects_on_nonzero_returncode_even_if_everything_else_passed():
    results_text = (
        "test_acceptance.py::test_a\tpassed\n"
        "test_acceptance.py::test_b\tpassed\n"
        "test_acceptance.py::test_c\tpassed\n"
        "test_acceptance.py::test_d\tpassed\n"
        "__DONE__\n"
    )

    result = _verdict(results_text, tests_expected=4, returncode=1, stdout="", stderr="")

    assert result.accepted is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_grading.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness.grading'`

- [ ] **Step 3: Write `GradeResult` and `_verdict`**

```python
# harness/grading.py
from dataclasses import dataclass

from harness.grading_plugin import DONE_SENTINEL


@dataclass(frozen=True)
class GradeResult:
    accepted: bool
    tests_executed: int
    tests_expected: int
    returncode: int
    stdout: str
    stderr: str


def _verdict(
    results_text: str, tests_expected: int, returncode: int, stdout: str, stderr: str
) -> GradeResult:
    lines = results_text.splitlines()
    done = DONE_SENTINEL in lines

    outcomes: dict[str, str] = {}
    for line in lines:
        if "\t" not in line:
            continue
        nodeid, outcome = line.split("\t", 1)
        outcomes[nodeid] = outcome
    tests_executed = len(outcomes)

    accepted = (
        done
        and tests_executed == tests_expected
        and tests_expected > 0
        and all(outcome == "passed" for outcome in outcomes.values())
        and returncode == 0
    )

    return GradeResult(
        accepted=accepted,
        tests_executed=tests_executed,
        tests_expected=tests_expected,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_grading.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add harness/grading.py tests/test_grading.py
git commit -m "feat(grading): GradeResult and a pure verdict function over results-file text"
```

---

### Task 3: `grade()` — orchestrate a real pytest run against a workspace

**Files:**
- Modify: `harness/grading.py`
- Modify: `tests/test_grading.py`

**Interfaces:**
- Consumes: `prepare_workspace(source_dir: Path) -> Iterator[Path]` from
  `harness.workspace` (cycle 2); `RESULTS_ENV_VAR` from
  `harness.grading_plugin` (Task 1); `GradeResult` and `_verdict` from
  Task 2, in the same module.
- Produces: `grade(workspace: Path, suite: Path, timeout: int = 30) -> GradeResult`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_grading.py`:

```python
from pathlib import Path

from harness.grading import grade
from harness.workspace import prepare_workspace

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_1 = REPO_ROOT / "examples" / "agentclinic" / "phase-1"


def test_grade_accepts_the_reference_solution():
    with prepare_workspace(PHASE_1 / "reference") as workspace:
        result = grade(workspace, PHASE_1 / "acceptance" / "test_acceptance.py")

    assert result.accepted is True
    assert result.tests_executed == result.tests_expected == 4


def test_grade_rejects_the_broken_solution():
    with prepare_workspace(PHASE_1 / "broken") as workspace:
        result = grade(workspace, PHASE_1 / "acceptance" / "test_acceptance.py")

    assert result.accepted is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_grading.py -v`
Expected: FAIL with `ImportError: cannot import name 'grade' from 'harness.grading'`

- [ ] **Step 3: Write `grade()`**

Append to `harness/grading.py` (and add the new imports at the top):

```python
import ast
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from harness.grading_plugin import DONE_SENTINEL, RESULTS_ENV_VAR
```

(`DONE_SENTINEL` import already exists from Task 2 — extend that same
import line with `RESULTS_ENV_VAR` rather than duplicating it.)

```python
def grade(workspace: Path, suite: Path, timeout: int = 30) -> GradeResult:
    """Copy suite into workspace, run pytest there with the grading
    plugin loaded, and return the verdict read from the results file the
    plugin's hooks wrote."""
    shutil.copy2(suite, workspace / suite.name)
    tests_expected = _test_count(suite)

    results_fd, results_path = tempfile.mkstemp(
        prefix="satyrn-grade-results-", suffix=".txt"
    )
    os.close(results_fd)
    results_path = Path(results_path)
    try:
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env[RESULTS_ENV_VAR] = str(results_path)
        env["PYTHONPATH"] = str(repo_root)

        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "harness.grading_plugin"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        results_text = results_path.read_text() if results_path.is_file() else ""
        return _verdict(
            results_text,
            tests_expected=tests_expected,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    finally:
        results_path.unlink(missing_ok=True)


def _test_count(suite: Path) -> int:
    tree = ast.parse(suite.read_text(), filename=str(suite))
    return sum(
        isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        for node in tree.body
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_grading.py -v`
Expected: 12 passed

- [ ] **Step 5: Run the full test suite**

Run: `uv run pytest -q`
Expected: 18 passed (6 pre-existing + 12 new)

- [ ] **Step 6: Commit**

```bash
git add harness/grading.py tests/test_grading.py
git commit -m "feat(grading): grade() runs pytest against a workspace and returns a verdict"
```
