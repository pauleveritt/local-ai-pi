"""The harness-owned Pi agent directory, and the env var that delivers it.

Phase 5 cycle 9. The subject is the *child*: it is spawned by Pi's shipped
subagent extension with none of the parent's suppression flags, so user-scope
resources load in it unconditionally. `PI_CODING_AGENT_DIR` is the only seam
that reaches it, because the extension's `spawn` passes no `env`.

These are static and unit checks. That the child stops loading the operator's
extensions is a claim about a live run, and lives in the cycle 9 record.
"""

import json

import pytest

from harness import runner
from harness.processes import ProcessResult


def test_pi_env_points_pi_at_the_harness_agent_dir():
    env = runner.pi_env()

    assert env["PI_CODING_AGENT_DIR"] == str(runner.AGENT_DIR)


def test_pi_env_keeps_the_inherited_environment():
    """`run_process` passes `env` straight to `Popen`, and `Popen` *replaces*
    the environment rather than merging it. Returning a bare one-key dict
    would strip `PATH`, and `pi` is resolved through it -- the failure would
    be an unrunnable batch, not a subtly wrong one, but it would cost a
    batch to find out.
    """
    import os

    env = runner.pi_env()

    assert env["PATH"] == os.environ["PATH"]
    assert len(env) > 1


def test_run_suite_runs_pi_under_that_environment(tmp_path, monkeypatch):
    """The mutation this catches is dropping `env=pi_env()` from the call
    site. `test_pi_env_*` would stay green -- testing the collaborator is not
    testing the caller, which this suite has now been bitten by four times.
    """
    from harness.grading import GradeResult
    from tests.support import make_conditions

    seen = {}

    def fake_run_process(command, **kwargs):
        seen["env"] = kwargs.get("env")
        return ProcessResult(0, "", "", False)

    monkeypatch.setattr(runner, "check_model_server_alive", lambda: None)
    monkeypatch.setattr(
        runner, "_conditions", lambda *args, **kwargs: make_conditions()
    )
    monkeypatch.setattr(runner, "run_process", fake_run_process)
    monkeypatch.setattr(
        runner,
        "grade",
        lambda *args, **kwargs: GradeResult(True, 1, 1, 0, "1 passed", "", ()),
    )

    runner.run_suite(runner.DURATION)

    assert seen["env"] is not None
    assert seen["env"]["PI_CODING_AGENT_DIR"] == str(runner.AGENT_DIR)


def test_conditions_record_the_agent_dir(tmp_path, monkeypatch):
    """Without this the child's whole resource set stays an unrecorded
    condition -- the gap that let every orchestrated arm run a bash-rewriting
    extension in its child while every recorded field stayed identical.
    """
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: type("R", (), {"stdout": "x", "returncode": 0})(),
    )
    suite = runner.DURATION

    conditions = runner._conditions(suite, "model", ["pi", "prompt"], 600)

    assert conditions.agent_dir_digest not in ("", "<pre-cycle9>")
    assert conditions.agent_dir_digest == runner._path_digest(runner.AGENT_DIR)


def test_the_agent_dir_names_no_packages_or_skills():
    """The contamination this cycle removes came through exactly these two
    keys in the operator's settings. A future edit that copies their file
    wholesale would reintroduce it silently.
    """
    settings = json.loads((runner.AGENT_DIR / "settings.json").read_text())

    assert "packages" not in settings
    assert "skills" not in settings


def test_the_agent_dir_holds_no_credentials():
    """The harness points processes at this directory. It should never be a
    place a credential can be read from, and `omlx` needs none.

    This asserts *emptiness*, not absence, because Pi creates `auth.json`
    itself on startup -- the first preflight under the new agent dir wrote
    one. An absence assertion passed until a run happened and then began
    failing for a reason unrelated to the risk, which is the wrong shape for
    a guard: what matters is that nothing secret is in it.
    """
    auth = runner.AGENT_DIR / "auth.json"

    if auth.exists():
        assert json.loads(auth.read_text()) == {}


def test_pi_runtime_state_in_the_agent_dir_is_not_committed():
    """The companion to the test above. Pi writes sessions, caches and that
    `auth.json` into whatever directory it is pointed at; only the files the
    harness authored belong in git.
    """
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files", "pi-agent-dir"],
        cwd=runner.REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()

    assert set(tracked) == {
        "pi-agent-dir/README.md",
        "pi-agent-dir/settings.json",
        "pi-agent-dir/models.json",
        "pi-agent-dir/extensions/loop-breaker.ts",
    }


def test_the_agent_dir_serves_the_model_the_harness_runs():
    """The agent dir replaces `~/.pi/agent`, which is where the `omlx`
    provider was defined. Getting this wrong makes every run fail to resolve
    its model.
    """
    models = json.loads((runner.AGENT_DIR / "models.json").read_text())
    provider, model = runner.DEFAULT_MODEL.split("/", 1)

    assert provider in models["providers"]
    assert model in [m["id"] for m in models["providers"][provider]["models"]]


def test_the_child_and_parent_loop_breakers_are_the_same_file():
    """Two copies exist because they are delivered by different routes: the
    parent gets an explicit `--extension`, the child can only get a
    user-scope extension in the agent dir. Copies drift; this is the same
    guard the prompt files carry.
    """
    child_copy = runner.AGENT_DIR / "extensions" / "loop-breaker.ts"

    assert child_copy.read_bytes() == runner.LOOP_BREAKER.read_bytes()


@pytest.mark.parametrize("name", ["settings.json", "models.json"])
def test_the_agent_dir_files_are_valid_json(name):
    json.loads((runner.AGENT_DIR / name).read_text())
