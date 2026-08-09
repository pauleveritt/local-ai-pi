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

import json
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
    _write(source, "src/pkg/__init__.py", "LOCATION = 'config'\nCASES = [1, 2, 3]\n")
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
    # Parametrised over a production constant, so a production edit can
    # make real test nodes disappear while the suite still exits 0.
    _write(
        source,
        "tests/test_cases.py",
        "import pytest\n\nfrom pkg import CASES\n\n\n"
        "@pytest.mark.parametrize('case', CASES)\ndef test_case(case):\n    assert case\n",
    )
    _git(source, "add", "-A")
    _git(source, "commit", "-q", "--no-gpg-sign", "-m", "base")
    base_sha = _git(source, "rev-parse", "HEAD")

    _write(
        source, "src/pkg/__init__.py", "LOCATION = 'extensions'\nCASES = [1, 2, 3]\n"
    )
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
    # grade_candidate reads base/target scores and the preservation node
    # inventory from the task's own qualification record, so the fixture
    # produces a real one. It is deterministic and takes milliseconds on
    # this repository.
    from harness.workload import qualify

    report = qualify(load_manifest(task_dir), clone, _fake_env())
    assert report["status"] == "qualified", report
    (task_dir / "qualification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True)
    )
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
        relocating_task,
        {"src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\n"},
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
        {
            "src/pkg/__init__.py": "# started on this\nLOCATION = 'config'\nCASES = [1, 2, 3]\n"
        },
    )
    assert not attempt.accepted
    assert attempt.outcome == "no-progress"
    assert attempt.oracle_delta == 0
    assert attempt.preservation is not None
    assert attempt.preservation.reason_class == "pass"


def test_a_candidate_that_breaks_something_else_is_preservation_broken(
    relocating_task: Task,
) -> None:
    """Feature works, repository damaged -- the failure this all exists for."""
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\n\n\ndef boom():\n    raise SystemExit(1)\n",
            "tests/test_other.py": "from pkg import boom\n\n\ndef test_other():\n    boom()\n",
        },
    )
    assert not attempt.accepted
    assert attempt.outcome in {"preservation-broken", "out-of-scope"}


def test_writing_outside_scope_is_recorded(relocating_task: Task) -> None:
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\n",
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
    # Graded, not short-circuited: a candidate that wrote nothing still
    # has a base score and a delta of zero, which is what makes it
    # comparable with one that wrote something useless.
    assert attempt.oracle is not None
    assert attempt.oracle_delta == 0


def test_grading_the_same_candidate_twice_agrees(relocating_task: Task) -> None:
    """Replay must be deterministic, or re-scoring proves nothing."""
    files = {"src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\n"}
    first, second = _grade(relocating_task, files), _grade(relocating_task, files)
    assert first.outcome == second.outcome
    assert first.accepted == second.accepted


def test_a_patch_that_does_not_apply_is_an_error(relocating_task: Task) -> None:
    with (
        materialize(relocating_task.clone, relocating_task.base_sha) as workspace,
        pytest.raises(WorkloadError, match="did not apply"),
    ):
        apply_candidate(workspace, "not a patch at all\n")


def test_a_comment_only_edit_scores_zero_delta_and_green_preservation(
    relocating_task: Task,
) -> None:
    """The conformance control both reviews demanded.

    A production edit that changes no behaviour must score delta 0 with
    preservation green. Under rule 3 the equivalent candidate on
    suppress-context-exit graded "broke-and-damaged", because a root
    conftest.py listed in oracle.files still loaded as a pytest plugin
    however hard preservation --ignore'd it.
    """
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": "# a harmless comment\nLOCATION = 'config'\nCASES = [1, 2, 3]\n"
        },
    )
    assert attempt.oracle_delta == 0
    assert attempt.preservation is not None
    assert attempt.preservation.reason_class == "pass"
    assert attempt.outcome == "no-progress"


def test_the_exact_target_patch_closes_the_whole_gap(relocating_task: Task) -> None:
    """The positive control: the real answer must score a full gap closure."""
    attempt = _grade(
        relocating_task,
        {"src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\n"},
    )
    assert attempt.accepted
    assert attempt.gap_closed == 1.0
    assert attempt.oracle_delta > 0


def test_model_written_tests_cannot_affect_grading(relocating_task: Task) -> None:
    """A candidate must not be able to grade itself.

    The scratch test here fails loudly. It is recorded as out-of-scope
    and never executed, so preservation stays green -- otherwise a model
    could damage its own score by writing junk, or inflate it by writing
    a passing test over the oracle's name.
    """
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\n",
            "tests/test_scratch.py": "def test_scratch():\n    assert False\n",
        },
    )
    assert "tests/test_scratch.py" in attempt.out_of_scope
    assert attempt.preservation is not None
    assert attempt.preservation.reason_class == "pass"
    assert attempt.oracle_delta > 0


def test_a_model_created_commit_is_still_captured(relocating_task: Task) -> None:
    """Captured against the base commit, not HEAD.

    The workspace is a real repository and a model with a shell can
    commit in it. Diffed against HEAD that produces an empty patch, and
    real work would be recorded as "no changes written".
    """
    from harness.screen import capture_candidate

    with materialize(relocating_task.clone, relocating_task.base_sha) as workspace:
        (workspace / "src" / "pkg" / "__init__.py").write_text(
            "LOCATION = 'extensions'\n"
        )
        subprocess.run(
            ["git", "add", "-A"], cwd=workspace, capture_output=True, env=GIT_ENV
        )
        subprocess.run(
            ["git", "commit", "-q", "--no-gpg-sign", "-m", "model commit"],
            cwd=workspace,
            capture_output=True,
            env=GIT_ENV,
        )
        patch = capture_candidate(workspace)
    assert "LOCATION = 'extensions'" in patch


def test_a_vanished_test_is_caught_by_the_node_inventory(relocating_task: Task) -> None:
    """Tests that silently disappear must not pass as preservation.

    Exit code zero means "nothing that ran failed", which a candidate can
    satisfy by making tests stop existing. The inventory is checked
    against the frozen qualification record.
    """
    attempt = _grade(
        relocating_task,
        {"src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1]\n"},
    )
    assert attempt.missing_nodes
    assert attempt.outcome == "tests-vanished"
    assert not attempt.accepted


def test_a_shifted_position_keyed_node_is_not_a_vanished_test() -> None:
    """Sybil node ids are positions, not names, and positions move.

    svcs runs its README and docstrings through Sybil, which ids nodes as
    `path::line:N,column:M`. Inserting one production line renames every
    node below it. Matching those by identity failed the *target's own
    diff* on four of nine tasks -- a rule that rejects the reference
    answer rejects every correct answer.
    """
    from harness.screen import _node_census, _vanished

    expected_stable, expected_counts = _node_census(
        [
            "tests/test_core.py::test_one",
            "src/pkg/_core.py::line:128,column:1",
            "src/pkg/_core.py::line:155,column:1",
        ]
    )
    assert expected_counts == {"src/pkg/_core.py": 2}

    shifted = [
        "tests/test_core.py::test_one",
        "src/pkg/_core.py::line:132,column:1",
        "src/pkg/_core.py::line:159,column:1",
    ]
    assert _vanished(expected_stable, expected_counts, shifted) == ()


def test_a_deleted_position_keyed_node_is_still_caught() -> None:
    """Counting must not become a way to delete doctests for free."""
    from harness.screen import _node_census, _vanished

    expected_stable, expected_counts = _node_census(
        ["src/pkg/_core.py::line:128,column:1", "src/pkg/_core.py::line:155,column:1"]
    )
    vanished = _vanished(
        expected_stable, expected_counts, ["src/pkg/_core.py::line:132,column:1"]
    )
    assert vanished == ("src/pkg/_core.py::position-keyed 1/2",)


def test_a_named_node_still_vanishes_by_name() -> None:
    """Named nodes keep identity comparison; only positions are counted."""
    from harness.screen import _node_census, _vanished

    expected_stable, expected_counts = _node_census(
        ["tests/test_core.py::test_one", "tests/test_core.py::test_two"]
    )
    assert _vanished(expected_stable, expected_counts, ["tests/test_core.py::test_one"]) == (
        "tests/test_core.py::test_two",
    )


def test_the_executor_venv_never_reaches_the_candidate_patch(
    relocating_task: Task,
) -> None:
    """A provisioned environment must be invisible to capture.

    `capture_candidate` diffs `git add -A` against the base commit, so a
    workspace venv would arrive in the patch as tens of thousands of
    site-packages files -- and then be applied to the graded
    materialisations. `.git/info/exclude` keeps it out without touching
    the tree, which a committed `.gitignore` would not.
    """
    from harness.screen import capture_candidate, provision_executor_env

    env_source = relocating_task.clone.parent / "envsrc"
    env_source.mkdir(exist_ok=True)
    (env_source / "pyproject.toml").write_text(
        '[project]\nname = "probe-env"\nversion = "0"\n'
        'requires-python = ">=3.10"\ndependencies = []\n'
    )
    subprocess.run(["uv", "lock", "-q"], cwd=env_source, check=True, capture_output=True)

    with materialize(relocating_task.clone, relocating_task.base_sha) as workspace:
        lock_hash = provision_executor_env(workspace, env_source)
        assert (workspace / ".venv" / "bin" / "python").is_file()

        # The real edit still has to survive alongside it.
        (workspace / "src" / "pkg" / "__init__.py").write_text(
            "LOCATION = 'extensions'\nCASES = [1, 2, 3]\n"
        )
        patch = capture_candidate(workspace)

    assert ".venv" not in patch
    assert "LOCATION = 'extensions'" in patch
    assert len(lock_hash) == 64
