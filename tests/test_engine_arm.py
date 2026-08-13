"""The engine arm is a well-formed, hermetic Improvement.

Phase 9. The shootout compares a suite with the engine loaded versus
without it. The seam is an extension-only Improvement so the comparison
reuses the harness's existing arm machinery: same task, same prompt, same
model, engine extensions added. These tests are hermetic — no model
server, no Pi run.
"""

from harness import runner

ENGINE_FILE = runner.REPO_ROOT / ".pi" / "extensions" / "engine.ts"


def test_the_engine_improvement_is_extension_only():
    imp = runner.ENGINE_IMPROVEMENT
    assert imp.name == "engine"
    assert imp.seed_dir is None
    assert imp.system_prompt is None
    assert imp.extensions == (ENGINE_FILE,)


def test_the_engine_file_exists_and_digests_stably():
    assert ENGINE_FILE.is_file()
    digest = runner._path_digest(ENGINE_FILE)
    assert isinstance(digest, str) and len(digest) == 64
    assert runner._path_digest(ENGINE_FILE) == digest


def test_conditions_record_the_arm_without_a_model(monkeypatch):
    # _conditions shells out to git and pi --version; stub both so the
    # test stays hermetic on any machine.
    import subprocess

    def fake_run(cmd, **kwargs):
        out = "fake" if cmd[:2] == ["git", "rev-parse"] else "0.84.1"
        return subprocess.CompletedProcess(cmd, 0, stdout=out)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    conditions = runner._conditions(
        runner.AGENTCLINIC_PHASE_1,
        runner.DEFAULT_MODEL,
        ["pi", "--print", "<task-spec>"],
        600,
        extensions=runner.ENGINE_EXTENSIONS,
        improvement=runner.ENGINE_IMPROVEMENT,
    )
    assert conditions.improvement_name == "engine"
    assert runner._path_digest(ENGINE_FILE) in conditions.extension_digests
