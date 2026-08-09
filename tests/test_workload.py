import json
import platform
import shutil
import subprocess
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pytest

import harness.workload as workload_module
from harness.workload import (
    CohortEnv,
    SuiteResult,
    WorkloadError,
    _verify_interpreter,
    ensure_clone,
    ensure_cohort_env,
    export_tree,
    load_cohort,
    load_manifest,
    materialize,
    overlay_oracle,
    qualify,
    run_suite,
    sha256_file,
)
from harness.workspace import GIT_ENV
from tools.qualify_workload import main as qualify_main


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
    assert result.outcomes == {"tests/test_add.py::test_add": "call:passed"}


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
    assert any("mul" in message for message in result.collection_errors.values())


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
    assert result.outcomes["tests/test_wrong.py::test_wrong"] == "call:failed"


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


def _write_manifest(task_dir: Path, clone: SyntheticClone, **overrides: str) -> Path:
    """A synthetic task manifest. Overrides let a test break exactly one field."""
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "brief.md").write_text("Add a mul function.\n")
    brief_sha = overrides.get("brief_sha256") or sha256_file(task_dir / "brief.md")
    body = f"""task_id = "{overrides.get("task_id", task_dir.name)}"
role = "floor"
axes = ["arithmetic"]

[source]
upstream = "{clone.bare}"
base_sha = "{overrides.get("base_sha", clone.base_sha)}"
target_sha = "{clone.target_sha}"

[task]
brief = "brief.md"
brief_sha256 = "{brief_sha}"
contract_version = 1

[policy]
readable = ["src/**", "tests/**"]
writable = ["{overrides.get("writable", "src/pkg/**")}"]
candidate_output = ["src/pkg/__init__.py"]

[oracle]
files = ["tests/test_mul.py"]
command = ["pytest", "-q", "-p", "no:cacheprovider", "tests/test_mul.py"]

[oracle.rejection]
class           = "{overrides.get("rejection_class", "collection-error")}"
missing_symbols = [{overrides.get("missing_symbols", '"mul"')}]
failing_nodes   = []

[oracle.files_sha256]
"tests/test_mul.py" = "{overrides.get("oracle_sha", "")}"

[preservation]
command = ["pytest", "-q", "-p", "no:cacheprovider"]
deselects = []
deselect_reason = ""

[environment]
id = "synthetic-env"
python = "{overrides.get("env_python", platform.python_version())}"
lock_sha256 = "{overrides.get("lock_sha256", "synthetic")}"

[attestations]
behavior_not_structure = "The oracle calls the public function."
statable_behaviorally = "{overrides.get("statable", "Multiply two numbers.")}"
substantive = "Adds a new public behavior."
writable_bounded = "One module."
adaptations = "None."
"""
    (task_dir / "manifest.toml").write_text(body)
    return task_dir


def _manifest_with_real_oracle_hash(
    tmp_path: Path, clone: SyntheticClone
) -> tuple[Path, Path]:
    bare = ensure_clone(str(clone.bare), tmp_path / "cache")
    export = tmp_path / "export"
    export_tree(bare, clone.target_sha, export)
    oracle_sha = sha256_file(export / "tests" / "test_mul.py")
    task_dir = _write_manifest(
        tmp_path / "tasks" / "synthetic", clone, oracle_sha=oracle_sha
    )
    return task_dir, bare


def test_load_manifest_reads_every_field(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir, _ = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    manifest = load_manifest(task_dir)
    assert manifest.task_id == "synthetic"
    assert manifest.role == "floor"
    assert manifest.base_sha == synthetic_clone.base_sha
    assert manifest.base_rejection == "collection-error"
    assert manifest.rejection_missing_symbols == ("mul",)
    assert manifest.rejection_failing_nodes == ()
    assert manifest.oracle_files == ("tests/test_mul.py",)
    assert manifest.preservation_command == ("pytest", "-q", "-p", "no:cacheprovider")
    assert manifest.attestations["substantive"]


def test_load_manifest_rejects_a_drifted_brief(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = _write_manifest(
        tmp_path / "tasks" / "s", synthetic_clone, brief_sha256="0" * 64
    )
    with pytest.raises(WorkloadError, match="brief.md"):
        load_manifest(task_dir)


def test_load_manifest_rejects_an_unknown_reason_class(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = _write_manifest(
        tmp_path / "tasks" / "s", synthetic_clone, rejection_class="nonsense"
    )
    with pytest.raises(WorkloadError, match="oracle.rejection.class"):
        load_manifest(task_dir)


def test_load_manifest_refuses_pass_as_a_rejection(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = _write_manifest(
        tmp_path / "tasks" / "s", synthetic_clone, rejection_class="pass"
    )
    with pytest.raises(WorkloadError, match="cannot be 'pass'"):
        load_manifest(task_dir)


def test_load_manifest_requires_a_rejection_fingerprint(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """A bare class cannot tell a real task from a typo'd oracle."""
    task_dir = _write_manifest(
        tmp_path / "tasks" / "s", synthetic_clone, missing_symbols=""
    )
    with pytest.raises(WorkloadError, match="missing_symbols or failing_nodes"):
        load_manifest(task_dir)


def test_load_manifest_requires_every_attestation(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = _write_manifest(
        tmp_path / "tasks" / "s", synthetic_clone, statable="   "
    )
    with pytest.raises(WorkloadError, match="statable_behaviorally"):
        load_manifest(task_dir)


def test_load_manifest_rejects_an_abbreviated_sha(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """A short SHA is not immutable -- it can become ambiguous as history grows."""
    task_dir = _write_manifest(
        tmp_path / "tasks" / "s", synthetic_clone, base_sha=synthetic_clone.base_sha[:7]
    )
    with pytest.raises(WorkloadError, match="40-character"):
        load_manifest(task_dir)


def test_load_manifest_rejects_an_absolute_policy_path(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = _write_manifest(
        tmp_path / "tasks" / "s", synthetic_clone, writable="/etc/**"
    )
    with pytest.raises(WorkloadError, match="repository-relative"):
        load_manifest(task_dir)


def test_load_manifest_rejects_a_parent_traversal_policy_path(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = _write_manifest(
        tmp_path / "tasks" / "s", synthetic_clone, writable="../elsewhere/**"
    )
    with pytest.raises(WorkloadError, match="repository-relative"):
        load_manifest(task_dir)


def test_overlay_oracle_places_the_hidden_tests(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    manifest = load_manifest(task_dir)
    with materialize(bare, manifest.base_sha) as workspace:
        assert not (workspace / "tests" / "test_mul.py").exists()
        overlay_oracle(bare, manifest, workspace)
        assert (workspace / "tests" / "test_mul.py").is_file()


def test_overlay_oracle_rejects_a_drifted_oracle(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Drift is an error, never a silent re-baseline."""
    task_dir = _write_manifest(
        tmp_path / "tasks" / "s", synthetic_clone, oracle_sha="0" * 64
    )
    manifest = load_manifest(task_dir)
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with (
        materialize(clone, manifest.base_sha) as workspace,
        pytest.raises(WorkloadError, match="drift"),
    ):
        overlay_oracle(clone, manifest, workspace)


def test_overlay_oracle_requires_a_recorded_hash(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = _write_manifest(tmp_path / "tasks" / "s", synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace('"tests/test_mul.py" = ""', "")
    )
    manifest = load_manifest(task_dir)
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with (
        materialize(clone, manifest.base_sha) as workspace,
        pytest.raises(WorkloadError, match="no recorded hash"),
    ):
        overlay_oracle(clone, manifest, workspace)


def _condition_of(report: dict[str, object], key: str) -> dict[str, object]:
    """`qualify` returns a JSON-shaped dict[str, object]; narrow before indexing."""
    conditions = report["conditions"]
    assert isinstance(conditions, dict)
    value = conditions[key]
    assert isinstance(value, dict)
    return value


def test_qualify_accepts_a_well_formed_task(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
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
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    for condition in (
        "base_preservation",
        "base_oracle",
        "target_preservation",
        "target_oracle",
    ):
        assert _condition_of(report, condition)["runs"] == 3


def test_qualify_uses_a_fresh_materialization_per_run(
    tmp_path: Path, synthetic_clone: SyntheticClone, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Repeating inside one workspace measures idempotence, not determinism."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    seen: list[Path] = []
    original = materialize

    @contextmanager
    def counting(clone_path: Path, sha: str) -> Iterator[Path]:
        with original(clone_path, sha) as workspace:
            seen.append(workspace)
            yield workspace

    monkeypatch.setattr(workload_module, "materialize", counting)
    qualify(load_manifest(task_dir), bare, _fake_env())
    assert len(seen) == 12
    assert len(set(seen)) == 12


def test_qualify_disqualifies_a_wrong_reason_class(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """The import-typo case: the base is rejected, but not for the declared reason."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace(
            'class           = "collection-error"',
            'class           = "assertion-failure"',
        )
    )
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "base_rejection"


def test_qualify_disqualifies_a_missing_expected_symbol(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """The class matched, but not for the reason the manifest pre-registered."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
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

    The flaky module keys off a marker kept OUTSIDE the workspace --
    fresh materializations mean anything written inside one is gone by
    the next run, which is exactly the property being tested.
    """
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
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
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    report = qualify(load_manifest(task_dir), bare, _fake_env(), max_seconds=0.0)
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "runtime"


def test_qualify_refuses_a_mismatched_environment(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """A manifest naming a different lock must not be graded against this one."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace('lock_sha256 = "synthetic"', 'lock_sha256 = "deadbeef"')
    )
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "environment"


def test_qualification_records_provenance(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Evidence must name the exact manifest and environment it came from."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["manifest_sha256"] == sha256_file(task_dir / "manifest.toml")
    assert report["env_python"] == platform.python_version()
    assert report["base_sha"] == synthetic_clone.base_sha
    assert report["target_sha"] == synthetic_clone.target_sha


def test_a_suite_using_tmp_path_leaves_the_workspace_clean(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Regression: TMPDIR once pointed into the workspace.

    Any real suite touching `tmp_path` then left `pytest-of-<user>/`
    behind, which the later cycle that diffs a workspace to find
    candidate output would read as model changes. The synthetic suite
    never used tmp_path, so the byte-identical test passed anyway.
    """
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        (workspace / "tests" / "test_tmp.py").write_text(
            "def test_tmp(tmp_path):\n    (tmp_path / 'x').write_text('x')\n"
        )
        (workspace / "tests" / "test_home.py").write_text(
            "import pathlib\n\n\ndef test_home():\n"
            "    (pathlib.Path.home() / 'dropped').write_text('x')\n"
        )
        result = run_suite(workspace, _QUIET, _fake_env())
        assert result.reason_class == "pass"
        dirt = [
            line
            for line in _git(workspace, "status", "--short").splitlines()
            if "test_tmp.py" not in line and "test_home.py" not in line
        ]
    assert dirt == []


def test_materialized_mtimes_carry_no_commit_timestamp(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """`git archive` stamps each file with the commit time.

    That identifies the base in public history nearly as precisely as
    the SHA `_undo_export_subst` strips -- the same provenance channel
    in different clothes.
    """
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    commit_epoch = int(
        _git(clone, "show", "-s", "--format=%ct", synthetic_clone.base_sha)
    )
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        mtimes = {
            p.stat().st_mtime for p in workspace.rglob("*") if ".git" not in p.parts
        }
        assert mtimes, "expected files in the workspace"
        assert commit_epoch not in mtimes
        assert mtimes == {float(workload_module._FIXED_MTIME)}


def test_qualify_checks_the_rejection_fingerprint_on_every_repeat(
    tmp_path: Path, synthetic_clone: SyntheticClone, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The rejection fingerprint is checked on every repeat, not just the first.

    The motivating hazard: a collection error records no nodes, so its
    fingerprint is ("collection-error", 2, ()) and the stability gate
    cannot tell two collection errors apart by cause.

    What this test actually pins down is narrower and worth stating. The
    sabotage here changes the reason class too, so *stability* would also
    catch it -- but it would report `failed_gate == "stability"`, naming
    the wrong problem. With the per-repeat check the run is attributed to
    `base_rejection` and names which repeat diverged. Constructing a true
    same-class-different-cause collision synthetically is awkward, since
    overlay_oracle rewrites the oracle file after any sabotage; that case
    is argued from the fingerprint's shape rather than demonstrated.
    """
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    calls = {"n": 0}
    original = materialize

    @contextmanager
    def sabotage_later_runs(clone_path: Path, sha: str) -> Iterator[Path]:
        with original(clone_path, sha) as workspace:
            if sha == synthetic_clone.base_sha:
                calls["n"] += 1
                # Runs 4 and 5 are base_oracle's second and third; break
                # them for a reason that is NOT the pre-registered symbol.
                if calls["n"] > 4:
                    (workspace / "conftest.py").write_text(
                        "import nonexistent_module_xyz\n"
                    )
            yield workspace

    monkeypatch.setattr(workload_module, "materialize", sabotage_later_runs)
    report = qualify(load_manifest(task_dir), bare, _fake_env())

    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "base_rejection"
    assert "run 2" in str(report["detail"])


def test_qualify_applies_declared_deselects(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """A deselect that is validated and reported but never applied is a lie."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace(
            "deselects = []", 'deselects = ["tests/test_add.py::test_add"]'
        ).replace(
            'deselect_reason = ""',
            'deselect_reason = "exercised by the oracle instead"',
        )
    )
    manifest = load_manifest(task_dir)
    report = qualify(manifest, bare, _fake_env())
    assert report["effective_preservation_command"] == [
        *manifest.preservation_command,
        "--deselect",
        "tests/test_add.py::test_add",
    ]
    # With its only test deselected, the base suite collects nothing.
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "base_preservation"


def _write_cohort(root: Path, clone: SyntheticClone, **overrides: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "cohort.toml").write_text(
        f'''name = "synthetic"
upstream = "{clone.bare}"
env = "env"
tasks = ["synthetic"{overrides.get("extra_tasks", "")}]
included = [{overrides.get("included", "")}]

[excluded]
{overrides.get("excluded", "")}
'''
    )
    return root / "cohort.toml"


def test_load_cohort_reads_the_ladder(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    path = _write_cohort(tmp_path / "cohort", synthetic_clone)
    cohort = load_cohort(path)
    assert cohort.name == "synthetic"
    assert cohort.tasks == ("synthetic",)
    assert cohort.unaccounted == ("synthetic",)


def test_load_cohort_rejects_an_exclusion_without_a_reason(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """An exclusion without prose is indistinguishable from a forgotten task."""
    path = _write_cohort(
        tmp_path / "cohort", synthetic_clone, excluded='synthetic = "   "'
    )
    with pytest.raises(WorkloadError, match="no reason"):
        load_cohort(path)


def test_load_cohort_rejects_an_unknown_task(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    path = _write_cohort(tmp_path / "cohort", synthetic_clone, included='"ghost"')
    with pytest.raises(WorkloadError, match="not in the candidate ladder"):
        load_cohort(path)


def test_load_cohort_rejects_a_task_both_included_and_excluded(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    path = _write_cohort(
        tmp_path / "cohort",
        synthetic_clone,
        included='"synthetic"',
        excluded='synthetic = "changed my mind"',
    )
    with pytest.raises(WorkloadError, match="both included and excluded"):
        load_cohort(path)


def test_a_frozen_cohort_must_account_for_every_candidate(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """The freeze check: a candidate in neither list is a gap in the record."""
    path = _write_cohort(
        tmp_path / "cohort", synthetic_clone, extra_tasks=', "forgotten"'
    )
    load_cohort(path)  # fine during curation
    with pytest.raises(WorkloadError, match="does not account for"):
        load_cohort(path, require_accounting=True)


def test_cli_writes_a_qualification_report(
    tmp_path: Path, synthetic_clone: SyntheticClone, monkeypatch: pytest.MonkeyPatch
) -> None:
    task_dir, _ = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    cohort_root = tmp_path / "cohort"
    (cohort_root / "tasks").mkdir(parents=True)
    shutil.copytree(task_dir, cohort_root / "tasks" / "synthetic")
    _write_cohort(cohort_root, synthetic_clone)

    monkeypatch.setattr(
        workload_module, "ensure_cohort_env", lambda *a, **k: _fake_env()
    )
    exit_code = qualify_main(
        [
            "--cohort",
            str(cohort_root / "cohort.toml"),
            "--cache",
            str(tmp_path / "cache"),
        ]
    )
    assert exit_code == 0

    report = json.loads(
        (cohort_root / "tasks" / "synthetic" / "qualification.json").read_text()
    )
    assert report["status"] == "qualified"


def test_cli_records_a_task_whose_manifest_will_not_load(
    tmp_path: Path, synthetic_clone: SyntheticClone, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unreadable task must not be quieter than a failing one."""
    cohort_root = tmp_path / "cohort"
    (cohort_root / "tasks" / "synthetic").mkdir(parents=True)
    _write_cohort(cohort_root, synthetic_clone)

    monkeypatch.setattr(
        workload_module, "ensure_cohort_env", lambda *a, **k: _fake_env()
    )
    exit_code = qualify_main(
        [
            "--cohort",
            str(cohort_root / "cohort.toml"),
            "--cache",
            str(tmp_path / "cache"),
        ]
    )
    assert exit_code == 1

    report = json.loads(
        (cohort_root / "tasks" / "synthetic" / "qualification.json").read_text()
    )
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "manifest"


def test_a_setup_failure_is_not_an_assertion_failure(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """A missing fixture must not satisfy a task declaring assertion-failure.

    Both arrive from pytest as `failed`; only the phase distinguishes a
    test that ran and was wrong from one that never ran at all.
    """
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        (workspace / "tests" / "test_fixture.py").write_text(
            "def test_needs(nonexistent_fixture):\n    assert True\n"
        )
        result = run_suite(workspace, _QUIET, _fake_env())
    assert result.outcomes["tests/test_fixture.py::test_needs"] == "setup:failed"
    assert result.reason_class == "error"


def test_collection_errors_are_recorded_with_their_exception(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    with materialize(clone, synthetic_clone.base_sha) as workspace:
        (workspace / "tests" / "test_mul.py").write_text("from pkg import mul\n")
        result = run_suite(workspace, _QUIET, _fake_env())
    assert result.reason_class == "collection-error"
    (message,) = result.collection_errors.values()
    assert "mul" in message


def test_collection_error_messages_carry_no_workspace_path(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Otherwise every collection-error task is spuriously unstable.

    Each run gets a fresh materialization under a new temp directory, so
    an unnormalised message differs on every run and the fingerprint
    would disqualify the task for a difference carrying no information.
    """
    clone = ensure_clone(str(synthetic_clone.bare), tmp_path / "cache")
    fingerprints = set()
    for _ in range(2):
        with materialize(clone, synthetic_clone.base_sha) as workspace:
            (workspace / "tests" / "test_mul.py").write_text("from pkg import mul\n")
            result = run_suite(workspace, _QUIET, _fake_env())
            assert str(workspace) not in " ".join(result.collection_errors.values())
        fingerprints.add(result.fingerprint_sha256)
    assert len(fingerprints) == 1


def test_qualify_refuses_fewer_than_three_repeats(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """One run makes every task trivially stable, and still says "qualified"."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    with pytest.raises(WorkloadError, match="minimum"):
        qualify(load_manifest(task_dir), bare, _fake_env(), repeats=1)


def test_qualify_refuses_a_raised_time_ceiling(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    with pytest.raises(WorkloadError, match="ceiling"):
        qualify(load_manifest(task_dir), bare, _fake_env(), max_seconds=600.0)


def test_qualify_refuses_a_mismatched_interpreter(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Always compared -- not opt-in behind a flag someone must remember."""
    task_dir, bare = _manifest_with_real_oracle_hash(tmp_path, synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace(f'python = "{platform.python_version()}"', 'python = "3.99.0"')
    )
    report = qualify(load_manifest(task_dir), bare, _fake_env())
    assert report["status"] == "disqualified"
    assert report["failed_gate"] == "environment"
    assert "3.99.0" in str(report["detail"])


def _suite_result(
    reason_class: str,
    outcomes: dict[str, str],
    collection_errors: dict[str, str] | None = None,
    returncode: int = 1,
) -> SuiteResult:
    """A hand-built SuiteResult, so the pure matcher can be tested directly."""
    return SuiteResult(
        returncode=returncode,
        reason_class=reason_class,
        outcomes=outcomes,
        collection_errors=collection_errors or {},
        tests_passed=sum(1 for o in outcomes.values() if o.endswith(":passed")),
        wall_seconds=0.1,
        timed_out=False,
        stdout_tail="",
        output="",
    )


def test_rejection_matches_when_the_failures_are_exactly_declared(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = _write_manifest(tmp_path / "tasks" / "s", synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace(
            'class           = "collection-error"',
            'class           = "assertion-failure"',
        )
        .replace('missing_symbols = ["mul"]', "missing_symbols = []")
        .replace("failing_nodes   = []", 'failing_nodes   = ["a::one"]')
    )
    manifest = load_manifest(task_dir)
    observed = _suite_result(
        "assertion-failure", {"a::one": "call:failed", "b::two": "call:passed"}
    )
    assert workload_module._rejection_mismatch(manifest, observed) is None


def test_rejection_refuses_an_undeclared_extra_failure(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """Exact equality, not a subset.

    A base failing the declared node AND an unrelated one is not the
    task the manifest describes; admitting it would let unrelated
    breakage ride along inside a qualified task.
    """
    task_dir = _write_manifest(tmp_path / "tasks" / "s", synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace(
            'class           = "collection-error"',
            'class           = "assertion-failure"',
        )
        .replace('missing_symbols = ["mul"]', "missing_symbols = []")
        .replace("failing_nodes   = []", 'failing_nodes   = ["a::one"]')
    )
    manifest = load_manifest(task_dir)
    observed = _suite_result(
        "assertion-failure", {"a::one": "call:failed", "b::two": "call:failed"}
    )
    detail = workload_module._rejection_mismatch(manifest, observed)
    assert detail is not None
    assert "unexpected=['b::two']" in detail


def test_rejection_refuses_a_symbol_absent_from_the_collection_failure(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """A symbol echoed in stdout proves nothing about what caused the error.

    The declared symbol must appear in the recorded collection failure
    itself, not merely somewhere in pytest's output.
    """
    task_dir = _write_manifest(tmp_path / "tasks" / "s", synthetic_clone)
    manifest = load_manifest(task_dir)  # declares missing_symbols = ["mul"]
    observed = _suite_result(
        "collection-error",
        {},
        collection_errors={
            "tests/test_mul.py": "ImportError: cannot import name 'other'"
        },
        returncode=2,
    )
    detail = workload_module._rejection_mismatch(manifest, observed)
    assert detail is not None
    assert "mul" in detail


def test_rejection_refuses_missing_symbols_with_no_collection_failure(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = _write_manifest(tmp_path / "tasks" / "s", synthetic_clone)
    manifest = load_manifest(task_dir)
    observed = _suite_result("collection-error", {}, collection_errors={}, returncode=2)
    detail = workload_module._rejection_mismatch(manifest, observed)
    assert detail is not None
    assert "no collection failure" in detail


def test_load_manifest_requires_a_nonblank_lock_hash(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    """A blank hash accepts whatever environment is present -- not a freeze."""
    task_dir = _write_manifest(
        tmp_path / "tasks" / "s", synthetic_clone, lock_sha256=""
    )
    with pytest.raises(WorkloadError, match="must be a real hash"):
        load_manifest(task_dir)


def test_load_manifest_requires_task_id_to_match_its_directory(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = _write_manifest(
        tmp_path / "tasks" / "s", synthetic_clone, task_id="elsewhere"
    )
    with pytest.raises(WorkloadError, match="does not match its directory"):
        load_manifest(task_dir)


def test_load_manifest_rejects_an_absolute_oracle_path(
    tmp_path: Path, synthetic_clone: SyntheticClone
) -> None:
    task_dir = _write_manifest(tmp_path / "tasks" / "s", synthetic_clone)
    text = (task_dir / "manifest.toml").read_text()
    (task_dir / "manifest.toml").write_text(
        text.replace('files = ["tests/test_mul.py"]', 'files = ["/etc/passwd"]')
    )
    with pytest.raises(WorkloadError, match="repository-relative"):
        load_manifest(task_dir)
