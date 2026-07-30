# Phase 1, Cycle 1: Accept/Reject Fixture Pair — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove, with plain `pytest` and no grader/harness/model in the loop, that the AgentClinic Phase 1 acceptance suite accepts a known-good solution and rejects a known-broken one.

**Architecture:** Three fixtures under `examples/agentclinic/phase-1/` — `reference/` (transplanted verbatim, known-good), `broken/` (freshly authored, known-broken), `acceptance/` (transplanted verbatim, the contract). A single root `pyproject.toml` supplies the dependencies both fixtures need. Verification is manual: copy the acceptance suite next to one fixture at a time, run `uv run pytest -q`, record the result, remove the copy.

**Tech Stack:** Python >=3.14,<3.15, managed with `uv`. `fastapi[standard]==0.115.10` (brings in Jinja2 and httpx), `pytest==8.3.4`, `turbohtml==1.5.0` — exact versions the acceptance suite was validated against on `user-story-batch`.

## Global Constraints

- Python `>=3.14,<3.15`.
- `fastapi[standard]==0.115.10`, `pytest==8.3.4`, `turbohtml==1.5.0` — exact pinned versions, copied from the old branch's grader stamp (`harness/grading.py::_stamp_pyproject`), not re-resolved.
- `reference/` and `acceptance/` are transplanted **verbatim** — byte-for-byte identical to `user-story-batch`. No edits, no reformatting.
- `broken/` is authored **fresh** — never transplanted from the old branch's break catalog.
- Never have `acceptance/test_acceptance.py` copied into more than one fixture directory at the same time (same-named test module collision risk).
- Source repo for transplants: `user-story-batch` branch, same repository (`local-ai-pi`), accessed via `git show <branch>:<path>` — read-only, no merge, no checkout of the branch itself.

---

### Task 1: Bootstrap the Python project

**Files:**
- Create: `pyproject.toml`

**Interfaces:**
- Produces: a `uv`-managed project at repo root with `fastapi[standard]==0.115.10`, `pytest==8.3.4`, `turbohtml==1.5.0` installed into `.venv`. Later tasks run `uv run pytest` from inside fixture subdirectories, relying on `uv` walking up to this root project.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "satyrn-engine"
version = "0.1.0"
requires-python = ">=3.14,<3.15"
dependencies = [
    "fastapi[standard]==0.115.10",
    "pytest==8.3.4",
    "turbohtml==1.5.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
norecursedirs = ["examples/agentclinic", "docs/_build"]
```

- [ ] **Step 2: Sync dependencies**

Run: `uv sync`
Expected: completes without error; creates `.venv/` and `uv.lock`.

- [ ] **Step 3: Verify the three key imports resolve**

Run: `uv run python -c "import fastapi, httpx, jinja2, turbohtml; print('ok')"`
Expected: prints `ok`, exit code 0. (This is the precondition the spec calls out: if any of these fail to import, the reject-check in Task 6 would "pass" via a collection error instead of a real assertion failure — proving nothing.)

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "Bootstrap uv project: fastapi, pytest, turbohtml"
```

---

### Task 2: Transplant the `reference/` fixture

**Files:**
- Create: `examples/agentclinic/phase-1/reference/app.py`
- Create: `examples/agentclinic/phase-1/reference/templates/base.html`
- Create: `examples/agentclinic/phase-1/reference/templates/home.html`

**Interfaces:**
- Consumes: nothing from Task 1 directly (this task only copies files).
- Produces: a working FastAPI app at `examples/agentclinic/phase-1/reference/app.py` importable as `from app import app` when `cwd` is that directory — consumed by Task 4's accept-check.

- [ ] **Step 1: Copy `app.py` verbatim from `user-story-batch`**

Run:
```bash
mkdir -p examples/agentclinic/phase-1/reference/templates
git show user-story-batch:examples/reference/phase-1/app.py > examples/agentclinic/phase-1/reference/app.py
```

Resulting file content (for verification against Step 4 below):
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

- [ ] **Step 2: Copy `templates/base.html` verbatim**

Run:
```bash
git show user-story-batch:examples/reference/phase-1/templates/base.html > examples/agentclinic/phase-1/reference/templates/base.html
```

- [ ] **Step 3: Copy `templates/home.html` verbatim**

Run:
```bash
git show user-story-batch:examples/reference/phase-1/templates/home.html > examples/agentclinic/phase-1/reference/templates/home.html
```

- [ ] **Step 4: Verify byte-for-byte match against the source branch**

Run:
```bash
diff <(git show user-story-batch:examples/reference/phase-1/app.py) examples/agentclinic/phase-1/reference/app.py
diff <(git show user-story-batch:examples/reference/phase-1/templates/base.html) examples/agentclinic/phase-1/reference/templates/base.html
diff <(git show user-story-batch:examples/reference/phase-1/templates/home.html) examples/agentclinic/phase-1/reference/templates/home.html
```
Expected: all three `diff` commands produce no output and exit 0.

- [ ] **Step 5: Commit**

```bash
git add examples/agentclinic/phase-1/reference/
git commit -m "Transplant reference/phase-1 fixture verbatim from user-story-batch"
```

---

### Task 3: Transplant the `acceptance/` suite

**Files:**
- Create: `examples/agentclinic/phase-1/acceptance/test_acceptance.py`

**Interfaces:**
- Produces: the acceptance contract file, consumed by Task 4 (accept-check) and Task 6 (reject-check). Never modified by either.

- [ ] **Step 1: Copy verbatim from `user-story-batch`**

Run:
```bash
mkdir -p examples/agentclinic/phase-1/acceptance
git show user-story-batch:examples/acceptance/phase-1/test_acceptance.py > examples/agentclinic/phase-1/acceptance/test_acceptance.py
```

Resulting file content (for verification against Step 2 below):
```python
"""Acceptance contract — Phase 1 (Home Page). Harness-owned; the model cannot edit this.

Cumulative scope: Phase 1 only.

Contract source: examples/agentclinic/specs/roadmap.md, "## Phase 1 — Home Page".
Assert user-visible behavior and exact literals. Do not assert on internal
function names or file layout — a correct-but-different solution must pass.
"""
from starlette.testclient import TestClient
from turbohtml import Doctype, parse

from app import app

client = TestClient(app)

TAGLINE = "Come in. Sit down. Tell us about your human."


def _normalized_text(element) -> str:
    return " ".join(element.text.split())


def test_home_returns_200():
    assert client.get("/").status_code == 200


def test_home_shows_the_tagline_verbatim():
    """The roadmap names this string exactly; it is a contract literal."""
    assert TAGLINE in client.get("/").text


def test_home_extends_the_shared_layout():
    """base.html supplies the navbar; home.html must extend it rather than
    duplicate a standalone page. Asserted through rendered output (the navbar
    brand and both nav links), not by inspecting template source."""
    body = client.get("/").text
    document = parse(body)

    assert "AgentClinic" in body
    assert any(
        link.attr("href") == "/" and _normalized_text(link).casefold() == "home"
        for link in document.select("a")
    )
    assert any(
        link.attr("href") == "/complaints"
        and _normalized_text(link).casefold() == "complaints"
        for link in document.select("a")
    )


def test_home_declares_html5_and_language():
    document = parse(client.get("/").text)

    assert any(
        isinstance(node, Doctype) and node.name.casefold() == "html"
        for node in document.children
    )
    html = document.select_one("html")
    assert html is not None and (html.attr("lang") or "").casefold() == "en"
```

- [ ] **Step 2: Verify byte-for-byte match against the source branch**

Run:
```bash
diff <(git show user-story-batch:examples/acceptance/phase-1/test_acceptance.py) examples/agentclinic/phase-1/acceptance/test_acceptance.py
```
Expected: no output, exit 0.

- [ ] **Step 3: Commit**

```bash
git add examples/agentclinic/phase-1/acceptance/
git commit -m "Transplant phase-1 acceptance suite verbatim from user-story-batch"
```

---

### Task 4: Accept-check — the acceptance suite accepts the reference solution

**Files:**
- Create (temporary, removed by Step 4): `examples/agentclinic/phase-1/reference/test_acceptance.py`
- Create: `docs/superpowers/research/2026-07-30-phase1-cycle1-fixture-results.md`

**Interfaces:**
- Consumes: `examples/agentclinic/phase-1/reference/app.py` (Task 2), `examples/agentclinic/phase-1/acceptance/test_acceptance.py` (Task 3), the `.venv` from Task 1.
- Produces: a written record of the accept-check result, consumed by Task 6's step that writes the same file's reject-check section.

- [ ] **Step 1: Copy the acceptance suite alongside `reference/`**

Run:
```bash
cp examples/agentclinic/phase-1/acceptance/test_acceptance.py examples/agentclinic/phase-1/reference/test_acceptance.py
```

- [ ] **Step 2: Run pytest from inside `reference/`**

Run:
```bash
cd examples/agentclinic/phase-1/reference && uv run pytest -q ; cd -
```
Expected: exit code 0, final summary line reads `4 passed` (the suite has exactly 4 test functions). Record the exact final summary line for Step 4.

- [ ] **Step 3: Remove the copy**

Run:
```bash
rm examples/agentclinic/phase-1/reference/test_acceptance.py
```

- [ ] **Step 4: Write the results note**

Create `docs/superpowers/research/2026-07-30-phase1-cycle1-fixture-results.md`:

```markdown
# Phase 1, Cycle 1 — fixture pair verification results

Manual verification per the [design spec](../specs/2026-07-30-phase1-cycle1-fixture-pair-design.md)
and [plan](../plans/2026-07-30-phase1-cycle1-fixture-pair.md). No grader, no
harness, no model — plain `pytest` run by hand against each fixture.

## Accept-check: `acceptance/` against `reference/`

- Command: `uv run pytest -q` from `examples/agentclinic/phase-1/reference/`
- Exit code: 0
- Result: 4 passed
- Verdict: **PASS** — the suite accepts the known-good solution.

## Reject-check: `acceptance/` against `broken/`

(filled in by Task 6)
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/research/2026-07-30-phase1-cycle1-fixture-results.md
git commit -m "Record accept-check result: acceptance suite passes reference/phase-1"
```

---

### Task 5: Author the `broken/` fixture

**Files:**
- Create: `examples/agentclinic/phase-1/broken/app.py`

**Interfaces:**
- Produces: a FastAPI app with zero routes, importable as `from app import app` when `cwd` is `broken/` — consumed by Task 6's reject-check.

- [ ] **Step 1: Write the broken fixture**

```bash
mkdir -p examples/agentclinic/phase-1/broken
```

`examples/agentclinic/phase-1/broken/app.py`:
```python
from fastapi import FastAPI

app = FastAPI()
```

- [ ] **Step 2: Sanity-check it imports and serves nothing at `/`**

Run:
```bash
cd examples/agentclinic/phase-1/broken && uv run python -c "
from starlette.testclient import TestClient
from app import app
client = TestClient(app)
r = client.get('/')
print(r.status_code)
" ; cd -
```
Expected: prints `404`, exit code 0 (the import and request succeed; the route simply doesn't exist).

- [ ] **Step 3: Commit**

```bash
git add examples/agentclinic/phase-1/broken/
git commit -m "Author broken/phase-1 fixture: bare FastAPI app, zero routes"
```

---

### Task 6: Reject-check — the acceptance suite rejects the broken solution

**Files:**
- Create (temporary, removed by Step 3): `examples/agentclinic/phase-1/broken/test_acceptance.py`
- Modify: `docs/superpowers/research/2026-07-30-phase1-cycle1-fixture-results.md`

**Interfaces:**
- Consumes: `examples/agentclinic/phase-1/broken/app.py` (Task 5), `examples/agentclinic/phase-1/acceptance/test_acceptance.py` (Task 3).
- Produces: the completed results note — the Definition of Done for this feature cycle.

- [ ] **Step 1: Copy the acceptance suite alongside `broken/`**

Run:
```bash
cp examples/agentclinic/phase-1/acceptance/test_acceptance.py examples/agentclinic/phase-1/broken/test_acceptance.py
```

- [ ] **Step 2: Run pytest from inside `broken/`**

Run:
```bash
cd examples/agentclinic/phase-1/broken && uv run pytest -q ; cd -
```
Expected: exit code 1 (pytest's code for "tests ran, some failed" — NOT exit code 2, which would mean a collection/usage error). Read the actual output: every failure must be an `AssertionError` (e.g. `assert 404 == 200`), not an `ImportError`, `ModuleNotFoundError`, or collection error. If any test errors instead of fails, stop — this fixture does not satisfy the reject-check and the fixture needs revising, not the result note.

- [ ] **Step 3: Remove the copy**

Run:
```bash
rm examples/agentclinic/phase-1/broken/test_acceptance.py
```

- [ ] **Step 4: Complete the results note**

Edit `docs/superpowers/research/2026-07-30-phase1-cycle1-fixture-results.md`, replacing the `(filled in by Task 6)` line with the actual recorded outcome, e.g.:

```markdown
## Reject-check: `acceptance/` against `broken/`

- Command: `uv run pytest -q` from `examples/agentclinic/phase-1/broken/`
- Exit code: 1
- Result: 4 failed (all four via `AssertionError` — `assert 404 == 200` and
  three related failures on tagline/layout/doctype checks against the 404
  response body; zero import or collection errors)
- Verdict: **PASS** — the suite rejects the known-broken solution, for the
  right reason.

## Definition of Done

Both directions confirmed. This feature cycle is complete.
```

(Use the actual exit code and summary line from Step 2's real output, not this example if it differs.)

- [ ] **Step 5: Update the roadmap**

Edit `ROADMAP.md`'s Phase 1 feature-cycle table row for Cycle 1: change `State` from `Spec drafted` to `Done`, and add a `Plan` link to `docs/superpowers/plans/2026-07-30-phase1-cycle1-fixture-pair.md`.

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/research/2026-07-30-phase1-cycle1-fixture-results.md ROADMAP.md
git commit -m "Record reject-check result: acceptance suite rejects broken/phase-1; cycle 1 done"
```
