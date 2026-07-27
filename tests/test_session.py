# tests/test_session.py
import subprocess
from pathlib import Path
from unittest.mock import patch

from harness.session import InvocationProfile, SessionResult, run_session


def test_turbohtml_stays_out_of_model_visible_workspace_stamp():
    """The grader's pyproject.toml (harness/grading.py) declares TurboHTML;
    the model-visible workspace stamp must never mention it."""
    from harness.workspace import _stamp_pyproject_text

    assert "turbohtml" not in _stamp_pyproject_text().casefold()


def test_session_result_fields():
    from harness.telemetry import RunTelemetry
    r = SessionResult(
        run_id="test-1",
        outcome="exited",
        returncode=0,
        telemetry=RunTelemetry(prompts=["test"], turns=5),
        changed_files=["app.py"],
        diff="+ # hello",
        tests_pass=True,
        wall_time_s=12.3,
        task_duration_s=9.5,
        artifact_path="research/sessions/test-1.jsonl",
        stderr_text="",
    )
    assert r.outcome == "exited"
    assert r.tests_pass is True
    assert r.run_id == "test-1"
    assert r.is_success is True  # exited + tests_pass + changed_files > 0
    assert r.stderr_text == ""
    assert r.task_duration_s == 9.5


def test_session_result_timeout_not_success():
    from harness.telemetry import RunTelemetry
    r = SessionResult(
        run_id="t1",
        outcome="timeout",
        returncode=None,
        telemetry=RunTelemetry(),
        changed_files=[],
        diff="",
        tests_pass=False,
        wall_time_s=300.0,
        artifact_path="sessions/t1.jsonl",
        stderr_text="Killed after 300s",
    )
    assert r.is_success is False
    assert r.outcome == "timeout"


def test_session_result_exited_with_hang_is_success():
    """exited-with-hang is success-eligible when tests pass and files changed."""
    from harness.telemetry import RunTelemetry
    r = SessionResult(
        run_id="hang-1",
        outcome="exited-with-hang",
        returncode=-15,
        telemetry=RunTelemetry(prompts=["test"], turns=5),
        changed_files=["app.py"],
        diff="+ # hello",
        tests_pass=True,
        wall_time_s=350.0,
        task_duration_s=12.0,
        artifact_path="sessions/hang-1.jsonl",
        stderr_text="",
    )
    assert r.is_success is True
    assert r.outcome == "exited-with-hang"
    # task_duration_s reflects real work (12s), not total wall (350s)
    assert r.task_duration_s == 12.0
    assert r.wall_time_s == 350.0


def test_exited_with_hang_complete_output_times_out(tmp_path: Path, monkeypatch):
    """Path (b): single attempt, complete output (agent_settled present),
    but the process is killed at timeout → exited-with-hang, not timeout."""
    import harness.session as mod

    workspace = tmp_path / "ws"
    workspace.mkdir()
    # Create a minimal git repo so capture_diff works.
    subprocess.run(["git", "init", "-q"], cwd=workspace, capture_output=True)
    (workspace / ".gitignore").write_text(".venv/\n")
    subprocess.run(["git", "add", "-A"], cwd=workspace, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", "pristine"], cwd=workspace, capture_output=True)
    pristine = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=workspace, capture_output=True, text=True
    ).stdout.strip()

    artifact_lines = [
        '{"type": "session", "timestamp": "2026-07-23T09:38:10.000Z"}\n',
        '{"type": "agent_start"}\n',
        '{"type": "agent_settled", "timestamp": "2026-07-23T09:38:20.000Z"}\n',
    ]
    artifact_text = "".join(artifact_lines)

    # Build a mock proc: first communicate() raises TimeoutExpired,
    # second (after kill) returns the artifact.
    call_count = [0]

    class MockProc:
        returncode = -15
        pid = 999999999  # implausible pid -- os.killpg raises ProcessLookupError,
                         # falls back to .kill() below, same as a real dead group

        def kill(self):
            pass

        def communicate(self, timeout=None):
            call_count[0] += 1
            if call_count[0] == 1:
                raise subprocess.TimeoutExpired(cmd=["pi"], timeout=10, output="")
            return (artifact_text, "")

    mock_proc = MockProc()

    # Patch _find_pi to avoid needing pi on PATH.
    monkeypatch.setattr(mod, "_find_pi", lambda: "/fake/pi")

    with patch("subprocess.Popen", return_value=mock_proc):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = type("MockResult", (), {
                "returncode": 0,
                "stdout": "1 passed\n",
                "stderr": "",
            })()

            result = run_session(
                workspace=str(workspace),
                phase_prompt="Test prompt",
                model="test/model",
                pristine_hash=pristine,
                profile=InvocationProfile.sp1(),
                timeout=10,
                max_startup_attempts=1,
                research_dir=tmp_path,
            )

    # The key assertion: complete output + timeout = exited-with-hang, NOT timeout.
    assert result.outcome == "exited-with-hang", \
        f"Expected exited-with-hang but got {result.outcome}"


def _git_pristine_workspace(path: Path) -> str:
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, capture_output=True)
    (path / ".gitignore").write_text(".venv/\n")
    subprocess.run(["git", "add", "-A"], cwd=path, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", "pristine"], cwd=path, capture_output=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True
    ).stdout.strip()


def test_run_session_isolates_pi_into_its_own_process_group(tmp_path: Path, monkeypatch):
    """Rule 8 review, 2026-07-27: pi is an agentic CLI that shells out
    (bash, pytest, git); a grandchild it spawns can inherit the stdout/
    stderr pipes. Popen must isolate pi into its own process group
    (start_new_session=True) so a timeout can kill the whole group, not
    just the direct child -- proc.kill() alone left a real run hung for
    45-60 min with the direct child already a zombie and the parent still
    blocked in communicate()."""
    import harness.session as mod

    workspace = tmp_path / "ws"
    pristine = _git_pristine_workspace(workspace)
    monkeypatch.setattr(mod, "_find_pi", lambda: "/fake/pi")

    captured_kwargs = {}

    class MockProc:
        returncode = 0
        pid = 12345

        def communicate(self, timeout=None):
            return ("some output\n", "")

    def fake_popen(*args, **kwargs):
        captured_kwargs.update(kwargs)
        return MockProc()

    with patch("subprocess.Popen", side_effect=fake_popen):
        with patch("subprocess.run") as mock_run:
            # subprocess.run() internally uses Popen as a context manager;
            # patching Popen globally would otherwise break the model's-
            # own-tests subprocess.run() call inside run_session too.
            mock_run.return_value = type("MockResult", (), {
                "returncode": 0, "stdout": "1 passed\n", "stderr": "",
            })()
            run_session(
                workspace=str(workspace),
                phase_prompt="Test prompt",
                model="test/model",
                pristine_hash=pristine,
                profile=InvocationProfile.sp1(),
                timeout=10,
                max_startup_attempts=1,
                research_dir=tmp_path,
            )

    assert captured_kwargs.get("start_new_session") is True


def test_run_session_kills_process_group_on_timeout(tmp_path: Path, monkeypatch):
    """On timeout, os.killpg is used against the whole group, not just
    proc.kill() on the direct child -- the fix for the 2026-07-27 hang."""
    import signal
    import harness.session as mod

    workspace = tmp_path / "ws"
    pristine = _git_pristine_workspace(workspace)
    monkeypatch.setattr(mod, "_find_pi", lambda: "/fake/pi")

    call_count = [0]

    class MockProc:
        returncode = -9
        pid = 54321

        def kill(self):
            pass

        def communicate(self, timeout=None):
            call_count[0] += 1
            if call_count[0] == 1:
                raise subprocess.TimeoutExpired(cmd=["pi"], timeout=10, output="")
            return ("", "")

    with patch("subprocess.Popen", return_value=MockProc()), \
         patch("os.killpg") as mock_killpg, \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = type("MockResult", (), {
            "returncode": 0, "stdout": "1 passed\n", "stderr": "",
        })()
        result = run_session(
            workspace=str(workspace),
            phase_prompt="Test prompt",
            model="test/model",
            pristine_hash=pristine,
            profile=InvocationProfile.sp1(),
            timeout=10,
            max_startup_attempts=1,
            research_dir=tmp_path,
        )

    mock_killpg.assert_called_once_with(54321, signal.SIGKILL)
    assert result.outcome == "timeout"


def test_run_session_survives_a_second_timeout_on_drain(tmp_path: Path, monkeypatch):
    """If even the drain communicate() times out -- a process outside pi's
    own group still holding a pipe open -- the harness must not hang
    forever. It kills the group again and proceeds with whatever partial
    output the timeout exception carries, rather than blocking a second
    time with no way out."""
    import harness.session as mod

    workspace = tmp_path / "ws"
    pristine = _git_pristine_workspace(workspace)
    monkeypatch.setattr(mod, "_find_pi", lambda: "/fake/pi")

    call_count = [0]

    class MockProc:
        returncode = None
        pid = 11111

        def communicate(self, timeout=None):
            call_count[0] += 1
            # CPython's TimeoutExpired carries bytes here even in text
            # mode -- verified against a real text=True Popen (Rule 8
            # review, 2026-07-27 -- Fable). A plain-str mock would have
            # masked the bytes/str bug the review actually found.
            raise subprocess.TimeoutExpired(cmd=["pi"], timeout=timeout or 10, output=b"")

    with patch("subprocess.Popen", return_value=MockProc()), \
         patch("os.killpg") as mock_killpg, \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = type("MockResult", (), {
            "returncode": 0, "stdout": "1 passed\n", "stderr": "",
        })()
        result = run_session(
            workspace=str(workspace),
            phase_prompt="Test prompt",
            model="test/model",
            pristine_hash=pristine,
            profile=InvocationProfile.sp1(),
            timeout=10,
            max_startup_attempts=1,
            research_dir=tmp_path,
        )

    assert mock_killpg.call_count == 2
    assert result.outcome == "timeout"


def test_run_session_decodes_bytes_partial_output_from_drain_timeout(tmp_path: Path, monkeypatch):
    """Rule 8 review, 2026-07-27 (Fable): the drain-timeout recovery path
    crashed the whole batch with a TypeError when real partial output was
    present, because TimeoutExpired.stdout/.stderr are bytes even in
    text-mode Popen and the recovery code passed that straight to
    Path.write_text(str). This pins the fix with non-empty bytes -- the
    exact shape that crashed -- and confirms the run completes instead of
    raising."""
    import harness.session as mod

    workspace = tmp_path / "ws"
    pristine = _git_pristine_workspace(workspace)
    monkeypatch.setattr(mod, "_find_pi", lambda: "/fake/pi")

    class MockProc:
        returncode = None
        pid = 22222

        def communicate(self, timeout=None):
            raise subprocess.TimeoutExpired(
                cmd=["pi"], timeout=timeout or 10,
                output=b'{"type": "agent_settled"}\n',
            )

    with patch("subprocess.Popen", return_value=MockProc()), \
         patch("os.killpg"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = type("MockResult", (), {
            "returncode": 0, "stdout": "1 passed\n", "stderr": "",
        })()
        result = run_session(
            workspace=str(workspace),
            phase_prompt="Test prompt",
            model="test/model",
            pristine_hash=pristine,
            profile=InvocationProfile.sp1(),
            timeout=10,
            max_startup_attempts=1,
            research_dir=tmp_path,
        )

    # Must not have raised; partial output present means not a true hang.
    assert result.outcome == "exited-with-hang"
    assert Path(result.artifact_path).read_text() == '{"type": "agent_settled"}\n'


def test_sp1_exited_no_subagent_calls_is_success():
    """Plain baselines (SP1) are not vetoed by the no-delegation check.
    
    SP1 profiles never delegate by design (expects_delegation=False).
    A SessionResult from a plain run with exited+tests_pass+changed_files
    must be is_success=True, even with zero subagent calls in the artifact.
    Regression test for C1 fix — before the fix, this would be classified
    as no-delegation and is_success would be False."""
    from harness.telemetry import RunTelemetry
    r = SessionResult(
        run_id="sp1-1",
        outcome="exited",
        returncode=0,
        telemetry=RunTelemetry(prompts=["test"], turns=5),
        changed_files=["app.py"],
        diff="+ # hello",
        tests_pass=True,
        wall_time_s=45.0,
        task_duration_s=30.0,
        artifact_path="sessions/sp1-1.jsonl",
        stderr_text="",
    )
    assert r.is_success is True, (
        "SP1 plain run with exited+tests_pass+changed_files must be success "
        "even when no subagent calls occurred"
    )
    from harness.session import run_session
    import inspect
    sig = inspect.signature(run_session)
    params = list(sig.parameters.keys())
    assert "workspace" in params
    assert "phase_prompt" in params
    assert "model" in params
    assert "pristine_hash" in params
    assert "profile" in params
