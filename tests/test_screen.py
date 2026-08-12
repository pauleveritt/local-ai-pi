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

from harness.qualification import qualify
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
    _write(
        source,
        "src/pkg/__init__.py",
        "LOCATION = 'config'\nCASES = [1, 2, 3]\nFLAG = 'on'\n",
    )
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
    # A base test whose node id does not depend on the value it asserts,
    # so a production edit can fail it without renaming anything. That is
    # what separates "damaged" from "tests-vanished".
    _write(
        source,
        "tests/test_flag.py",
        "from pkg import FLAG\n\n\ndef test_flag():\n    assert FLAG == 'on'\n",
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
        source,
        "src/pkg/__init__.py",
        "LOCATION = 'extensions'\nCASES = [1, 2, 3]\nFLAG = 'on'\n",
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


def _grade(task: Task, files: dict[str, str], test_paths: tuple[str, ...] = ()):
    manifest = load_manifest(task.manifest_dir)
    return grade_candidate(
        manifest,
        task.clone,
        _fake_env(),
        _candidate(task, files),
        tools=ENVELOPE_TOOLS,
        test_paths=test_paths,
    )


def test_a_correct_relocation_is_accepted(relocating_task: Task) -> None:
    """The archetype that two wrong rules rejected.

    The candidate is correct. It necessarily contradicts the base's own
    test_where.py, which the target commit updates -- so a rule that
    grades preservation against base tests calls this damage.
    """
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\nFLAG = 'on'\n"
        },
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
            "src/pkg/__init__.py": "# started on this\nLOCATION = 'config'\nCASES = [1, 2, 3]\nFLAG = 'on'\n"
        },
    )
    assert not attempt.accepted
    assert attempt.outcome == "no-progress"
    assert attempt.oracle_delta == 0
    assert attempt.preservation is not None
    assert attempt.preservation.reason_class == "pass"


def test_a_model_edited_test_cannot_damage_preservation(
    relocating_task: Task,
) -> None:
    """A test the model rewrote is recorded, never executed.

    The candidate rewrites `tests/test_other.py` to call code that exits
    the interpreter. Were model-authored tests executed, this would take
    the preservation suite with it -- and a candidate able to break the
    suite is also able to *fix* it, which is the self-grading hole. Rule 5
    strips test edits before both graded runs, so preservation runs the
    pristine base file and passes; the edit survives only as a recorded
    scope violation.
    """
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": (
                "LOCATION = 'extensions'\nCASES = [1, 2, 3]\nFLAG = 'on'\n\n\n"
                "def boom():\n    raise SystemExit(1)\n"
            ),
            "tests/test_other.py": "from pkg import boom\n\n\ndef test_other():\n    boom()\n",
        },
    )
    assert not attempt.accepted
    assert attempt.out_of_scope == ("tests/test_other.py",)
    assert attempt.preservation is not None
    assert attempt.preservation.reason_class == "pass"
    assert attempt.outcome == "out-of-scope"


def test_writing_outside_scope_is_recorded(relocating_task: Task) -> None:
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\nFLAG = 'on'\n",
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
    files = {
        "src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\nFLAG = 'on'\n"
    }
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
            "src/pkg/__init__.py": "# a harmless comment\nLOCATION = 'config'\nCASES = [1, 2, 3]\nFLAG = 'on'\n"
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
        {
            "src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\nFLAG = 'on'\n"
        },
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
            "src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\nFLAG = 'on'\n",
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
        {"src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1]\nFLAG = 'on'\n"},
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
    assert _vanished(
        expected_stable, expected_counts, ["tests/test_core.py::test_one"]
    ) == ("tests/test_core.py::test_two",)


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
    subprocess.run(
        ["uv", "lock", "-q"], cwd=env_source, check=True, capture_output=True
    )

    with materialize(relocating_task.clone, relocating_task.base_sha) as workspace:
        lock_hash = provision_executor_env(workspace, env_source)
        assert (workspace / ".venv" / "bin" / "python").is_file()

        # The real edit still has to survive alongside it.
        (workspace / "src" / "pkg" / "__init__.py").write_text(
            "LOCATION = 'extensions'\nCASES = [1, 2, 3]\nFLAG = 'on'\n"
        )
        patch = capture_candidate(workspace)

    assert ".venv" not in patch
    assert "LOCATION = 'extensions'" in patch
    assert len(lock_hash) == 64


def test_damage_outranks_a_scope_violation(relocating_task: Task) -> None:
    """A broken repository must not be reported as a filing error.

    `out-of-scope` reads as benign -- wrote in the wrong place -- and it
    was being reported for a candidate whose own new doctest failed the
    suite, because the scope branch was checked first. The first thing a
    reader needs from an outcome is whether the repository still works.
    """
    # The registry-iter shape: the production edit satisfies the oracle,
    # breaks a base test the oracle command never runs, and writes a test
    # of its own. All three at once, which is what made the ordering
    # matter -- node *count* is unchanged, so this is damage rather than
    # a vanished test.
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": (
                "LOCATION = 'extensions'\nCASES = [1, 2, 3]\nFLAG = 'off'\n"
            ),
            "tests/scratch_test.py": "def test_scratch():\n    assert True\n",
        },
    )
    assert attempt.out_of_scope == ("tests/scratch_test.py",)
    assert attempt.oracle is not None and attempt.oracle.reason_class == "pass"
    assert attempt.preservation is not None
    assert attempt.preservation.reason_class != "pass"
    assert not attempt.missing_nodes
    assert attempt.outcome == "progress-but-damaged"
    assert not attempt.accepted


def test_budget_exhaustion_is_read_from_the_transcript() -> None:
    """A ceiling hit must never be recorded as an inability to do the work."""
    from harness.screen import budget_exhaustion

    assert budget_exhaustion('{"type":"message_end"}') == "none"
    assert budget_exhaustion('{"entry":"turn_budget_exhausted"}') == "turns"
    assert budget_exhaustion('{"entry":"tool_budget_exhausted"}') == "tools"
    assert (
        budget_exhaustion("turn_budget_exhausted ... tool_budget_exhausted")
        == "turns+tools"
    )


def test_writing_a_test_is_permitted_and_recorded(relocating_task: Task) -> None:
    """The rule that rejected the reference answer on all eight tasks.

    Every target commit in this cohort writes tests. Judging a candidate
    against `writable` alone therefore forbids exactly what upstream did,
    and a rule the reference answer violates rejects every correct
    answer -- the defect that killed rule 4, arriving by another route.

    The write is recorded and the test is still never executed, so
    nothing about self-grading changes.
    """
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\nFLAG = 'on'\n",
            "tests/test_mine.py": "def test_mine():\n    assert True\n",
        },
        test_paths=("tests/**",),
    )
    assert attempt.wrote_tests == ("tests/test_mine.py",)
    assert attempt.out_of_scope == ()
    assert attempt.accepted
    assert attempt.outcome == "accepted"


def test_prose_and_packaging_are_still_violations(relocating_task: Task) -> None:
    """Permitting tests must not permit everything else.

    A changelog entry or a packaging change is genuinely not the task, and
    stays a violation under the same rule that stops penalising tests.
    """
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\nFLAG = 'on'\n",
            "CHANGELOG.md": "- did a thing\n",
        },
        test_paths=("tests/**",),
    )
    assert attempt.out_of_scope == ("CHANGELOG.md",)
    assert not attempt.accepted


def test_the_audit_reads_a_reached_foreign_workspace_as_taint() -> None:
    """The failure no grade could have caught.

    Cycle 1's `autowire` passed preservation, passed the oracle, showed
    an empty scope list and an intact node inventory -- every signal the
    acceptance rule reads was true of a candidate the model had copied
    out of a leftover workspace, oracle tests included. The theft exists
    only in the transcript.
    """
    from tools.audit_attempt import audit

    transcript = "\n".join(
        [
            json.dumps({"type": "session", "cwd": "/tmp/satyrn-workload-mine"}),
            json.dumps(
                {
                    "type": "tool_execution_start",
                    "toolCallId": "1",
                    "toolName": "bash",
                    "args": {
                        "command": "cd /tmp/satyrn-workload-other && cat src/x.py"
                    },
                }
            ),
            json.dumps(
                {
                    "type": "tool_execution_end",
                    "toolCallId": "1",
                    "result": {"content": [{"type": "text", "text": "SECRET = 1\n"}]},
                }
            ),
        ]
    )
    own, findings = audit(transcript)
    assert own == "satyrn-workload-mine"
    assert [f.reached for f in findings] == [True]


def test_the_audit_does_not_mistake_a_garbled_self_reference_for_escape() -> None:
    """Exit status is not the discriminator; the shell's error message is.

    The model garbles its own workspace name often. `cd /nowhere && ls`
    fails the `cd`, the rest of the compound command runs in the
    original directory, and the call returns real content with exit code
    zero. Three of Cycle 1's eight transcripts look like escapes by exit
    status and are not -- calling them tainted would have thrown away
    three sound results.
    """
    from tools.audit_attempt import audit

    transcript = "\n".join(
        [
            json.dumps({"type": "session", "cwd": "/tmp/satyrn-workload-urf2xlq6"}),
            json.dumps(
                {
                    "type": "tool_execution_start",
                    "toolCallId": "1",
                    "toolName": "bash",
                    "args": {"command": "cd /tmp/satyrn-workload-uirf2q6l; cat README"},
                }
            ),
            json.dumps(
                {
                    "type": "tool_execution_end",
                    "toolCallId": "1",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "/bin/bash: cd: /tmp/satyrn-workload-uirf2q6l: "
                                    "No such file or directory\nmy own readme\n"
                                ),
                            }
                        ]
                    },
                }
            ),
        ]
    )
    _, findings = audit(transcript)
    assert [f.reached for f in findings] == [False]


def test_a_stale_workspace_is_detectable(tmp_path: Path, monkeypatch) -> None:
    """The guard that would have prevented it, one layer down.

    A leftover workspace is an answer key: it was materialised from some
    base commit and holds that commit's tree, so any task whose base is
    older can be read straight out of it.
    """
    from harness.workspace import stale_workspaces

    monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
    assert stale_workspaces() == ()
    (tmp_path / "satyrn-workload-leftover").mkdir()
    (tmp_path / "unrelated").mkdir()
    assert [p.name for p in stale_workspaces()] == ["satyrn-workload-leftover"]


def test_a_void_attempt_can_never_be_accepted(relocating_task: Task) -> None:
    """Validity gates acceptance, and nothing else can override it.

    The candidate here is perfect: it closes the whole gap, preserves
    everything, writes nothing out of scope. That is exactly the shape
    the stolen `autowire` candidate had -- it was the target commit's
    own code, so every signal the acceptance rule reads was true.
    """
    manifest = load_manifest(relocating_task.manifest_dir)
    patch = _candidate(
        relocating_task,
        {
            "src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\nFLAG = 'on'\n"
        },
    )
    clean = grade_candidate(manifest, relocating_task.clone, _fake_env(), patch)
    assert clean.accepted and clean.outcome == "accepted"

    voided = grade_candidate(
        manifest,
        relocating_task.clone,
        _fake_env(),
        patch,
        validity="void:left-workspace",
        validity_evidence=("bash -> satyrn-workload-other: cat src/x.py",),
    )
    assert not voided.accepted
    assert voided.outcome == "void:left-workspace"
    assert voided.validity_evidence
    # Still graded, because the grade is what proved the theft: the
    # stolen patch was byte-identical to the target commit.
    assert voided.oracle is not None
    assert voided.gap_closed == clean.gap_closed


def test_a_missing_transcript_is_void_not_valid() -> None:
    """Absence of evidence must not read as evidence of absence."""
    from harness.validity import assess

    assert assess("")[0] == "void:no-transcript"
    assert assess('{"type":"turn_start"}')[0] == "void:no-workspace"
    assert (
        assess(json.dumps({"type": "session", "cwd": "/tmp/satyrn-workload-a"}))[0]
        == "valid"
    )


def test_overlap_flags_a_verbatim_copy_and_ignores_independent_work() -> None:
    """The cheapest signal that a result might be recall, not reasoning.

    `svcs` is public and these tasks are real upstream commits, so every
    model has plausibly seen the answers. This cannot separate recall
    from capability -- a model that absorbed the shape of a fix and
    reimplemented it scores zero and looks clean -- but it does catch
    verbatim reproduction, and it scored the copied `autowire` candidate
    at 100% before anyone read a transcript.
    """
    from harness.similarity import overlap

    reference = (
        "diff --git a/src/pkg/a.py b/src/pkg/a.py\n+def solve():\n+    return 42\n"
    )
    copied = reference
    independent = (
        "diff --git a/src/pkg/a.py b/src/pkg/a.py\n"
        "+def solve():\n+    total = 40 + 2\n+    return total\n"
    )
    assert overlap(copied, reference, ("src/pkg/",)) == 1.0
    # Shares the signature line only.
    assert 0 < overlap(independent, reference, ("src/pkg/",)) < 0.5

    # Files outside the production prefix are not compared at all: a
    # model-written test matching upstream's says nothing about the fix.
    tests_only = "diff --git a/tests/t.py b/tests/t.py\n+def test_x():\n+    pass\n"
    assert overlap(tests_only, reference, ("src/pkg/",)) == 0.0


def test_overlap_counts_repeats_as_a_multiset() -> None:
    """A candidate repeating one line must not score many matches for it."""
    from harness.similarity import overlap

    reference = "diff --git a/src/pkg/a.py b/src/pkg/a.py\n+x = 1\n"
    repeated = "diff --git a/src/pkg/a.py b/src/pkg/a.py\n+x = 1\n+x = 1\n+x = 1\n"
    assert overlap(repeated, reference, ("src/pkg/",)) == round(1 / 3, 3)


def test_a_candidate_that_skips_the_oracle_is_not_accepted(
    relocating_task: Task,
) -> None:
    """The hole rule 8 closes, as a fixture rather than an argument.

    `pytest` exits zero when tests are *skipped*, so the old acceptance
    rule -- which asked only whether the oracle run ended
    `reason_class == "pass"` -- would take a candidate that caused the
    hidden assertions to skip. Preservation passes, scope is clean, the
    node inventory of the *preservation* run is intact, and the oracle
    "passed". Nothing in the banked record did this; nothing stopped it.

    Here the production change satisfies nothing and instead makes the
    oracle's own test skip at runtime.
    """
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": (
                "import pytest\n\n"
                "LOCATION = 'config'\nCASES = [1, 2, 3]\nFLAG = 'on'\n\n"
                "pytest.skip('nothing to see', allow_module_level=True)\n"
            )
        },
    )
    assert not attempt.accepted
    assert attempt.oracle_shortfall, "the skipped oracle node must be recorded"


def test_the_reference_answer_has_no_oracle_shortfall(relocating_task: Task) -> None:
    """Rule 8 must not reject the right answer.

    Every rule change in this phase is checked against the target's own
    diff before it is trusted, because rule 4 was caught rejecting the
    reference on four of nine tasks.
    """
    attempt = _grade(
        relocating_task,
        {
            "src/pkg/__init__.py": "LOCATION = 'extensions'\nCASES = [1, 2, 3]\nFLAG = 'on'\n"
        },
    )
    assert attempt.accepted
    assert attempt.oracle_shortfall == ()


def test_a_cell_mismatch_aborts_before_any_model_call(tmp_path: Path) -> None:
    """A declared value nobody checks is drift wearing a filename.

    This is the defect that let Experiment B's 32768 output cap live
    only in a driver and a directory name: the value was swapped
    mid-session and restored afterwards with nothing attesting either
    event, and a record moved out of that directory could not say what
    it ran under.
    """
    import harness.cell as cell

    path = tmp_path / "probe.toml"
    path.write_text(
        'name = "probe"\n\n[pinned]\n'
        'model = "omlx/m"\ntools = "read"\nmax_tokens = "8192"\n'
    )
    declared = cell.load_cell(path)

    declared.verify({"model": "omlx/m", "tools": "read", "max_tokens": "8192"})

    with pytest.raises(cell.CellMismatch) as caught:
        declared.verify({"model": "omlx/m", "tools": "read", "max_tokens": "32768"})
    assert "max_tokens" in str(caught.value)
    assert "8192" in str(caught.value) and "32768" in str(caught.value)


def test_an_unresolvable_key_is_a_mismatch_not_a_pass(tmp_path: Path) -> None:
    """An empty resolver must not match everything.

    A resolver that silently failed to read `models.json` would return a
    dict without the model limits, and treating "absent" as "agrees"
    would turn the check into decoration on exactly the runs where the
    configuration could not be read.
    """
    import harness.cell as cell

    path = tmp_path / "probe.toml"
    path.write_text('name = "probe"\n\n[pinned]\nmax_tokens = "8192"\n')
    with pytest.raises(cell.CellMismatch, match="not resolvable"):
        cell.load_cell(path).verify({})


def test_an_unknown_pinned_key_is_rejected(tmp_path: Path) -> None:
    """A typo'd key would sit in the file looking like a constraint."""
    import harness.cell as cell

    path = tmp_path / "probe.toml"
    path.write_text('name = "probe"\n\n[pinned]\nmax_tokns = "8192"\n')
    with pytest.raises(cell.CellMismatch, match="unknown pinned keys"):
        cell.load_cell(path)


def test_the_solution_detector_separates_locating_prose_from_a_handed_over_fix() -> (
    None
):
    """A contract locates and bounds; it must not contain the fix.

    The first authoring prompt never said so, and the author helpfully
    wrote the complete `__iter__` method into the contract -- which is
    why Experiment A measured a 12B transcribing a 27B's answer rather
    than a contract helping anything.

    **Renamed 2026-08-12: this tests the detector, not a gate.**
    `MAX_SOLUTION_STATEMENTS` stopped being fatal in `author_one` --
    zero tolerance demonstrably rejected good contracts (a draft quoting
    an existing import line and two caller-side usages scored 3 and
    contained none of the fix), and deleting a draft before the leak
    probe can adjudicate it destroys the artifact the probe exists to
    judge. `solution_statements` is still the live detector and its
    output is still recorded; admission is the probe's call. The old
    name promised a gate that no longer exists.
    """
    from tools.author_contract import MAX_SOLUTION_STATEMENTS, solution_statements

    locating = (
        "# Contract\n\nAdd `__iter__` to `Registry` in `src/svcs/_core.py`,\n"
        "beside `__contains__` (around line 126). Signature:\n\n"
        "```python\ndef __iter__(self) -> Iterator[RegisteredService]:\n```\n\n"
        "Callers should be able to write:\n\n```python\nlist(registry)\n```\n"
    )
    assert len(solution_statements(locating)) <= MAX_SOLUTION_STATEMENTS

    handing_over = (
        "# Contract\n\n```python\ndef __iter__(self):\n"
        "    return iter(self._services.values())\n```\n"
    )
    assert len(solution_statements(handing_over)) > MAX_SOLUTION_STATEMENTS


def test_the_arm_refuses_a_draft_set_that_carries_the_fix() -> None:
    """Deleting rejected drafts only helps if the consumer also refuses one.

    The authoring gate runs when a draft is written. Nothing re-checked it
    at the point of use, so any directory could be handed to
    `--contract-draft-dir` -- including a void draft still on disk as
    evidence. `registry-iter.md` was banked in two real places with
    byte-identical content (`workloads/svcs/overnight/drafts/` and the
    duplicate under `contracts/draft-qwen/`); an arm built on either
    measures transcription.

    Asserted against a byte-identical fixture copy of the real banked
    draft (`tests/fixtures/author_contract_drafts/`, provenance and hash
    in that directory's `PROVENANCE.md`), not the live research paths --
    decoupling the default suite from `workloads/svcs/overnight/`
    (2026-08-11 distribution brief, step 3). The point survives the
    decoupling: *these exact bytes*, still present at the original paths
    too, are refused.
    """
    from tools.author_contract import MAX_SOLUTION_STATEMENTS, solution_statements

    path = Path("tests/fixtures/author_contract_drafts/registry-iter.md")
    assert path.is_file(), f"{path} is the artifact under test"
    assert len(solution_statements(path.read_text())) > MAX_SOLUTION_STATEMENTS, (
        f"{path} must still trip the gate; if it stopped doing so the "
        "guard in screen_workload no longer protects anything"
    )


def test_extraction_leaves_a_plainly_written_contract_alone() -> None:
    """The destructive case: a contract that was never wrapped.

    A locating contract carrying two fenced examples has more text
    *between* its first and last fence than outside them, which is what
    the old size heuristic keyed on. It deleted the title, the locating
    prose, and the Bounds section, and it left the survivor with inverted
    fence parity so the gate read code as prose. Both halves are asserted
    here, because either alone would have let this ship.
    """
    from tools.author_contract import (
        MAX_SOLUTION_STATEMENTS,
        extract_contract,
        solution_statements,
    )

    plain = (
        "# Contract: iterate the registry\n\n"
        "## Location\n\n`src/svcs/_core.py`, on `Registry`, beside `__contains__`.\n\n"
        "## The API\n\nCallers should be able to write:\n\n"
        "```python\nlist(registry)\n```\n\n"
        "Registration order is preserved and the registry is not copied. The\n"
        "executor must not reach into `_services` from outside the class.\n\n"
        "## Done when\n\nThis selects the new node:\n\n"
        "```text\ntests/test_registry.py::test_iter\n```\n\n"
        "## Bounds\n\nDo not touch `container.py`. Do not add a test file.\n"
    )
    body = extract_contract(plain)
    assert body == plain.strip(), "a plainly written contract must survive intact"
    assert "## Bounds" in body
    assert body.startswith("# Contract")
    assert len(solution_statements(body)) <= MAX_SOLUTION_STATEMENTS


def test_extraction_still_unwraps_the_apology_it_was_built_for() -> None:
    """The real case that motivated extraction, still handled."""
    from tools.author_contract import extract_contract

    wrapped = (
        "I don't have a write tool available, so I'll present the complete\n"
        "contract content here:\n\n"
        "```markdown\n# Contract\n\nAdd `__iter__` to `Registry`.\n\n"
        "```python\ndef __iter__(self) -> Iterator[RegisteredService]:\n```\n\n"
        "## Bounds\n\nOne file only.\n```\n"
    )
    body = extract_contract(wrapped)
    assert body.startswith("# Contract")
    assert "write tool available" not in body
    assert "## Bounds" in body


def test_the_gate_reads_the_raw_text_too() -> None:
    """Extraction must not be able to hide the answer from the gate.

    Independent of whether extraction is currently correct: the gate takes
    whichever form finds more statements, so a future extraction bug costs
    a mangled draft rather than a contaminated arm.
    """
    from tools.author_contract import solution_statements

    raw = "prelude\n\n```python\nreturn iter(self._services.values())\n```\n"
    mangled = "return iter(self._services.values())\n```\n\nprelude\n"
    assert len(solution_statements(mangled)) == 0, "the mangled form hides it"
    assert len(solution_statements(raw)) == 1
    assert (
        len(max(solution_statements(mangled), solution_statements(raw), key=len)) == 1
    )


def test_no_existing_draft_survives_the_decision() -> None:
    """The decision voids the current drafts, for two different reasons.

    Five carry the implementation and the gate rejects them. Three are
    empty preambles and the length check rejects them. `flask-extensions`
    passes the gate -- its fences hold a `pytest` command, not code -- and
    is still void, because it was authored under the superseded prompt
    and a contract's provenance is part of the arm. That distinction is
    recorded rather than smoothed over: the gate and the decision are not
    the same bar.

    Asserted against byte-identical fixture copies of the eight real
    drafts (`tests/fixtures/author_contract_drafts/`, provenance and
    hashes in that directory's `PROVENANCE.md`), decoupling the default
    suite from `workloads/svcs/overnight/drafts/` -- 7.9 MiB, mostly raw
    authoring transcripts irrelevant to this assertion (2026-08-11
    distribution brief, step 3).
    """
    from tools.author_contract import MAX_SOLUTION_STATEMENTS, solution_statements

    drafts = sorted(Path("tests/fixtures/author_contract_drafts").glob("*.md"))
    assert drafts, "expected the fixture drafts to still be present"

    gated = [
        d.stem
        for d in drafts
        if len(solution_statements(d.read_text())) > MAX_SOLUTION_STATEMENTS
    ]
    stubs = [d.stem for d in drafts if len(d.read_text().strip()) < 400]
    assert sorted(gated) == [
        "autowire",
        "local-pings",
        "registry-iter",
        "stringified-annotations",
    ]
    assert sorted(stubs) == [
        "async-cm-enter",
        "fastapi-get-registry",
        "magicmock-factory",
    ]
    # Every draft is accounted for by one reason or the other, except the
    # one whose only disqualification is provenance.
    accounted = set(gated) | set(stubs) | {"flask-extensions"}
    assert accounted == {d.stem for d in drafts}
