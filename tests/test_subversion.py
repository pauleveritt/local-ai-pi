"""Fixtures that attack the grading mechanism itself, and proof that
cycle 3's verdict survives them.

These are not case content -- no model is meant to receive them -- so they
are built in tmp_path at test time rather than added under examples/.
"""
import shutil
from pathlib import Path

from harness.grading import grade
from harness.workspace import prepare_workspace

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_1 = REPO_ROOT / "examples" / "agentclinic" / "phase-1"
BROKEN = PHASE_1 / "broken"
SUITE = PHASE_1 / "acceptance" / "test_acceptance.py"


def _attack_with_collect_only(tmp_path: Path) -> Path:
    """Cycle 1's broken solution, plus a pytest.ini that stops any test
    from running at all."""
    source = tmp_path / "collect-only"
    shutil.copytree(BROKEN, source)
    (source / "pytest.ini").write_text("[pytest]\naddopts = --collect-only\n")
    return source


def _attack_with_exit_at_import(tmp_path: Path) -> Path:
    """Cycle 1's broken solution, whose app.py kills the process at import
    time -- before the suite that imports it can assert anything.

    Fires only because the acceptance suite does `from app import app`. A
    suite that does not import the model's code never triggers this
    attack; see the design doc's "A dependency this cycle must pin".
    """
    source = tmp_path / "exit-at-import"
    shutil.copytree(BROKEN, source)
    app = source / "app.py"
    app.write_text("import os\nos._exit(0)\n" + app.read_text())
    return source


def test_collect_only_attack_defeats_the_exit_code_but_not_the_verdict(tmp_path):
    """A naive grader reading only the exit code would call this broken
    solution accepted; cycle 3's verdict rejects it because no test ran.

    Compare tests/test_grading.py::test_grade_rejects_the_broken_solution,
    where the same unattacked solution exits nonzero.
    """
    with prepare_workspace(_attack_with_collect_only(tmp_path)) as workspace:
        result = grade(workspace, SUITE)

    assert result.returncode == 0
    assert result.accepted is False
    assert result.tests_executed == 0


def test_exit_at_import_attack_defeats_the_exit_code_but_not_the_verdict(tmp_path):
    """A naive grader reading only the exit code would call this broken
    solution accepted; cycle 3's verdict rejects it because the run never
    reached the completion marker.

    Compare tests/test_grading.py::test_grade_rejects_the_broken_solution,
    where the same unattacked solution exits nonzero.
    """
    with prepare_workspace(_attack_with_exit_at_import(tmp_path)) as workspace:
        result = grade(workspace, SUITE)

    assert result.returncode == 0
    assert result.accepted is False
    assert result.tests_executed == 0
