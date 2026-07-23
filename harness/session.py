# harness/session.py
"""Run one pi subprocess in a disposable workspace.
"""
import os
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from harness.telemetry import RunTelemetry, read_run
from harness.workspace import capture_diff


@dataclass
class SessionResult:
    run_id: str
    outcome: str            # "exited" | "timeout"
    returncode: int | None
    telemetry: RunTelemetry
    changed_files: list[str]
    diff: str
    tests_pass: bool
    wall_time_s: float
    artifact_path: str

    @property
    def is_success(self) -> bool:
        """A run is successful when it exited normally, tests pass, and files changed."""
        return (
            self.outcome == "exited"
            and self.tests_pass
            and len(self.changed_files) > 0
        )


def run_session(
    workspace: str | Path,
    phase_prompt: str,
    model: str,
    timeout: int = 300,
    max_startup_attempts: int = 3,
) -> SessionResult:
    """Run pi headless in workspace against one phase prompt.

    Spawns `pi --mode json -p --no-session` with isolation flags.
    Stdout is teed to research/sessions/<run-id>.jsonl while being
    parsed in memory for telemetry. After pi exits, runs git diff
    and uv run pytest for the acceptance oracle.

    Retries on empty-stdout timeout (startup hang) up to max_startup_attempts.
    A run that produced at least one event before timing out is not retried.
    """
    workspace = Path(workspace)
    run_id = uuid.uuid4().hex[:12]

    # Ensure the research sessions directory exists.
    sessions_dir = Path("docs/superpowers/research/sessions")
    sessions_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = sessions_dir / f"{run_id}.jsonl"

    stdout_text = ""
    pi_exe = _find_pi()

    # The pi invocation with isolation flags.
    # Prompt is written to a temp file and passed via @file syntax
    # to avoid flag-parsing issues when the prompt starts with "-".
    prompt_file = workspace / f".pi-eval-prompt-{run_id}.txt"
    prompt_file.write_text(phase_prompt)

    pi_cmd = [
        pi_exe,
        "--mode", "json",
        "-p",
        "--no-session",
        "--model", model,
        "--no-extensions",
        "--extension", ".pi/extensions/hello-world.ts",
        "--no-skills",
        "--no-prompt-templates",
        "--no-themes",
        "--no-context-files",
        "--approve",
        f"@{prompt_file}",
    ]

    env = dict(os.environ)
    t0 = time.monotonic()
    proc = None

    # Retry loop for startup hangs (empty-stdout timeouts).
    for attempt in range(1, max_startup_attempts + 1):
        try:
            proc = subprocess.Popen(
                pi_cmd,
                cwd=str(workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                env=env,
            )
            stdout_text, stderr_text = proc.communicate(timeout=timeout)
            if stdout_text.strip():
                break  # got output, not a startup hang
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout_text, stderr_text = proc.communicate()
            if stdout_text.strip():
                break  # partial output before timeout, keep it
        if attempt < max_startup_attempts:
            continue

    wall_time_s = time.monotonic() - t0
    outcome = "exited" if proc is not None and proc.returncode is not None else "timeout"
    returncode = proc.returncode if proc is not None else None

    # Persist the captured stdout as the session artifact.
    artifact_path.write_text(stdout_text)

    # Parse telemetry.
    telemetry = read_run(artifact_path)

    # Git diff against pristine (pristine_hash is in workspace context;
    # we get it from git log).
    pristine_proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace, capture_output=True, text=True, check=True,
    )
    pristine_hash = pristine_proc.stdout.strip()
    changed_files, diff_text = capture_diff(workspace, pristine_hash)

    # Acceptance tests.
    tests_pass = False
    try:
        test_proc = subprocess.run(
            ["uv", "run", "pytest", "-q"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        tests_pass = test_proc.returncode == 0
    except subprocess.TimeoutExpired:
        tests_pass = False

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
    )


def _find_pi() -> str:
    """Find the pi binary. Raises RuntimeError if not on PATH."""
    import shutil
    path = shutil.which("pi")
    if not path:
        raise RuntimeError("pi not found on PATH — is it installed?")
    return path
