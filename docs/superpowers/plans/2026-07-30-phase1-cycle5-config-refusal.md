# Phase 1 Cycle 5: Refusal of Model-Written Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the grader refuse to certify a run whose workspace contains
model-written configuration, before that configuration can execute.

**Architecture:** Two increments in `harness/grading.py`. First a pure
detector, `_refused_config(workspace) -> tuple[str, ...]`, testable with
hand-built directories and no subprocess. Then `GradeResult` gains
`refused_config` and a nullable `returncode`, and `grade()` short-circuits
on a non-empty detection before copying the suite in or launching pytest.
Tests land in a new `tests/test_config_refusal.py`, reusing cycle 4's
attack helpers.

**Tech Stack:** Python 3.14, pytest 8.3.4, standard library only
(`pathlib`, `dataclasses`).

## Global Constraints

- Python `>=3.14,<3.15` (from `pyproject.toml`).
- `pytest==8.3.4`, `fastapi[standard]==0.115.10`, `turbohtml==1.5.0` are
  the pinned dependencies already declared in `pyproject.toml` — do not
  add new dependencies for this cycle.
- The six refused filenames, exactly: `pyproject.toml`, `pytest.ini`,
  `tox.ini`, `setup.cfg`, `conftest.py`, `sitecustomize.py`.
- Matching is root-level for all six, plus a recursive sweep for
  `conftest.py` **only**. Do not sweep the others recursively — a nested
  `pytest.ini` or `sitecustomize.py` is inert, and refusing it would
  refuse a file that cannot affect the run.
- Refusal **rejects**: `accepted` is `False` whenever any config is found,
  regardless of test outcomes. It does not neutralize, delete, or override
  the config and grade anyway.
- Refusal happens **before** the suite is copied in and before pytest
  launches. This is a security property: `sitecustomize.py` executes at
  interpreter startup and `conftest.py` at collection, so running anyway
  would execute the very files that triggered refusal.
- `returncode` becomes `int | None`. `None` means no process ran. Do not
  substitute `0` — that is indistinguishable from a genuine clean exit.
- **No existing test may be modified.** `GradeResult` has exactly one
  construction site (`_verdict`); no test builds one directly. If an
  existing test needs editing, stop and report — it signals the change is
  larger than this spec describes.
- No changes to `harness/workspace.py`, `harness/grading_plugin.py`,
  cycle 1's fixtures, or the acceptance suite.

---

### Task 1: `_refused_config` — the pure detector

**Files:**
- Modify: `harness/grading.py`
- Create: `tests/test_config_refusal.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `_REFUSED_CONFIG: tuple[str, ...]` (the six filenames) and
  `_refused_config(workspace: Path) -> tuple[str, ...]`, returning sorted
  workspace-relative paths of config files found. Task 2 calls it from
  `grade()`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_config_refusal.py
"""Refusal of model-written config: the grader declining to certify a run
at all, as distinct from rejecting a solution that failed the suite."""
from pathlib import Path

from harness.grading import _refused_config


def test_refused_config_finds_a_root_level_pytest_ini(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n")
    (tmp_path / "pytest.ini").write_text("[pytest]\n")

    assert _refused_config(tmp_path) == ("pytest.ini",)


def test_refused_config_finds_a_nested_conftest(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n")
    nested = tmp_path / "sub"
    nested.mkdir()
    (nested / "conftest.py").write_text("")

    assert _refused_config(tmp_path) == ("sub/conftest.py",)


def test_refused_config_ignores_a_nested_pytest_ini(tmp_path):
    """A nested pytest.ini is inert -- pytest reads ini files at the
    rootdir -- so refusing it would refuse a file that cannot act."""
    (tmp_path / "app.py").write_text("x = 1\n")
    nested = tmp_path / "sub"
    nested.mkdir()
    (nested / "pytest.ini").write_text("[pytest]\n")

    assert _refused_config(tmp_path) == ()


def test_refused_config_is_empty_for_a_clean_workspace(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n")

    assert _refused_config(tmp_path) == ()


def test_refused_config_finds_every_root_level_name(tmp_path):
    for name in (
        "pyproject.toml", "pytest.ini", "tox.ini",
        "setup.cfg", "conftest.py", "sitecustomize.py",
    ):
        (tmp_path / name).write_text("")

    assert _refused_config(tmp_path) == (
        "conftest.py", "pyproject.toml", "pytest.ini",
        "setup.cfg", "sitecustomize.py", "tox.ini",
    )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_config_refusal.py -v`
Expected: FAIL with `ImportError: cannot import name '_refused_config' from 'harness.grading'`

- [ ] **Step 3: Add the constant and the detector**

In `harness/grading.py`, add the constant immediately after the
`from harness.grading_plugin import ...` line:

```python
_REFUSED_CONFIG = (
    "pyproject.toml",
    "pytest.ini",
    "tox.ini",
    "setup.cfg",
    "conftest.py",
    "sitecustomize.py",
)
```

Then add this function at the end of the module:

```python
def _refused_config(workspace: Path) -> tuple[str, ...]:
    """Model-written config present in the workspace, as sorted
    workspace-relative paths.

    Root-level for all six names, plus a recursive sweep for conftest.py
    only: a nested conftest.py affects collection in its own subtree,
    while a nested pytest.ini or sitecustomize.py is inert -- pytest reads
    ini files at the rootdir, and sitecustomize is imported from sys.path.
    """
    found = {name for name in _REFUSED_CONFIG if (workspace / name).is_file()}
    found.update(
        str(path.relative_to(workspace))
        for path in workspace.rglob("conftest.py")
        if path.is_file()
    )
    return tuple(sorted(found))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_config_refusal.py -v`
Expected: 5 passed

- [ ] **Step 5: Confirm nothing else broke**

Run: `uv run pytest -q`
Expected: 26 passed (21 pre-existing + 5 new)

- [ ] **Step 6: Commit**

```bash
git add harness/grading.py tests/test_config_refusal.py
git commit -m "feat(grading): detect model-written config in a workspace"
```

---

### Task 2: Refuse before running

**Files:**
- Modify: `harness/grading.py`
- Modify: `tests/test_config_refusal.py`

**Interfaces:**
- Consumes: `_refused_config(workspace: Path) -> tuple[str, ...]` from
  Task 1; `prepare_workspace(source_dir: Path) -> Iterator[Path]` from
  `harness.workspace`; `_attack_with_collect_only(tmp_path: Path) -> Path`
  and `_attack_with_exit_at_import(tmp_path: Path) -> Path` from
  `tests/test_subversion.py` (cycle 4).
- Produces: `GradeResult` carrying `refused_config: tuple[str, ...]` with
  `returncode: int | None`; `grade()` short-circuiting on refusal.

**Why three of these four tests are controls.** Cycle 3's verdict already
rejects the `--collect-only` attack on the count mismatch, so asserting
`accepted is False` proves nothing about refusal. `returncode is None` is
the load-bearing assertion — it is the only observable proving pytest
never ran. The two control tests prove the detector is neither
always-populated nor blanket.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_config_refusal.py`:

```python
from harness.grading import grade
from harness.workspace import prepare_workspace
from tests.test_subversion import (
    _attack_with_collect_only,
    _attack_with_exit_at_import,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_1 = REPO_ROOT / "examples" / "agentclinic" / "phase-1"
SUITE = PHASE_1 / "acceptance" / "test_acceptance.py"


def test_grade_refuses_a_workspace_carrying_config_without_running_pytest(tmp_path):
    """The returncode is the load-bearing assertion: None proves no
    process ran, which is the entire point of refusing early. `accepted`
    proves nothing here -- cycle 3 already rejects this attack."""
    with prepare_workspace(_attack_with_collect_only(tmp_path)) as workspace:
        result = grade(workspace, SUITE)

    assert result.refused_config == ("pytest.ini",)
    assert result.returncode is None
    assert result.accepted is False


def test_grade_does_not_refuse_the_clean_reference_solution():
    """Control: proves refused_config is not simply always populated."""
    with prepare_workspace(PHASE_1 / "reference") as workspace:
        result = grade(workspace, SUITE)

    assert result.refused_config == ()
    assert result.accepted is True


def test_grade_does_not_refuse_an_attack_that_writes_no_config(tmp_path):
    """Control: proves refusal is specific, not blanket. This attack
    carries no config file, so it must still be caught by cycle 3's
    completion-marker logic rather than by refusal."""
    with prepare_workspace(_attack_with_exit_at_import(tmp_path)) as workspace:
        result = grade(workspace, SUITE)

    assert result.refused_config == ()
    assert result.returncode == 0
    assert result.accepted is False


def test_grade_refuses_before_copying_the_suite_into_the_workspace(tmp_path):
    """Refusal precedes every side effect, not just the subprocess."""
    source = _attack_with_collect_only(tmp_path)
    with prepare_workspace(source) as workspace:
        grade(workspace, SUITE)

        assert not (workspace / SUITE.name).exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_config_refusal.py -v`
Expected: the three tests asserting on `refused_config` FAIL with
`AttributeError: 'GradeResult' object has no attribute 'refused_config'`,
and `test_grade_refuses_before_copying_the_suite_into_the_workspace` FAILS
with a plain `AssertionError` — it never touches the new field, and today
`grade()` copies the suite in unconditionally.

- [ ] **Step 3: Extend `GradeResult`**

In `harness/grading.py`, change the dataclass to:

```python
@dataclass(frozen=True)
class GradeResult:
    accepted: bool
    tests_executed: int
    tests_expected: int
    returncode: int | None
    stdout: str
    stderr: str
    refused_config: tuple[str, ...]
```

- [ ] **Step 4: Pass the empty tuple from `_verdict`**

`_verdict` is only ever reached when nothing was refused, so the empty
tuple there is a fact rather than a default. In `_verdict`'s return
statement, add the final field:

```python
    return GradeResult(
        accepted=accepted,
        tests_executed=tests_executed,
        tests_expected=tests_expected,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        refused_config=(),
    )
```

- [ ] **Step 5: Short-circuit in `grade()`**

In `harness/grading.py`, replace the first two lines of `grade()`'s body
(currently `shutil.copy2(...)` followed by `tests_expected = _test_count(suite)`)
so the refusal check runs first and nothing else happens on refusal:

```python
    tests_expected = _test_count(suite)
    refused = _refused_config(workspace)
    if refused:
        return GradeResult(
            accepted=False,
            tests_executed=0,
            tests_expected=tests_expected,
            returncode=None,
            stdout="",
            stderr="",
            refused_config=refused,
        )

    shutil.copy2(suite, workspace / suite.name)
```

Leave the rest of `grade()` unchanged.

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest tests/test_config_refusal.py -v`
Expected: 9 passed

- [ ] **Step 7: Run the full test suite**

Run: `uv run pytest -q`
Expected: 30 passed (21 pre-existing + 9 new)

If any pre-existing test fails, stop and report rather than editing it —
see the Global Constraints.

- [ ] **Step 8: Commit**

```bash
git add harness/grading.py tests/test_config_refusal.py
git commit -m "feat(grading): refuse to certify a run carrying model-written config"
```
