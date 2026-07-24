"""Oracle validation: the acceptance oracle must pass a known-good solution.

If this test fails, no measurement batch may be trusted or published.
Re-run it whenever harness/workspace.py or the acceptance command changes.
Motivated by docs/section-2-measurement/research/2026-07-24-oracle-invalid-incident.md
"""
import subprocess
from pathlib import Path

from harness.workspace import prepare_workspace

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCE_PHASE1 = REPO_ROOT / "examples" / "agentclinic" / "reference" / "phase-1"


def test_oracle_accepts_reference_solution():
    """Provision the reference solution through the real harness and assert
    the acceptance oracle (uv run pytest -q) passes."""
    # prepare_workspace copies app_dir into a disposable workspace, stamps
    # pyproject.toml (with pythonpath), runs uv sync, and inits git.
    # Using reference/phase-1 directly means the workspace contains exactly
    # the spec-compliant solution files — no extras, no conflicts.
    workspace, _pristine_hash = prepare_workspace(REFERENCE_PHASE1)
    proc = subprocess.run(
        ["uv", "run", "pytest", "-q"],
        cwd=workspace, capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 0, (
        f"Oracle rejected the reference solution.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )
