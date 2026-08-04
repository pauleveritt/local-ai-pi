"""Phase 5 cycle 1 — the improvement mechanism.

An *improvement* is a named, optional change to how a run is steered. The
harness has to record that a run had one applied, or a batch resumes a
checkpoint produced under different steering with nothing noticing. These
tests cover the recording, not the steering's effect.
"""

from pathlib import Path
from types import SimpleNamespace

import harness.runner as runner
from harness.runner import Suite


def _stub_subprocess(monkeypatch):
    """`_conditions` shells out for the harness revision and Pi's version.

    Both are irrelevant here and one of them requires Pi installed, so the
    tests below stub them rather than skipping without Pi.
    """
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda command, **kwargs: SimpleNamespace(stdout="stub\n"),
    )
    monkeypatch.setattr(runner, "_path_digest", lambda path: "digest")


def _suite(tmp_path, allowlist=("thing.py",)) -> Suite:
    spec = tmp_path / "spec.md"
    spec.write_text("build a thing")
    acceptance = tmp_path / "test_acceptance.py"
    acceptance.write_text("def test_one(): assert True\n")
    return Suite("s", spec, acceptance, allowlist)


def test_uncommitted_acceptance_edit_changes_conditions(tmp_path, monkeypatch):
    """`harness_revision` is `git rev-parse HEAD`, so an *uncommitted* edit
    to an acceptance file sails past it. Without `acceptance_sha256` a batch
    resumes a checkpoint graded under a different contract."""
    _stub_subprocess(monkeypatch)
    suite = _suite(tmp_path)

    before = runner._conditions(suite, "model", ["pi", "prompt"], 600)
    suite.acceptance.write_text("def test_one(): assert False\n")
    after = runner._conditions(suite, "model", ["pi", "prompt"], 600)

    assert before.acceptance_sha256 != after.acceptance_sha256
    assert before != after


def test_changing_the_allowlist_changes_conditions(tmp_path, monkeypatch):
    """Two suites differing only in which model-written paths get copied
    out and graded must not share conditions."""
    _stub_subprocess(monkeypatch)
    narrow_suite = _suite(tmp_path, allowlist=("thing.py",))
    wide_suite = Suite(
        "s", narrow_suite.task_spec, narrow_suite.acceptance, ("thing.py", "templates")
    )

    narrow = runner._conditions(narrow_suite, "model", ["pi", "p"], 600)
    wide = runner._conditions(wide_suite, "model", ["pi", "p"], 600)

    assert narrow.source_allowlist != wide.source_allowlist
    assert narrow != wide


def test_conditions_without_an_improvement_say_so(tmp_path, monkeypatch):
    """A run with no improvement records that explicitly, so a reader of a
    checkpoint line never has to infer it from an absent field -- and so no
    real improvement name can collide with the pre-phase-5 sentinel."""
    _stub_subprocess(monkeypatch)

    conditions = runner._conditions(_suite(tmp_path), "model", ["pi", "prompt"], 600)

    assert conditions.improvement_name == "none"
    assert conditions.improvement_digest == "<none>"


def _tree(root, marker="name: implementer\n"):
    (root / "agents").mkdir(parents=True)
    (root / "index.ts").write_text("export const x = 1\n")
    (root / "agents" / "implementer.md").write_text(marker)
    return root


def test_tree_digest_changes_on_any_nested_file(tmp_path):
    """A digest that only saw top-level files would let an edit deep in
    Pi's shipped subagent tree pass unnoticed -- and its specialists live
    exactly one level down, in `agents/`."""
    tree = _tree(tmp_path / "ext")

    before = runner._path_digest(tree)
    (tree / "agents" / "implementer.md").write_text("name: implementer!\n")
    after = runner._path_digest(tree)

    assert before != after


def test_tree_digest_ignores_the_trees_own_path(tmp_path):
    """Pi's shipped extension sits at a different absolute path on every
    contributor's machine and moves on every upgrade. A path-sensitive
    digest would report drift that is not there, and `run_batch` would
    refuse to resume a checkpoint that is in fact still valid."""
    first = _tree(tmp_path / "a" / "ext")
    second = _tree(tmp_path / "b" / "ext")

    assert runner._path_digest(first) == runner._path_digest(second)


def test_tree_digest_sorts_rather_than_trusting_iteration_order(tmp_path, monkeypatch):
    """Filesystem iteration order is not guaranteed, and the same
    extension must digest identically on two machines.

    This perturbs `rglob` directly instead of building two trees in
    different creation orders. **The creation-order version was written
    first and was vacuous**: `rglob` returned both trees' entries in the
    same order anyway, so removing `sorted()` left it green. It was
    replaced rather than kept, because a test that cannot fail is worse
    than no test -- it reports coverage that is not there.
    """
    tree = tmp_path / "ext"
    tree.mkdir()
    for name in ("one.ts", "two.ts", "three.ts"):
        (tree / name).write_text(name)

    natural = runner._path_digest(tree)

    real_rglob = Path.rglob
    monkeypatch.setattr(
        Path, "rglob", lambda self, pattern: reversed(list(real_rglob(self, pattern)))
    )

    assert runner._path_digest(tree) == natural


def test_tree_digest_notices_a_file_moving_within_the_tree(tmp_path):
    """Contents alone are not enough: two trees holding the same bytes at
    different paths are different extensions. Hashing the concatenated
    file digests without their names would call them equal."""
    first = tmp_path / "a"
    second = tmp_path / "b"
    (first / "agents").mkdir(parents=True)
    (second / "prompts").mkdir(parents=True)
    (first / "agents" / "one.md").write_text("body\n")
    (second / "prompts" / "one.md").write_text("body\n")

    assert runner._path_digest(first) != runner._path_digest(second)


def _seed_with_implementer(root: Path) -> Path:
    (root / ".pi" / "agents").mkdir(parents=True)
    (root / ".pi" / "agents" / "implementer.md").write_text(
        "---\nname: implementer\n---\nBuild exactly the packet.\n"
    )
    return root


def test_pi_command_appends_the_system_prompt_before_the_task_spec(tmp_path):
    """`_conditions` normalizes the *last* command element to
    "<task-spec>". A flag appended after the prompt would be hashed as the
    prompt, and the real prompt would be recorded as a bare argument."""
    orchestrator = tmp_path / "orchestrator.md"
    orchestrator.write_text("You orchestrate.\n")

    command = runner._pi_command("model", "build a thing", system_prompt=orchestrator)

    assert command[-1] == "build a thing"
    assert command[command.index("--append-system-prompt") + 1] == str(orchestrator)


def test_pi_command_omits_the_flag_without_a_system_prompt():
    """A run with no improvement must produce byte-identical arguments to
    every run recorded before this cycle, or the bare arm stops being
    comparable with Phase 1's evidence."""
    assert "--append-system-prompt" not in runner._pi_command("model", "build a thing")


def test_seeded_files_do_not_appear_in_the_run_diff(tmp_path):
    """`prepare_workspace` copies *before* git-init and commits, so seeded
    files are in the initial commit. If that order ever flips, every
    orchestrated run's diff carries the improvement's own files and the
    record of what the *model* wrote is polluted."""
    import subprocess as sp

    from harness.workspace import prepare_workspace

    with prepare_workspace(_seed_with_implementer(tmp_path / "seed")) as workspace:
        assert (workspace / ".pi" / "agents" / "implementer.md").is_file()
        head = sp.run(
            ["git", "rev-parse", "HEAD"], cwd=workspace,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        sp.run(["git", "add", "-A"], cwd=workspace, check=True, capture_output=True)
        diff = sp.run(
            ["git", "diff", "--cached", head], cwd=workspace,
            check=True, capture_output=True, text=True,
        ).stdout

    assert "implementer.md" not in diff


def test_run_suite_seeds_the_workspace_from_the_improvement(tmp_path, monkeypatch):
    """Goes through `run_suite` rather than calling `prepare_workspace`
    directly. A test that exercises the collaborator instead of the caller
    stays green when the caller stops passing `seed_dir` -- which is the
    near-miss phase 4 cycle 1 recorded, arriving here one layer over.

    Pi discovers project-local specialists under `.pi/agents/` relative to
    its cwd, which is the workspace. Without seeding no delegation is
    possible at all, and the arm would silently measure a bare run.
    """
    from harness.grading import GradeResult
    from harness.processes import ProcessResult

    seen = {}

    monkeypatch.setattr(runner, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(
        runner,
        "run_process",
        lambda command, **kwargs: seen.update(
            agent=(kwargs["cwd"] / ".pi" / "agents" / "implementer.md").is_file()
        )
        or ProcessResult(0, "", "", False),
    )
    monkeypatch.setattr(
        runner,
        "grade",
        lambda *args, **kwargs: GradeResult(True, 1, 1, 0, "1 passed", "", ()),
    )

    improvement = runner.Improvement(
        "sdd-orchestrator", _seed_with_implementer(tmp_path / "seed"), (), None
    )
    runner.run_suite(runner.DURATION, improvement=improvement)

    assert seen["agent"] is True


def test_editing_a_seeded_file_changes_conditions(tmp_path, monkeypatch):
    """The improvement is data. Editing that data must change the
    conditions, or a batch resumes a checkpoint recorded under different
    steering -- the bug `extension_digests` closed, one layer over."""
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda command, **kwargs: SimpleNamespace(stdout="stub\n"),
    )
    suite = _suite(tmp_path)
    seed = _seed_with_implementer(tmp_path / "seed")
    improvement = runner.Improvement("sdd-orchestrator", seed, (), None)

    before = runner._conditions(
        suite, "model", ["pi", "p"], 600, runner.EXTENSIONS, improvement
    )
    (seed / ".pi" / "agents" / "implementer.md").write_text(
        "---\nname: implementer\n---\nBuild whatever you like.\n"
    )
    after = runner._conditions(
        suite, "model", ["pi", "p"], 600, runner.EXTENSIONS, improvement
    )

    assert before.improvement_digest != after.improvement_digest
    assert before.improvement_name == after.improvement_name == "sdd-orchestrator"
    assert before != after


def test_run_batch_refuses_a_pre_phase5_checkpoint(tmp_path, monkeypatch):
    """Old evidence stays readable but must not be resumed: those runs
    recorded no improvement, and no real value can equal the sentinel."""
    import pytest

    from harness.checkpoint import append_checkpoint
    from harness.grading import GradeResult
    from harness.runner import RunResult
    from tests.support import PRE_PHASE5, make_conditions

    checkpoint = tmp_path / "runs.jsonl"
    append_checkpoint(
        checkpoint,
        RunResult(
            "diff",
            GradeResult(True, 1, 1, 0, "1 passed", "", ()),
            "", "", 0,
            conditions=make_conditions(
                pi_version=runner.EXPECTED_PI_VERSION,
                improvement_name=PRE_PHASE5,
                improvement_digest=PRE_PHASE5,
                acceptance_sha256=PRE_PHASE5,
                source_allowlist=(PRE_PHASE5,),
            ),
        ),
    )

    monkeypatch.setattr(
        runner,
        "_conditions",
        lambda *args, **kwargs: make_conditions(pi_version=runner.EXPECTED_PI_VERSION),
    )
    monkeypatch.setattr(
        runner, "preflight_model", lambda model: pytest.fail("preflight called")
    )
    monkeypatch.setattr(
        runner, "run_suite", lambda suite, **kwargs: pytest.fail("run called")
    )

    with pytest.raises(ValueError, match="checkpoint conditions do not match"):
        runner.run_batch(checkpoint, suite=runner.AGENTCLINIC_PHASE_1, target=2)


def test_run_suite_forwards_the_improvement_to_conditions(tmp_path, monkeypatch):
    """`test_editing_a_seeded_file_changes_conditions` proves `_conditions`
    *uses* an improvement; this proves `run_suite` actually *hands* it one.

    Both are needed. Dropping the argument from the `run_suite` call site
    left the whole suite green when the mutation was run -- the third time
    this shape has appeared, after phase 4 cycle 1's `suite.*` near-miss
    and this cycle's own vacuous ordering test. Testing the collaborator is
    not testing the caller.
    """
    from harness.grading import GradeResult
    from harness.processes import ProcessResult
    from tests.support import make_conditions

    seen = {}

    def fake_conditions(suite, model, command, timeout, extensions, improvement=None):
        seen["improvement"] = improvement
        return make_conditions()

    monkeypatch.setattr(runner, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(runner, "_conditions", fake_conditions)
    monkeypatch.setattr(
        runner, "run_process", lambda command, **kwargs: ProcessResult(0, "", "", False)
    )
    monkeypatch.setattr(
        runner,
        "grade",
        lambda *args, **kwargs: GradeResult(True, 1, 1, 0, "1 passed", "", ()),
    )

    improvement = runner.Improvement(
        "sdd-orchestrator", _seed_with_implementer(tmp_path / "seed"), (), None
    )
    result = runner.run_suite(runner.DURATION, improvement=improvement)

    assert seen["improvement"] is improvement
    assert result.conditions is not None


def test_pi_package_root_contains_the_shipped_subagent_extension():
    """The delegation mechanism is Pi's, not ours. If this fails, the
    improvement is pointing at nothing and every orchestrated run would
    quietly be a bare run."""
    subagent = runner.pi_package_root() / "examples" / "extensions" / "subagent"

    assert (subagent / "index.ts").is_file()
    assert (subagent / "agents").is_dir()


def test_sdd_orchestrator_points_at_files_that_exist():
    improvement = runner.sdd_orchestrator()

    assert improvement.seed_dir is not None
    assert (improvement.seed_dir / ".pi" / "agents" / "implementer.md").is_file()
    assert improvement.system_prompt is not None
    assert improvement.system_prompt.is_file()
    assert improvement.extensions
    assert all(path.exists() for path in improvement.extensions)


def test_the_orchestrator_prompt_is_not_a_discoverable_specialist():
    """Any `.md` under `.pi/agents/` carrying name/description frontmatter
    is discovered as a *callable* specialist. An orchestrator kept there
    could delegate to itself, with no depth cap on the nesting."""
    system_prompt = runner.sdd_orchestrator().system_prompt
    assert system_prompt is not None
    assert ".pi/agents" not in system_prompt.as_posix()


def test_the_implementer_is_seeded_where_pi_looks_for_it():
    """Pi scans `.pi/agents/` relative to its cwd, which is the workspace.
    A specialist seeded anywhere else is never found."""
    seed = runner.sdd_orchestrator().seed_dir
    assert seed is not None
    relative = (seed / ".pi" / "agents" / "implementer.md").relative_to(seed)

    assert relative.as_posix() == ".pi/agents/implementer.md"


def test_the_subagent_extension_is_a_file_not_a_directory():
    """Pi's `--extension` needs the entry-point *file*. Pointing it at the
    `subagent/` directory produces no error and no stderr; the tool simply
    never registers, and the only symptom is `"Tool subagent not found"`
    when the model finally calls it -- by which point the parent has often
    done the work itself and the run grades accepted.

    Verified by two live runs on 2026-08-04: directory -> isError true,
    `index.ts` -> isError false. This test is cheap insurance against the
    path quietly reverting to the directory, which no unit test would
    otherwise notice.
    """
    (extension,) = runner.sdd_orchestrator().extensions

    assert extension.is_file()
    assert extension.name == "index.ts"


def test_the_user_story_suite_shares_agentclinics_contract():
    """The two AgentClinic suites must grade against one contract, or the
    comparison measures two different targets rather than two descriptions
    of one. Conditions still differ, because the task spec does."""
    detailed = runner.AGENTCLINIC_PHASE_1
    user_story = runner.AGENTCLINIC_PHASE_1_USER_STORY

    assert user_story.acceptance == detailed.acceptance
    assert user_story.source_allowlist == detailed.source_allowlist
    assert user_story.task_spec != detailed.task_spec


def test_the_user_story_spec_names_no_framework_and_no_module():
    """The leak this suite exists to avoid. `agentclinic-phase-1`'s spec
    names FastAPI, Jinja2, httpx, and `app.py`; the acceptance suite
    imports `from app import app`. Supplying the technology stack is the
    single strongest lever the prior project found -- it is a cycle 5+
    improvement, and if it leaks in here there is nothing left to improve.
    """
    spec = runner.AGENTCLINIC_PHASE_1_USER_STORY.task_spec.read_text().lower()

    for leaked in ("fastapi", "jinja", "httpx", "starlette", "app.py", "uvicorn"):
        assert leaked not in spec, f"user-story spec leaks {leaked!r}"


def test_the_user_story_spec_still_states_the_environment():
    """Phase 2 cycle 3 found environment friction was ~95% of turn-count
    variance. Dropping the environment note to avoid the leak would trade
    one confound for a worse one."""
    spec = runner.AGENTCLINIC_PHASE_1_USER_STORY.task_spec.read_text()

    assert "already installed" in spec
    assert "python -m pytest" in spec


def test_the_user_story_spec_quotes_the_tagline_verbatim():
    """The acceptance suite asserts the tagline character for character.
    A spec that paraphrased it would be testing a fact it never stated."""
    tagline = "Come in. Sit down. Tell us about your human."

    assert tagline in runner.AGENTCLINIC_PHASE_1_USER_STORY.task_spec.read_text()
