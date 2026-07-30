# Phase 1 Cycle 2: Workspace Provisioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `prepare_workspace` context manager that copies a fixture
directory into a fresh, git-initialized, disposable temp workspace, and
prove it via an automated pytest test that re-runs cycle 1's accept/reject
procedure through it.

**Architecture:** One new module, `harness/workspace.py`, exporting a
single `@contextmanager` function. One new test file,
`tests/test_workspace.py`, built up in four TDD increments: copy behavior,
cleanup behavior, git-init behavior, then the two integration tests
(accept-check, reject-check) that exercise it against cycle 1's real
fixtures.

**Tech Stack:** Python 3.14, pytest 8.3.4, `tempfile`/`shutil`/`subprocess`
from the standard library, `git` CLI (assumed on PATH).

## Global Constraints

- Python `>=3.14,<3.15` (from `pyproject.toml`).
- `pytest==8.3.4`, `fastapi[standard]==0.115.10`, `turbohtml==1.5.0` are
  the pinned dependencies already declared in `pyproject.toml` — do not
  add new dependencies for this cycle.
- `prepare_workspace` must take the fixture directory as a parameter —
  never a hardcoded path (spec's "seams, not hardcodes" rule).
- No allowlist, config refusal, hook-written verdict, checkpointing, or
  diff exercise this cycle — all deferred (see `ROADMAP.md`'s Deferred
  candidates list).
- No changes to `examples/agentclinic/phase-1/{reference,broken,acceptance}`
  — cycle 1's fixtures and suite are read-only inputs here.

---

### Task 1: `prepare_workspace` — copy into a fresh workspace, clean up on exit

**Files:**
- Create: `conftest.py` (repo root, empty) — pytest imports `conftest.py`
  from the directory it lives in first; since that directory has no
  `__init__.py`, pytest inserts repo root onto `sys.path`, which is what
  makes `from harness.workspace import prepare_workspace` resolve from
  `tests/test_workspace.py`.
- Create: `harness/__init__.py` (empty) — makes `harness` a package.
- Create: `harness/workspace.py`
- Test: `tests/test_workspace.py`

**Interfaces:**
- Produces: `prepare_workspace(source_dir: Path) -> Iterator[Path]`, a
  `@contextmanager`. Later tasks (2, 3, 4) call it as
  `with prepare_workspace(some_dir) as workspace:`.

- [ ] **Step 1: Create the repo-root conftest.py**

```python
# Empty on purpose — its presence puts the repo root on sys.path for
# test collection, so `import harness` resolves from tests/.
```

Write this as the entire contents of `conftest.py` at the repo root.

- [ ] **Step 2: Create the harness package**

Create `harness/__init__.py` with empty contents (0 bytes).

- [ ] **Step 3: Write the failing tests**

```python
# tests/test_workspace.py
from harness.workspace import prepare_workspace


def test_prepare_workspace_copies_files_into_a_new_directory(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("x = 1\n")

    with prepare_workspace(source) as workspace:
        assert workspace != source
        assert (workspace / "app.py").read_text() == "x = 1\n"


def test_prepare_workspace_cleans_up_on_exit(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("x = 1\n")

    with prepare_workspace(source) as workspace:
        created = workspace

    assert not created.exists()
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `uv run pytest tests/test_workspace.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'harness.workspace'`

- [ ] **Step 5: Write the minimal implementation**

```python
# harness/workspace.py
from __future__ import annotations

import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def prepare_workspace(source_dir: Path) -> Iterator[Path]:
    """Copy source_dir into a fresh temp directory and yield the path.

    The workspace is removed on exit.
    """
    workspace = Path(tempfile.mkdtemp(prefix="satyrn-workspace-"))
    try:
        shutil.copytree(source_dir, workspace, dirs_exist_ok=True)
        yield workspace
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_workspace.py -v`
Expected: PASS (2 tests)

- [ ] **Step 7: Commit**

```bash
git add conftest.py harness/__init__.py harness/workspace.py tests/test_workspace.py
git commit -m "feat: add prepare_workspace, copying into a disposable temp workspace"
```

---

### Task 2: git-init the workspace with an initial commit

**Files:**
- Modify: `harness/workspace.py`
- Test: `tests/test_workspace.py`

**Interfaces:**
- Consumes: `prepare_workspace(source_dir: Path) -> Iterator[Path]` from Task 1.
- Produces: same signature; behavior extended so the yielded workspace
  contains a git repo with one commit of the copied state. Task 3 and 4
  rely only on the copy + git-init behavior already established here,
  not on any new name.

- [ ] **Step 1: Write the failing test**

```python
# add to tests/test_workspace.py
import subprocess


def test_prepare_workspace_git_inits_with_a_commit(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("x = 1\n")

    with prepare_workspace(source) as workspace:
        assert (workspace / ".git").is_dir()
        log = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )
        assert log.stdout.strip() != ""
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_workspace.py -v`
Expected: FAIL — `assert (workspace / ".git").is_dir()` is false (no git repo yet).

- [ ] **Step 3: Extend the implementation**

```python
# harness/workspace.py
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "satyrn-engine",
    "GIT_AUTHOR_EMAIL": "satyrn-engine@localhost",
    "GIT_COMMITTER_NAME": "satyrn-engine",
    "GIT_COMMITTER_EMAIL": "satyrn-engine@localhost",
}


@contextmanager
def prepare_workspace(source_dir: Path) -> Iterator[Path]:
    """Copy source_dir into a fresh temp directory, git-init it with an
    initial commit of the copied state, and yield the workspace path.

    The workspace is removed on exit.
    """
    workspace = Path(tempfile.mkdtemp(prefix="satyrn-workspace-"))
    try:
        shutil.copytree(source_dir, workspace, dirs_exist_ok=True)
        subprocess.run(
            ["git", "init", "-q"], cwd=workspace, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "add", "-A"], cwd=workspace, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-q", "--no-gpg-sign", "-m", "initial workspace state"],
            cwd=workspace,
            check=True,
            capture_output=True,
            env=_GIT_ENV,
        )
        yield workspace
    finally:
        shutil.rmtree(workspace, ignore_errors=True)
```

The explicit `_GIT_ENV` author/committer identity avoids depending on the
machine's global `git config` — this is not the hermetic grader (no
allowlist, no config refusal), but there's no reason to make `git commit`
fail on a machine with no global `user.name` set.

- [ ] **Step 4: Run all workspace tests to verify they pass**

Run: `uv run pytest tests/test_workspace.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add harness/workspace.py tests/test_workspace.py
git commit -m "feat: git-init the workspace with an initial commit"
```

---

### Task 3: Accept-check — reference fixture through a provisioned workspace

**Files:**
- Test: `tests/test_workspace.py`

**Interfaces:**
- Consumes: `prepare_workspace(source_dir: Path) -> Iterator[Path]` from Task 2.
  No changes to `harness/workspace.py` in this task.

- [ ] **Step 1: Write the test**

```python
# add to tests/test_workspace.py
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_1 = REPO_ROOT / "examples" / "agentclinic" / "phase-1"


def test_prepare_workspace_accepts_the_reference_solution():
    with prepare_workspace(PHASE_1 / "reference") as workspace:
        shutil.copy(
            PHASE_1 / "acceptance" / "test_acceptance.py",
            workspace / "test_acceptance.py",
        )
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )

    assert result.returncode == 0
    assert "4 passed" in result.stdout
```

This mirrors cycle 1's manually-recorded result exactly: exit code 0, "4
passed" (see
`docs/superpowers/research/2026-07-30-phase1-cycle1-fixture-results.md`).
It shells out to `sys.executable -m pytest` (the same interpreter already
running the outer test suite, with `fastapi`/`turbohtml`/`pytest` already
installed) rather than `uv run pytest`, since the temp workspace has no
`pyproject.toml` of its own for `uv` to resolve a project from.

- [ ] **Step 2: Run the test to verify it passes**

Run: `uv run pytest tests/test_workspace.py -v`
Expected: PASS (4 tests total). If it fails, check that `fastapi`,
`turbohtml`, and `starlette` (a `fastapi` dependency) are actually
importable in the active environment — a missing dependency here would
produce a collection error inside the subprocess, not a real failure, and
is the same false-pass trap cycle 1's spec called out.

- [ ] **Step 3: Commit**

```bash
git add tests/test_workspace.py
git commit -m "test: accept-check the reference fixture through prepare_workspace"
```

---

### Task 4: Reject-check — broken fixture through a provisioned workspace

**Files:**
- Test: `tests/test_workspace.py`

**Interfaces:**
- Consumes: `prepare_workspace(source_dir: Path) -> Iterator[Path]` from
  Task 2, and the `REPO_ROOT`/`PHASE_1` constants from Task 3.

- [ ] **Step 1: Write the test**

```python
# add to tests/test_workspace.py
def test_prepare_workspace_rejects_the_broken_solution():
    with prepare_workspace(PHASE_1 / "broken") as workspace:
        shutil.copy(
            PHASE_1 / "acceptance" / "test_acceptance.py",
            workspace / "test_acceptance.py",
        )
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=workspace,
            capture_output=True,
            text=True,
        )

    assert result.returncode != 0
    assert "4 failed" in result.stdout
    assert "assert 404 == 200" in result.stdout
```

This mirrors cycle 1's other recorded result: exit code 1, "4 failed", all
via genuine `AssertionError` including `assert 404 == 200` (same results
doc as Task 3).

- [ ] **Step 2: Run the full test file to verify everything passes**

Run: `uv run pytest tests/test_workspace.py -v`
Expected: PASS (5 tests total)

- [ ] **Step 3: Run the whole suite once more as a final check**

Run: `uv run pytest -q`
Expected: PASS, 5 passed, no errors or warnings about collection.

- [ ] **Step 4: Commit**

```bash
git add tests/test_workspace.py
git commit -m "test: reject-check the broken fixture through prepare_workspace"
```
