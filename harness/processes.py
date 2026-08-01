import os
import signal
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

_DRAIN_TIMEOUT = 5


@dataclass(frozen=True)
class ProcessResult:
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool


def run_process(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout: int | float,
    env: dict[str, str] | None = None,
) -> ProcessResult:
    """Run one child with a bounded timeout and process-group teardown."""
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _signal_process_group(process, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=_DRAIN_TIMEOUT)
        except subprocess.TimeoutExpired:
            _signal_process_group(process, signal.SIGKILL)
            try:
                stdout, stderr = process.communicate(timeout=_DRAIN_TIMEOUT)
            except subprocess.TimeoutExpired as forced_error:
                stdout = _as_text(forced_error.stdout)
                stderr = _as_text(forced_error.stderr)
        return ProcessResult(process.returncode, stdout, stderr, timed_out=True)
    return ProcessResult(process.returncode, stdout, stderr, timed_out=False)


def _signal_process_group(process: subprocess.Popen[str], signal_number: int) -> None:
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal_number)
        else:
            process.send_signal(signal_number)
    except ProcessLookupError:
        pass


def _as_text(output: str | bytes | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode(errors="replace")
    return output
