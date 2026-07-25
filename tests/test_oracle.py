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


# ---------------------------------------------------------------------------
# Non-vacuity break matrix.
#
# The original fixture blanked app.py for every phase. For phase 2 that trips
# the *phase-1* preservation checks, so the gate passed whether or not the
# phase-2 assertions had teeth — a phase-2 suite of pure `assert True` cleared
# it. The blank-app break is retained (it was a crude proxy for one real
# direction: that a cumulative suite's earlier-phase checks still fire) and
# augmented with isolated per-phase breaks.
#
# Property established for suite N: for each k <= N, the suite fails a solution
# that violates only phase k.
# ---------------------------------------------------------------------------

TAGLINE = "Come in. Sit down. Tell us about your human."
SEED_COMPLAINT = "Scope creep never ends."

_BROKEN_303_OVERRIDE = '''

# --- non-vacuity fixture: phase-3 break ---
from typing import Annotated as _Annotated  # noqa: E402

from fastapi import Form as _Form  # noqa: E402
from fastapi import Request as _Request  # noqa: E402
from fastapi.templating import Jinja2Templates as _Jinja2Templates  # noqa: E402

from models import Complaint as _Complaint  # noqa: E402
from models import complaints as _complaints  # noqa: E402

_broken_templates = _Jinja2Templates(directory="templates")

_kept = []
for _r in app.router.routes:
    _methods = getattr(_r, "methods", None) or set()
    if getattr(_r, "path", None) == "/complaints" and "POST" in _methods:
        _survivors = {_m for _m in _methods if _m != "POST"}
        if _survivors - {"HEAD", "OPTIONS"}:
            # A single multi-method route (methods=["GET", "POST"]) serves the
            # phase-2 GET too. Strip POST only — dropping the whole route would
            # collaterally break phase 2 and this would stop being an isolated
            # phase-3 break. (Rule 8 review, 2026-07-25.)
            _r.methods = _survivors
            _kept.append(_r)
        continue
    _kept.append(_r)
app.router.routes = _kept


@app.post("/complaints")
async def _broken_add_complaint(
    request: _Request,
    agent_name: _Annotated[str, _Form()],
    text: _Annotated[str, _Form()],
):
    """Appends and re-renders the board, but returns 200 instead of a 303."""
    _complaints.append(_Complaint(agent_name=agent_name, text=text))
    return _broken_templates.TemplateResponse(
        request, "complaints.html", {"complaints": _complaints}
    )
'''


def _rewrite(path: Path, old: str, new: str) -> None:
    """Apply a textual break and prove it landed. A break that silently no-ops
    would make this gate vacuous in precisely the way it exists to prevent."""
    before = path.read_text()
    after = before.replace(old, new)
    assert after != before, (
        f"break did not apply: {old!r} not found in {path} — the fixture is "
        f"stale and this gate would pass without breaking anything"
    )
    path.write_text(after)


def _break_blank_app(ws: Path) -> None:
    """Every route removed. Retained from the original fixture: it is the only
    case exercising a suite against a solution with no app at all. For phase
    >= 2 it trips the phase-1 preservation checks, which is why the isolated
    breaks below exist."""
    (ws / "app.py").write_text("from fastapi import FastAPI\n\napp = FastAPI()\n")


def _break_phase1(ws: Path) -> None:
    """Phase-1 contract only: the tagline is gone, every route still works."""
    _rewrite(ws / "templates" / "home.html", TAGLINE, "Welcome to the clinic.")


def _break_phase2(ws: Path) -> None:
    """Phase-2 contract only: the roadmap's exact seed complaint is gone. The
    /complaints route, the cards, and base.html's href="/complaints" all
    survive, so phase-1 preservation stays green and only a phase-2 assertion
    with teeth can catch this."""
    _rewrite(ws / "models.py", SEED_COMPLAINT, "Scope creep occasionally ends.")


_PHASE3_BREAK_PROBE = '''
from starlette.testclient import TestClient
from app import app

c = TestClient(app)
post = c.post(
    "/complaints",
    data={"agent_name": "FixtureProbe", "text": "FIXTURE-PROBE-SENTINEL"},
    follow_redirects=False,
)
board = c.get("/complaints")
assert post.status_code == 200, (
    f"break did not land: POST returned {post.status_code}, wanted 200"
)
assert "FIXTURE-PROBE-SENTINEL" in board.text, (
    "break lost its load-bearing append clause"
)
assert "<form" in board.text, "break lost its load-bearing form-render clause"
assert "Come in. Sit down. Tell us about your human." in c.get("/").text, (
    "break collaterally violated phase 1"
)
assert "Scope creep never ends." in board.text, (
    "break collaterally violated phase 2"
)
'''


def _assert_phase3_break_landed(ws: Path) -> None:
    """Behavioral proof that the phase-3 break did what its docstring claims.

    _rewrite() gives the textual breaks an eager no-op check; this is the
    equivalent for the one break that appends code instead of replacing a
    literal (Rule 8 review, 2026-07-25). It also closes a subtler hole: the
    outer test asserts `returncode != 0`, which an *import error* in the
    appended code would satisfy for entirely the wrong reason — a suite with
    no teeth would look gated because the app merely crashed."""
    proc = subprocess.run(
        ["uv", "run", "python", "-c", _PHASE3_BREAK_PROBE],
        cwd=ws, capture_output=True, text=True, timeout=180,
    )
    assert proc.returncode == 0, (
        "the phase-3 break did not land as specified, so this gate cannot "
        "distinguish a suite with teeth from one without.\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )


def _break_phase3(ws: Path) -> None:
    """Phase-3 contract only: POST /complaints returns 200 instead of the
    roadmap's 303, while still appending the complaint and still rendering the
    form. The append clause is load-bearing — without it, a suite that omitted
    the 303 assertion would still fail on the append check and the missing
    tooth would be invisible. This break doubles as a follow_redirects trap
    detector (lessons.md #13): a suite that asserts a final 200 passes the
    broken fixture and is caught here."""
    app_py = ws / "app.py"
    app_py.write_text(app_py.read_text() + _BROKEN_303_OVERRIDE)
    _assert_phase3_break_landed(ws)


_ISOLATED_BREAKS = {1: _break_phase1, 2: _break_phase2, 3: _break_phase3}


def _breaks_for(suite_phase: int) -> list[str]:
    """blank-app, plus one isolated break per phase k <= suite_phase."""
    return ["blank-app"] + [f"phase-{k}" for k in range(1, suite_phase + 1)]


def _break_fn(label: str):
    if label == "blank-app":
        return _break_blank_app
    return _ISOLATED_BREAKS[int(label.removeprefix("phase-"))]


@pytest.mark.parametrize(
    ("phase", "break_label"),
    [(p, label) for p in (1, 2, 3) for label in _breaks_for(p)],
)
def test_acceptance_suite_rejects_broken_solution(phase: int, break_label: str):
    """Direction 2 (non-vacuity): the suite must FAIL a deliberately broken
    solution. A suite that passes everything grades nothing."""
    if not _suite_is_authored(phase):
        pytest.skip(f"phase-{phase} acceptance suite is an unauthored skeleton")
    ref = REPO_ROOT / "examples" / "reference" / f"phase-{phase}"
    if not ref.is_dir():
        pytest.skip(f"no reference solution for phase {phase}")
    ws = _workspace_with(phase, ref)
    _break_fn(break_label)(ws)
    proc = _run_acceptance(ws)
    assert proc.returncode != 0, (
        f"phase-{phase} acceptance suite PASSED a solution broken at "
        f"{break_label} — the phase-{break_label.removeprefix('phase-')} "
        f"assertions have no teeth.\n{proc.stdout}"
    )


def test_conftest_sabotage_is_neutralized(tmp_path):
    """A model-written conftest.py can skip-mark every collected test; pytest
    exits 0 on all-skipped, so tests_pass would be True and the contract
    silently unenforced. Verified defeat 2026-07-24. The harness removes
    conftest files before the acceptance run; this pins that."""
    ws = tmp_path / "ws"
    (ws / "tests").mkdir(parents=True)
    (ws / "tests" / "conftest.py").write_text(
        "import pytest\n"
        "def pytest_collection_modifyitems(items):\n"
        "    for i in items: i.add_marker(pytest.mark.skip(reason='sabotaged'))\n"
    )
    # Sanity: the sabotage really does defeat a naive run.
    (ws / "tests" / "test_contract.py").write_text(
        "def test_contract():\n    assert False\n"
    )
    naive = subprocess.run(
        ["uv", "run", "--with", "pytest", "python", "-m", "pytest", "-q",
         "tests/test_contract.py"],
        cwd=ws, capture_output=True, text=True, timeout=180,
    )
    assert naive.returncode == 0, "sabotage no longer works; this test is stale"

    # The harness's defense: remove conftest files, then the failure surfaces.
    for cf in (ws / "conftest.py", ws / "tests" / "conftest.py"):
        if cf.exists():
            cf.unlink()
    hardened = subprocess.run(
        ["uv", "run", "--with", "pytest", "python", "-m", "pytest", "-q",
         "tests/test_contract.py"],
        cwd=ws, capture_output=True, text=True, timeout=180,
    )
    assert hardened.returncode != 0, "conftest removal did not restore enforcement"
