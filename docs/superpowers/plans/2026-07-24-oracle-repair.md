# Oracle Repair Implementation Plan

> **For agentic workers:** execute task-by-task, in order. Each task ends with a
> verification command and a commit. Do not reorder: the incident must be
> recorded before anything is repaired, and the oracle must be repaired and
> validated before any batch is re-run.

**Goal:** Record, repair, and re-measure after the discovery that the
acceptance oracle was invalid: the harness-stamped workspace fails pytest
collection for a textbook-correct Phase 1 solution, so every recorded baseline
(SP1 0/8; SP2 3/8 pre, 5/8 post, and the earlier 3/8→4/8 chain) measured an
unstated pytest-configuration puzzle, not model competence.

**Architecture of the fix:** one-line oracle repair in the workspace stamp; a
reference solution as a permanent fixture; an oracle-validation test that gates
all future measurement; superseded banners on every invalidated report; a
pre-registered scout-then-pool re-run protocol; narrative updates in every
document that cites the old numbers.

## The verified facts (use these verbatim in the incident report)

- `harness/workspace.py::_stamp_pyproject` writes a `pyproject.toml` with no
  `[tool.pytest.ini_options]` section and provisioning creates no
  `conftest.py`.
- `uv run pytest -q` does not put the workspace root on `sys.path` (unlike the
  prior course's `.venv/bin/python -m pytest`, where `python -m` adds cwd).
  So `import app` from `tests/test_app.py` fails at collection.
- Deterministic experiment (2026-07-24, no model involved): a spec-compliant
  Phase 1 solution in a freshly stamped workspace yields
  `ModuleNotFoundError: No module named 'app'` →
  `Interrupted: 1 error during collection` (pytest exit 2). Adding a single
  empty `tests/__init__.py` — a file the spec never mentions — makes the
  identical solution pass (`1 passed`).
- Therefore: every recorded success required the model to stumble onto one of
  two unstated workarounds (`tests/__init__.py` or a `sys.path` hack); every
  recorded failure includes runs that may have written correct code. The
  steered-vs-unsteered comparison is confounded (steered runs got more turns,
  hence more chances to find the workaround).
- The pytest exit-code detail matters and was previously misreported: exit 5 is
  "no tests collected"; exit 2 is "errors during collection" (an import crash).
  The failures were exit-2 collection crashes.

## Global constraints

- Do **not** delete any invalidated report or session JSONL. Superseded
  evidence stays on disk, banner-marked. The incident chapter depends on it.
- Do **not** modify `docs/lessons.md` (verbatim prior-course catalog). The new
  lesson lands in `docs/superpowers/policies/evidence.md` and the incident
  report.
- The oracle repair is exactly one addition to the stamped pyproject. No other
  workspace changes — the workload must stay otherwise identical.
- All re-run batches: model `omlx/gemma-4-12B-it-MLX-8bit`, fixed harness
  (verify preconditions in Task 3), report hang incidence, and state n and
  pooling explicitly.
- Every new report carries evidence-tier lines that are *assessed*, not
  template text.

---

### Task 1: Record the incident

**Create:** `docs/section-2-measurement/research/2026-07-24-oracle-invalid-incident.md`

Sections, in order:

1. **What happened** — the acceptance oracle (`uv run pytest -q` in the stamped
   workspace) fails a textbook-correct Phase 1 solution. One paragraph, then
   the two experiment transcripts (Run A fails collection, Run B with
   `tests/__init__.py` passes) as fenced blocks. Reproduce the experiment
   rather than pasting from memory: stamp a temp dir exactly as
   `_stamp_pyproject` does, write the reference solution from Task 2, run
   `uv run pytest -q` twice (without and with `tests/__init__.py`), capture
   real output.
2. **Root cause** — the two bullets from "verified facts" above, citing
   `harness/workspace.py::_stamp_pyproject` and the `python -m pytest` →
   `uv run pytest` command change relative to the prior course.
3. **What is invalidated** — a table listing every superseded report (the six
   files in Task 5) with their headline numbers, and one sentence: these
   numbers measured luck on an unstated workaround, not competence.
4. **What survives** — harness code, telemetry reader, subagent mechanism,
   prompts, all teaching content about method. Only the numbers regenerate.
5. **The doctrine extension** — "An oracle's verdict is not evidence until the
   oracle has been validated against a known-good solution." Note the
   precedent: the Tainie project's generalization campaign found its
   repo-pytest oracle vacuous (zero tests collected on all 34 targets) and ran
   an oracle-repair phase before trusting anything downstream.
6. **The repair and the re-run protocol** — link to Tasks 2–6 outcomes.

Tier line: GREEN — the experiment is deterministic and artifact-backed.

**Verify:** `uv run --group docs sphinx-build -b html docs docs/_build/html`
builds with no new warnings.

**Commit:** `evidence: oracle-invalid incident report — acceptance oracle fails correct solutions`

---

### Task 2: Reference solution fixture

**Create:** `examples/agentclinic/reference/phase-1/` with four files. This is
ground truth: the fully spec-compliant Phase 1 solution per
`examples/agentclinic/specs/roadmap.md`, with **no** pytest workarounds — no
`tests/__init__.py`, no `sys.path` manipulation, no conftest.

`app.py`:

```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request, "home.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", reload=True)
```

`templates/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="https://www.python.org/static/favicon.ico">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <title>{% block title %}AgentClinic{% endblock %}</title>
</head>
<body>
<nav class="navbar navbar-expand-lg bg-body-tertiary">
    <div class="container-fluid">
        <a class="navbar-brand" href="/">AgentClinic</a>
        <ul class="navbar-nav">
            <li class="nav-item"><a class="nav-link" href="/">Home</a></li>
            <li class="nav-item"><a class="nav-link" href="/complaints">Complaints</a></li>
        </ul>
    </div>
</nav>
{% block content %}{% endblock %}
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

`templates/home.html`:

```html
{% extends "base.html" %}
{% block content %}
<div class="container py-5">
    <div class="p-5 bg-body-tertiary rounded-3">
        <h1 class="display-5"><em>"Come in. Sit down. Tell us about your human."</em></h1>
        <p class="lead">Welcome to AgentClinic, a safe space for AI agents to air
            their grievances about the humans they work with.</p>
    </div>
</div>
{% endblock %}
```

`tests/test_app.py`:

```python
from starlette.testclient import TestClient

from app import app

client = TestClient(app)


def test_home_returns_200_and_tagline():
    response = client.get("/")
    assert response.status_code == 200
    assert "Come in. Sit down. Tell us about your human." in response.text
```

Add `examples/agentclinic/reference/README.md` (three sentences): what this is,
that it deliberately contains no pytest workarounds, and that the oracle-
validation test in `tests/test_oracle.py` provisions it through the real
harness and requires acceptance to pass.

**Verify:** files exist; no `__init__.py` anywhere under `reference/`.

**Commit:** `fixture: spec-compliant Phase 1 reference solution (no pytest workarounds)`

---

### Task 3: Repair the oracle

**Preconditions — verify before editing, stop and report if any fails:**

```bash
grep -n "expects_delegation" harness/session.py        # C1 fix present
grep -n "exited-with-hang" harness/session.py          # hang semantics present
grep -n "task_duration_s\|pytest_stdout" harness/*.py  # wall-time/output capture present
```

**Modify:** `harness/workspace.py::_stamp_pyproject` — append the pytest
config to the written pyproject so it becomes:

```toml
[project]
name = "agentclinic"
version = "0.1.0"
requires-python = ">=3.14,<3.15"
dependencies = [
    "fastapi[standard]==0.115.10",
    "uvicorn==0.51.0",
    "pytest==8.3.4",
]

[tool.pytest.ini_options]
pythonpath = ["."]
```

Add a comment above the write: this line is load-bearing — without it,
`uv run pytest` cannot import `app` from `tests/` and the acceptance oracle
fails correct solutions (link the incident report by path). The decision was
pyproject config, not `conftest.py`, matching how this course's own repo
solves the same problem.

**Create:** `tests/test_oracle.py` — the permanent gate:

```python
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
REFERENCE = REPO_ROOT / "examples" / "agentclinic" / "reference" / "phase-1"


def test_oracle_accepts_reference_solution(tmp_path):
    ws = prepare_workspace(
        REPO_ROOT / "examples" / "agentclinic", tmp_path / "ws"
    )
    workspace = Path(ws.path) if hasattr(ws, "path") else Path(ws)
    # ^ match prepare_workspace's actual return type; adjust after reading it.
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
```

Read `prepare_workspace`'s real signature/return first and adapt the two
marked lines; do not guess. If provisioning also needs the git/pristine-hash
step for `uv run` to work, mirror what `run_session` does before the pi spawn.

**Verify:** `uv run pytest tests/test_oracle.py -v` passes. Then confirm the
repair is what fixed it: temporarily comment the `pythonpath` line out, the
test must fail with the collection error; restore it.

**Commit:** `fix(harness): stamp pythonpath into workspace pyproject; oracle-validation test`

---

### Task 4: Extend the evidence policy

**Modify:** `docs/superpowers/policies/evidence.md` — add rule 6:

> 6. **Validate the oracle before trusting a batch.** An oracle's verdict is
>    not evidence until the oracle has been shown to accept a known-good
>    solution (see `tests/test_oracle.py`). Any change to the workload, the
>    workspace stamp, or the acceptance command re-triggers this validation
>    before the next published batch.

**Commit:** `policy: rule 6 — oracle validation gates every batch`

---

### Task 5: Mark every invalidated report superseded

**Modify** each of these six files by inserting, directly under the H1:

```markdown
```{warning}
**Superseded (2026-07-24).** The acceptance oracle behind this report was
invalid — it failed textbook-correct solutions — so these numbers measure an
unstated pytest-configuration workaround, not model competence. Kept for the
historical record. See the
[oracle-invalid incident report](<relative path to incident report>) and the
post-repair reports that replace this one.
```
```

Files (fix the relative link per location):

1. `docs/section-2-measurement/research/2026-07-23-baseline-phase-1.md` (0/8)
2. `docs/section-3-sdd/research/2026-07-23-sp2-baseline-phase-1.md` (3/8)
3. `docs/section-3-sdd/research/2026-07-23-sp2-baseline-phase-1-post-tuning.md` (4/8)
4. `docs/section-3-sdd/research/2026-07-24-sp2-baseline-phase-1.md` (3/8)
5. `docs/section-3-sdd/research/2026-07-24-sp2-baseline-phase-1-post-tuning.md` (5/8)
6. `docs/section-3-sdd/research/2026-07-24-sp2-deep-dive.md` (analysis built on the above; its drift *mechanism* findings remain informative — say so in its banner: the narrowing behavior was real, but it was partly a rational response to an unpassable command)

Session JSONLs stay untouched.

**Verify:** sphinx build clean; every banner link resolves.

**Commit:** `evidence: mark all pre-repair reports superseded`

---

### Task 6: Re-run protocol (pre-registered — execute exactly, no improvisation)

**Preconditions:** Tasks 1–5 committed; `tests/test_oracle.py` green; drift
metric present in the harness (`grep -in "drift" harness/*.py` — if absent,
implement the Section-3 cleanup brief's drift detection **before the steered
batches**; the unsteered scouts in step 1 may proceed without it).

**Step 1 — locate the ditch (unsteered scouts, n=4).** For each phase in
order (1, then 2, then 3): run n=4 with the SP1 (no-delegation) profile.
Decision rule, fixed in advance:
- 4/4 pass → this phase is solved; escalate to the next phase.
- ≤3/4 → this phase is the **candidate ditch**; stop escalating.
- If all three phases go 4/4: record that result honestly — the repaired
  workload has no Phase 1–3 ditch for this model — and stop; the roadmap
  decision about where the course's failure evidence comes from returns to
  the human. Do not invent a harder workload unilaterally.

**Step 2 — canonical unsteered baseline (pooled n=8).** At the candidate
ditch phase, run 4 more identical-config runs and pool with the scouts
(report as "n=8, pooled 4+4, same configuration").

**Step 3 — steered arms (n=8 each) at the same phase:**
- Arm A: subagent + orchestrator, **untuned** prompts (the SP2 pre-tuning
  configuration) — preserves Section 3's teaching arc.
- Arm B: subagent + orchestrator, **current tuned** prompts.

**Step 4 — reports.** One dated report per batch in the owning section's
`research/`: per-row tables with artifact links, success rate, hang incidence,
drift incidence (steered arms), task-duration mean, assessed tier lines, and
an explicit "oracle validated: `tests/test_oracle.py` green at commit `<sha>`"
line. Success-rate deltas at these n values are within noise unless extreme —
say so wherever two arms are compared.

**Commit** (per batch): `evidence: post-repair <arm> baseline, phase <N> (n=8)`

---

### Task 7: Update every document that cites the old numbers

Grep first, then edit each hit in context:

```bash
grep -rn "0/8\|3/8\|4/8\|5/8\|smoking gun\|the ditch" \
  README.md KICKOFF.md docs/index.md docs/how-this-was-built.md \
  docs/section-*/ docs/superpowers/roadmap.md --include="*.md" \
  | grep -v research/
```

Known required edits (the grep will find more):

- **`docs/superpowers/roadmap.md`** — SP1/SP2 Evidence links point to the
  post-repair reports (old links may stay, labeled "superseded"); the
  "Current phase" paragraph reflects the incident and re-run; add a one-line
  incident entry so the roadmap records that the evidence chain was rebuilt.
- **`KICKOFF.md`** — "What is done" numbers; add the incident report to the
  read-first list; the SP1 bullet's "0/8, the ditch" claim.
- **Section 2** — `smoking-gun.md` re-narrated around the post-repair ditch
  phase (and honestly noting Phase 1's old 0/8 was an oracle artifact);
  `eval-session.md` gains a short "validate the oracle" subsection pointing
  at `tests/test_oracle.py`.
- **Section 3** — `index.md` (0/8→4/8 arc), the implementer/orchestrator and
  lessons-from-handoff chapters: replace numbers; reframe the drift analysis
  ("narrowing" was partly a rational escape from an unpassable command —
  whether drift persists under a passable command is exactly what the
  post-repair batches answer).
- **Section 4** — `index.md` baseline table and failure-profile table rebuilt
  from the post-repair arms; the chapter lineup re-evaluated against the new
  failure profile (Terminal Validation's 3/3 drift motivation must be
  re-established or the chapter is re-scoped; the backlog demotion rule
  applies symmetrically).
- **`docs/section-4-keeping-on-track/terminal-validation/spec.md`** — add a
  status note: motivating incidence must be re-established post-repair before
  implementation proceeds.

**Verify:** the grep above returns no unbannered stale citation; sphinx build
clean.

**Commit:** `docs: rebuild narrative on post-repair evidence chain`

---

### Task 8: Close out

- Move this plan to wherever completed plans live per current convention, or
  mark the roadmap row.
- Confirm `just quality` and the full `uv run pytest` suite pass.
- Final check, one sentence in the incident report's end: what the new ditch
  is, or that none exists in Phases 1–3.

**Commit:** `docs: oracle-repair cycle complete`
