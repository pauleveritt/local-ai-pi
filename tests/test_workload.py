import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from harness.workload import (
    CohortEnv,
    WorkloadError,
    _verify_interpreter,
    ensure_clone,
    ensure_cohort_env,
    materialize,
    run_suite,
    sha256_file,
)
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


def test_sha256_file_is_stable(tmp_path: Path) -> None:
    path = tmp_path / "f.txt"
    path.write_text("hello")
    assert sha256_file(path) == sha256_file(path)
    assert len(sha256_file(path)) == 64


def test_sha256_file_distinguishes_content(tmp_path: Path) -> None:
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("hello")
    b.write_text("hellp")
    assert sha256_file(a) != sha256_file(b)


def test_verify_interpreter_reports_the_running_version() -> None:
    version, plat = _verify_interpreter(Path(sys.executable), None)
    assert version == platform.python_version()
    assert plat == sys.platform


def test_verify_interpreter_refuses_a_mismatched_version() -> None:
    """A lock pins packages; it does not pin the interpreter that reads them.

    `requires-python = ">=3.14,<3.15"` admits 3.14.0 and 3.14.7 alike,
    and two reviewers resolving the same dependency list already
    produced different test collections. The interpreter is part of the
    freeze.
    """
    with pytest.raises(WorkloadError, match="3.99.0"):
        _verify_interpreter(Path(sys.executable), "3.99.0")


def test_ensure_cohort_env_requires_a_lock(tmp_path: Path) -> None:
    env_source = tmp_path / "env"
    env_source.mkdir()
    with pytest.raises(WorkloadError, match="no uv.lock"):
        ensure_cohort_env(env_source, tmp_path / "cache")


@pytest.mark.integration
def test_cohort_env_reports_the_lock_hash(tmp_path: Path) -> None:
    """Syncs the real frozen environment; needs the network on a cold cache."""
    env_source = Path("workloads/svcs/env")
    env = ensure_cohort_env(env_source, tmp_path / "cache", require_python="3.14.2")
    assert env.lock_sha256 == sha256_file(env_source / "uv.lock")
    assert env.python.is_file()
    assert env.python_version == "3.14.2"


@pytest.mark.integration
def test_cohort_env_does_not_install_svcs(tmp_path: Path) -> None:
    """PYTHONPATH must be the only source of svcs, so the env must not carry one."""
    env = ensure_cohort_env(Path("workloads/svcs/env"), tmp_path / "cache")
    probe = subprocess.run(
        [str(env.python), "-c", "import svcs"],
        capture_output=True,
        text=True,
    )
    assert probe.returncode != 0
    assert "No module named 'svcs'" in probe.stderr


def test_export_subst_placeholders_are_not_expanded(tmp_path: Path) -> None:
    """`git archive` would stamp the upstream SHA into the workspace.

    A file marked `export-subst` has its `$Format:...$` placeholders
    expanded by archive. That would put the exact base commit id inside
    a workspace whose whole point is not to hand over provenance -- and
    it differs from what a real checkout contains.
    """
    source = tmp_path / "source"
    source.mkdir()
    _git(source, "init", "-q")
    _write(source, ".gitattributes", "archival.txt export-subst\n")
    _write(source, "archival.txt", "node: $Format:%H$\n")
    _write(source, "keep.py", "x = 1\n")
    _git(source, "add", "-A")
    _git(source, "commit", "-q", "--no-gpg-sign", "-m", "base")
    sha = _git(source, "rev-parse", "HEAD")

    bare = tmp_path / "upstream.git"
    subprocess.run(
        ["git", "clone", "--bare", "-q", str(source), str(bare)],
        check=True,
        capture_output=True,
        env=GIT_ENV,
    )
    clone = ensure_clone(str(bare), tmp_path / "cache")
    with materialize(clone, sha) as workspace:
        archival = (workspace / "archival.txt").read_text()
        assert sha not in archival
        assert archival == "node: $Format:%H$\n"
        assert (workspace / "keep.py").read_text() == "x = 1\n"


def _fake_env() -> CohortEnv:
    """The project's own interpreter, standing in for the cohort env.

    The synthetic repo needs only stdlib plus pytest, both of which this
    project's venv has -- so the runner's behavior can be tested without
    resolving the real svcs environment.
    """
    return CohortEnv(
        python=Path(sys.executable),
        lock_sha256="synthetic",
        python_version=platform.python_version(),
        platform=sys.platform,
    )


_QUIET = ["pytest", "-q", "-p", "no:cacheprovider"]


def test_run_suite_reports_pass(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        result = run_suite(workspace, _QUIET, _fake_env())
    assert result.reason_class == "pass"
    assert result.returncode == 0
    assert result.tests_passed == 1


def test_run_suite_records_node_level_outcomes(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Node ids and outcomes, from pytest's hooks -- not a count scraped from prose."""
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        result = run_suite(workspace, _QUIET, _fake_env())
    assert result.outcomes == {"tests/test_add.py::test_add": "passed"}


def test_run_suite_classifies_a_collection_error(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """The base-plus-oracle shape: the oracle imports a symbol that does not exist yet."""
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        (workspace / "tests" / "test_mul.py").write_text(
            "from pkg import mul\n\n\ndef test_mul():\n    assert mul(2, 3) == 6\n"
        )
        result = run_suite(workspace, _QUIET, _fake_env())
    assert result.reason_class == "collection-error"
    assert "mul" in result.output


def test_run_suite_classifies_an_assertion_failure(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        (workspace / "tests" / "test_wrong.py").write_text(
            "from pkg import add\n\n\ndef test_wrong():\n    assert add(1, 1) == 3\n"
        )
        result = run_suite(workspace, _QUIET, _fake_env())
    assert result.reason_class == "assertion-failure"
    assert result.outcomes["tests/test_wrong.py::test_wrong"] == "failed"


def test_a_command_collecting_nothing_is_an_error_not_a_rejection(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """pytest exit 5. A mistyped oracle path must never qualify as a base rejection."""
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        result = run_suite(
            workspace,
            [*_QUIET, "tests/test_add.py::test_absent"],
            _fake_env(),
        )
    assert result.reason_class == "error"


def test_different_failures_produce_different_fingerprints(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Why a coarse class is not enough.

    Both runs below are `assertion-failure`. If stability compared only
    the class, a suite failing a *different* test on every run would
    look perfectly stable.
    """
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    fingerprints = []
    for name in ("test_first", "test_second"):
        with materialize(clone, synthetic_clone.base_sha) as workspace:
            (workspace / "tests" / "test_x.py").write_text(
                f"def {name}():\n    assert False\n"
            )
            result = run_suite(workspace, _QUIET, _fake_env())
        assert result.reason_class == "assertion-failure"
        fingerprints.append(result.fingerprint)
    assert fingerprints[0] != fingerprints[1]


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
        result = run_suite(workspace, _QUIET, _fake_env())
    assert result.reason_class == "pass"


def test_run_suite_leaves_the_workspace_byte_identical(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """The plugin and its results file must live outside the workspace."""
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        run_suite(workspace, _QUIET, _fake_env())
        assert _git(workspace, "status", "--short") == ""
        assert not (workspace / "grading_plugin.py").exists()


def test_run_suite_times_out_without_leaking_the_child(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        (workspace / "tests" / "test_slow.py").write_text(
            "import time\n\n\ndef test_slow():\n    time.sleep(60)\n"
        )
        result = run_suite(workspace, _QUIET, _fake_env(), timeout=3.0)
    assert result.timed_out is True
    assert result.reason_class == "timeout"
    assert result.wall_seconds >= 3.0
