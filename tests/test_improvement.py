"""Phase 5 cycle 1 — the improvement mechanism.

An *improvement* is a named, optional change to how a run is steered. The
harness has to record that a run had one applied, or a batch resumes a
checkpoint produced under different steering with nothing noticing. These
tests cover the recording, not the steering's effect.
"""

import subprocess
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


def test_a_model_created_nested_repo_does_not_abort_the_run(tmp_path, monkeypatch):
    """Observed live during phase 5 cycle 4, at run 15 of 16.

    A model given a spec with no file layout ran `git init` in a
    subdirectory. `git add -A` then refuses outright -- "does not have a
    commit checked out", exit 128 -- and the exception propagated out of
    `run_suite`, killing the batch: the completed run discarded and every
    queued run cancelled, over a step that only produces a diagnostic
    record. The verdict never depended on it, because `grade` copies
    allowlisted files into a fresh directory and never reads the diff.
    """
    from harness.grading import GradeResult
    from harness.processes import ProcessResult

    def fake_pi(command, **kwargs):
        workspace = kwargs["cwd"]
        (workspace / "app.py").write_text("app = object()\n")
        nested = workspace / "scaffold"
        nested.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=nested, check=True, capture_output=True)
        (nested / "note.txt").write_text("scaffolded\n")
        return ProcessResult(0, "", "", False)

    graded = {}
    monkeypatch.setattr(runner, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(runner, "run_process", fake_pi)
    monkeypatch.setattr(
        runner,
        "grade",
        lambda *args, **kwargs: graded.setdefault("ran", True)
        and GradeResult(True, 1, 1, 0, "1 passed", "", ()),
    )

    result = runner.run_suite(runner.DURATION)

    assert graded["ran"] is True, "grading must still happen"
    assert result.diff.startswith("<diff unavailable:")
    assert "128" in result.diff


def _subagent_schema_keys() -> set[str]:
    """Parameter names the installed subagent tool actually declares.

    Read from Pi's own `SubagentParams` rather than hardcoded, so the test
    fails loudly if an upgrade renames them instead of rotting into a
    check of names nobody uses any more.
    """
    source = (
        runner.pi_package_root()
        / "examples" / "extensions" / "subagent" / "index.ts"
    ).read_text()
    block = source.split("const SubagentParams = Type.Object({", 1)[1].split("});", 1)[0]
    return {
        line.split(":", 1)[0].strip()
        for line in block.splitlines()
        if ":" in line and not line.strip().startswith("//")
    }


def test_the_orchestrator_prompt_names_the_tools_real_parameters():
    """Four calls across cycles 2 and 4 sent `{agentScope, task}` and
    omitted `agent`, so `hasSingle` was false, `modeCount` was 0, and the
    tool answered "Invalid parameters. Provide exactly one mode." No child
    ran. The prompt named the specialist in prose and never said which
    parameter carries it.

    The rejection is returned as a *non-error* end with an empty
    `results[]`, so no `isError` check can catch it -- which is why this
    is asserted statically instead of being left to a batch to discover.
    """
    prompt = runner.sdd_orchestrator().system_prompt
    assert prompt is not None
    text = prompt.read_text()
    declared = _subagent_schema_keys()

    for parameter in ("agent", "task", "agentScope"):
        assert parameter in declared, f"{parameter!r} is no longer in Pi's schema"
        assert f"`{parameter}`" in text, f"prompt does not name the {parameter!r} parameter"
    assert '"implementer"' in text


def test_the_orchestrator_prompt_says_the_workspace_is_empty():
    """Cycle 4: bare Pi asked a human which file to start with in all 16
    runs, and one orchestrated run ran `ls -R` 245 times against a
    genuinely empty directory. Both are consistent with a model that
    believes it is joining an existing project."""
    prompt = runner.sdd_orchestrator().system_prompt
    assert prompt is not None
    text = prompt.read_text().lower()

    assert "workspace is empty" in text
    assert "must be created" in text or "created from nothing" in text


def test_the_orchestrator_prompt_leaks_no_stack_or_module():
    """Supplying the technology stack is cycle 7's lever. Leaking it into
    the orchestrator prompt would hand the user-story arm the fact whose
    absence that suite exists to measure."""
    prompt = runner.sdd_orchestrator().system_prompt
    assert prompt is not None
    text = prompt.read_text().lower()

    for leaked in ("fastapi", "jinja", "httpx", "starlette", "uvicorn", "app.py"):
        assert leaked not in text, f"orchestrator prompt leaks {leaked!r}"


def test_run_batch_records_and_uses_the_timeout_it_was_given(tmp_path, monkeypatch):
    """`run_batch` computed its `requested` conditions with a hardcoded 600
    while `run_suite` recorded whatever it was handed, so a batch at any
    other cap aborted on its first run with "run conditions changed during
    batch". The refusal was correct; the gap was that the cap could not be
    expressed at all.

    Found 2026-08-04 by phase 5 cycle 5's pilot, whose own plan called for
    n=6 at 300 s -- machinery the committed testing-economics section
    depended on and the harness did not have.

    Asserts both halves of the wiring, because either alone leaves the
    mismatch that caused the abort: the cap must reach `_conditions` (so
    the batch compares against what it will actually do) *and* reach the
    child process.
    """
    from harness.grading import GradeResult
    from harness.processes import ProcessResult
    from tests.support import make_conditions

    seen = {}

    def fake_conditions(suite, model, command, timeout, extensions=None, improvement=None):
        seen.setdefault("conditions_timeout", timeout)
        return make_conditions(
            pi_version=runner.EXPECTED_PI_VERSION, run_timeout=timeout
        )

    def fake_process(command, **kwargs):
        seen["process_timeout"] = kwargs["timeout"]
        return ProcessResult(0, "", "", False)

    monkeypatch.setattr(runner, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(runner, "preflight_model", lambda model: None)
    monkeypatch.setattr(runner, "_conditions", fake_conditions)
    monkeypatch.setattr(runner, "run_process", fake_process)
    monkeypatch.setattr(
        runner,
        "grade",
        lambda *args, **kwargs: GradeResult(True, 1, 1, 0, "1 passed", "", ()),
    )

    records = runner.run_batch(
        tmp_path / "pilot.jsonl", suite=runner.DURATION, target=1, timeout=300
    )

    assert seen["conditions_timeout"] == 300, "the cap must reach _conditions"
    assert seen["process_timeout"] == 300, "the cap must reach the child"
    assert records[0].conditions is not None
    assert records[0].conditions.run_timeout == 300


def test_the_guarded_improvement_carries_both_extensions():
    """`Improvement.extensions` is a tuple, so two extensions need no
    composition machinery and the phase's one-improvement-per-run rule
    stays intact. The unguarded improvement must survive: cycle 8 needs it
    as the comparison."""
    plain = runner.sdd_orchestrator()
    guarded = runner.sdd_orchestrator_guarded()

    assert guarded.name != plain.name
    assert set(plain.extensions) < set(guarded.extensions)
    assert runner.LOOP_BREAKER in guarded.extensions
    assert guarded.seed_dir == plain.seed_dir
    assert guarded.system_prompt == plain.system_prompt


def test_the_guarded_improvement_has_its_own_digest():
    """Two improvements differing only in an extension must not produce
    equal conditions, or their checkpoints become mutually resumable."""
    assert runner.LOOP_BREAKER.is_file()
    plain = runner.sdd_orchestrator()
    guarded = runner.sdd_orchestrator_guarded()

    # The loop breaker rides in `extensions`, which reaches conditions via
    # `extension_digests` rather than `improvement_digest` -- the latter
    # covers the seed and prompt, which are shared by design.
    assert runner._improvement_digest(plain) == runner._improvement_digest(guarded)
    assert [runner._path_digest(p) for p in plain.extensions] != [
        runner._path_digest(p) for p in guarded.extensions
    ]


def test_the_loop_breaker_trips_on_successful_repeats():
    """The property the unmerged `pi-circuit-breaker` branch lacks: it
    counts only *failing* identical calls, and all 245 of cycle 4's `ls -R`
    calls succeeded. `tool_call` fires before execution, so success is not
    even knowable here -- the source must not reference it."""
    source = runner.LOOP_BREAKER.read_text()

    assert 'pi.on("tool_call"' in source
    assert "block: true" in source
    assert "isError" not in source, "the hook fires before execution; success is unknowable"
    assert 'pi.appendEntry("loop_broken"' in source


def test_the_stack_prompt_is_the_guarded_prompt_plus_a_section():
    """Two prompt files that share a base drift apart silently. Asserting
    the stack variant *starts with* the base verbatim is cheaper than
    conditional includes and fails the moment someone edits one only."""
    guarded = runner.sdd_orchestrator_guarded().system_prompt
    stack = runner.sdd_orchestrator_guarded_stack().system_prompt
    assert guarded is not None and stack is not None

    assert stack != guarded
    assert stack.read_text().startswith(guarded.read_text())


def test_the_stack_prompt_names_the_framework_and_the_module():
    """The lever is exactly two facts, and the record must be able to say
    which. FastAPI, because every run that wrote app.py failed with
    `TypeError: Flask.__call__()` -- the suite drives ASGI and the model
    chose WSGI. `app.py`, because `source_allowlist` copies that path and
    a solution under `app/main.py` never reaches the grader."""
    prompt = runner.sdd_orchestrator_guarded_stack().system_prompt
    assert prompt is not None
    text = prompt.read_text()

    assert "FastAPI" in text
    assert "`app.py`" in text
    assert "Jinja2" in text


def test_the_stack_lever_does_not_leak_into_the_suite():
    """The lever lives in the improvement. If it reached the task spec it
    would be a different workload, not a steered run of the same one."""
    spec = runner.AGENTCLINIC_PHASE_1_USER_STORY.task_spec.read_text().lower()

    for leaked in ("fastapi", "jinja", "app.py", "flask"):
        assert leaked not in spec


def test_the_implementer_is_told_to_stop_repeating_a_failing_command():
    """Phase 5 cycle 8. Two of cycle 7's six runs were killed with the
    delegated child still going at 98 and 103 turns; one made 83 identical
    `pytest` calls out of 103 bash calls. The specialist said "run
    validation before you report completion" and nothing about what to do
    when it fails, and the child obeyed that literally and forever.

    The loop-breaker cannot help: it runs in the parent, and a
    child-style invocation does not load project-local extensions -- 
    verified with a probe, `--approve` included.
    """
    seed = runner.sdd_orchestrator().seed_dir
    assert seed is not None
    text = (seed / ".pi" / "agents" / "implementer.md").read_text().lower()

    assert "same command over and over" in text
    assert "fails twice" in text
    assert "report and stop" in text


def test_the_control_arm_carries_the_stack_facts_verbatim():
    """`tech-stack-only` exists to isolate cycle 7's two facts from the
    orchestration wrapped around them. If its prompt drifts from the section
    inside the orchestrator's prompt, the two arms stop differing by exactly
    orchestration and the control stops controlling anything.
    """
    control = runner.tech_stack_only().system_prompt
    orchestrated = runner.sdd_orchestrator_guarded_stack().system_prompt
    assert control is not None and orchestrated is not None

    section = control.read_text()

    assert section.startswith("## Technology")
    assert orchestrated.read_text().endswith(section)


def test_the_control_arm_delegates_nothing():
    """No seed means no `.pi/agents/implementer.md`, so there is no
    specialist to delegate to even if the model tried. That absence is the
    whole point of the arm and is cheap to assert.
    """
    control = runner.tech_stack_only()
    assert control.system_prompt is not None

    assert control.seed_dir is None
    assert "orchestrat" not in control.system_prompt.read_text().lower()
