# Phase 1 Cycle 6: The AgentClinic Task Spec Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put the document a model builds from onto this branch, and fix
the grading regression that document makes reachable.

**Architecture:** Two independent tasks. Task 1 transplants Phase 1's
section of the AgentClinic roadmap from the `user-story-batch` branch to
`examples/agentclinic/specs/roadmap.md`, verbatim, resolving a citation
`test_acceptance.py` has carried since cycle 1. Task 2 restores an
explicit suite path to `grade()`'s pytest invocation, so a workspace
carrying model-written tests still grades on the acceptance suite alone.

**Tech Stack:** Python 3.14, pytest 8.3.4, standard library only. Task 1
is a file copy; Task 2 is a one-argument change plus a test.

## Global Constraints

- Python `>=3.14,<3.15` (from `pyproject.toml`).
- `pytest==8.3.4`, `fastapi[standard]==0.115.10`, `turbohtml==1.5.0` are
  the pinned dependencies already declared in `pyproject.toml` — do not
  add new dependencies for this cycle.
- The transplanted document is **verbatim** — no added commentary, no note
  about omitted phases, no harness annotations. This file is read by the
  model under test at cycle 8; anything added to it is a difference from
  the conditions the trusted number was produced under.
- **Phase 1's section only.** Do not transplant Phase 2 or Phase 3.
- **Do not remove the smoke-test bullet** ("Write a smoke test in
  `tests/test_app.py`"). It was present in the runs that scored 16/16.
  Task 2 makes the grader tolerate it; the spec is not edited to avoid it.
- No changes to `examples/agentclinic/phase-1/` (cycle 1's fixtures and
  acceptance suite), `harness/workspace.py`, `harness/grading_plugin.py`,
  or cycle 5's refusal logic in `harness/grading.py`.
- The `tests_executed == tests_expected` condition stays intact. Task 2
  narrows *what* pytest collects; it must not weaken the check on *how
  many* tests ran.

---

### Task 1: Transplant Phase 1's section of the AgentClinic roadmap

**Files:**
- Create: `examples/agentclinic/specs/roadmap.md`

**Interfaces:**
- Consumes: nothing.
- Produces: `examples/agentclinic/specs/roadmap.md` — the document cycle 8
  gives a model to build from. `examples/agentclinic/phase-1/acceptance/test_acceptance.py:5`
  already cites this exact path and the `## Phase 1 — Home Page` heading;
  this task makes that citation resolve. No code imports it.

**Note on why there is no test.** This task produces data a model reads,
not code with behavior. The assertion that matters is cycle 8's, when a
model builds from it. Step 3 verifies the citation resolves, which is the
only checkable property this cycle owns.

- [ ] **Step 1: Create the directory and file**

Create `examples/agentclinic/specs/roadmap.md` with exactly this content —
the `# Roadmap` title and the `## Phase 1 — Home Page` section, copied
verbatim from `user-story-batch`'s `examples/agentclinic/specs/roadmap.md`
lines 1–23. Nothing else; the file ends after the last bullet.

```markdown
# Roadmap

## Phase 1 — Home Page

- Create `app.py` with the FastAPI application instance
- Create `templates/` directory
- Create `templates/base.html` — shared Jinja2 layout with:
  - HTML5 doctype and `<html lang="en">`
  - `<head>` with charset, viewport meta, Bootstrap 5 CSS CDN link
  - `<link>` favicon pointing to `https://www.python.org/static/favicon.ico`
  - A title block (default: "AgentClinic")
  - A simple navbar with "AgentClinic" brand and links to Home (`/`) and Complaints (`/complaints`)
  - A `{% block content %}` for page-specific content
  - Bootstrap 5 JS bundle CDN at bottom of `<body>`
- Create `templates/home.html` that extends `base.html` with:
  - A hero/jumbotron section with the tagline: *"Come in. Sit down. Tell us about your human."*
  - A brief welcoming paragraph about the clinic
- Add the `/` route in `app.py` returning the home template
- Add a `if __name__ == "__main__"` block to run with `uvicorn.run("app:app", reload=True)`
- Write a smoke test in `tests/test_app.py`:
  - Import `TestClient` from `starlette.testclient`
  - `GET /` returns status 200
  - Response body contains the tagline text
```

The em-dashes (`—`), the curly quotes in *"Come in. Sit down. Tell us
about your human."*, and the backticks are all part of the source text —
preserve them exactly. The tagline in particular is a contract literal
that `test_acceptance.py` asserts on verbatim.

The file must end with exactly one trailing newline after the last bullet
(`  - Response body contains the tagline text`) — no blank line, no
missing newline. Step 2's `diff` compares against `sed -n '1,23p'` of the
source, which emits precisely that, so any deviation shows up as a diff
hunk.

- [ ] **Step 2: Confirm it is byte-identical to the source's Phase 1 section**

Run:

```bash
diff <(sed -n '1,23p' ../user-story-batch/examples/agentclinic/specs/roadmap.md) examples/agentclinic/specs/roadmap.md
```

Expected: no output (empty diff, exit 0).

If the `user-story-batch` worktree is not at that relative path, find it
with `git worktree list` and adjust. If it is unavailable entirely, skip
this step and rely on Step 3.

- [ ] **Step 3: Confirm the acceptance suite's citation now resolves**

`examples/agentclinic/phase-1/acceptance/test_acceptance.py:5` reads:

> Contract source: examples/agentclinic/specs/roadmap.md, "## Phase 1 — Home Page".

Verify both halves of that citation:

```bash
test -f examples/agentclinic/specs/roadmap.md && echo "path OK"
grep -c '^## Phase 1 — Home Page$' examples/agentclinic/specs/roadmap.md
```

Expected: `path OK`, then `1`.

Also confirm the later phases were not transplanted:

```bash
grep -c '^## Phase' examples/agentclinic/specs/roadmap.md
```

Expected: `1`.

- [ ] **Step 4: Confirm the existing suite is unaffected**

This task adds a file nothing imports, so nothing should change.

Run: `uv run pytest -q`
Expected: 31 passed

- [ ] **Step 5: Commit**

```bash
git add examples/agentclinic/specs/roadmap.md
git commit -m "feat(examples): transplant Phase 1 of the AgentClinic roadmap"
```

---

### Task 2: Grade on the acceptance suite alone

**Files:**
- Modify: `harness/grading.py`
- Modify: `tests/test_grading.py`
- Modify: `ROADMAP.md`

**Interfaces:**
- Consumes: `grade(workspace: Path, suite: Path, timeout: int = 30) -> GradeResult`
  and `prepare_workspace(source_dir: Path) -> Iterator[Path]`, both
  unchanged in signature by this task.
- Produces: no new interface. `grade()`'s behavior narrows — pytest now
  collects only the acceptance suite, not every test file in the
  workspace.

**Why this is a real red step.** Unlike cycle 4, this task's test fails
before the change and passes after. `grade()` currently invokes pytest
with `cwd=workspace` and no path argument, so pytest collects everything
in the workspace. A model following the roadmap's own smoke-test
instruction produces extra tests and fails cycle 3's
`tests_executed == tests_expected` condition — a correct solution
rejected. This was measured, not predicted: `accepted=False, executed=6,
expected=4`.

- [ ] **Step 1: Write the failing test**

`tests/test_grading.py` does **not** currently import `shutil` (its
imports are `SimpleNamespace`, the plugin constants, `_verdict`, `Path`,
`grade`, and `prepare_workspace`). Add it alongside the `from pathlib
import Path` line at line 151, matching that file's existing style of
grouping imports where they are first used:

```python
import shutil
from pathlib import Path
```

Then append to the same file:

```python
def test_grade_ignores_model_written_tests_and_grades_the_suite_alone(tmp_path):
    """The AgentClinic roadmap tells the model to write its own smoke test
    in tests/test_app.py, so a correct solution ships extra test files.
    Those must not count toward the verdict: pytest is given the
    acceptance suite's path explicitly, as the old harness did with
    `tests/test_acceptance.py` in its argv. Without that, a correct
    solution grades as executed=6 against expected=4 and is rejected."""
    source = tmp_path / "with-model-tests"
    shutil.copytree(PHASE_1 / "reference", source)
    model_tests = source / "tests"
    model_tests.mkdir()
    (model_tests / "test_app.py").write_text(
        "from starlette.testclient import TestClient\n"
        "from app import app\n"
        "\n"
        "client = TestClient(app)\n"
        "\n"
        "\n"
        "def test_home_ok():\n"
        "    assert client.get('/').status_code == 200\n"
        "\n"
        "\n"
        "def test_home_has_tagline():\n"
        "    assert 'Come in. Sit down.' in client.get('/').text\n"
    )

    with prepare_workspace(source) as workspace:
        result = grade(workspace, PHASE_1 / "acceptance" / "test_acceptance.py")

    assert result.accepted is True
    assert result.tests_executed == result.tests_expected == 4
```

`PHASE_1`, `prepare_workspace`, and `grade` are already in scope in that
file (defined/imported around line 151–157); only `shutil` needs adding,
per the note above.

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_grading.py::test_grade_ignores_model_written_tests_and_grades_the_suite_alone -v`

Expected: FAIL on `assert result.accepted is True`, because
`tests_executed` is 6 (the suite's 4 plus the model's 2) against
`tests_expected` of 4.

- [ ] **Step 3: Pass the suite's path to pytest**

In `harness/grading.py`, `grade()` currently invokes:

```python
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "harness.grading_plugin"],
            cwd=workspace,
```

Add `suite.name` as the final argv element:

```python
        proc = subprocess.run(
            [
                sys.executable, "-m", "pytest", "-q",
                "-p", "harness.grading_plugin",
                # Collect the acceptance suite and nothing else. The
                # AgentClinic roadmap instructs the model to write its own
                # tests/test_app.py, so a workspace legitimately contains
                # test files the verdict must ignore -- without this path,
                # they inflate tests_executed past tests_expected and a
                # correct solution is rejected. The old harness passed
                # tests/test_acceptance.py here for the same reason.
                suite.name,
            ],
            cwd=workspace,
```

Leave every other argument to `subprocess.run` unchanged.

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_grading.py::test_grade_ignores_model_written_tests_and_grades_the_suite_alone -v`
Expected: PASS

- [ ] **Step 5: Confirm the count check is still load-bearing**

The fix narrows *what* pytest collects. It must not weaken the check on
*how many* tests ran — cycle 4's `--collect-only` attack must still be
rejected.

Run: `uv run pytest tests/test_subversion.py -v`
Expected: 2 passed

- [ ] **Step 6: Run the full test suite**

Run: `uv run pytest -q`
Expected: 32 passed (31 pre-existing + 1 new)

If any pre-existing test fails, stop and report rather than editing it.

- [ ] **Step 7: Correct the ROADMAP note that named the wrong fix**

`ROADMAP.md`'s Deferred candidates section carries a note headed **"A live
collision cycle 6 must resolve"**, listing three candidate fixes. Its
option 1 — dropping the smoke-test bullet from the transplanted spec — is
now known to be the wrong direction, because the runs that scored 16/16
included that bullet; removing it would move this reboot's conditions away
from the ones being reproduced. Leaving it top of a list of three invites
someone to pick it.

Replace that note's three-option list and the sentence introducing it with:

```markdown
**Resolved by cycle 6.** `grade()` now passes the acceptance suite's
filename to pytest, so only the suite is collected — restoring what the
old harness got from `tests/test_acceptance.py` in its argv, and what the
trusted number was produced under. Pinned by
`tests/test_grading.py::test_grade_ignores_model_written_tests_and_grades_the_suite_alone`.

Two alternatives were considered and rejected. Editing the smoke-test
bullet out of the transplanted spec would work, and is the wrong
direction: the 16/16 runs included that bullet, so removing it moves our
conditions away from the ones being reproduced. Deriving `tests_expected`
from what pytest collected would discard the count check that catches
`--collect-only`.

Cycle 9's allowlist, if it takes the copy-only-allowlisted-files shape,
would close this a second way by never copying model-written tests into a
graded directory — independent of this fix, not superseded by it.
```

Leave the paragraphs above it (the description of the collision and its
measured `accepted=False, executed=6, expected=4` evidence) intact — they
are the record of why the fix exists.

- [ ] **Step 8: Commit**

```bash
git add harness/grading.py tests/test_grading.py ROADMAP.md
git commit -m "fix(grading): collect the acceptance suite alone, not model-written tests"
```
