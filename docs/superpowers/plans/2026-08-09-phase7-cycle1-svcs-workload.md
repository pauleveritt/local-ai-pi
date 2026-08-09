# Phase 7 Cycle 1 — `svcs` Replay Workload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a qualified, frozen commit-replay workload drawn from the `svcs` library, so Phase 7 has an instrument that can distinguish executor approaches.

**Architecture:** A repo-managed bare clone of upstream `svcs` supplies immutable base and target trees. Each task materializes its base tree into a *synthetic single-commit git repository* — a real committable repo whose object store physically lacks the target commit, with no remote and no alternates. That is a *history invariant*, deliberately not called a seal: it says nothing about reading the clone cache by path, and confinement belongs to the executor cycle. A frozen union environment (dependencies only, project never installed) runs preservation and hidden-oracle suites via `PYTHONPATH`. A deterministic qualification pipeline proves each task is real: base green, oracle rejects the base matching a pre-registered fingerprint, target green, and all four conditions agreeing at node level across three fresh materializations. No model executor runs in this cycle.

**Tech Stack:** Python 3.14, stdlib `tomllib` for manifests, `uv` for the cohort environment, pytest for both the project's own tests and the workload's suites, existing `harness/processes.py` for bounded subprocess execution.

**Spec:** [`../specs/2026-08-09-phase7-cycle1-svcs-workload-design.md`](../specs/2026-08-09-phase7-cycle1-svcs-workload-design.md)

**Worktree:** Create a fresh worktree named `phase7-workload` off commit `de27b4d` before Task 1 — **not off `main`**, which does not contain this plan or its spec. Do not implement in `phase6-orchestrator-spike`; that branch holds Phase 7-pre research and its own uncommitted changes.

## Global Constraints

- Python `>=3.14,<3.15`. The project venv is managed by `uv`; never activate it by hand.
- Every command runs through `uv run --locked` — e.g. `uv run --locked pytest`.
- Quality gates, all three must pass before any commit: `uv run --locked ruff check .`, `uv run --locked ruff format --diff`, `uv run --locked pyrefly check`.
- Ruff lint selects `E`, `F`, `I`, `UP`, `B`, `SIM`; `E501` (line length) is ignored. Import sorting is enforced — put imports in one block at the top of the file.
- `pyrefly` type-checks `harness` and `tests`. Annotate every public function signature.
- No new third-party dependency may be added to this project. `tomllib` is stdlib; `uv` is invoked as a subprocess, never imported.
- The cohort environment is a *separate* venv from this project's. Never run workload suites with this project's interpreter.
- Commit messages end with a trailing line: `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`
- Tests must pass offline with no `svcs` clone present. Anything needing the real clone or the network is marked `@pytest.mark.skipif` on the absence of the cache.
- Never touch `/Users/pauleveritt/PycharmProjects/svcs`. It is a working checkout on `feature/autowiring` and is not this workload's source of truth.

---

## File Structure

| File | Responsibility |
|---|---|
| `harness/workload.py` | Create/modify. All workload primitives: clone cache, materialization, oracle overlay, cohort env, suite runner, manifest model, qualification pipeline. Knows nothing about `svcs` specifically. |
| `tools/qualify_workload.py` | Create. CLI driver only: read `cohort.toml`, loop tasks, write `qualification.json`, print a summary, set exit code. |
| `workloads/svcs/env/pyproject.toml` | Create. The frozen union environment declaration. Committed. |
| `workloads/svcs/env/uv.lock` | Create (generated). Committed — it *is* the freeze. |
| `workloads/svcs/cohort.toml` | Create. Upstream URL, env pointer, included/excluded task lists with reasons. |
| `workloads/svcs/tasks/<task_id>/manifest.toml` | Create ×10. Per-task SHAs, commands, hashes, attestations. |
| `workloads/svcs/tasks/<task_id>/brief.md` | Create ×10. Behavior-only task brief. |
| `workloads/svcs/tasks/<task_id>/contract.md` | Create (qualified tasks only, Task 9). |
| `workloads/svcs/tasks/<task_id>/contract-draft.md` | Create (qualified tasks only, Task 9). Firewalled author's uncorrected draft. |
| `workloads/svcs/tasks/<task_id>/qualification.json` | Generated, committed. Evidence. |
| `tests/test_workload.py` | Create. Unit tests over a synthetic git repo. Offline, no `svcs`. |
| `.gitignore` | Modify. Add `.workloads/`. |
| `pyproject.toml` | Modify. Add `.workloads` and `workloads` to pytest `norecursedirs`. |
| `docs/superpowers/specs/2026-08-08-phase7-cycle*.md` | Rename to `phase7-pre-*` (Task 1). |

---

### Task 1: Retire Phase 7-pre

Renaming precondition. Two committed specs currently claim the cycle numbers this plan uses; until they are renamed every forward reference is ambiguous.

**Files:**
- Rename: `docs/superpowers/specs/2026-08-08-phase7-cycle1-batch-integrity-design.md` → `docs/superpowers/specs/2026-08-08-phase7-pre-batch-integrity-design.md`
- Rename: `docs/superpowers/specs/2026-08-08-phase7-cycle2-bounded-executor-design.md` → `docs/superpowers/specs/2026-08-08-phase7-pre-bounded-executor-design.md`
- Rename: `docs/superpowers/plans/2026-08-08-phase7-cycle1-batch-integrity.md` → `docs/superpowers/plans/2026-08-08-phase7-pre-batch-integrity.md`
- Rename: `docs/superpowers/plans/2026-08-08-phase7-cycle2-bounded-executor.md` → `docs/superpowers/plans/2026-08-08-phase7-pre-bounded-executor.md`
- Modify: every file containing a link to a renamed path

- [ ] **Step 1: Find every reference before moving anything**

```bash
grep -rn "2026-08-08-phase7-cycle1\|2026-08-08-phase7-cycle2" --include="*.md" docs/ README.md BRIEF.md
```

Record the list. Each hit is a link that will break.

The date prefix is load-bearing: a bare `phase7-cycle1` also matches this cycle's own new filenames, so the check could never come back clean.

- [ ] **Step 2: Rename with git mv**

```bash
git mv docs/superpowers/specs/2026-08-08-phase7-cycle1-batch-integrity-design.md docs/superpowers/specs/2026-08-08-phase7-pre-batch-integrity-design.md
git mv docs/superpowers/specs/2026-08-08-phase7-cycle2-bounded-executor-design.md docs/superpowers/specs/2026-08-08-phase7-pre-bounded-executor-design.md
git mv docs/superpowers/plans/2026-08-08-phase7-cycle1-batch-integrity.md docs/superpowers/plans/2026-08-08-phase7-pre-batch-integrity.md
git mv docs/superpowers/plans/2026-08-08-phase7-cycle2-bounded-executor.md docs/superpowers/plans/2026-08-08-phase7-pre-bounded-executor.md
```

If a listed plan file does not exist, skip that line — only the two spec files are known to exist for certain.

- [ ] **Step 3: Add a retirement banner to each renamed document**

Insert immediately after the `# Title` line of all four files:

```markdown
> **Retired — Phase 7-pre.** This work is banked, not current. Its instruments
> (prompt ledger, prompt/tool coherence checks, estimator and `insufficient-n`
> behavior, process sentinel, block-boundary split, extension-lifecycle fix)
> remain in the tree and are still maintained. Forward work continues in
> [the Phase 7 workload-first roadmap](../plans/2026-08-09-phase7-workload-first-roadmap.md).
```

- [ ] **Step 4: Fix every link found in Step 1**

Update each referencing file so the path points at the new `phase7-pre-` name. Leave prose that says "cycle 1" alone where it describes Phase 7-pre's own internal numbering; only paths change.

- [ ] **Step 5: Verify no dangling references**

```bash
grep -rn "2026-08-08-phase7-cycle1\|2026-08-08-phase7-cycle2" --include="*.md" docs/ README.md BRIEF.md
```

Expected: no output, or only hits inside `docs/_build/` (generated, ignore). Searching the dated names only — a bare `phase7-cycle1` matches this cycle's own files and would never be empty.

- [ ] **Step 6: Verify the docs suite still passes**

```bash
uv run --locked pytest tests/test_research_records.py tests/test_doc_quotes.py -q
```

Expected: PASS. These suites assert properties of the docs tree and will catch a broken cross-reference.

- [ ] **Step 7: Commit**

```bash
git add -A docs/ README.md BRIEF.md
git commit -m "docs(phase7): retire last night's phase 7 as phase 7-pre

Two specs owned the names 'phase 7 cycle 1' and 'cycle 2'. The
workload-first roadmap renumbers, so those names now belong to the svcs
workload. Renaming rather than deleting: the instruments stay in the
tree and are still maintained.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Clone cache and the workspace history invariant

**Files:**
- Create: `harness/workload.py`
- Modify: `harness/workspace.py` (extract two reusable helpers)
- Modify: `.gitignore`
- Modify: `pyproject.toml`
- Test: `tests/test_workload.py`

**Interfaces:**
- Consumes: `harness.workspace.prepare_workspace` (existing; refactored in place, behavior unchanged).
- Produces:
  - `harness.workspace.GIT_ENV: dict[str, str]`
  - `harness.workspace.disposable_dir(prefix: str) -> Iterator[Path]` — a `@contextmanager` yielding a temp dir, removed on exit including on exception.
  - `harness.workspace.git_init_commit(workspace: Path, message: str) -> None`
  - `harness.workload.ensure_clone(upstream: str, cache_root: Path) -> Path` — returns the bare clone path.
  - `harness.workload.export_tree(clone: Path, sha: str, destination: Path) -> None`
  - `harness.workload.materialize(clone: Path, sha: str) -> Iterator[Path]` — a `@contextmanager` yielding a workspace path; removes it on exit including on exception.
  - `harness.workload.WorkloadError` — the module's single exception type.

- [ ] **Step 1: Make the hermetic git env reusable**

In `harness/workspace.py`, rename the module-level `_GIT_ENV` to `GIT_ENV` and update its three uses inside that file (the `git init`, `git add`, and `git commit` calls). No behavior change.

- [ ] **Step 2: Extract the two halves of `prepare_workspace`**

`prepare_workspace` does three separable things: make a disposable temp dir, populate it, and turn it into a one-commit git repo. `materialize` needs the first and third with a different middle. Rather than duplicate the init/commit/cleanup semantics — and then have them drift — extract them.

Replace the body of `harness/workspace.py` below `GIT_ENV` with:

```python
@contextmanager
def disposable_dir(prefix: str) -> Iterator[Path]:
    """Yield a fresh temp directory, removed on exit including on exception."""
    workspace = Path(tempfile.mkdtemp(prefix=prefix))
    try:
        yield workspace
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def git_init_commit(workspace: Path, message: str) -> None:
    """Turn a populated directory into a git repo with exactly one commit.

    Hermetic by construction: `GIT_ENV` disables global and system
    config, and `core.hooksPath` is pointed at the null device, so a
    developer's own hooks and identity cannot reach in and change what a
    workspace looks like.

    The `.git/info/exclude` entries keep Python's runtime droppings out
    of `git status`. That matters more than tidiness here: a later cycle
    diffs a workspace to decide what a model changed, and a stray
    `__pycache__` would read as candidate output.
    """
    subprocess.run(
        ["git", "init", "-q"], cwd=workspace, check=True, capture_output=True, env=GIT_ENV
    )
    subprocess.run(
        ["git", "add", "-A"], cwd=workspace, check=True, capture_output=True, env=GIT_ENV
    )
    subprocess.run(
        [
            "git",
            "-c",
            f"core.hooksPath={os.devnull}",
            "commit",
            "-q",
            "--no-gpg-sign",
            "--allow-empty",
            "-m",
            message,
        ],
        cwd=workspace,
        check=True,
        capture_output=True,
        env=GIT_ENV,
    )
    (workspace / ".git" / "info" / "exclude").write_text(
        "# Satyrn harness runtime artifacts\n__pycache__/\n*.pyc\n.pytest_cache/\n"
    )


@contextmanager
def prepare_workspace(*source_dirs: Path | None) -> Iterator[Path]:
    """Copy each source directory, in order, into a fresh temp directory,
    git-init it with an initial commit, and yield the workspace path.

    Passing nothing (or only `None`s) creates a literally empty workspace.
    The workspace is removed on exit.

    **Order is the contract**, and it became load-bearing in phase 6 when a
    suite gained a seed of its own. Two layers can now arrive: the suite's
    starting codebase, then the improvement's seed on top. Later directories
    overwrite earlier ones on collision, so an improvement can override a
    file the workload supplies -- which is the direction an intervention
    should be able to act in, and not the reverse.

    `None` entries are skipped rather than rejected so callers can pass an
    optional layer positionally without branching at every call site.
    """
    with disposable_dir("satyrn-workspace-") as workspace:
        for source_dir in source_dirs:
            if source_dir is None:
                continue
            shutil.copytree(
                source_dir,
                workspace,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
            )
        git_init_commit(workspace, "initial workspace state")
        yield workspace
```

This is a pure refactor: same commands, same order, same hermetic env, same cleanup, same docstring. `materialize` in Step 5 then reuses both helpers with `export_tree` as its middle step, so there is one definition of what a harness workspace *is*.

- [ ] **Step 3: Verify the refactor changed no behavior**

```bash
grep -rn "_GIT_ENV" harness/ tests/ tools/
```

Expected: no output.

```bash
uv run --locked pytest tests/test_workspace.py tests/test_runner.py tests/test_improvement.py -q
```

Expected: PASS. `prepare_workspace` is used throughout the runner and improvement suites, so those are the regression surface for this change — not `test_workspace.py` alone.

- [ ] **Step 4: Write the failing tests**

Create `tests/test_workload.py`:

Note on imports: this file grows across Tasks 2–7. Ruff's `E402` and `I` rules
are on, so every task must *extend the single block at the top* rather than add
a mid-file or in-function import. Each task's step says which names to add. The
block starts as:

```python
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from harness.workload import WorkloadError, ensure_clone, materialize
from harness.workspace import GIT_ENV


@dataclass(frozen=True)
class SyntheticClone:
    """A bare git repo with two commits, standing in for upstream svcs."""

    bare: Path
    base_sha: str
    target_sha: str


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=GIT_ENV,
    )
    return result.stdout.strip()


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture
def synthetic_clone(tmp_path: Path) -> SyntheticClone:
    source = tmp_path / "source"
    source.mkdir()
    _git(source, "init", "-q")

    _write(source, "src/pkg/__init__.py", "def add(a, b):\n    return a + b\n")
    _write(source, "tests/test_add.py", "from pkg import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n")
    _git(source, "add", "-A")
    _git(source, "commit", "-q", "--no-gpg-sign", "-m", "base")
    base_sha = _git(source, "rev-parse", "HEAD")

    _write(source, "src/pkg/__init__.py", "def add(a, b):\n    return a + b\n\n\ndef mul(a, b):\n    return a * b\n")
    _write(source, "tests/test_mul.py", "from pkg import mul\n\n\ndef test_mul():\n    assert mul(2, 3) == 6\n")
    _git(source, "add", "-A")
    _git(source, "commit", "-q", "--no-gpg-sign", "-m", "target")
    target_sha = _git(source, "rev-parse", "HEAD")

    bare = tmp_path / "upstream.git"
    subprocess.run(
        ["git", "clone", "--bare", "-q", str(source), str(bare)],
        check=True,
        capture_output=True,
        env=GIT_ENV,
    )
    return SyntheticClone(bare, base_sha, target_sha)


def test_ensure_clone_creates_a_bare_repo(tmp_path: Path, synthetic_clone: SyntheticClone) -> None:
    cache = tmp_path / "cache"
    clone = ensure_clone(str(synthetic_clone.bare), cache)
    assert clone.is_dir()
    assert (clone / "HEAD").is_file()


def test_ensure_clone_is_idempotent(tmp_path: Path, synthetic_clone: SyntheticClone) -> None:
    cache = tmp_path / "cache"
    first = ensure_clone(str(synthetic_clone.bare), cache)
    second = ensure_clone(str(synthetic_clone.bare), cache)
    assert first == second


def test_materialize_yields_the_base_tree(tmp_path: Path, synthetic_clone: SyntheticClone) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        assert (workspace / "tests" / "test_add.py").is_file()
        assert not (workspace / "tests" / "test_mul.py").exists()


def test_materialized_workspace_has_exactly_one_commit(tmp_path: Path, synthetic_clone: SyntheticClone) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        count = _git(workspace, "rev-list", "--count", "HEAD")
        assert count == "1"


def test_target_commit_is_absent_from_the_workspace_history(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """The history invariant asserted directly.

    This is the narrow claim and the only one these tests support: the
    target is not in *this* object store. It says nothing about whether
    a process could read the clone cache by path.
    """
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        probe = subprocess.run(
            ["git", "cat-file", "-e", synthetic_clone.target_sha],
            cwd=workspace,
            capture_output=True,
            env=GIT_ENV,
        )
        assert probe.returncode != 0


def test_workspace_has_no_remote_and_no_alternates(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Absence of the object is worth little if a path back to the cache remains."""
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        remotes = subprocess.run(
            ["git", "remote"], cwd=workspace, capture_output=True, text=True, env=GIT_ENV
        )
        assert remotes.stdout.strip() == ""
        assert not (workspace / ".git" / "objects" / "info" / "alternates").exists()


def test_materialize_removes_the_workspace_on_exception(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    escaped: Path | None = None
    with pytest.raises(RuntimeError, match="boom"):
        with materialize(clone, synthetic_clone.base_sha) as workspace:
            escaped = workspace
            raise RuntimeError("boom")
    assert escaped is not None
    assert not escaped.exists()


def test_materialize_rejects_an_unknown_sha(tmp_path: Path, synthetic_clone: SyntheticClone) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with pytest.raises(WorkloadError, match="not present"):
        with materialize(clone, "0" * 40):
            pass
```

- [ ] **Step 5: Run the tests to verify they fail**

```bash
uv run --locked pytest tests/test_workload.py -q
```

Expected: collection error — `ModuleNotFoundError: No module named 'harness.workload'`.

- [ ] **Step 6: Write the implementation**

Create `harness/workload.py`:

```python
import shutil
import subprocess
import tarfile
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from harness.workspace import GIT_ENV, disposable_dir, git_init_commit


class WorkloadError(RuntimeError):
    """Any failure that makes a workload operation untrustworthy.

    Deliberately one type. A caller cannot usefully recover from "the
    oracle hash drifted" differently from "the base SHA is missing" --
    both mean the instrument is not in the state its manifest claims,
    and the only correct response is to stop and show the operator why.
    """


def ensure_clone(upstream: str, cache_root: Path) -> Path:
    """Return a bare clone of `upstream` under `cache_root`, creating it once.

    Bare rather than a working clone: nothing ever checks out here. Trees
    are exported into disposable workspaces, so the cache stays a
    read-only object store that no task can perturb.

    The directory is named from the upstream URL, not hardcoded -- this
    module is workload-agnostic, and the postponed application cohort
    will point it somewhere else entirely.
    """
    cache_root.mkdir(parents=True, exist_ok=True)
    name = upstream.rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
    clone = cache_root / f"{name}.git"
    if clone.is_dir():
        return clone
    result = subprocess.run(
        ["git", "clone", "--bare", "-q", upstream, str(clone)],
        capture_output=True,
        text=True,
        env=GIT_ENV,
    )
    if result.returncode != 0:
        shutil.rmtree(clone, ignore_errors=True)
        raise WorkloadError(f"cloning {upstream} failed: {result.stderr.strip()}")
    return clone


def _require_sha(clone: Path, sha: str) -> None:
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=clone,
        capture_output=True,
        env=GIT_ENV,
    )
    if probe.returncode == 0:
        return
    subprocess.run(
        ["git", "fetch", "-q", "origin", "+refs/heads/*:refs/heads/*", "--tags"],
        cwd=clone,
        capture_output=True,
        env=GIT_ENV,
    )
    retry = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=clone,
        capture_output=True,
        env=GIT_ENV,
    )
    if retry.returncode != 0:
        raise WorkloadError(f"commit {sha} is not present in {clone} after a fetch")


def export_tree(clone: Path, sha: str, destination: Path) -> None:
    """Extract the tree at `sha` into `destination`, which must exist.

    Via `git archive` rather than a checkout so the destination never
    receives git metadata from the clone -- that absence is what the
    history invariant rests on.
    """
    _require_sha(clone, sha)
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".tar") as archive:
        result = subprocess.run(
            ["git", "archive", "--format=tar", sha],
            cwd=clone,
            stdout=archive,
            stderr=subprocess.PIPE,
            env=GIT_ENV,
        )
        if result.returncode != 0:
            raise WorkloadError(f"git archive {sha} failed: {result.stderr.decode(errors='replace').strip()}")
        archive.flush()
        with tarfile.open(archive.name) as tar:
            tar.extractall(destination, filter="data")


@contextmanager
def materialize(clone: Path, sha: str) -> Iterator[Path]:
    """Yield a synthetic single-commit git repository holding the tree at `sha`.

    The workspace is a real, committable repo -- a later cycle turns
    candidate work into a commit here -- but its object store contains
    exactly one commit, the one `git_init_commit` just wrote. The
    upstream history, and therefore every target commit and hidden
    oracle, is absent from *this* object store, and the repo has no
    remote and no alternates pointing back at the clone.

    That is the whole claim. It is not confinement: nothing here stops a
    process from reading the clone cache by path.

    Disposable-dir and init-commit semantics are shared with
    `prepare_workspace` rather than reimplemented, so there is one
    definition of what a harness workspace is, and no second copy to
    drift from it.

    Removed on exit, including on exception.
    """
    with disposable_dir("satyrn-workload-") as workspace:
        export_tree(clone, sha, workspace)
        git_init_commit(workspace, f"materialized base {sha}")
        yield workspace
```

- [ ] **Step 7: Run the tests to verify they pass**

```bash
uv run --locked pytest tests/test_workload.py -q
```

Expected: 8 passed.

- [ ] **Step 8: Keep derived state out of git and out of pytest**

In `.gitignore`, add below the `# Local workspace state` block:

```
.workloads/
```

In `pyproject.toml`, extend `norecursedirs` to include the workload directories. The full replacement value:

```toml
norecursedirs = ["examples/agentclinic", "examples/duration", "examples/preservation", "examples/fanout", "examples/fanout-blind", "improvements", "docs/_build", ".worktrees", ".workloads", "workloads"]
```

`workloads` is listed because it will hold materialized `svcs` test files that must never be collected as this project's tests. `.workloads` is listed because gitignoring a directory does not stop pytest from walking into it.

- [ ] **Step 9: Verify the whole suite still collects cleanly**

```bash
uv run --locked pytest -q
```

Expected: PASS, with no attempt to collect anything under `workloads/` or `.workloads/`.

- [ ] **Step 10: Quality gates**

```bash
uv run --locked ruff check . && uv run --locked ruff format --diff && uv run --locked pyrefly check
```

Expected: all three clean.

- [ ] **Step 11: Commit**

```bash
git add harness/workload.py harness/workspace.py tests/test_workload.py .gitignore pyproject.toml
git commit -m "feat(workload): materialize a base with no path to its future

A workspace is a fresh one-commit repo: the target is absent from its
object store, and it has no remote and no alternates. Tests assert both
directly.

The disposable-dir and init-commit halves of prepare_workspace are
extracted and shared rather than reimplemented, so one definition of a
harness workspace serves both callers and there is no second copy to
drift.

Deliberately NOT called a seal. This is a history invariant about one
object store -- it says nothing about reading the clone cache by path,
about the network, or about model priors. Confinement belongs to the
executor cycle.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: The frozen cohort environment

**Files:**
- Create: `workloads/svcs/env/pyproject.toml`
- Create: `workloads/svcs/env/uv.lock` (generated by `uv lock`)
- Modify: `harness/workload.py`
- Test: `tests/test_workload.py`

**Interfaces:**
- Consumes: `WorkloadError` from Task 2.
- Produces:
  - `harness.workload.CohortEnv` — frozen dataclass with `python: Path`, `lock_sha256: str`.
  - `harness.workload.sha256_file(path: Path) -> str`
  - `harness.workload.ensure_cohort_env(env_source: Path, cache_root: Path) -> CohortEnv`

- [ ] **Step 1: Write the environment declaration**

Create `workloads/svcs/env/pyproject.toml` with exactly this content. Every pin here was derived by running the ladder's ten base suites against candidate resolutions; the comments record why, because a later reader will otherwise "tidy" them away.

```toml
# The frozen cohort environment for the svcs replay workload.
#
# Dependencies ONLY -- svcs itself is deliberately not installed. Each
# materialized workspace supplies svcs through PYTHONPATH=<workspace>/src,
# so there is exactly one importable copy and no question of which one a
# test got.
#
# This is a hand-authored UNION of what the ladder's bases need, not any
# single base's own lockfile. Three pins are load-bearing:
#
#   httpx AND httpx2   Bases before the 2026 migration `import httpx`;
#                      later ones `import httpx2`. The ladder spans both.
#   httpx<0.28         The historical Pyramid tests construct
#                      httpx.Client(app=...), which 0.28 removed. Without
#                      this ceiling four bases fail collection.
#   pyramid,           In the older bases' `optional` group, dropped from
#   setuptools<82      the newest. Kept so historical integration tests
#                      actually run instead of being excused.
#
# Measured against this environment, all ten ladder bases pass their FULL
# preservation suites in under 0.3s each. There are no deselects.
[project]
name = "svcs-cohort-env"
version = "0"
requires-python = ">=3.14,<3.15"
dependencies = [
  "attrs>=21.3.0",
  "typing_extensions>=4.13.0",
  "pytest",
  "pytest-asyncio",
  "sybil>=6",
  "aiohttp",
  "fastapi",
  "flask",
  "httpx<0.28",
  "httpx2",
  "pyramid",
  "setuptools<82",
  "starlette",
  "sqlalchemy",
]
```

- [ ] **Step 2: Generate and inspect the lock**

```bash
cd workloads/svcs/env && uv lock && shasum -a 256 uv.lock
```

Expected: a resolution of roughly 55 packages. Record the printed hash — Task 8's manifests carry it as `environment.lock_sha256`.

- [ ] **Step 3: Register the integration marker**

In `pyproject.toml`, add to `[tool.pytest.ini_options]`:

```toml
markers = ["integration: needs the real clone cache or network; excluded from the offline unit run"]
```

The offline guarantee is about the *unit* suite. Run it as
`uv run --locked pytest -m "not integration"`; the full run including
integration tests is a deliberate, network-having choice.

- [ ] **Step 4: Write the failing tests**

Extend the import block with `ensure_cohort_env` and `sha256_file` from
`harness.workload`, then append to `tests/test_workload.py`:

```python
def test_sha256_file_is_stable(tmp_path: Path) -> None:
    path = tmp_path / "f.txt"
    path.write_text("hello")
    assert sha256_file(path) == sha256_file(path)
    assert len(sha256_file(path)) == 64


@pytest.mark.integration
def test_cohort_env_reports_the_lock_hash(tmp_path: Path) -> None:
    """The env is identified by its lock, so a silent re-resolution is visible.

    Marked integration: it runs a real `uv sync`, which needs the
    network on a cold cache. The offline guarantee covers the unit
    suite, and this is deliberately outside it.
    """
    env_source = Path("workloads/svcs/env")
    env = ensure_cohort_env(env_source, tmp_path / "cache")
    assert env.lock_sha256 == sha256_file(env_source / "uv.lock")
    assert env.python.is_file()


def test_cohort_env_refuses_a_mismatched_interpreter(tmp_path: Path) -> None:
    """A lock pins packages; it does not pin the interpreter that reads them."""
    env_source = tmp_path / "env"
    env_source.mkdir()
    (env_source / "uv.lock").write_text("# not a real lock\n")
    (env_source / "pyproject.toml").write_text(
        '[project]\nname = "x"\nversion = "0"\nrequires-python = ">=3.14,<3.15"\ndependencies = []\n'
    )
    with pytest.raises(WorkloadError, match="3.99.0"):
        ensure_cohort_env(env_source, tmp_path / "cache", require_python="3.99.0")
```

- [ ] **Step 4: Run to verify failure**

```bash
uv run --locked pytest tests/test_workload.py -q -k "sha256 or cohort_env"
```

Expected: FAIL with `ImportError: cannot import name 'sha256_file'`.

- [ ] **Step 5: Implement**

Add to `harness/workload.py` — imports go into the existing top-of-file block:

```python
import hashlib
import os
from dataclasses import dataclass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class CohortEnv:
    """The one interpreter every workload suite runs under."""

    python: Path
    lock_sha256: str
    python_version: str
    platform: str


def ensure_cohort_env(
    env_source: Path,
    cache_root: Path,
    require_python: str | None = None,
) -> CohortEnv:
    """Sync the frozen cohort environment and return its interpreter.

    `uv sync --locked` refuses to update the lockfile, so a drifted
    declaration fails loudly here rather than quietly producing a
    different environment than the one every recorded result was
    measured against.

    `require_python` is checked because a lock pins *packages*, not the
    interpreter that reads them. `requires-python = ">=3.14,<3.15"`
    admits 3.14.0 and 3.14.7 alike, and two reviewers resolving the same
    dependency list already produced different test collections -- so
    the interpreter is part of the freeze, not an ambient detail.

    The venv is placed under the cache, not inside `env_source`, so the
    committed declaration directory stays free of build output.
    """
    lock = env_source / "uv.lock"
    if not lock.is_file():
        raise WorkloadError(f"no uv.lock in {env_source}; run `uv lock` there first")

    venv = (cache_root / "env").resolve()
    venv.parent.mkdir(parents=True, exist_ok=True)
    environ = dict(os.environ)
    environ["UV_PROJECT_ENVIRONMENT"] = str(venv)
    result = subprocess.run(
        ["uv", "sync", "--locked", "--no-install-project", "-q"],
        cwd=env_source,
        capture_output=True,
        text=True,
        env=environ,
    )
    if result.returncode != 0:
        raise WorkloadError(f"cohort env sync failed: {result.stderr.strip()}")

    python = venv / "bin" / "python"
    if not python.is_file():
        raise WorkloadError(f"cohort env has no interpreter at {python}")

    probe = subprocess.run(
        [str(python), "-c", "import platform, sys; print(platform.python_version()); print(sys.platform)"],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        raise WorkloadError(f"cohort interpreter is not runnable: {probe.stderr.strip()}")
    version, _, plat = probe.stdout.strip().partition("\n")
    if require_python is not None and version != require_python:
        raise WorkloadError(
            f"cohort env interpreter is {version}, manifest requires {require_python}"
        )
    return CohortEnv(
        python=python,
        lock_sha256=sha256_file(lock),
        python_version=version,
        platform=plat,
    )
```

- [ ] **Step 6: Run to verify passing**

```bash
uv run --locked pytest tests/test_workload.py -q
```

Expected: 10 passed, 1 skipped when offline.

- [ ] **Step 7: Quality gates**

```bash
uv run --locked ruff check . && uv run --locked ruff format --diff && uv run --locked pyrefly check
```

- [ ] **Step 8: Commit**

```bash
git add workloads/svcs/env/pyproject.toml workloads/svcs/env/uv.lock harness/workload.py tests/test_workload.py
git commit -m "feat(workload): frozen union environment, no deselects needed

The research doc's Pyramid exclusion was an artifact of the inspecting
venv lacking httpx2, not a property of the workload. A union pinning
both httpx<0.28 and httpx2 runs all ten ladder bases' full preservation
suites green in under 0.3s each. Deps only, project never installed, so
PYTHONPATH is the single source of svcs.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Suite runner with reason classification

The gate that makes a base rejection mean something: an import typo and a genuinely missing behavior both exit non-zero, and only one of them is evidence.

**Files:**
- Modify: `harness/workload.py`
- Test: `tests/test_workload.py`

**Interfaces:**
- Consumes: `CohortEnv` (Task 3), `materialize` (Task 2), `harness.processes.run_process`.
- Produces:
  - `harness.workload.SuiteResult` — frozen dataclass: `returncode: int | None`, `reason_class: str`, `tests_passed: int`, `wall_seconds: float`, `timed_out: bool`, `stdout_tail: str`.
  - `harness.workload.REASON_CLASSES: tuple[str, ...]` — `("pass", "collection-error", "assertion-failure", "error", "timeout")`.
  - `harness.workload.run_suite(workspace: Path, command: Sequence[str], env: CohortEnv, timeout: float = 300.0) -> SuiteResult`

- [ ] **Step 1: Write the failing tests**

Extend the import block with `import sys` and with `CohortEnv` and `run_suite`
from `harness.workload`, then append to `tests/test_workload.py`:

Note the four `pytest` exit codes these tests pin down — 0 pass, 1 tests failed,
2 interrupted (which is what a collection error produces), 5 nothing collected.
The last one matters most: a mistyped oracle path exits 5, and a classifier that
called that a rejection would qualify a broken task.

```python
def _fake_env() -> CohortEnv:
    """The project's own interpreter, standing in for the cohort env.

    The synthetic repo needs only stdlib plus pytest, both of which this
    project's venv has -- so the runner's behavior can be tested without
    resolving the real svcs environment.
    """
    return CohortEnv(python=Path(sys.executable), lock_sha256="synthetic")


def test_run_suite_reports_pass(tmp_path: Path, synthetic_clone: SyntheticClone) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        result = run_suite(workspace, ["pytest", "-q", "-p", "no:cacheprovider"], _fake_env())
    assert result.reason_class == "pass"
    assert result.returncode == 0
    assert result.tests_passed == 1


def test_run_suite_classifies_a_collection_error(tmp_path: Path, synthetic_clone: SyntheticClone) -> None:
    """The base-plus-oracle shape: the oracle imports a symbol that does not exist yet."""
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        (workspace / "tests" / "test_mul.py").write_text(
            "from pkg import mul\n\n\ndef test_mul():\n    assert mul(2, 3) == 6\n"
        )
        result = run_suite(workspace, ["pytest", "-q", "-p", "no:cacheprovider"], _fake_env())
    assert result.reason_class == "collection-error"


def test_run_suite_classifies_an_assertion_failure(tmp_path: Path, synthetic_clone: SyntheticClone) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        (workspace / "tests" / "test_wrong.py").write_text(
            "from pkg import add\n\n\ndef test_wrong():\n    assert add(1, 1) == 3\n"
        )
        result = run_suite(workspace, ["pytest", "-q", "-p", "no:cacheprovider"], _fake_env())
    assert result.reason_class == "assertion-failure"


def test_run_suite_imports_from_the_workspace_not_the_environment(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """PYTHONPATH must win. If it did not, every result would be about the wrong code."""
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        (workspace / "tests" / "test_origin.py").write_text(
            "import pkg\n\n\ndef test_origin():\n"
            f"    assert pkg.__file__.startswith({str(workspace)!r})\n"
        )
        result = run_suite(workspace, ["pytest", "-q", "-p", "no:cacheprovider"], _fake_env())
    assert result.reason_class == "pass"


def test_run_suite_times_out_without_leaking_the_child(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        (workspace / "tests" / "test_slow.py").write_text(
            "import time\n\n\ndef test_slow():\n    time.sleep(60)\n"
        )
        result = run_suite(
            workspace, ["pytest", "-q", "-p", "no:cacheprovider"], _fake_env(), timeout=3.0
        )
    assert result.timed_out is True
    assert result.reason_class == "timeout"


def test_run_suite_records_node_level_outcomes(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Node ids and outcomes, from pytest's hooks -- not a count scraped from prose."""
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        result = run_suite(workspace, ["pytest", "-q", "-p", "no:cacheprovider"], _fake_env())
    assert result.outcomes == {"tests/test_add.py::test_add": "passed"}
    assert result.tests_passed == 1


def test_different_failures_produce_different_fingerprints(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """The reason a coarse class is not enough.

    Both runs below are `assertion-failure`. If stability compared only
    the class, a suite that fails a *different* test on every run would
    look perfectly stable.
    """
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    fingerprints = []
    for name in ("test_first", "test_second"):
        with materialize(clone, synthetic_clone.base_sha) as workspace:
            (workspace / "tests" / "test_x.py").write_text(
                f"def {name}():\n    assert False\n"
            )
            result = run_suite(workspace, ["pytest", "-q", "-p", "no:cacheprovider"], _fake_env())
        assert result.reason_class == "assertion-failure"
        fingerprints.append(result.fingerprint)
    assert fingerprints[0] != fingerprints[1]


def test_a_command_collecting_nothing_is_an_error_not_a_rejection(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """pytest exit 5. A mistyped oracle path must never qualify as a base rejection."""
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        result = run_suite(
            workspace,
            ["pytest", "-q", "-p", "no:cacheprovider", "tests/test_add.py::test_absent"],
            _fake_env(),
        )
    assert result.reason_class == "error"
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run --locked pytest tests/test_workload.py -q -k run_suite
```

Expected: FAIL with `ImportError: cannot import name 'run_suite'`.

- [ ] **Step 3: Implement**

Add to `harness/workload.py`:

```python
from collections.abc import Sequence

import harness.grading_plugin as grading_plugin
from harness.processes import run_process

REASON_CLASSES = ("pass", "collection-error", "assertion-failure", "error", "timeout")


@dataclass(frozen=True)
class SuiteResult:
    """One suite run, described by what pytest's own hooks reported.

    `outcomes` maps node id to final outcome, read from the results file
    `harness.grading_plugin` writes through `pytest_runtest_logreport`.
    That is trustworthy in a way parsing stdout is not: hooks fire only
    when pytest actually ran a test, while stdout can be written to by
    the code under test. `fingerprint` is the stable comparison key --
    two runs that fail *different* assertions must not look identical.
    """

    returncode: int | None
    reason_class: str
    outcomes: dict[str, str]
    tests_passed: int
    wall_seconds: float
    timed_out: bool
    stdout_tail: str

    @property
    def fingerprint(self) -> tuple[object, ...]:
        return (
            self.reason_class,
            self.returncode,
            tuple(sorted(self.outcomes.items())),
        )


# pytest's documented exit codes. Reading these is far more robust than
# matching summary-line prose, which changes between pytest releases and
# can be forged by the code under test writing to stdout.
_PYTEST_OK = 0
_PYTEST_TESTS_FAILED = 1
_PYTEST_INTERRUPTED = 2
_PYTEST_NO_TESTS = 5


def _read_outcomes(path: Path) -> tuple[dict[str, str], bool]:
    """Parse the grading plugin's results file into {nodeid: outcome}, plus done.

    Last line wins per nodeid. That is deliberate and matches
    `harness/grading.py`: a test whose call phase passed but whose
    teardown then failed appends a second, later `failed` line, and the
    later one is the truth.
    """
    outcomes: dict[str, str] = {}
    done = False
    if not path.is_file():
        return outcomes, done
    for line in path.read_text().splitlines():
        if line == grading_plugin.DONE_MARKER:
            done = True
            continue
        nodeid, separator, outcome = line.partition("\t")
        if separator:
            outcomes[nodeid] = outcome
    return outcomes, done


def classify(
    returncode: int | None,
    outcomes: dict[str, str],
    done: bool,
    timed_out: bool,
) -> str:
    """Name *how* a suite failed, not merely that it did.

    A base that fails at collection because the API does not exist yet
    is the evidence a replay task needs. A base that collects and fails
    an assertion is a different -- often broken -- task. Both exit
    non-zero, so an exit code alone cannot qualify a task, and an import
    typo in an oracle would otherwise sail through as a valid rejection.

    Decided from pytest's exit code and the plugin's recorded outcomes,
    never from summary prose. Exit 2 is pytest interrupting itself,
    which is what a collection error produces -- and in that case the
    session still finishes, so `done` is true while `outcomes` is empty.
    Exit 5 means nothing was collected at all, which is a broken command
    rather than a rejection, and must not be mistaken for one.
    """
    if timed_out:
        return "timeout"
    if returncode == _PYTEST_INTERRUPTED:
        return "collection-error"
    if returncode == _PYTEST_NO_TESTS:
        return "error"
    if returncode == _PYTEST_OK and done:
        return "pass"
    if returncode == _PYTEST_TESTS_FAILED and any(o == "failed" for o in outcomes.values()):
        return "assertion-failure"
    return "error"


def run_suite(
    workspace: Path,
    command: Sequence[str],
    env: CohortEnv,
    timeout: float = 300.0,
) -> SuiteResult:
    """Run one suite in `workspace` under the cohort interpreter.

    `command` is argv *after* `python -m`, so a manifest's
    `["pytest", "-q"]` becomes `<cohort python> -m pytest -q`.

    The grading plugin is staged into a temp directory *outside* the
    workspace, along with its results file. Two reasons: the workspace
    must stay byte-identical to the base tree, and pointing PYTHONPATH
    at this project's `harness/` would make every harness module
    importable from inside a suite under test.

    The child environment is built from nothing rather than inherited.
    The cohort env supplies dependencies, PYTHONPATH supplies exactly
    one copy of the project under test, and HOME and TMPDIR point into
    the disposable workspace so nothing a suite writes lands in the
    operator's home directory. No proxy variables are passed through --
    which is most of what "no network" means in practice, and is
    hygiene rather than a guarantee.
    """
    with tempfile.TemporaryDirectory(prefix="satyrn-suite-") as staging_name:
        staging = Path(staging_name)
        shutil.copy2(Path(grading_plugin.__file__), staging / "grading_plugin.py")
        results = staging / "results.txt"
        results.touch()
        child_env = {
            "PATH": os.defpath,
            "PYTHONPATH": os.pathsep.join([str(workspace / "src"), str(staging)]),
            "PYTHONDONTWRITEBYTECODE": "1",
            "HOME": str(workspace),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "TMPDIR": str(workspace),
            grading_plugin.RESULTS_ENV_VAR: str(results),
        }
        result = run_process(
            [str(env.python), "-m", *command, "-p", "grading_plugin"],
            cwd=workspace,
            timeout=timeout,
            env=child_env,
        )
        outcomes, done = _read_outcomes(results)

    output = result.stdout + result.stderr
    return SuiteResult(
        returncode=result.returncode,
        reason_class=classify(result.returncode, outcomes, done, result.timed_out),
        outcomes=outcomes,
        tests_passed=sum(1 for outcome in outcomes.values() if outcome == "passed"),
        wall_seconds=result.wall_seconds,
        timed_out=result.timed_out,
        stdout_tail=output[-4000:],
    )
```

- [ ] **Step 4: Run to verify passing**

```bash
uv run --locked pytest tests/test_workload.py -q
```

Expected: 20 passed. The timeout test takes about 3 seconds; the rest are milliseconds.

- [ ] **Step 5: Quality gates**

```bash
uv run --locked ruff check . && uv run --locked ruff format --diff && uv run --locked pyrefly check
```

- [ ] **Step 6: Commit**

```bash
git add harness/workload.py tests/test_workload.py
git commit -m "feat(workload): node-level outcomes, not scraped summary prose

Outcomes come from pytest's own runtest hooks via the existing
grading_plugin, so a run is described by node ids rather than by a
regex over stdout the code under test can write to. Classification
reads exit codes: 2 is a collection error, 5 is a mistyped command that
collected nothing and must never pass as a rejection.

The fingerprint exists because two runs failing *different* assertions
are both "assertion-failure" -- comparing classes alone would call a
randomly-failing suite stable.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Manifest model and oracle overlay

**Files:**
- Modify: `harness/workload.py`
- Test: `tests/test_workload.py`

**Interfaces:**
- Consumes: `WorkloadError`, `sha256_file`, `export_tree` (Tasks 2–3).
- Produces:
  - `harness.workload.Manifest` — frozen dataclass, fields listed in the implementation below.
  - `harness.workload.load_manifest(task_dir: Path) -> Manifest`
  - `harness.workload.overlay_oracle(clone: Path, manifest: Manifest, destination: Path) -> None`

- [ ] **Step 1: Write the failing tests**

Extend the import block with `export_tree`, `load_manifest`, and `overlay_oracle`
from `harness.workload`, then append to `tests/test_workload.py`:

```python
def _write_manifest(task_dir: Path, clone: SyntheticClone, **overrides: object) -> Path:
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "brief.md").write_text("Add a mul function.\n")
    brief_sha = sha256_file(task_dir / "brief.md")
    body = f"""
task_id = "synthetic"
role = "floor"
axes = ["arithmetic"]

[source]
upstream = "{clone.bare}"
base_sha = "{clone.base_sha}"
target_sha = "{clone.target_sha}"

[task]
brief = "brief.md"
brief_sha256 = "{overrides.get("brief_sha256", brief_sha)}"
contract_version = 1

[policy]
readable = ["src/**", "tests/**"]
writable = ["src/pkg/**"]
candidate_output = ["src/pkg/__init__.py"]

[oracle]
files = ["tests/test_mul.py"]
command = ["pytest", "-q", "-p", "no:cacheprovider", "tests/test_mul.py"]

[oracle.rejection]
class           = "collection-error"
missing_symbols = ["mul"]
failing_nodes   = []

[oracle.files_sha256]
"tests/test_mul.py" = "{overrides.get("oracle_sha", "")}"

[preservation]
command = ["pytest", "-q", "-p", "no:cacheprovider"]
deselects = []
deselect_reason = ""

[environment]
id = "synthetic-env"
python = "3.14"
lock_sha256 = "synthetic"

[attestations]
behavior_not_structure = "The oracle calls the public function."
statable_behaviorally = "Multiply two numbers."
substantive = "Adds a new public behavior."
writable_bounded = "One module."
adaptations = "None."
"""
    (task_dir / "manifest.toml").write_text(body.lstrip())
    return task_dir


def test_load_manifest_reads_every_field(tmp_path: Path, synthetic_clone: SyntheticClone) -> None:
    task_dir = tmp_path / "tasks" / "synthetic"
    _write_manifest(task_dir, synthetic_clone)
    # The oracle hash is only knowable after export, so patch it in.
    export = tmp_path / "export"
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    export_tree(clone, synthetic_clone.target_sha, export)
    oracle_sha = sha256_file(export / "tests" / "test_mul.py")
    _write_manifest(task_dir, synthetic_clone, oracle_sha=oracle_sha)

    manifest = load_manifest(task_dir)
    assert manifest.task_id == "synthetic"
    assert manifest.base_sha == synthetic_clone.base_sha
    assert manifest.base_rejection == "collection-error"
    assert manifest.oracle_files == ("tests/test_mul.py",)
    assert manifest.preservation_command == ("pytest", "-q", "-p", "no:cacheprovider")


def test_load_manifest_rejects_a_drifted_brief(tmp_path: Path, synthetic_clone: SyntheticClone) -> None:
    task_dir = tmp_path / "tasks" / "synthetic"
    _write_manifest(task_dir, synthetic_clone, brief_sha256="0" * 64)
    with pytest.raises(WorkloadError, match="brief.md"):
        load_manifest(task_dir)


def test_load_manifest_rejects_an_unknown_reason_class(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = tmp_path / "tasks" / "synthetic"
    _write_manifest(task_dir, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(text.replace('"collection-error"', '"probably-broken"'))
    with pytest.raises(WorkloadError, match="oracle.rejection.class"):
        load_manifest(task_dir)


def test_load_manifest_requires_a_rejection_fingerprint(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """A bare class does not distinguish a real task from a typo'd oracle."""
    task_dir = tmp_path / "tasks" / "synthetic"
    _write_manifest(task_dir, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(text.replace('missing_symbols = ["mul"]', "missing_symbols = []"))
    with pytest.raises(WorkloadError, match="missing_symbols or failing_nodes"):
        load_manifest(task_dir)


def test_load_manifest_requires_every_attestation(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = tmp_path / "tasks" / "synthetic"
    _write_manifest(task_dir, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace('substantive = "Adds a new public behavior."', 'substantive = "   "')
    )
    with pytest.raises(WorkloadError, match="substantive"):
        load_manifest(task_dir)


def test_load_manifest_rejects_an_abbreviated_sha(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """A short SHA is not immutable -- it can become ambiguous as history grows."""
    task_dir = tmp_path / "tasks" / "synthetic"
    _write_manifest(task_dir, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace(synthetic_clone.base_sha, synthetic_clone.base_sha[:7])
    )
    with pytest.raises(WorkloadError, match="40-character"):
        load_manifest(task_dir)


def test_load_manifest_rejects_an_absolute_policy_path(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = tmp_path / "tasks" / "synthetic"
    _write_manifest(task_dir, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(text.replace('writable = ["src/pkg/**"]', 'writable = ["/etc/**"]'))
    with pytest.raises(WorkloadError, match="repository-relative"):
        load_manifest(task_dir)


def test_overlay_oracle_rejects_a_drifted_oracle(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = tmp_path / "tasks" / "synthetic"
    _write_manifest(task_dir, synthetic_clone, oracle_sha="0" * 64)
    manifest = load_manifest(task_dir)
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        with pytest.raises(WorkloadError, match="drift"):
            overlay_oracle(clone, manifest, workspace)
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run --locked pytest tests/test_workload.py -q -k "manifest or overlay"
```

Expected: FAIL with `ImportError: cannot import name 'load_manifest'`.

- [ ] **Step 3: Implement**

Add to `harness/workload.py`:

```python
import tomllib
from collections.abc import Mapping


@dataclass(frozen=True)
class Manifest:
    task_id: str
    role: str
    axes: tuple[str, ...]
    upstream: str
    base_sha: str
    target_sha: str
    brief_path: Path
    contract_path: Path | None
    contract_version: int
    readable: tuple[str, ...]
    writable: tuple[str, ...]
    candidate_output: tuple[str, ...]
    oracle_files: tuple[str, ...]
    oracle_files_sha256: dict[str, str]
    oracle_command: tuple[str, ...]
    base_rejection: str
    rejection_missing_symbols: tuple[str, ...]
    rejection_failing_nodes: tuple[str, ...]
    preservation_command: tuple[str, ...]
    deselects: tuple[str, ...]
    deselect_reason: str
    env_id: str
    env_lock_sha256: str
    attestations: dict[str, str]
    task_dir: Path


def _table(data: Mapping[str, object], key: str, where: str) -> dict[str, object]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise WorkloadError(f"manifest is missing the [{where}] table" if value is None else f"{where} is not a table")
    return dict(value)


def _string(table: Mapping[str, object], key: str, where: str) -> str:
    if key not in table:
        raise WorkloadError(f"manifest is missing {where}.{key}")
    return str(table[key])


def _strings(table: Mapping[str, object], key: str, where: str) -> tuple[str, ...]:
    if key not in table:
        raise WorkloadError(f"manifest is missing {where}.{key}")
    value = table[key]
    if not isinstance(value, list):
        raise WorkloadError(f"{where}.{key} must be a list")
    return tuple(str(item) for item in value)


def load_manifest(task_dir: Path) -> Manifest:
    """Read and validate one task manifest.

    Validation is not politeness. A manifest is the frozen claim a task
    makes about itself, and every field here is something a later result
    is reported against -- so a missing field, a drifted brief, or a
    reason class nobody defined has to stop the run rather than be
    filled in with a default.
    """
    path = task_dir / "manifest.toml"
    if not path.is_file():
        raise WorkloadError(f"no manifest.toml in {task_dir}")
    data = tomllib.loads(path.read_text())

    source = _table(data, "source", "source")
    task = _table(data, "task", "task")
    policy = _table(data, "policy", "policy")
    oracle = _table(data, "oracle", "oracle")
    preservation = _table(data, "preservation", "preservation")
    environment = _table(data, "environment", "environment")
    raw_attestations = data.get("attestations", {})
    attestations = (
        {str(k): str(v) for k, v in raw_attestations.items()}
        if isinstance(raw_attestations, dict)
        else {}
    )

    brief_path = task_dir / _string(task, "brief", "task")
    if not brief_path.is_file():
        raise WorkloadError(f"brief {brief_path} does not exist")
    declared_brief = _string(task, "brief_sha256", "task")
    actual_brief = sha256_file(brief_path)
    if declared_brief != actual_brief:
        raise WorkloadError(
            f"brief.md drift in {task_dir}: manifest says {declared_brief[:12]}, file is {actual_brief[:12]}"
        )

    contract_path: Path | None = None
    if "contract" in task:
        contract_path = task_dir / _string(task, "contract", "task")
        if not contract_path.is_file():
            raise WorkloadError(f"contract {contract_path} does not exist")
        declared_contract = _string(task, "contract_sha256", "task")
        actual_contract = sha256_file(contract_path)
        if declared_contract != actual_contract:
            raise WorkloadError(
                f"contract drift in {task_dir}: manifest says {declared_contract[:12]}, file is {actual_contract[:12]}"
            )

    rejection = _table(oracle, "rejection", "oracle.rejection")
    base_rejection = _string(rejection, "class", "oracle.rejection")
    if base_rejection not in REASON_CLASSES:
        raise WorkloadError(
            f"oracle.rejection.class {base_rejection!r} is not one of {REASON_CLASSES}"
        )
    if base_rejection == "pass":
        raise WorkloadError(
            "oracle.rejection.class cannot be 'pass' -- the oracle must reject the base"
        )
    missing_symbols = (
        _strings(rejection, "missing_symbols", "oracle.rejection")
        if "missing_symbols" in rejection
        else ()
    )
    failing_nodes = (
        _strings(rejection, "failing_nodes", "oracle.rejection")
        if "failing_nodes" in rejection
        else ()
    )
    if not missing_symbols and not failing_nodes:
        raise WorkloadError(
            "oracle.rejection needs missing_symbols or failing_nodes -- a bare class "
            "does not distinguish 'this API does not exist yet' from 'the oracle has a typo'"
        )

    for label, shas in (("base_sha", source.get("base_sha")), ("target_sha", source.get("target_sha"))):
        text = str(shas)
        if len(text) != 40 or not all(c in "0123456789abcdef" for c in text):
            raise WorkloadError(f"{label} must be a full 40-character SHA, got {text!r}")

    for label, patterns in (("readable", policy.get("readable")), ("writable", policy.get("writable"))):
        for pattern in patterns if isinstance(patterns, list) else ():
            if str(pattern).startswith("/") or ".." in str(pattern):
                raise WorkloadError(
                    f"policy.{label} entry {pattern!r} must be repository-relative with no '..'"
                )

    required_attestations = (
        "behavior_not_structure",
        "statable_behaviorally",
        "substantive",
        "writable_bounded",
        "adaptations",
    )
    for key in required_attestations:
        if not attestations.get(key, "").strip():
            raise WorkloadError(
                f"attestation {key!r} is missing or empty. Five rubric items are curator "
                "judgment rather than machine checks; an attestation that silently "
                "defaults to absent is the same as no attestation while looking like one."
            )
    if preservation.get("deselects") and not str(preservation.get("deselect_reason", "")).strip():
        raise WorkloadError("a deselect list requires a written deselect_reason")

    raw_hashes = oracle.get("files_sha256", {})
    oracle_hashes = (
        {str(k): str(v) for k, v in raw_hashes.items()} if isinstance(raw_hashes, dict) else {}
    )

    return Manifest(
        task_id=_string(data, "task_id", "manifest"),
        role=_string(data, "role", "manifest"),
        axes=_strings(data, "axes", "manifest") if "axes" in data else (),
        upstream=_string(source, "upstream", "source"),
        base_sha=_string(source, "base_sha", "source"),
        target_sha=_string(source, "target_sha", "source"),
        brief_path=brief_path,
        contract_path=contract_path,
        contract_version=int(str(task.get("contract_version", 1))),
        readable=_strings(policy, "readable", "policy"),
        writable=_strings(policy, "writable", "policy"),
        candidate_output=_strings(policy, "candidate_output", "policy") if "candidate_output" in policy else (),
        oracle_files=_strings(oracle, "files", "oracle"),
        oracle_files_sha256=oracle_hashes,
        oracle_command=_strings(oracle, "command", "oracle"),
        base_rejection=base_rejection,
        rejection_missing_symbols=missing_symbols,
        rejection_failing_nodes=failing_nodes,
        preservation_command=_strings(preservation, "command", "preservation"),
        deselects=_strings(preservation, "deselects", "preservation") if "deselects" in preservation else (),
        deselect_reason=str(preservation.get("deselect_reason", "")),
        env_id=_string(environment, "id", "environment"),
        env_lock_sha256=_string(environment, "lock_sha256", "environment"),
        attestations=attestations,
        task_dir=task_dir,
    )


def overlay_oracle(clone: Path, manifest: Manifest, destination: Path) -> None:
    """Copy the hidden oracle files from the target commit into `destination`.

    Called only on a grading *copy*, never on a workspace an executor
    will touch -- so no candidate workspace contains an oracle file at
    any point in its life.

    Oracle content is verified against the manifest's hashes. Drift is
    an error and never a silent re-baseline: an oracle that changed
    under a frozen manifest means every earlier result for this task was
    measured against different tests.
    """
    with tempfile.TemporaryDirectory(prefix="satyrn-oracle-") as staging_name:
        staging = Path(staging_name)
        export_tree(clone, manifest.target_sha, staging)
        for relative in manifest.oracle_files:
            source = staging / relative
            if not source.is_file():
                raise WorkloadError(
                    f"oracle file {relative} is not present at target {manifest.target_sha}"
                )
            declared = manifest.oracle_files_sha256.get(relative)
            if declared is None:
                raise WorkloadError(f"no recorded hash for oracle file {relative}")
            actual = sha256_file(source)
            if declared != actual:
                raise WorkloadError(
                    f"oracle drift in {relative}: manifest says {declared[:12]}, target has {actual[:12]}"
                )
            target_path = destination / relative
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target_path)
```

- [ ] **Step 4: Run to verify passing**

```bash
uv run --locked pytest tests/test_workload.py -q -m "not integration"
```

Expected: 29 passed, 1 deselected.

- [ ] **Step 5: Quality gates**

```bash
uv run --locked ruff check . && uv run --locked ruff format --diff && uv run --locked pyrefly check
```

- [ ] **Step 6: Commit**

```bash
git add harness/workload.py tests/test_workload.py
git commit -m "feat(workload): manifests that fail loudly when they drift

A manifest is the frozen claim a task makes about itself. A drifted
brief, an abbreviated SHA, an absolute policy path, an empty
attestation, or an oracle whose content changed under a frozen hash all
stop the run.

The attestations are required rather than defaulted: five rubric items
are curator judgment, and one that silently becomes absent is the same
as no attestation while still looking like one.

The rejection fingerprint is required for the same reason -- a bare
reason class cannot tell "this API does not exist yet" apart from "the
oracle file has a typo".

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 6: The qualification pipeline

Four conditions, each run three times in its own fresh materialization, compared
at node level. The earlier draft of this task ran target preservation once,
reused one workspace across repeats, and compared only the coarse reason class —
all three of which would have let an unstable or mis-specified task qualify.

**Files:**
- Modify: `harness/workload.py`
- Test: `tests/test_workload.py`

**Interfaces:**
- Consumes: everything from Tasks 2–5.
- Produces:
  - `harness.workload.CONDITIONS: tuple[str, ...]` — `("base_preservation", "base_oracle", "target_preservation", "target_oracle")`
  - `harness.workload.qualify(manifest: Manifest, clone: Path, env: CohortEnv, repeats: int = 3, timeout: float = 300.0, max_seconds: float = 60.0) -> dict[str, object]` — the `qualification.json` payload, with `status` either `"qualified"` or `"disqualified"`.

- [ ] **Step 1: Write the failing tests**

Extend the import block with `from contextlib import contextmanager`, with
`import harness.workload as workload_module`, and with `qualify` from
`harness.workload`, then append to `tests/test_workload.py`:

```python
def _qualified_task(tmp_path: Path, clone: SyntheticClone) -> tuple[Path, Path]:
    """A synthetic task whose manifest carries the real oracle hash."""
    cache = tmp_path / "cache"
    bare = ensure_clone(str(clone.bare), cache)
    export = tmp_path / "export"
    export_tree(bare, clone.target_sha, export)
    oracle_sha = sha256_file(export / "tests" / "test_mul.py")
    task_dir = _write_manifest(tmp_path / "tasks" / "synthetic", clone, oracle_sha=oracle_sha)
    return task_dir, bare


def _condition_of(report: dict[str, object], key: str) -> dict[str, object]:
    """`qualify` returns a JSON-shaped dict[str, object]; narrow before indexing."""
    conditions = report["conditions"]
    assert isinstance(conditions, dict)
    value = conditions[key]
    assert isinstance(value, dict)
    return value


def test_qualify_accepts_a_well_formed_task(tmp_path: Path, synthetic_clone: SyntheticClone) -> None:
    task_dir, bare = _qualified_task(tmp_path, synthetic_clone)
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["status"] == "qualified"
    assert _condition_of(report, "base_preservation")["reason_class"] == "pass"
    assert _condition_of(report, "base_oracle")["reason_class"] == "collection-error"
    assert _condition_of(report, "target_preservation")["reason_class"] == "pass"
    assert _condition_of(report, "target_oracle")["reason_class"] == "pass"


def test_qualify_runs_every_condition_three_times(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Including target preservation, which an earlier draft ran only once."""
    task_dir, bare = _qualified_task(tmp_path, synthetic_clone)
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    for condition in ("base_preservation", "base_oracle", "target_preservation", "target_oracle"):
        assert _condition_of(report, condition)["runs"] == 3


def test_qualify_uses_a_fresh_materialization_per_run(
    tmp_path: Path, synthetic_clone: SyntheticClone, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Repeating inside one workspace measures idempotence, not determinism."""
    task_dir, bare = _qualified_task(tmp_path, synthetic_clone)
    seen: list[Path] = []
    original = materialize

    @contextmanager
    def counting(clone_path: Path, sha: str) -> Iterator[Path]:
        with original(clone_path, sha) as workspace:
            seen.append(workspace)
            yield workspace

    monkeypatch.setattr(workload_module, "materialize", counting)
    qualify(load_manifest(task_dir), bare, _fake_env())
    assert len(seen) == len(set(seen)) == 12  # 4 conditions x 3 runs, no reuse


def test_qualify_disqualifies_a_wrong_reason_class(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """The import-typo case: the base is rejected, but not for the declared reason."""
    task_dir, bare = _qualified_task(tmp_path, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace('class           = "collection-error"', 'class           = "assertion-failure"')
    )
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "base_rejection"


def test_qualify_disqualifies_a_missing_expected_symbol(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """The class matched, but not for the reason the manifest pre-registered."""
    task_dir, bare = _qualified_task(tmp_path, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace('missing_symbols = ["mul"]', 'missing_symbols = ["divide"]')
    )
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "base_rejection"
    assert "divide" in str(report["detail"])


def test_qualify_disqualifies_an_unstable_suite(
    tmp_path: Path, synthetic_clone: SyntheticClone, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Three runs, identical node-level outcomes required.

    The flaky module fails on alternating runs by keying off a marker
    kept OUTSIDE the workspace -- fresh materializations mean anything
    written inside one is gone by the next run, which is exactly the
    property being tested.
    """
    task_dir, bare = _qualified_task(tmp_path, synthetic_clone)
    marker = tmp_path / "flaky-counter"
    flaky = (
        "import pathlib\n\n\n"
        "def test_flaky():\n"
        f"    marker = pathlib.Path({str(marker)!r})\n"
        "    seen = len(marker.read_text()) if marker.exists() else 0\n"
        "    marker.write_text('x' * (seen + 1))\n"
        "    assert seen % 2 == 0\n"
    )
    original = materialize

    @contextmanager
    def patched(clone_path: Path, sha: str) -> Iterator[Path]:
        with original(clone_path, sha) as workspace:
            if sha == synthetic_clone.base_sha:
                (workspace / "tests" / "test_flaky.py").write_text(flaky)
            yield workspace

    monkeypatch.setattr(workload_module, "materialize", patched)
    report = qualify(load_manifest(task_dir), bare, _fake_env())

    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "stability"


def test_qualify_disqualifies_a_slow_suite(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """The sub-minute threshold is enforced, not merely stated."""
    task_dir, bare = _qualified_task(tmp_path, synthetic_clone)
    report = qualify(load_manifest(task_dir), bare, _fake_env(), max_seconds=0.0)
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "runtime"


def test_qualification_records_the_manifest_hash(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Evidence must name the exact manifest it was produced from."""
    task_dir, bare = _qualified_task(tmp_path, synthetic_clone)
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["manifest_sha256"] == sha256_file(task_dir / "manifest.toml")
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run --locked pytest tests/test_workload.py -q -k qualify
```

Expected: FAIL with `ImportError: cannot import name 'qualify'`.

- [ ] **Step 3: Implement**

Add to `harness/workload.py`:

```python
from datetime import UTC, datetime

CONDITIONS = ("base_preservation", "base_oracle", "target_preservation", "target_oracle")


@dataclass(frozen=True)
class ConditionRun:
    """One condition, run `repeats` times, each in its own materialization."""

    name: str
    results: tuple[SuiteResult, ...]

    @property
    def first(self) -> SuiteResult:
        return self.results[0]

    @property
    def stable(self) -> bool:
        return all(r.fingerprint == self.results[0].fingerprint for r in self.results)

    @property
    def slowest(self) -> float:
        return max(r.wall_seconds for r in self.results)

    def payload(self) -> dict[str, object]:
        return {
            "reason_class": self.first.reason_class,
            "returncode": self.first.returncode,
            "tests_passed": self.first.tests_passed,
            "runs": len(self.results),
            "stable": self.stable,
            "wall_seconds": [round(r.wall_seconds, 3) for r in self.results],
            "node_count": len(self.first.outcomes),
        }


def _run_condition(
    name: str,
    clone: Path,
    sha: str,
    command: Sequence[str],
    env: CohortEnv,
    manifest: Manifest,
    overlay: bool,
    repeats: int,
    timeout: float,
) -> ConditionRun:
    """Run one condition `repeats` times, each in a fresh materialization.

    Freshness is the point. Repeating inside a single workspace tells
    you whether a suite is idempotent within a directory -- a weaker
    and different property than whether two independent runs of the
    same commit agree, which is what a replay task needs.
    """
    results = []
    for _ in range(repeats):
        with materialize(clone, sha) as workspace:
            if overlay:
                overlay_oracle(clone, manifest, workspace)
            results.append(run_suite(workspace, command, env, timeout))
    return ConditionRun(name=name, results=tuple(results))


def _rejection_mismatch(manifest: Manifest, observed: SuiteResult) -> str | None:
    """Compare the observed base rejection against the pre-registered fingerprint.

    A class alone is not evidence. `collection-error` is produced both
    by "the API this task adds does not exist yet" and by "the oracle
    file has a typo in an unrelated import", and only the first is a
    task. So the manifest names either the symbols expected to be
    missing or the nodes expected to fail, and both are checked.
    """
    if observed.reason_class != manifest.base_rejection:
        return f"base was {observed.reason_class}, manifest declares {manifest.base_rejection}"

    haystack = observed.stdout_tail
    for symbol in manifest.rejection_missing_symbols:
        if symbol not in haystack:
            return f"expected the base to be missing {symbol!r}, but it is not named in the failure"

    if manifest.rejection_failing_nodes:
        failed = {node for node, outcome in observed.outcomes.items() if outcome == "failed"}
        expected = set(manifest.rejection_failing_nodes)
        if not expected.issubset(failed):
            return f"expected these nodes to fail: {sorted(expected - failed)}"
    return None


def qualify(
    manifest: Manifest,
    clone: Path,
    env: CohortEnv,
    repeats: int = 3,
    timeout: float = 300.0,
    max_seconds: float = 60.0,
) -> dict[str, object]:
    """Prove one task is a real replay task. No model calls.

    Four conditions, in the only order that makes sense: a base that
    cannot pass its own suite is not a starting point; an oracle that
    does not reject that base for the pre-registered reason is not
    measuring the task; a target that cannot pass both is not a
    solution. Each runs `repeats` times in fresh materializations, and
    all runs must agree at node level.

    `max_seconds` enforces the sub-minute validation the design
    requires. `timeout` is the far larger backstop that kills a hung
    child; a suite between the two is a qualification failure, not a
    crash.
    """
    report: dict[str, object] = {
        "task_id": manifest.task_id,
        "role": manifest.role,
        "base_sha": manifest.base_sha,
        "target_sha": manifest.target_sha,
        "manifest_sha256": sha256_file(manifest.task_dir / "manifest.toml"),
        "env_id": manifest.env_id,
        "env_lock_sha256": env.lock_sha256,
        "env_python": env.python_version,
        "env_platform": env.platform,
        "preservation_command": list(manifest.preservation_command),
        "oracle_command": list(manifest.oracle_command),
        "deselects": list(manifest.deselects),
        "recorded_at": datetime.now(UTC).isoformat(),
        "repeats": repeats,
        "max_seconds": max_seconds,
        "conditions": {},
    }

    def _disqualify(gate: str, detail: str) -> dict[str, object]:
        report["status"] = "disqualified"
        report["failed_gate"] = gate
        report["detail"] = detail
        return report

    if manifest.env_lock_sha256 not in ("", env.lock_sha256):
        return _disqualify(
            "environment",
            f"manifest declares lock {manifest.env_lock_sha256[:12]}, cohort env is {env.lock_sha256[:12]}",
        )

    conditions: dict[str, object] = report["conditions"]  # type: ignore[assignment]
    plan = (
        ("base_preservation", manifest.base_sha, manifest.preservation_command, False),
        ("base_oracle", manifest.base_sha, manifest.oracle_command, True),
        ("target_preservation", manifest.target_sha, manifest.preservation_command, False),
        ("target_oracle", manifest.target_sha, manifest.oracle_command, True),
    )

    runs: dict[str, ConditionRun] = {}
    for name, sha, command, overlay in plan:
        run = _run_condition(
            name, clone, sha, command, env, manifest, overlay, repeats, timeout
        )
        runs[name] = run
        conditions[name] = run.payload()

        if name == "base_oracle":
            mismatch = _rejection_mismatch(manifest, run.first)
            if mismatch is not None:
                report["base_oracle_tail"] = run.first.stdout_tail
                return _disqualify("base_rejection", mismatch)
        elif run.first.reason_class != "pass":
            report[f"{name}_tail"] = run.first.stdout_tail
            return _disqualify(name, f"{name} is {run.first.reason_class}, expected pass")

    unstable = [name for name, run in runs.items() if not run.stable]
    if unstable:
        return _disqualify("stability", f"runs disagreed at node level for: {unstable}")

    slow = {name: round(run.slowest, 3) for name, run in runs.items() if run.slowest > max_seconds}
    if slow:
        return _disqualify("runtime", f"conditions exceeded {max_seconds}s: {slow}")

    report["status"] = "qualified"
    return report
```

Note the ordering: every condition runs to completion before the stability and
runtime gates are evaluated. That is deliberate — a task that fails one gate
should still report what the other three conditions did, because triage needs
the whole picture rather than the first stopping point. The exception is a
condition that outright fails its own expectation, which stops immediately since
the remaining conditions would be measuring nothing.

- [ ] **Step 4: Run to verify passing**

```bash
uv run --locked pytest tests/test_workload.py -q -m "not integration"
```

Expected: 28 passed, 1 deselected. Qualification runs 12 suites per task, so the
qualify tests take a few seconds each on the synthetic repo.

- [ ] **Step 5: Quality gates**

```bash
uv run --locked ruff check . && uv run --locked ruff format --diff && uv run --locked pyrefly check
```

- [ ] **Step 6: Commit**

```bash
git add harness/workload.py tests/test_workload.py
git commit -m "feat(workload): four conditions, three fresh runs, node-level agreement

A base that cannot pass its own suite is not a starting point; an
oracle that does not reject it for the PRE-REGISTERED reason is not
measuring the task; a target that cannot pass both is not a solution.

Three things a first draft got wrong and this does not: target
preservation is repeated like everything else; every repeat gets its
own materialization, since repeating in one workspace measures
idempotence rather than determinism; and agreement is compared at node
level, because two runs failing different assertions are both
'assertion-failure'.

The sub-minute threshold is now enforced rather than stated.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: CLI driver and cohort file

**Files:**
- Create: `tools/qualify_workload.py`
- Create: `workloads/svcs/cohort.toml`
- Test: `tests/test_workload.py`

**Interfaces:**
- Consumes: `load_manifest`, `qualify`, `ensure_clone`, `ensure_cohort_env`.
- Produces: `tools.qualify_workload.main(argv: Sequence[str] | None = None) -> int`; writes `qualification.json` per task; exit code 0 only when every attempted task qualified.

- [ ] **Step 1: Write the cohort file**

Create `workloads/svcs/cohort.toml`. The task list is the full ladder; `included`/`excluded` stay empty until Task 8 produces evidence.

```toml
# The svcs replay cohort.
#
# `tasks` is the candidate ladder -- everything qualification will be run
# against. `included` and `excluded` are the frozen result of that run, and
# an exclusion without a reason is not allowed to exist.
name = "svcs"
upstream = "https://github.com/hynek/svcs"
env = "env"

tasks = [
  "registry-iter",
  "magicmock-factory",
  "async-cm-enter",
  "local-pings",
  "flask-extensions",
  "register-value-enter",
  "stringified-annotations",
  "fastapi-get-registry",
  "suppress-context-exit",
  "autowire",
]

included = []

[excluded]
# task_id = "reason this task is not in the frozen cohort"
```

- [ ] **Step 2: Write the failing test**

Extend the import block with `import json` and
`from tools.qualify_workload import main`, then append to
`tests/test_workload.py`:

```python
def test_cli_writes_a_qualification_report(
    tmp_path: Path, synthetic_clone: SyntheticClone, monkeypatch: pytest.MonkeyPatch
) -> None:
    task_dir, bare = _qualified_task(tmp_path, synthetic_clone)
    cohort_dir = tmp_path / "cohort"
    (cohort_dir / "tasks").mkdir(parents=True)
    shutil.copytree(task_dir, cohort_dir / "tasks" / "synthetic")
    (cohort_dir / "cohort.toml").write_text(
        f'name = "synthetic"\nupstream = "{synthetic_clone.bare}"\nenv = "env"\n'
        'tasks = ["synthetic"]\nincluded = []\n\n[excluded]\n'
    )

    monkeypatch.setattr(workload_module, "ensure_cohort_env", lambda *a, **k: _fake_env())

    exit_code = main(["--cohort", str(cohort_dir / "cohort.toml"), "--cache", str(tmp_path / "cache")])
    assert exit_code == 0

    report = json.loads((cohort_dir / "tasks" / "synthetic" / "qualification.json").read_text())
    assert report["status"] == "qualified"
```

- [ ] **Step 3: Run to verify failure**

```bash
uv run --locked pytest tests/test_workload.py -q -k cli
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.qualify_workload'`. If `tools/` has no `__init__.py`, create an empty one — `harness/` has one, so this matches the existing convention.

- [ ] **Step 4: Implement**

Create `tools/qualify_workload.py`:

```python
"""Qualify a replay workload cohort. Deterministic; makes no model calls."""

import argparse
import json
import sys
import tomllib
from collections.abc import Sequence
from pathlib import Path

import harness.workload as workload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", required=True, type=Path, help="path to cohort.toml")
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(".workloads"),
        help="derived state: clone cache and cohort venv",
    )
    parser.add_argument("--task", action="append", default=None, help="qualify only these task ids")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args(argv)

    cohort_root = args.cohort.parent
    cohort = tomllib.loads(args.cohort.read_text())
    task_ids = args.task or list(cohort["tasks"])

    clone = workload.ensure_clone(str(cohort["upstream"]), args.cache)
    env = workload.ensure_cohort_env(cohort_root / str(cohort["env"]), args.cache)

    failures = 0
    for task_id in task_ids:
        task_dir = cohort_root / "tasks" / task_id
        try:
            manifest = workload.load_manifest(task_dir)
            report = workload.qualify(manifest, clone, env, repeats=args.repeats, timeout=args.timeout)
        except workload.WorkloadError as error:
            report = {"task_id": task_id, "status": "disqualified", "failed_gate": "manifest", "detail": str(error)}
        (task_dir).mkdir(parents=True, exist_ok=True)
        (task_dir / "qualification.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

        status = str(report.get("status"))
        if status != "qualified":
            failures += 1
            print(f"{task_id:28} {status:14} {report.get('failed_gate', '')}: {report.get('detail', '')}")
        else:
            base = report.get("base_preservation")
            summary = (
                f"{base.get('tests_passed', '?')} preserved, {base.get('wall_seconds', '?')}s"
                if isinstance(base, dict)
                else ""
            )
            print(f"{task_id:28} qualified      {summary}")

    print(f"\n{len(task_ids) - failures}/{len(task_ids)} qualified")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run to verify passing**

```bash
uv run --locked pytest tests/test_workload.py -q
```

Expected: 22 passed.

- [ ] **Step 6: Quality gates**

```bash
uv run --locked ruff check . && uv run --locked ruff format --diff && uv run --locked pyrefly check
```

- [ ] **Step 7: Commit**

```bash
git add tools/qualify_workload.py tools/__init__.py workloads/svcs/cohort.toml tests/test_workload.py
git commit -m "feat(workload): cohort CLI, exclusions that must carry a reason

An exclusion without a written reason cannot exist in cohort.toml --
'record every exclusion' becomes a property of the data layout rather
than something to remember at write-up time.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: Curate and qualify the ten ladder tasks

Curation work, not new code. The curator sees target diffs — that is unavoidable and is why briefs stay behavioral and attestations are signed prose.

**Files:**
- Create ×10: `workloads/svcs/tasks/<task_id>/manifest.toml`
- Create ×10: `workloads/svcs/tasks/<task_id>/brief.md`
- Generated ×10: `workloads/svcs/tasks/<task_id>/qualification.json`
- Modify: `workloads/svcs/cohort.toml`

**Interfaces:**
- Consumes: the CLI from Task 7.
- Produces: at least six `status = "qualified"` reports, and a frozen `cohort.toml`.

The ladder, with verified parents:

| task_id | Target | Base (parent) | Role |
|---|---|---|---|
| `registry-iter` | `c016b37` | `32ddce2` | floor |
| `magicmock-factory` | `c91f1f1` | `f8585ce` | medium |
| `async-cm-enter` | `32ddce2` | `25d8a0b` | medium |
| `local-pings` | `52c6689` | `31bc6df` | medium |
| `flask-extensions` | `012b6a9` | `85827a1` | medium |
| `register-value-enter` | `c5c5f48` | `e9d9cc1` | medium |
| `stringified-annotations` | `f81e493` | `4b05ab8` | medium |
| `fastapi-get-registry` | `7d56b11` | `98198df` | stretch |
| `suppress-context-exit` | `c0bd379` | `1676980` | stretch |
| `autowire` | `6bb3f28` | `816403b` | ceiling |

- [ ] **Step 1: Prime the clone cache**

```bash
uv run --locked python -c "
from pathlib import Path
from harness.workload import ensure_clone
print(ensure_clone('https://github.com/hynek/svcs', Path('.workloads')))
"
```

Expected: a path to `.workloads/svcs.git`.

- [ ] **Step 2: For each task, identify its oracle files**

```bash
git -C .workloads/svcs.git diff --name-only <base_sha> <target_sha> -- tests/
```

Oracle files are **every** test file this diff adds or changes — not just the obviously-named one. Naming only `tests/test_autowire.py` when the target also touched a shared fixtures module or a supporting integration test would grade against a partial oracle, and a partial oracle silently lowers the bar for every attempt.

Check each hit: a test file the diff merely reformats is not an oracle. If the diff touches no test file, the task cannot be qualified — record it in `cohort.toml`'s `[excluded]` with that reason and move on.

Also inspect what the diff does to `conftest.py` and any fixtures the changed tests import. Those are oracle support files even when the diff leaves them alone, and if the base's copy cannot support the target's tests, the task needs them listed too.

- [ ] **Step 3: For each task, compute the oracle hashes**

```bash
uv run --locked python -c "
import sys, tempfile
from pathlib import Path
from harness.workload import export_tree, sha256_file
target, files = sys.argv[1], sys.argv[2:]
with tempfile.TemporaryDirectory() as d:
    export_tree(Path('.workloads/svcs.git'), target, Path(d))
    for f in files:
        print(f'\"{f}\" = \"{sha256_file(Path(d) / f)}\"')
" <target_sha> tests/test_autowire.py
```

Paste the output into the manifest's `[oracle.files_sha256]` table.

- [ ] **Step 4: Write each brief**

`brief.md` states the behavior a user would observe, in the vocabulary of the library's public API, and never names a private helper, a file to create, or an implementation strategy. Worked example for `local-pings` (target `52c6689`):

```markdown
# Include locally registered services in health pings

`Container.get_pings()` currently reports only services registered on the
registry. A service registered directly on a container -- a local override --
is invisible to it, even when that service declares a ping.

Make `get_pings()` report every service the container would actually resolve,
including locally registered ones. Where a local registration shadows a
registry registration for the same type, the local one is what gets reported.

Existing behavior for registry-only services, and for services without a
ping, must not change.
```

Note what it does not say: no mention of `_local_registry`, no file paths, no
data-structure choice. A brief that reveals the patch fails attestation
`statable_behaviorally`.

- [ ] **Step 5: Write each manifest**

Worked example, `workloads/svcs/tasks/local-pings/manifest.toml`. Fill `brief_sha256` from `uv run --locked python -c "from harness.workload import sha256_file; from pathlib import Path; print(sha256_file(Path('workloads/svcs/tasks/local-pings/brief.md')))"`, and `environment.lock_sha256` from the value recorded in Task 3 Step 2.

```toml
task_id = "local-pings"
role = "medium"
axes = ["override-semantics", "discovery"]

[source]
upstream = "https://github.com/hynek/svcs"
base_sha = "<full 40-char SHA of 31bc6df>"
target_sha = "<full 40-char SHA of 52c6689>"

[task]
brief = "brief.md"
brief_sha256 = "<from the command above>"
contract_version = 1

[policy]
readable = ["src/**", "tests/**", "docs/**", "README.md", "CHANGELOG.md"]
writable = ["src/svcs/**"]
candidate_output = ["src/svcs/_core.py"]

[oracle]
files = ["tests/test_registry.py"]
command = ["pytest", "-q", "-p", "no:cacheprovider", "tests/test_registry.py"]

[oracle.rejection]
class           = "assertion-failure"
missing_symbols = []
failing_nodes   = ["tests/test_registry.py::TestContainer::test_get_pings_local"]

[oracle.files_sha256]
"tests/test_registry.py" = "<from Step 3>"

[preservation]
command = ["pytest", "-q", "-p", "no:cacheprovider"]
deselects = []
deselect_reason = ""

[environment]
id = "svcs-cohort-2026-08-09"
python = "3.14.2"
lock_sha256 = "<from Task 3 Step 2>"

[attestations]
behavior_not_structure = "The oracle calls get_pings() and inspects the returned pings' public attributes. It does not reach into the container's private registry storage."
statable_behaviorally = "The brief describes what get_pings() reports and how local registrations shadow registry ones, without naming the storage attribute or the file that holds it."
substantive = "Changes which services a public API reports, including override precedence. Not formatting, not a rename."
writable_bounded = "src/svcs/** only. Chosen from the library's own layout before any model output existed."
adaptations = "None. The oracle is the upstream test file unmodified."
```

`[oracle.rejection]` is a prediction and is often wrong on the first pass — a task whose oracle adds a new test function to an existing file usually yields `assertion-failure` with specific `failing_nodes`, while one importing a symbol that does not exist yields `collection-error` with `missing_symbols`. Run qualification, read the observed value, and correct the manifest. Correcting a *prediction* before any model has run is not tuning; it is what qualification is for.

What you may **not** do is weaken the fingerprint to make a task pass. Deleting `failing_nodes` to get past the gate converts a real check into a rubber stamp. If the observed failure is not the one the task is about, the task is wrong — exclude it.

- [ ] **Step 6: Qualify the whole ladder**

```bash
uv run --locked python -m tools.qualify_workload --cohort workloads/svcs/cohort.toml
```

Expected: a per-task line and a final count. Every task should either qualify or name the gate it failed.

- [ ] **Step 7: Triage the failures**

For each disqualified task, read its `qualification.json` `detail` and `*_tail`, then act:

- `base_preservation` failed → the frozen env cannot run this base. Do not add a deselect reflexively. First check whether the union is missing a dependency the base needs; if so, add it to `workloads/svcs/env/pyproject.toml`, re-lock, re-run *every* task, and update `lock_sha256` everywhere. Only if no union satisfies it, exclude the task.
- `base_rejection` failed → usually a wrong prediction. Set the declared class to the observed one if the observed one is genuinely the intended missing behavior; exclude the task if the base fails for an unrelated reason.
- `target_oracle` failed → the oracle depends on something outside the target tree. Exclude.
- `stability` failed → the suite is nondeterministic. Exclude.
- `manifest` failed → fix the manifest and re-run.

- [ ] **Step 8: Check cohort shape**

Confirm the qualified set has at least six tasks, containing at least one `floor`, three `medium` on *different* `axes`, one `stretch`, and the `autowire` ceiling. If it does not, qualify more candidates from svcs history rather than relaxing the requirement — the roadmap's stop rule is that a cohort at universal floor or ceiling means the reset is reconsidered, not that thresholds move.

- [ ] **Step 9: Freeze the cohort file**

Fill `included` with the qualified task ids, and `[excluded]` with one `task_id = "reason"` line per exclusion. The reason is prose, not a gate name.

- [ ] **Step 10: Verify the frozen cohort re-qualifies from scratch**

```bash
rm -rf .workloads
uv run --locked python -c "
import subprocess, sys, tomllib
from pathlib import Path
cohort = tomllib.loads(Path('workloads/svcs/cohort.toml').read_text())
args = [a for task_id in cohort['included'] for a in ('--task', task_id)]
sys.exit(subprocess.run([sys.executable, '-m', 'tools.qualify_workload',
                         '--cohort', 'workloads/svcs/cohort.toml', *args]).returncode)
"
```

Expected: exit 0, with every included task qualifying from a cold cache and no manual steps. This is the run that proves the cohort is reproducible rather than an accident of the machine's current state — it re-clones, re-syncs the environment, and re-runs every gate.

- [ ] **Step 11: Commit**

```bash
git add workloads/svcs/
git commit -m "feat(workload): qualify the svcs ladder

Ten candidates run through four gates and three-run stability. What
qualified, what did not, and why, is in cohort.toml and each task's
qualification.json -- including the base_rejection predictions that
turned out wrong and were corrected before any model ran.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: Firewalled contract authoring

The one task that spends model calls. Per qualified task, roughly one authoring call plus a human correction pass.

**Files:**
- Create per qualified task: `workloads/svcs/tasks/<task_id>/contract-draft.md`, `contract.md`
- Modify per qualified task: `manifest.toml` (`[task]` and `[authoring]` blocks)

**Interfaces:**
- Consumes: qualified manifests from Task 8; `Manifest.contract_path` support already exists from Task 5.
- Produces: every included task carrying a contract whose hash is recorded in its manifest.

- [ ] **Step 1: Stage the author packet — outside `.workloads/`**

```bash
uv run --locked python -c "
import shutil, sys
from pathlib import Path
from harness.workload import ensure_clone, export_tree, sha256_file
base_sha, task_id = sys.argv[1], sys.argv[2]
packet = Path.home() / '.satyrn-authoring' / task_id
shutil.rmtree(packet, ignore_errors=True)
export_tree(ensure_clone('https://github.com/hynek/svcs', Path('.workloads')), base_sha, packet / 'repo')
shutil.copy2(Path('workloads/svcs/tasks') / task_id / 'brief.md', packet / 'brief.md')
print('packet:', packet)
print('brief_sha256:', sha256_file(packet / 'brief.md'))
" <base_sha> <task_id>
```

The packet deliberately does **not** live under `.workloads/`. That directory's
immediate sibling is `svcs.git`, which contains every target commit and every
oracle — staging the author's inputs next to the answer key and then asking it
not to look is not a firewall, it is a request. Putting the packet on a
different path makes "the author cannot reach the clone" a statement about
layout rather than only about instructions.

This is layout hygiene, not confinement. Nothing here prevents a process that
goes looking for `.workloads/`; that is the executor cycle's problem, and the
design says so.
```

- [ ] **Step 2: Run the firewalled author**

Start a **fresh session** — not this one, and not one that has read this repository's docs. Its entire input is the packet from Step 1:

1. the base tree at `~/.satyrn-authoring/<task_id>/repo/`
2. the brief at `~/.satyrn-authoring/<task_id>/brief.md`

It must not be given, and its working root must not contain: the clone cache, the oracle files, the target tree or SHA, the `qualification.json`, this plan, or the design spec.

Record, for the manifest's `[authoring]` block: model and version, tool grants, budget, the working root you gave it, and start/end time. The prompt below is committed as `workloads/svcs/authoring-prompt.md` and hashed, so a later reader can tell whether two tasks were authored under the same instruction.

Its instruction:

> You are writing a complete implementation contract for a bounded coding agent
> that will make this change with no further guidance and no ability to ask
> questions. It sees this repository at this commit and your contract, nothing
> else. Read the repository, then write a contract covering: the behavior
> required, the public API involved, which files should change, the invariants
> that must be preserved, and how a reader would know the work is done. Do not
> speculate about tests you cannot see. Write it as `contract.md`.

Save the unedited output as `contract-draft.md`.

- [ ] **Step 3: Correct the draft**

Copy `contract-draft.md` to `contract.md` and edit. Time the editing. The draft is frequently wrong about which module holds the extension point — that is exactly the signal being measured, so fix it in `contract.md` and leave `contract-draft.md` untouched.

- [ ] **Step 4: Record the authoring cost**

```bash
uv run --locked python -c "
import subprocess, sys
from pathlib import Path
from harness.workload import sha256_file
task = sys.argv[1]
d = Path('workloads/svcs/tasks') / task
print('contract_sha256 =', sha256_file(d / 'contract.md'))
diff = subprocess.run(['git','diff','--no-index','--numstat',str(d/'contract-draft.md'),str(d/'contract.md')], capture_output=True, text=True)
print('numstat:', diff.stdout.strip() or '0\t0')
" <task_id>
```

Add to that task's `manifest.toml`:

```toml
[task]
# ... existing fields ...
contract = "contract.md"
contract_sha256 = "<from the command above>"

[authoring]
brief_author           = "curator"
contract_author        = "firewalled-model"
author_model           = "<model id and version>"
author_prompt_sha256   = "<sha256 of workloads/svcs/authoring-prompt.md>"
author_tools           = ["read"]
author_root            = "~/.satyrn-authoring/<task_id>"
draft_sha256           = "<sha256 of contract-draft.md>"
authoring_seconds      = <Step 2 elapsed>
correction_seconds     = <Step 3 elapsed>
correction_diff_lines  = <added + deleted from numstat>
corrector_blind        = false
```

`corrector_blind = false` is not a placeholder — it is the honest value. The
corrector is the curator, who has read every target diff, so `contract.md` is
diff-informed. That makes the later comparison an ablation of *diff-informed
human correction against a firewalled draft*, not a blind-human-versus-planner
comparison. The field exists so no future write-up can quietly assume otherwise.

- [ ] **Step 5: Verify every manifest still loads**

```bash
uv run --locked python -c "
import tomllib
from pathlib import Path
from harness.workload import load_manifest
cohort = tomllib.loads(Path('workloads/svcs/cohort.toml').read_text())
for task_id in cohort['included']:
    m = load_manifest(Path('workloads/svcs/tasks') / task_id)
    assert m.contract_path is not None, f'{task_id} has no contract'
    print(f'{task_id}: contract v{m.contract_version} ok')
"
```

Expected: one `ok` line per included task. A hash mismatch raises here — which is the point, since `contract.md` is now frozen.

- [ ] **Step 6: Re-run qualification to confirm contracts changed nothing**

```bash
uv run --locked python -m tools.qualify_workload --cohort workloads/svcs/cohort.toml
```

Expected: the same qualified set as Task 8. A contract is input for the *next* cycle; if adding one changes a qualification result, something reads a file it should not.

- [ ] **Step 7: Full verification**

```bash
uv run --locked pytest -q && uv run --locked ruff check . && uv run --locked ruff format --diff && uv run --locked pyrefly check
```

- [ ] **Step 8: Commit**

```bash
git add workloads/svcs/
git commit -m "feat(workload): firewalled contracts, corrections measured

The author sees the base tree and the brief -- never the target, the
oracle, or the curator's reasoning. Human corrections are recorded as
time and diff lines, which is what keeps the later planner arm a real
comparison: same authoring process, with and without correction.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Done When

- [ ] Phase 7-pre renamed; `grep -rn "2026-08-08-phase7-cycle1\|2026-08-08-phase7-cycle2" docs/` is clean outside `_build/`.
- [ ] `uv run --locked pytest tests/test_workload.py -q -m "not integration"` passes offline with no `svcs` clone present.
- [ ] A committed `workloads/svcs/env/uv.lock`, a verified 3.14.2 interpreter, and the spec's provisional preservation counts replaced by figures measured against them.
- [ ] At least six qualified tasks: one floor, three medium on different axes, one stretch, the autowiring ceiling.
- [ ] Zero deselects across the qualified cohort, or a written justification per deselect frozen before any attempt.
- [ ] Every qualified task's `qualification.json` shows all four conditions run three times in fresh materializations, agreeing at node level, with the base rejection matching its pre-registered fingerprint and every condition under the enforced `max_seconds`.
- [ ] `cohort.toml` accounts for every candidate as included or excluded, each exclusion with a prose reason.
- [ ] Every included task carries a contract with recorded hash, author model, prompt hash, tool grants, author root, authoring time, correction diff size, and `corrector_blind = false`.
- [ ] `workloads/svcs/authoring-prompt.md` committed and hashed into every manifest that used it.
- [ ] `uv run --locked ruff check .`, `ruff format --diff`, and `pyrefly check` all clean.
