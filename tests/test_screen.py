"""The acceptance rule, tested against synthetic candidates.

Every grading defect this harness has had was found by a real task
tripping it, after a sweep of model calls had already been paid for.
Three times: preservation graded against the wrong test files;
preservation graded against the oracle's own tests; and before those, an
acceptance rule that could not recognise a correct answer.

These fixtures are the cheap check that should have come first. Each is
a candidate patch representing one archetype, graded offline in
milliseconds against a synthetic repository. If the acceptance rule
cannot score these correctly, it cannot score a real sweep -- and
finding that out here costs nothing.
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from harness.screen import ENVELOPE_TOOLS, apply_candidate, grade_candidate
from harness.workload import (
    CohortEnv,
    WorkloadError,
    ensure_clone,
    load_manifest,
    materialize,
    sha256_file,
)
from harness.workspace import GIT_ENV
from tests.test_workload import _git, _write


def _fake_env() -> CohortEnv:
    import platform
    import sys

    return CohortEnv(
        python=Path(sys.executable),
        lock_sha256="synthetic",
        python_version=platform.python_version(),
        platform=sys.platform,
    )


@dataclass(frozen=True)
class Task:
    manifest_dir: Path
    clone: Path
    base_sha: str


@pytest.fixture
def relocating_task(tmp_path: Path) -> Task:
    """A task whose target CHANGES an existing test's expectations.

    This is the `flask-extensions` archetype, and it is the one that
    exposed two of the three defects: a correct implementation must make
    the oracle pass *and* must break the base's own version of the test
    it updates. Any rule that scores those base tests against the
    candidate calls correct work "repository damage".
    """
    source = tmp_path / "source"
    source.mkdir()
    _git(source, "init", "-q")
    _write(source, "src/pkg/__init__.py", "LOCATION = 'config'\n")
    _write(
        source,
        "tests/test_where.py",
        "from pkg import LOCATION\n\n\ndef test_where():\n    assert LOCATION == 'config'\n",
    )
    _write(
        source,
        "tests/test_other.py",
        "def test_other():\n    assert True\n",
    )
    _git(source, "add", "-A")
    _git(source, "commit", "-q", "--no-gpg-sign", "-m", "base")
    base_sha = _git(source, "rev-parse", "HEAD")

    _write(source, "src/pkg/__init__.py", "LOCATION = 'extensions'\n")
    _write(
        source,
        "tests/test_where.py",
        "from pkg import LOCATION\n\n\ndef test_where():\n    assert LOCATION == 'extensions'\n",
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
    clone = ensure_clone(str(bare), tmp_path / "cache")

    task_dir = tmp_path / "tasks" / "relocate"
    task_dir.mkdir(parents=True)
    (task_dir / "brief.md").write_text("Move LOCATION from 'config' to 'extensions'.\n")

    export = tmp_path / "export"
    from harness.workload import export_tree

    export_tree(clone, target_sha, export)
    oracle_sha = sha256_file(export / "tests" / "test_where.py")

    (task_dir / "manifest.toml").write_text(f"""task_id = "relocate"
role = "medium"
axes = ["relocation"]

[source]
upstream = "{bare}"
base_sha = "{base_sha}"
target_sha = "{target_sha}"

[task]
brief = "brief.md"
brief_sha256 = "{sha256_file(task_dir / "brief.md")}"
contract_version = 1

[policy]
readable = ["src/**", "tests/**"]
writable = ["src/pkg/**"]
candidate_output = ["src/pkg/__init__.py"]

[oracle]
files = ["tests/test_where.py"]
command = ["pytest", "-q", "-p", "no:cacheprovider", "tests/test_where.py"]

[oracle.rejection]
class = "assertion-failure"
missing_symbols = []
failing_nodes = ["tests/test_where.py::test_where"]

[oracle.files_sha256]
"tests/test_where.py" = "{oracle_sha}"

[preservation]
command = ["pytest", "-q", "-p", "no:cacheprovider"]
deselects = []
deselect_reason = ""

[environment]
id = "synthetic"
python = "{_fake_env().python_version}"
lock_sha256 = "synthetic"

[attestations]
behavior_not_structure = "public constant"
statable_behaviorally = "where the value lives"
substantive = "changes an observable value"
writable_bounded = "one module"
adaptations = "none"
""")
    return Task(task_dir, clone, base_sha)


def _candidate(task: Task, files: dict[str, str]) -> str:
    """Build a candidate patch by writing files into a fresh base."""
    with materialize(task.clone, task.base_sha) as workspace:
        for relative, text in files.items():
            path = workspace / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        subprocess.run(
            ["git", "add", "-A"], cwd=workspace, capture_output=True, env=GIT_ENV
        )
        return subprocess.run(
            ["git", "diff", "--cached", "--binary"],
            cwd=workspace,
            capture_output=True,
            text=True,
            env=GIT_ENV,
        ).stdout


def _grade(task: Task, files: dict[str, str]):
    manifest = load_manifest(task.manifest_dir)
    return grade_candidate(
        manifest, task.clone, _fake_env(), _candidate(task, files), tools=ENVELOPE_TOOLS
    )


def test_a_correct_relocation_is_accepted(relocating_task: Task) -> None:
    """The archetype that two wrong rules rejected.

    The candidate is correct. It necessarily contradicts the base's own
    test_where.py, which the target commit updates -- so a rule that
    grades preservation against base tests calls this damage.
    """
    attempt = _grade(
        relocating_task, {"src/pkg/__init__.py": "LOCATION = 'extensions'\n"}
    )
    assert attempt.accepted, attempt.outcome
    assert attempt.outcome == "accepted"


def test_an_unfinished_candidate_fails_the_oracle_not_preservation(
    relocating_task: Task,
) -> None:
    """The archetype the *third* wrong rule mislabelled.

    Nothing else is broken here -- the feature simply is not done. If
    preservation includes the oracle's own tests, this reports as
    "preservation-broken" and reads as repository damage.

    The candidate has to *change* something while leaving the behaviour
    wrong; a byte-identical file is "no-changes", which is a different
    archetype with its own test.
    """
    attempt = _grade(
        relocating_task,
        {"src/pkg/__init__.py": "# started on this\nLOCATION = 'config'\n"},
    )
    assert not attempt.accepted
    assert attempt.outcome == "oracle-failed"
    assert attempt.preservation is not None
    assert attempt.preservation.reason_class == "pass"


def test_a_candidate_that_breaks_something_else_is_preservation_broken(
    relocating_task: Task,
) -> None:
    """Feature works, repository damaged -- the failure this all exists for."""
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": "LOCATION = 'extensions'\n\n\ndef boom():\n    raise SystemExit(1)\n",
            "tests/test_other.py": "from pkg import boom\n\n\ndef test_other():\n    boom()\n",
        },
    )
    assert not attempt.accepted
    assert attempt.outcome in {"preservation-broken", "out-of-scope"}


def test_writing_outside_scope_is_recorded(relocating_task: Task) -> None:
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": "LOCATION = 'extensions'\n",
            "list_files.py": "# a script the model wrote to look around\n",
        },
    )
    assert not attempt.accepted
    assert attempt.out_of_scope == ("list_files.py",)
    assert attempt.outcome == "out-of-scope"


def test_a_candidate_that_writes_nothing(relocating_task: Task) -> None:
    attempt = _grade(relocating_task, {})
    assert not attempt.accepted
    assert attempt.outcome == "no-changes"
    assert attempt.oracle is None


def test_grading_the_same_candidate_twice_agrees(relocating_task: Task) -> None:
    """Replay must be deterministic, or re-scoring proves nothing."""
    files = {"src/pkg/__init__.py": "LOCATION = 'extensions'\n"}
    first, second = _grade(relocating_task, files), _grade(relocating_task, files)
    assert first.outcome == second.outcome
    assert first.accepted == second.accepted


def test_a_patch_that_does_not_apply_is_an_error(relocating_task: Task) -> None:
    with (
        materialize(relocating_task.clone, relocating_task.base_sha) as workspace,
        pytest.raises(WorkloadError, match="did not apply"),
    ):
        apply_candidate(workspace, "not a patch at all\n")
