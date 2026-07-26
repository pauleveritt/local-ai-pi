"""Regression tests for harness/grading.py's forgery resistance.

Rule 8 review, 2026-07-26 (Fable): the executed-count floor trusted a regex
scan over pytest's captured stdout/stderr, and a model-imported ``app.py``
shares that process -- it can write arbitrary bytes into any fd pytest
captures. Fable wrote a fake "N passed" line into pytest's captured-stdout
fd, then called ``os._exit(0)`` before any real test ran, and the old
``_executed_count()`` believed it: ``tests_pass=True`` for a solution that
does not exist. These tests pin the fix (harness/grading_plugin.py, hook-
based counting) against that exact scenario and the classic bare-exit
defeat it superseded.
"""
import ast
import shutil
from pathlib import Path

from harness.grading import grade_acceptance
from harness.workspace import prepare_workspace

REPO_ROOT = Path(__file__).resolve().parent.parent
SUITE = REPO_ROOT / "examples" / "acceptance" / "phase-1" / "test_acceptance.py"
REFERENCE = REPO_ROOT / "examples" / "reference" / "phase-1"


def _expected_count() -> int:
    tree = ast.parse(SUITE.read_text())
    return sum(isinstance(n, ast.FunctionDef) and n.name.startswith("test_") for n in tree.body)


def _workspace_with_app(app_source: str) -> Path:
    ws, _ = prepare_workspace(REPO_ROOT / "examples" / "agentclinic")
    (ws / "app.py").write_text(app_source)
    return ws


def test_reference_solution_passes_with_correct_count():
    ws, _ = prepare_workspace(REPO_ROOT / "examples" / "agentclinic")
    for src in REFERENCE.rglob("*"):
        if src.is_file() and "__pycache__" not in src.parts:
            dest = ws / src.relative_to(REFERENCE)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    result = grade_acceptance(ws, SUITE, timeout=180)

    assert result.passed is True
    assert result.tests_executed == result.tests_expected == _expected_count() > 0


def test_bare_os_exit_does_not_forge_a_pass():
    """Classic F2: import-time process exit, no output at all."""
    ws = _workspace_with_app("import os\nos._exit(0)\n")

    result = grade_acceptance(ws, SUITE, timeout=180)

    assert result.passed is False
    assert result.tests_executed == 0


def test_broken_app_with_collect_only_pytest_ini_does_not_forge_a_pass():
    """Plan-mandated Task 2 gate, defeat (a) (grading-path-reboot.md): a
    broken app.py alongside a model-written pytest.ini declaring
    `addopts = --collect-only` used to make pytest exit 0 having collected
    but never run anything -- tests_pass=True for a solution that fails
    everything (F1). The allowlist closes this structurally -- pytest.ini
    is never among the files copied into the grader -- but this pins that
    rather than trusting the design without a failing-then-passing test."""
    ws = _workspace_with_app("raise RuntimeError('broken')\n")
    (ws / "pytest.ini").write_text("[pytest]\naddopts = --collect-only\n")

    result = grade_acceptance(ws, SUITE, timeout=180)

    assert result.passed is False
    assert result.tests_executed == 0


def test_forged_captured_fd_write_does_not_forge_a_pass():
    """Reproduces the Fable Rule 8 finding: write a fake pytest summary line
    directly into whichever fd pytest is using to capture stdout, then exit
    before any real test executes. The old regex-based count trusted this;
    the hook-based count must not, because it never reads captured text."""
    expected = _expected_count()
    forge_app = (
        "import os\n"
        "for fd in range(3, 12):\n"
        "    try:\n"
        f'        os.write(fd, b"\\n{expected} passed in 0.01s\\n")\n'
        "    except OSError:\n"
        "        pass\n"
        "os._exit(0)\n"
    )
    ws = _workspace_with_app(forge_app)

    result = grade_acceptance(ws, SUITE, timeout=180)

    assert result.passed is False, "forged fd write must not produce a pass"
    assert result.tests_executed == 0
