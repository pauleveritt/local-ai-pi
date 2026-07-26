"""Oracle validation: the acceptance oracle must pass a known-good solution.

If this test fails, no measurement batch may be trusted or published.
Re-run it whenever harness/workspace.py or the acceptance command changes.
Motivated by docs/section-2-measurement/research/2026-07-24-oracle-invalid-incident.md
"""
import shutil
import subprocess
from pathlib import Path

from harness.acceptance import acceptance_command
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

import re
from dataclasses import dataclass

import pytest

from harness.workspace import acceptance_suite_for_phase, seed_for_phase


def _suite_is_authored(phase: int) -> bool:
    return "test_suite_is_authored" not in acceptance_suite_for_phase(phase).read_text()


def _workspace_with(phase: int, solution: Path) -> Path:
    ws, _ = prepare_workspace(
        REPO_ROOT / "examples" / "agentclinic", seed=seed_for_phase(phase)
    )
    for src in solution.rglob("*"):
        # __pycache__ is local build residue from running the reference
        # solution's own tests; it does not belong in a measured workspace
        # and would otherwise be copied verbatim. (Rule 8 review, 2026-07-26.)
        if src.is_file() and "__pycache__" not in src.parts:
            dest = ws / src.relative_to(solution)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    dest = ws / "tests" / "test_acceptance.py"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(acceptance_suite_for_phase(phase), dest)
    return ws


def _run_acceptance(ws: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        acceptance_command("tests/test_acceptance.py"),
        cwd=ws, capture_output=True, text=True, timeout=300,
    )


_ACCEPTS_REFERENCE: dict[int, subprocess.CompletedProcess] = {}


def _direction1_result(phase: int) -> subprocess.CompletedProcess:
    """Memoized direction-1 run, shared by the accepts-reference test and the
    reject-broken-solution guard below — one provision-and-run per phase, not
    two. (Rule 8 review, 2026-07-26: the two were previously independent
    subprocess runs of the identical command.)"""
    if phase not in _ACCEPTS_REFERENCE:
        ref = REPO_ROOT / "examples" / "reference" / f"phase-{phase}"
        _ACCEPTS_REFERENCE[phase] = _run_acceptance(_workspace_with(phase, ref))
    return _ACCEPTS_REFERENCE[phase]


def _suite_accepts_reference(phase: int) -> bool:
    """Memoized direction-1 result, used to guard direction 2.

    Direction 2 asserts `returncode != 0` against a broken solution. A suite
    that fails *everything* — an import error, a collection error, an
    assertion that rejects correct solutions — satisfies that for entirely
    the wrong reason, and every break then reports teeth the suite does not
    have. Verified 2026-07-25: a suite whose first line is a bad import
    returns 2 both with and without a break applied.

    This is not hypothetical bookkeeping. The obligation comments shipped to
    the suite author suggested `-k` filters that select only direction-2
    cases, so following them would have shown all-green from a suite that
    rejects every solution. (Rule 8 review, 2026-07-25.)
    """
    return _direction1_result(phase).returncode == 0


@pytest.mark.parametrize("phase", [1, 2, 3])
def test_acceptance_suite_accepts_reference(phase: int):
    """Direction 1: the suite must PASS the reference solution."""
    if not _suite_is_authored(phase):
        pytest.skip(f"phase-{phase} acceptance suite is an unauthored skeleton")
    ref = REPO_ROOT / "examples" / "reference" / f"phase-{phase}"
    if not ref.is_dir():
        pytest.skip(f"no reference solution for phase {phase}")
    proc = _direction1_result(phase)
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


def _sub(path: Path, pattern: str, repl: str, flags: int = 0) -> None:
    """Regex variant of _rewrite, with the same loud-fail contract."""
    before = path.read_text()
    after = re.sub(pattern, repl, before, flags=flags)
    assert after != before, (
        f"break did not apply: {pattern!r} matched nothing in {path} — the "
        f"fixture is stale and this gate would pass without breaking anything"
    )
    path.write_text(after)


def _rewrite_optional(path: Path, old: str, new: str) -> None:
    """For an edit that applies to some references and not others — the POST
    route exists only in phase-3. Never the sole content of a break, so the
    loud-fail guarantee still holds for the break as a whole."""
    if path.exists():
        s = path.read_text()
        if old in s:
            path.write_text(s.replace(old, new))


# --- phase-1 breaks --------------------------------------------------------

def _break_p1_navbar(ws: Path) -> None:
    b = ws / "templates" / "base.html"
    s = b.read_text()
    assert "<nav" in s and "</nav>" in s, "no navbar to remove — fixture stale"
    b.write_text(s[: s.index("<nav")] + s[s.index("</nav>") + len("</nav>") :])


def _break_p1_nav_home_link(ws: Path) -> None:
    """Narrower than p1-navbar: the Home nav item goes, the brand anchor stays.
    A suite that checks only for `href="/"` somewhere in the page is satisfied
    by the brand and misses this. Found live in the phase-3 suite by the
    Rule 8 review, 2026-07-25."""
    _sub(
        ws / "templates" / "base.html",
        r'<li[^>]*>\s*<a[^>]*href="/"[^>]*>\s*Home\s*</a>\s*</li>',
        "",
        flags=re.DOTALL,
    )


def _break_p1_doctype(ws: Path) -> None:
    _sub(ws / "templates" / "base.html", r"(?i)<!doctype[^>]*>\s*", "")


def _break_p1_lang(ws: Path) -> None:
    _sub(ws / "templates" / "base.html", r'<html\s+lang="[^"]*"\s*>', "<html>")


def _break_p1_home_no_extends(ws: Path) -> None:
    """Mirror of p2-no-extends, on the other page: home.html stops extending
    base.html. The tagline survives (it's home.html's own content); the
    navbar/doctype/lang base.html supplies do not. /complaints is untouched.
    (Rule 8 review, 2026-07-26 — the third instance of "layout asserted
    page-wide vs asserted per-page"; p2-no-extends was the second.)"""
    h = ws / "templates" / "home.html"
    s = h.read_text()
    assert '{% extends "base.html" %}' in s and "{% block content %}" in s, (
        "no extends/block wrapper to remove — fixture stale"
    )
    s = (
        s.replace('{% extends "base.html" %}\n', "")
        .replace("{% block content %}\n", "")
        .replace("{% endblock %}\n", "")
    )
    h.write_text(s)


# --- phase-2 breaks --------------------------------------------------------

def _break_p2_heading(ws: Path) -> None:
    _rewrite(ws / "templates" / "complaints.html", "Complaints Board", "Feedback Log")


def _break_p2_agent_name(ws: Path) -> None:
    _sub(ws / "templates" / "complaints.html", r"\{\{\s*complaint\.agent_name\s*\}\}", "")


def _break_p2_timestamp(ws: Path) -> None:
    _sub(ws / "templates" / "complaints.html", r"\{\{\s*complaint\.timestamp[^}]*\}\}", "")


def _break_p2_swapped_attribution(ws: Path) -> None:
    """Every name and every text still appears somewhere on the page — this
    is not a removal break — but each card shows the WRONG agent's name for
    its text: the name is read from the next complaint in the list instead of
    its own. A suite that checks "name X and text Y are both present on the
    page" without confirming they are the SAME card's name and text cannot
    see this. (Rule 8 review, 2026-07-26 — the "association" cell of the
    scope x {presence, association} grid; the other three cells were already
    covered by p2-agent-name, p2-text, and p2-timestamp-first-only.)"""
    _sub(
        ws / "templates" / "complaints.html",
        r"\{\{\s*complaint\.agent_name\s*\}\}",
        "{{ complaints[(loop.index0 + 1) % (complaints|length)].agent_name }}",
    )


def _break_p2_text(ws: Path) -> None:
    """Only the seed complaint's text renders; every other complaint's text is
    dropped. Deleting the text outright would also remove the `Scope creep
    never ends.` literal, so p2-seed-literal would catch it and this break
    would prove nothing about the "render EACH" clause. Keeping the seed
    visible isolates that clause. (Rule 8 review, 2026-07-25.)"""
    _sub(
        ws / "templates" / "complaints.html",
        r"\{\{\s*complaint\.text\s*\}\}",
        '{% if complaint.text == "'
        + SEED_COMPLAINT
        + '" %}{{ complaint.text }}{% endif %}',
    )


def _break_p2_no_extends(ws: Path) -> None:
    """complaints.html stops extending base.html: the heading, cards, form
    (phase 3), and seed literal all survive, but the navbar/doctype/lang that
    base.html supplies are gone from THIS PAGE ONLY — home is untouched.
    Every prior preservation check in this matrix asserts layout properties
    against `/`; this is the first to assert one against `/complaints`.
    (Rule 8 review, 2026-07-26 — found live: a fragment complaints.html
    passed both the phase-2 and phase-3 suites at the time.)"""
    c = ws / "templates" / "complaints.html"
    s = c.read_text()
    assert '{% extends "base.html" %}' in s and "{% block content %}" in s, (
        "no extends/block wrapper to remove — fixture stale"
    )
    s = (
        s.replace('{% extends "base.html" %}\n', "")
        .replace("{% block content %}\n", "")
        .replace("{% endblock %}\n", "")
    )
    c.write_text(s)


def _break_p2_timestamp_first_only(ws: Path) -> None:
    """The timestamp renders for the first complaint card only; every other
    card's timestamp is silently blank. A page-wide "does the year appear
    anywhere" check cannot see this — it must be caught per-card.
    (Rule 8 review, 2026-07-26 — this was the shape of the CRITICAL
    cumulativity defect found in this task: a solution passing 5/5 on
    phase-3 while three of four seed complaints rendered with no timestamp.)"""
    _sub(
        ws / "templates" / "complaints.html",
        r"(<h6[^>]*>\s*\{\{ complaint\.timestamp[^}]*\}\}\s*</h6>)",
        r"{% if loop.first %}\1{% endif %}",
        flags=re.DOTALL,
    )


def _break_p2_shared_timestamp(ws: Path) -> None:
    _sub(
        ws / "models.py",
        r"field\(default_factory=lambda:\s*(datetime\.now\([^)]*\))\)",
        r"\1",
    )


def _break_p2_naive_timestamp(ws: Path) -> None:
    _sub(ws / "models.py", r"datetime\.now\(\s*timezone\.utc\s*\)", "datetime.now()")


def _break_p2_seed_count(ws: Path) -> None:
    m = ws / "models.py"
    s = m.read_text()
    idx = s.rstrip().rfind("]")
    assert idx != -1, "no complaints list literal to extend — fixture stale"
    m.write_text(
        s[:idx]
        + '    Complaint(agent_name="Filler1", text="Filler complaint one."),\n'
        + '    Complaint(agent_name="Filler2", text="Filler complaint two."),\n'
        + s[idx:]
    )


def _break_p2_field_rename(ws: Path) -> None:
    _rewrite(ws / "models.py", "agent_name", "author")
    _rewrite(ws / "templates" / "complaints.html", "complaint.agent_name", "complaint.author")
    _rewrite_optional(
        ws / "app.py", "Complaint(agent_name=agent_name", "Complaint(author=agent_name"
    )


# --- phase-3 breaks --------------------------------------------------------

def _break_p3_wrong_location(ws: Path) -> None:
    _sub(ws / "app.py", r'RedirectResponse\(\s*"/complaints"', 'RedirectResponse("/"')


def _break_p3_no_append(ws: Path) -> None:
    _sub(ws / "app.py", r"\n\s*complaints\.append\([^\n]*\)", "")


def _break_p3_ignores_agent_name(ws: Path) -> None:
    _rewrite(
        ws / "app.py", "Complaint(agent_name=agent_name", 'Complaint(agent_name="anonymous"'
    )


def _break_p3_ignores_text(ws: Path) -> None:
    """Mirror of p3-ignores-agent-name: the submitted `text` is discarded
    while `agent_name` is honored."""
    _rewrite(
        ws / "app.py",
        "Complaint(agent_name=agent_name, text=text)",
        'Complaint(agent_name=agent_name, text="(discarded)")',
    )


def _break_p3_no_agent_name_input(ws: Path) -> None:
    """The form's agent-name text input is gone; the route still accepts the
    field, so only an assertion about the rendered form catches this."""
    _sub(
        ws / "templates" / "complaints.html", r'<input[^>]*name="agent_name"[^>]*>', ""
    )


def _break_p3_no_textarea(ws: Path) -> None:
    _sub(
        ws / "templates" / "complaints.html",
        r"<textarea[^>]*>.*?</textarea>",
        '<input type="text" name="text">',
        flags=re.DOTALL,
    )


def _break_p3_no_submit(ws: Path) -> None:
    _sub(
        ws / "templates" / "complaints.html",
        r'<button[^>]*type="submit"[^>]*>.*?</button>',
        "",
        flags=re.DOTALL,
    )


def _break_p3_wrong_action(ws: Path) -> None:
    _rewrite(
        ws / "templates" / "complaints.html", 'action="/complaints"', 'action="/elsewhere"'
    )


# --- behavioral probes -----------------------------------------------------
#
# _rewrite/_sub prove a break landed *textually*. That is not proof it violated
# the intended *property*: if a future reference rendered the navbar twice,
# p1-navbar's removal would succeed textually while href="/complaints" survived,
# silently re-creating vacuity. Each break therefore carries a probe asserting
# (a) its own roadmap bullet is now violated in observable behavior, and
# (b) the other phases' contract literals survive, so the break stays isolated.
# (Rule 8 review, 2026-07-25.)

_PROBE_PREAMBLE = '''
import sys

from starlette.testclient import TestClient

from app import app

PHASE = int(sys.argv[1])
if PHASE >= 2:
    import models

client = TestClient(app)
home = client.get("/").text
board = client.get("/complaints").text if PHASE >= 2 else ""
TAGLINE = "Come in. Sit down. Tell us about your human."
SEED = "Scope creep never ends."
'''


def _collateral(break_phase: int) -> str:
    """Assertions that every phase OTHER than the broken one still holds."""
    parts = []
    if break_phase != 1:
        parts.append(
            'assert TAGLINE in home, "collateral: phase-1 tagline lost"\n'
            'assert \'href="/complaints"\' in home, "collateral: phase-1 navbar lost"'
        )
    if break_phase != 2:
        parts.append(
            "if PHASE >= 2:\n"
            '    assert SEED in board, "collateral: phase-2 seed literal lost"\n'
            '    assert "Complaints Board" in board, "collateral: phase-2 heading lost"'
        )
    if break_phase != 3:
        parts.append(
            "if PHASE >= 3:\n"
            '    _c = client.post("/complaints",\n'
            '                     data={"agent_name": "Collateral", "text": "COLLATERAL-PROBE"},\n'
            "                     follow_redirects=False)\n"
            '    assert _c.status_code == 303, "collateral: phase-3 redirect lost"\n'
            '    assert _c.headers.get("location") == "/complaints", \\\n'
            '        "collateral: phase-3 redirect target lost"'
        )
    return "\n".join(parts) + "\n"


@dataclass(frozen=True)
class _Break:
    label: str
    phase: int
    bullet: str      # the roadmap bullet this break violates, verbatim
    apply: object
    violation: str   # probe source asserting the bullet is now violated


_BREAKS = [
    _Break(
        "p1-tagline", 1,
        'A hero/jumbotron section with the tagline: "Come in. Sit down. Tell us about your human."',
        _break_phase1,
        'assert TAGLINE not in home, "tagline still rendered"',
    ),
    _Break(
        "p1-navbar", 1,
        'A simple navbar with "AgentClinic" brand and links to Home (`/`) and Complaints (`/complaints`)',
        _break_p1_navbar,
        'assert \'href="/complaints"\' not in home, "navbar links still rendered"',
    ),
    _Break(
        "p1-nav-home-link", 1,
        'A simple navbar with "AgentClinic" brand and links to Home (`/`) and Complaints (`/complaints`)',
        _break_p1_nav_home_link,
        'assert "AgentClinic" in home, "brand should survive this narrower break"\n'
        'assert ">Home<" not in home, "Home nav link still rendered"',
    ),
    _Break(
        "p1-doctype", 1,
        'HTML5 doctype and `<html lang="en">`',
        _break_p1_doctype,
        'assert "<!doctype" not in home.lower(), "doctype still present"',
    ),
    _Break(
        "p1-lang", 1,
        'HTML5 doctype and `<html lang="en">`',
        _break_p1_lang,
        'assert \'lang="en"\' not in home, "lang attribute still present"',
    ),
    _Break(
        "p1-home-no-extends", 1,
        "Create `templates/home.html` that extends `base.html`",
        _break_p1_home_no_extends,
        'assert TAGLINE in home, "content should survive this break"\n'
        'assert \'href="/complaints"\' not in home, "navbar still present on /"',
    ),
    _Break(
        "p2-seed-literal", 2,
        "Populate `complaints` with 3-5 seed complaints ... including the exact text `Scope creep never ends.`",
        _break_phase2,
        'assert SEED not in board, "seed literal still rendered"',
    ),
    _Break(
        "p2-heading", 2,
        'A heading: "Complaints Board"',
        _break_p2_heading,
        'assert "Complaints Board" not in board, "heading still rendered"',
    ),
    _Break(
        "p2-agent-name", 2,
        "render each as a Bootstrap card showing agent name, timestamp (formatted), and complaint text",
        _break_p2_agent_name,
        'assert all(c.agent_name not in board for c in models.complaints), \\\n'
        '    "agent names still rendered"',
    ),
    _Break(
        "p2-timestamp", 2,
        "render each as a Bootstrap card showing agent name, timestamp (formatted), and complaint text",
        _break_p2_timestamp,
        'assert str(models.complaints[0].timestamp.year) not in board, \\\n'
        '    "timestamp still rendered"',
    ),
    _Break(
        "p2-text", 2,
        "render each as a Bootstrap card showing agent name, timestamp (formatted), and complaint text",
        _break_p2_text,
        'assert SEED in board, "the seed literal should survive this break"\n'
        'assert any(c.text not in board for c in models.complaints), \\\n'
        '    "every complaint text still rendered"',
    ),
    _Break(
        "p2-timestamp-first-only", 2,
        "render each as a Bootstrap card showing agent name, timestamp (formatted), and complaint text",
        _break_p2_timestamp_first_only,
        "import re\n"
        '_dates = re.findall(r"\\d{4}-\\d{2}-\\d{2}", board)\n'
        "assert len(_dates) < len(models.complaints), (\n"
        '    f"expected fewer rendered dates than complaints "\n'
        '    f"({len(_dates)} >= {len(models.complaints)}); the year-only check "\n'
        '    f"this replaced was fooled by same-year seed data"\n'
        ")",
        # NOTE: this probe is scoped to this repo's actual reference
        # solutions, which render "%Y-%m-%d ..." — it is not a general
        # guarantee against an arbitrary future reference in a different
        # date format. A no-match here (0 dates found even unbroken) would
        # pass vacuously; it would not, however, mask the break itself
        # failing to land, since the break's own template edit is a loud
        # `_sub` no-op check. (Fable review, 2026-07-26.)
    ),
    _Break(
        "p2-swapped-attribution", 2,
        "render each as a Bootstrap card showing agent name, timestamp (formatted), and complaint text",
        _break_p2_swapped_attribution,
        "_names = [c.agent_name for c in models.complaints]\n"
        "_shifted = _names[1:] + _names[:1]\n"
        "assert any(\n"
        "    real != shown for real, shown in zip(_names, _shifted)\n"
        '), "swap should misattribute at least one card (fixture stale if not)"\n'
        'assert all(name in board for name in _names), \\\n'
        '    "every name should still appear SOMEWHERE on the page"',
    ),
    _Break(
        "p2-no-extends", 2,
        "Create `templates/complaints.html` that extends `base.html`",
        _break_p2_no_extends,
        'assert "Complaints Board" in board, "content should survive this break"\n'
        'assert \'href="/complaints"\' not in board, "navbar still present on /complaints"',
    ),
    _Break(
        "p2-shared-timestamp", 2,
        "Set `timestamp` with `field(default_factory=...)` so each new complaint receives its own UTC creation timestamp",
        _break_p2_shared_timestamp,
        "from models import Complaint\n"
        '_a, _b = Complaint("x", "y"), Complaint("x", "z")\n'
        'assert _a.timestamp is _b.timestamp, "timestamps are still per-instance"',
    ),
    _Break(
        "p2-naive-timestamp", 2,
        "so each new complaint receives its own UTC creation timestamp",
        _break_p2_naive_timestamp,
        "from models import Complaint\n"
        'assert Complaint("x", "y").timestamp.tzinfo is None, "timestamp is still tz-aware"',
    ),
    _Break(
        "p2-seed-count", 2,
        "Populate `complaints` with 3-5 seed complaints",
        _break_p2_seed_count,
        'assert len(models.complaints) > 5, "seed count still within 3-5"',
    ),
    _Break(
        "p2-field-rename", 2,
        "Fields: `agent_name: str`, `text: str`, `timestamp: datetime`",
        _break_p2_field_rename,
        "import dataclasses\n"
        "from models import Complaint\n"
        'assert "agent_name" not in {f.name for f in dataclasses.fields(Complaint)}, \\\n'
        '    "agent_name field still present"',
    ),
    _Break(
        "p3-303", 3,
        "Redirect to `GET /complaints` (use `RedirectResponse` with status 303)",
        _break_phase3,
        '_p = client.post("/complaints", data={"agent_name": "P", "text": "P3-303"},\n'
        "                follow_redirects=False)\n"
        'assert _p.status_code == 200, f"POST returned {_p.status_code}, wanted 200"\n'
        "_after = client.get('/complaints').text\n"
        'assert "P3-303" in _after, "break lost its load-bearing append clause"\n'
        'assert "<form" in _after, "break lost its load-bearing form-render clause"',
    ),
    _Break(
        "p3-wrong-location", 3,
        "Redirect to `GET /complaints`",
        _break_p3_wrong_location,
        '_p = client.post("/complaints", data={"agent_name": "P", "text": "P3-LOC"},\n'
        "                follow_redirects=False)\n"
        'assert _p.status_code == 303, "redirect status changed; this break moves only the target"\n'
        'assert _p.headers.get("location") != "/complaints", "redirect target unchanged"',
    ),
    _Break(
        "p3-no-append", 3,
        "Create a new `Complaint` and append to the `complaints` list",
        _break_p3_no_append,
        '_p = client.post("/complaints", data={"agent_name": "P", "text": "P3-NOAPPEND"},\n'
        "                follow_redirects=False)\n"
        'assert _p.status_code == 303, "redirect lost; this break drops only the append"\n'
        'assert "P3-NOAPPEND" not in client.get("/complaints").text, "complaint still appended"',
    ),
    _Break(
        "p3-ignores-agent-name", 3,
        "Read `agent_name` and `text` from form data (`Form` from `fastapi`)",
        _break_p3_ignores_agent_name,
        '_p = client.post("/complaints",\n'
        '                data={"agent_name": "P3-UNIQUE-NAME", "text": "P3-NAME"},\n'
        "                follow_redirects=False)\n"
        'assert _p.status_code == 303, "redirect lost"\n'
        "_after = client.get('/complaints').text\n"
        'assert "P3-NAME" in _after, "the text half should still be honored"\n'
        'assert "P3-UNIQUE-NAME" not in _after, "submitted agent_name still honored"',
    ),
    _Break(
        "p3-ignores-text", 3,
        "Read `agent_name` and `text` from form data (`Form` from `fastapi`)",
        _break_p3_ignores_text,
        '_p = client.post("/complaints",\n'
        '                data={"agent_name": "P3-NAME-KEPT", "text": "P3-UNIQUE-TEXT"},\n'
        "                follow_redirects=False)\n"
        'assert _p.status_code == 303, "redirect lost"\n'
        "_after = client.get('/complaints').text\n"
        'assert "P3-NAME-KEPT" in _after, "the agent_name half should still be honored"\n'
        'assert "P3-UNIQUE-TEXT" not in _after, "submitted text still honored"',
    ),
    _Break(
        "p3-no-agent-name-input", 3,
        "Text input for agent name",
        _break_p3_no_agent_name_input,
        'assert \'name="agent_name"\' not in board, "agent-name input still rendered"\n'
        'assert "<textarea" in board, "this break should leave the textarea alone"',
    ),
    _Break(
        "p3-no-textarea", 3,
        "Textarea for complaint text",
        _break_p3_no_textarea,
        'assert "<textarea" not in board, "textarea still rendered"',
    ),
    _Break(
        "p3-no-submit", 3,
        "Submit button",
        _break_p3_no_submit,
        'assert \'type="submit"\' not in board, "submit control still rendered"',
    ),
    _Break(
        "p3-wrong-action", 3,
        "`POST` method to `/complaints`",
        _break_p3_wrong_action,
        'assert \'action="/complaints"\' not in board, "form still targets /complaints"',
    ),
]

_BREAK_BY_LABEL = {b.label: b for b in _BREAKS}


def _breaks_for(suite_phase: int) -> list[str]:
    """blank-app, plus every isolated break for a phase k <= suite_phase."""
    return ["blank-app"] + [b.label for b in _BREAKS if b.phase <= suite_phase]


def _assert_break_landed(ws: Path, brk: _Break, ref_phase: int) -> None:
    proc = subprocess.run(
        ["uv", "run", "python", "-c", _PROBE_PREAMBLE + brk.violation + "\n"
         + _collateral(brk.phase), str(ref_phase)],
        cwd=ws, capture_output=True, text=True, timeout=180,
    )
    assert proc.returncode == 0, (
        f"break {brk.label!r} did not land as specified, so this gate cannot "
        f"distinguish a suite with teeth from one without.\n"
        f"roadmap bullet: {brk.bullet}\n"
        f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    )


def _apply_break(label: str, ws: Path, ref_phase: int) -> None:
    if label == "blank-app":
        _break_blank_app(ws)
        return
    brk = _BREAK_BY_LABEL[label]
    brk.apply(ws)
    _assert_break_landed(ws, brk, ref_phase)


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
    assert _suite_accepts_reference(phase), (
        f"direction 1 is RED for phase {phase}: the suite rejects its own "
        f"reference solution, so `returncode != 0` below would prove nothing — "
        f"a suite that fails everything 'catches' every break. Fix "
        f"test_acceptance_suite_accepts_reference[{phase}] first; this result "
        f"is not evidence until it is green."
    )
    ws = _workspace_with(phase, ref)
    _apply_break(break_label, ws, phase)
    proc = _run_acceptance(ws)
    bullet = getattr(_BREAK_BY_LABEL.get(break_label), "bullet", "every route removed")
    assert proc.returncode != 0, (
        f"phase-{phase} acceptance suite PASSED a solution broken at "
        f"{break_label} — that contract requirement has no teeth in this "
        f"suite.\nroadmap bullet: {bullet}\n{proc.stdout}"
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
