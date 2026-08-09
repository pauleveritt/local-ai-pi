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
    _write(
        source,
        "tests/test_add.py",
        "from pkg import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
    )
    _git(source, "add", "-A")
    _git(source, "commit", "-q", "--no-gpg-sign", "-m", "base")
    base_sha = _git(source, "rev-parse", "HEAD")

    _write(
        source,
        "src/pkg/__init__.py",
        "def add(a, b):\n    return a + b\n\n\ndef mul(a, b):\n    return a * b\n",
    )
    _write(
        source,
        "tests/test_mul.py",
        "from pkg import mul\n\n\ndef test_mul():\n    assert mul(2, 3) == 6\n",
    )
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


def test_ensure_clone_creates_a_bare_repo(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    cache = tmp_path / "cache"
    clone = ensure_clone(str(synthetic_clone.bare), cache)
    assert clone.is_dir()
    assert (clone / "HEAD").is_file()


def test_ensure_clone_is_idempotent(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    cache = tmp_path / "cache"
    first = ensure_clone(str(synthetic_clone.bare), cache)
    second = ensure_clone(str(synthetic_clone.bare), cache)
    assert first == second


def test_materialize_yields_the_base_tree(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        assert (workspace / "tests" / "test_add.py").is_file()
        assert not (workspace / "tests" / "test_mul.py").exists()


def test_materialized_workspace_has_exactly_one_commit(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        assert _git(workspace, "rev-list", "--count", "HEAD") == "1"


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
        assert _git(workspace, "remote") == ""
        assert not (workspace / ".git" / "objects" / "info" / "alternates").exists()


def test_materialize_removes_the_workspace_on_exception(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    escaped: Path | None = None
    with (
        pytest.raises(RuntimeError, match="boom"),
        materialize(clone, synthetic_clone.base_sha) as workspace,
    ):
        escaped = workspace
        raise RuntimeError("boom")
    assert escaped is not None
    assert not escaped.exists()


def test_materialize_rejects_an_unknown_sha(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with (
        pytest.raises(WorkloadError, match="not present"),
        materialize(clone, "0" * 40),
    ):
        pass


def test_materialize_leaves_no_pycache_in_git_status(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """A later cycle diffs a workspace to decide what a model changed."""
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        (workspace / "src" / "pkg" / "__pycache__").mkdir(parents=True)
        (workspace / "src" / "pkg" / "__pycache__" / "x.pyc").write_text("")
        assert _git(workspace, "status", "--short") == ""


def test_the_cache_is_named_from_the_upstream_not_hardcoded(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """This module must serve the postponed application cohort unchanged."""
    other = tmp_path / "renamed.git"
    shutil.copytree(synthetic_clone.bare, other)
    clone = ensure_clone(str(other), tmp_path / "cache")
    assert clone.name == "renamed.git"
