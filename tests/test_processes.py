import sys
import time

import harness.processes as processes
from harness.processes import run_process


def test_run_process_returns_an_ordinary_completed_child(tmp_path):
    result = run_process(
        [sys.executable, "-c", "print('complete')"],
        cwd=tmp_path,
        timeout=1,
    )

    assert result.timed_out is False
    assert result.returncode == 0
    assert result.stdout == "complete\n"


def test_run_process_kills_a_timed_out_child_group(tmp_path):
    marker = tmp_path / "grandchild-survived"
    child_program = (
        f"import time; time.sleep(0.4); open({str(marker)!r}, 'w').write('alive')"
    )
    program = (
        "import subprocess, sys, time; "
        "print('started', flush=True); "
        f"subprocess.Popen([sys.executable, '-c', {child_program!r}]); "
        "time.sleep(30)"
    )

    result = run_process([sys.executable, "-c", program], cwd=tmp_path, timeout=0.1)
    time.sleep(0.6)

    assert result.timed_out is True
    assert result.stdout == "started\n"
    assert not marker.exists()


def test_run_process_escalates_when_the_child_ignores_termination(tmp_path, monkeypatch):
    monkeypatch.setattr(processes, "_DRAIN_TIMEOUT", 0.1)
    program = "import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)"

    result = run_process([sys.executable, "-c", program], cwd=tmp_path, timeout=0.1)

    assert result.timed_out is True
    assert result.returncode is not None
