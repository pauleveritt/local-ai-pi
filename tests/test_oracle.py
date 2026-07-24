"""Oracle validation: the acceptance oracle must pass a known-good solution.

If this test fails, no measurement batch may be trusted or published.
Re-run it whenever harness/workspace.py or the acceptance command changes.
Motivated by docs/section-2-measurement/research/2026-07-24-oracle-invalid-incident.md
"""
import shutil
import subprocess
from pathlib import Path

from harness.workspace import prepare_workspace

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCE = REPO_ROOT / "examples" / "reference" / "phase-1"


def test_oracle_accepts_reference_solution():
    """Provision the production app_source, overlay the reference solution,
    and assert the acceptance oracle passes — exercising the exact workspace
    shape measurement runs use."""
    workspace, _pristine_hash = prepare_workspace(
        REPO_ROOT / "examples" / "agentclinic"
    )
    # The provisioned workspace must not contain the answer key.
    assert not (workspace / "reference").exists(), (
        "reference/ leaked into the provisioned workspace — "
        "the answer key contaminates every measurement run"
    )
    # Overlay the reference solution files into the workspace root.
    for src in REFERENCE.rglob("*"):
        if src.is_file():
            dest = workspace / src.relative_to(REFERENCE)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    proc = subprocess.run(
        ["uv", "run", "pytest", "-q"],
        cwd=workspace, capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 0, (
        f"Oracle rejected the reference solution.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )


REFERENCE_PHASE2 = REPO_ROOT / "examples" / "reference" / "phase-2"


def test_oracle_accepts_seeded_phase2_reference_solution():
    """Amendment 1 gate: provision with the phase-1 seed (the canonical
    phase-2 start state), overlay the phase-2 reference solution, and assert
    the acceptance oracle passes. Green before any seeded phase-2 batch."""
    workspace, _pristine_hash = prepare_workspace(
        REPO_ROOT / "examples" / "agentclinic",
        seed=REFERENCE,
    )
    # The seed must actually be present in the start state.
    assert (workspace / "app.py").exists(), "phase-1 seed missing from workspace"
    assert not (workspace / "reference").exists()
    # Overlay the cumulative phase-2 reference solution.
    for src in REFERENCE_PHASE2.rglob("*"):
        if src.is_file():
            dest = workspace / src.relative_to(REFERENCE_PHASE2)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    proc = subprocess.run(
        ["uv", "run", "pytest", "-q"],
        cwd=workspace, capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 0, (
        f"Oracle rejected the seeded phase-2 reference solution.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )


def test_seed_lands_in_pristine_baseline():
    """The seed must be committed into the pristine git baseline so
    changed_files reflects only the model's phase-N work."""
    from harness.workspace import capture_diff

    workspace, pristine_hash = prepare_workspace(
        REPO_ROOT / "examples" / "agentclinic",
        seed=REFERENCE,
    )
    changed, _diff = capture_diff(workspace, pristine_hash)
    assert changed == [], (
        f"seeded files appear as changes against pristine: {changed}"
    )


# ---------------------------------------------------------------------------
# Amendment 3: the acceptance suite is harness-owned and must be non-vacuous.
# Tainie's campaign found its repo-pytest oracle collected zero tests on all
# 34 targets and was silently vacuous. Both directions are gated here.
# ---------------------------------------------------------------------------

import pytest

from harness.workspace import acceptance_suite_for_phase, seed_for_phase


def _suite_is_authored(phase: int) -> bool:
    return "test_suite_is_authored" not in acceptance_suite_for_phase(phase).read_text()


def _workspace_with(phase: int, solution: Path) -> Path:
    ws, _ = prepare_workspace(
        REPO_ROOT / "examples" / "agentclinic", seed=seed_for_phase(phase)
    )
    for src in solution.rglob("*"):
        if src.is_file():
            dest = ws / src.relative_to(solution)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    dest = ws / "tests" / "test_acceptance.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(acceptance_suite_for_phase(phase), dest)
    return ws


def _run_acceptance(ws: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", "pytest", "-q", "tests/test_acceptance.py"],
        cwd=ws, capture_output=True, text=True, timeout=300,
    )


@pytest.mark.parametrize("phase", [1, 2, 3])
def test_acceptance_suite_accepts_reference(phase: int):
    """Direction 1: the suite must PASS the reference solution."""
    if not _suite_is_authored(phase):
        pytest.skip(f"phase-{phase} acceptance suite is an unauthored skeleton")
    ref = REPO_ROOT / "examples" / "reference" / f"phase-{phase}"
    if not ref.is_dir():
        pytest.skip(f"no reference solution for phase {phase}")
    proc = _run_acceptance(_workspace_with(phase, ref))
    assert proc.returncode == 0, (
        f"acceptance suite rejected the phase-{phase} reference solution\n"
        f"{proc.stdout}\n{proc.stderr}"
    )


@pytest.mark.parametrize("phase", [1, 2, 3])
def test_acceptance_suite_rejects_broken_solution(phase: int):
    """Direction 2 (non-vacuity): the suite must FAIL a deliberately broken
    solution. A suite that passes everything grades nothing."""
    if not _suite_is_authored(phase):
        pytest.skip(f"phase-{phase} acceptance suite is an unauthored skeleton")
    ref = REPO_ROOT / "examples" / "reference" / f"phase-{phase}"
    if not ref.is_dir():
        pytest.skip(f"no reference solution for phase {phase}")
    ws = _workspace_with(phase, ref)
    # Break the contract in the most basic way available: remove the home route
    # body so the tagline can no longer render.
    app_py = ws / "app.py"
    app_py.write_text(
        "from fastapi import FastAPI\n\napp = FastAPI()\n"
    )
    proc = _run_acceptance(ws)
    assert proc.returncode != 0, (
        f"phase-{phase} acceptance suite PASSED a deliberately broken solution "
        f"— the oracle is vacuous.\n{proc.stdout}"
    )
