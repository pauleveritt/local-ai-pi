# harness/session.py
"""Run one pi subprocess in a disposable workspace.
"""
import os
import signal
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from harness.grading import grade_acceptance
from harness.telemetry import (
    RunTelemetry, compute_task_duration_s, has_subagent_calls,
    inherited_file_activity, is_false_self_report, read_run,
)
from harness.workspace import capture_diff, seed_file_paths

# Resolve repo root for stable paths regardless of CWD.
_REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class InvocationProfile:
    """Describes how to invoke pi for a session."""
    extensions: list[str]     # --extension paths (empty = none beyond built-in)
    append_system_prompt: str | None = None  # --append-system-prompt path
    no_extensions: bool = True  # --no-extensions (strip global config)
    timeout: int | None = None  # override the default timeout (None = use caller's default)
    expects_delegation: bool = False  # expect subagent tool calls; False = plain run (SP1)

    @staticmethod
    def sp1() -> "InvocationProfile":
        """The SP1 profile: hello-world extension only."""
        return InvocationProfile(
            extensions=[".pi/extensions/hello-world.ts"],
            timeout=300,
        )

    @staticmethod
    def sp2(subagent_path: str) -> "InvocationProfile":
        """The SP2 profile: subagent extension + orchestrator prompt.

        The append_system_prompt path is relative — prepare_workspace copies
        prompts/ into the workspace so it resolves from the child's CWD."""
        return InvocationProfile(
            extensions=[subagent_path],
            append_system_prompt="prompts/orchestrator.md",
            timeout=900,
            expects_delegation=True,
        )


@dataclass
class SessionResult:
    run_id: str
    outcome: str            # "exited" | "timeout" | "no-delegation"
    returncode: int | None
    telemetry: RunTelemetry
    changed_files: list[str]
    diff: str
    tests_pass: bool
    wall_time_s: float
    artifact_path: str
    task_duration_s: float | None = None  # first-to-terminal timestamp delta from artifact; None if uncomputable
    stderr_text: str = ""   # captured stderr for diagnostics
    pytest_stdout: str = ""  # harness pytest stdout (for failure diagnosis)
    pytest_stderr: str = ""  # harness pytest stderr
    # Amendment 3: did the MODEL's own suite pass? None when not evaluated.
    # model_tests_pass=True with tests_pass=False is the false-self-report signal.
    model_tests_pass: bool | None = None
    # Files that would have steered grading, removed/restored before acceptance.
    grading_env_tampered: list[str] = field(default_factory=list)
    acceptance_tests_executed: int = 0
    acceptance_tests_expected: int = 0
    # Task 7 (grading-path reboot) -- standing behavioral instrumentation,
    # Amendment 2. Empty/"untouched" for an unseeded (phase-1) run.
    inherited_write_attempts: list[str] = field(default_factory=list)
    shared_file_classification: str = "untouched"  # "replace" | "extend" | "untouched"
    false_self_report: bool = False

    @property
    def is_success(self) -> bool:
        """A run is successful when it exited (or exited-with-hang), tests pass,
        and files changed. exited-with-hang means the agent completed its work
        but the process lifecycle misbehaved (server hang, failure to exit).
        Treating it as failure would charge task-level metrics for server
        symptoms uncorrelated with the interventions under test."""
        return (
            self.outcome in ("exited", "exited-with-hang")
            and self.tests_pass
            and len(self.changed_files) > 0
        )


def run_session(
    workspace: str | Path,
    phase_prompt: str,
    model: str,
    pristine_hash: str,
    profile: InvocationProfile,
    timeout: int = 300,
    acceptance_suite: str | Path | None = None,
    max_startup_attempts: int = 3,
    research_dir: Path | None = None,
    seed: str | Path | None = None,
) -> SessionResult:
    """Run pi headless in workspace against one phase prompt.

    Spawns `pi --mode json -p --no-session` with isolation flags from the
    InvocationProfile. After pi exits, runs git diff against pristine_hash
    and uv run pytest for the acceptance oracle.

    Retries on empty-stdout timeout (startup hang) up to max_startup_attempts.
    """
    workspace = Path(workspace)
    run_id = uuid.uuid4().hex[:12]

    # Ensure the research sessions directory exists.
    if research_dir is not None:
        sessions_dir = research_dir / "sessions"
    else:
        sessions_dir = _REPO_ROOT / "docs" / "superpowers" / "research" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = sessions_dir / f"{run_id}.jsonl"

    # Use profile timeout if set, otherwise caller's default.
    effective_timeout = profile.timeout if profile.timeout is not None else timeout

    stdout_text = ""
    stderr_text = ""
    pi_exe = _find_pi()

    # Prompt is written to a temp file and passed via @file syntax.
    prompt_file = workspace / f".pi-eval-prompt-{run_id}.txt"
    prompt_file.write_text(phase_prompt)

    # Build pi_cmd from the invocation profile.
    pi_cmd = [
        pi_exe,
        "--mode", "json",
        "-p",
        "--no-session",
        "--model", model,
        "--no-skills",
        "--no-prompt-templates",
        "--no-themes",
        "--no-context-files",
        "--approve",
    ]

    if profile.no_extensions:
        pi_cmd.append("--no-extensions")
    for ext in profile.extensions:
        pi_cmd.extend(["--extension", ext])
    if profile.append_system_prompt:
        pi_cmd.extend(["--append-system-prompt", profile.append_system_prompt])

    pi_cmd.append(f"@{prompt_file}")

    env = dict(os.environ)
    t0 = time.monotonic()
    proc = None
    timed_out = False
    prior_killed = False  # True if any earlier attempt was killed (hung)

    # Retry loop for startup hangs (empty-stdout timeouts).
    #
    # Incident, 2026-07-27 (Rule 8 review -- Fable): a batch run hung for
    # ~45-60 min with no progress and no oMLX traffic. Root cause, confirmed
    # by code: pi is an agentic CLI that shells out (bash, pytest, git); a
    # grandchild it spawns can inherit these pipes' write ends. proc.kill()
    # only signals the DIRECT child -- if pi dies but a grandchild still
    # holds a pipe open, proc.communicate() blocks forever waiting for EOF
    # that never comes, even though the direct child is already a zombie
    # (this matched every observed symptom exactly: child zombie, parent
    # still blocked, no model traffic since nothing was left running).
    # start_new_session=True gives pi and everything it spawns one process
    # group; killing the whole group on timeout, not just the direct PID,
    # closes the leak. The drain communicate() also now has its own
    # timeout, so even a group-escaped process (e.g. a double-forked
    # daemon) can't wedge the harness indefinitely.
    for attempt in range(1, max_startup_attempts + 1):
        timed_out = False  # reset per attempt — only THIS attempt's result matters
        try:
            proc = subprocess.Popen(
                pi_cmd,
                cwd=str(workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                env=env,
                start_new_session=True,
            )
            stdout_text, stderr_text = proc.communicate(timeout=effective_timeout)
            if stdout_text.strip():
                break  # got output, not a startup hang
            # Non-timeout empty exit — don't retry.
            if proc.returncode is not None:
                break
        except subprocess.TimeoutExpired:
            prior_killed = True
            _killpg_or_kill(proc)
            try:
                stdout_text, stderr_text = proc.communicate(timeout=30)
            except subprocess.TimeoutExpired as drain_timeout:
                # A process outside pi's own group is still holding a pipe
                # open (e.g. escaped via double-fork). Kill the group again
                # and take whatever partial output the drain captured
                # rather than block indefinitely.
                #
                # Rule 8 review, 2026-07-27 (Fable): even though Popen was
                # created with text=True, TimeoutExpired.stdout/.stderr are
                # bytes, not str -- CPython builds the exception directly
                # from the raw byte buffers on this path with no decoding
                # step. Passing bytes to artifact_path.write_text() below
                # would crash the whole batch with no except around it in
                # runner.py -- worse than the hang this fix closes.
                _killpg_or_kill(proc)
                stdout_text = _decode_partial(drain_timeout.stdout)
                stderr_text = _decode_partial(drain_timeout.stderr)
            if stdout_text.strip():
                # Got real output — not a startup hang, the process just
                # failed to exit cleanly. Don't mark this as timed_out.
                timed_out = False
                break
            else:
                timed_out = True  # empty output on timeout = true startup hang
        if attempt < max_startup_attempts:
            continue

    # Determine outcome:
    # - Timed out on final attempt → "timeout"
    # - Completed but a prior attempt was killed → "exited-with-hang"
    # - Completed cleanly → "exited"
    if timed_out:
        outcome = "timeout"
    elif prior_killed:
        outcome = "exited-with-hang"
    else:
        outcome = "exited"
    returncode = proc.returncode if proc is not None else None
    wall_time_s = time.monotonic() - t0

    # Persist the captured stdout as the session artifact.
    artifact_path.write_text(stdout_text)

    # Compute task duration from artifact timestamps.
    task_duration_s = compute_task_duration_s(artifact_path)

    # Parse telemetry.
    telemetry = read_run(artifact_path)

    # Detect no-delegation when the profile expects subagent calls
    # but none occurred. Only fire when expects_delegation is True —
    # plain baselines (SP1) never delegate by design.
    if outcome == "exited" and profile.expects_delegation and not has_subagent_calls(artifact_path):
        outcome = "no-delegation"

    # Git diff against the pristine commit, plus (when seeded) a hash
    # comparison of every seeded file against its reference source.
    changed_files, diff_text = capture_diff(workspace, pristine_hash, seed=seed)

    # --- Acceptance (Amendment 3) ----------------------------------------
    # The grade is the HARNESS-OWNED suite, overlaid now that the model has
    # finished so it cannot edit what judges it. The model's own tests are run
    # separately as a signal, never as the grade: model-tests-pass while
    # acceptance fails is the "false self-report" failure mode.
    model_tests_pass: bool | None = None
    grading_env_tampered: list[str] = []
    if acceptance_suite is not None:
        suite_src = Path(acceptance_suite).resolve()
        if not suite_src.is_file():
            raise FileNotFoundError(f"acceptance suite not found: {suite_src}")

        # Model's own suite first, before we overlay anything.
        try:
            own = subprocess.run(
                ["uv", "run", "pytest", "-q"],
                cwd=workspace, capture_output=True, text=True,
                timeout=effective_timeout,
            )
            model_tests_pass = own.returncode == 0
        except subprocess.TimeoutExpired:
            model_tests_pass = False

        # Grade in a fresh harness-owned directory. No model-controlled
        # configuration, modules, or workspace paths enter this process.
        # Verified defeats (2026-07-24), both exit 0 so tests_pass would be True:
        #   - a model-written conftest.py can skip-mark every collected test
        #     (pytest exits 0 on all-skipped), neutralizing the contract;
        #   - pyproject.toml is excluded from capture_diff, so a model edit to
        #     pytest config would steer grading INVISIBLY.
        # Both are recorded as evidence rather than silently repaired.
        grade = grade_acceptance(workspace, suite_src, effective_timeout)
        tests_pass = grade.passed
        pytest_stdout = grade.stdout
        pytest_stderr = grade.stderr
        grading_env_tampered = grade.refused_config_files
        acceptance_tests_executed = grade.tests_executed
        acceptance_tests_expected = grade.tests_expected
    else:
        tests_pass = False
        pytest_stdout = ""
        pytest_stderr = ""
        acceptance_tests_executed = 0
        acceptance_tests_expected = 0

    # Task 7 -- standing behavioral instrumentation (Amendment 2).
    inherited_files = seed_file_paths(seed) if seed is not None else frozenset()
    activity = inherited_file_activity(artifact_path, inherited_files)
    false_self_report = is_false_self_report(model_tests_pass, tests_pass)

    return SessionResult(
        run_id=run_id,
        outcome=outcome,
        returncode=returncode,
        telemetry=telemetry,
        changed_files=changed_files,
        diff=diff_text,
        tests_pass=tests_pass,
        wall_time_s=wall_time_s,
        artifact_path=str(artifact_path),
        task_duration_s=task_duration_s,
        stderr_text=stderr_text,
        pytest_stdout=pytest_stdout,
        pytest_stderr=pytest_stderr,
        model_tests_pass=model_tests_pass,
        grading_env_tampered=grading_env_tampered,
        acceptance_tests_executed=acceptance_tests_executed,
        acceptance_tests_expected=acceptance_tests_expected,
        inherited_write_attempts=activity.write_attempts,
        shared_file_classification=activity.classification,
        false_self_report=false_self_report,
    )


def _find_pi() -> str:
    """Find the pi binary. Raises RuntimeError if not on PATH."""
    import shutil
    path = shutil.which("pi")
    if not path:
        raise RuntimeError("pi not found on PATH — is it installed?")
    return path


def _killpg_or_kill(proc: subprocess.Popen) -> None:
    """Kill pi's whole process group, not just the direct PID -- proc.kill()
    alone leaves any grandchild that inherited the stdout/stderr pipes free
    to keep them open, which hangs proc.communicate() forever even after
    the direct child is dead (2026-07-27 incident). Requires
    start_new_session=True at Popen time so pi's group id equals its own
    pid. Falls back to a direct kill if the group is already gone."""
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        proc.kill()


def _decode_partial(output: str | bytes | None) -> str:
    """Normalize TimeoutExpired.stdout/.stderr to str. Despite Popen being
    created with text=True, CPython's TimeoutExpired carries raw bytes on
    this path (built directly from the byte buffers, no decode step) --
    verified against a real text-mode Popen, not assumed (Rule 8 review,
    2026-07-27 -- Fable). Passing bytes to Path.write_text() downstream
    would crash the whole batch."""
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode(errors="replace")
    return output
