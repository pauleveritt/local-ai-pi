# Phase 1 Cycle 4: Subversion Fixtures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the two attacks that defeat a naive exit-code grader —
`addopts = --collect-only` and an import-time `os._exit(0)` — as real
fixtures, and prove each both fools an exit-code check and is rejected by
cycle 3's verdict.

**Architecture:** One new test file, `tests/test_subversion.py`, holding
two helper functions that build an attacked source directory from cycle
1's `broken` solution, and two tests that grade each through
`prepare_workspace` + `grade()`. No production code changes — this cycle
adds fixtures and proof, not behavior.

**Tech Stack:** Python 3.14, pytest 8.3.4, standard library only
(`shutil`, `pathlib`).

## Global Constraints

- Python `>=3.14,<3.15` (from `pyproject.toml`).
- `pytest==8.3.4`, `fastapi[standard]==0.115.10`, `turbohtml==1.5.0` are
  the pinned dependencies already declared in `pyproject.toml` — do not
  add new dependencies for this cycle.
- **No production code changes.** `harness/grading.py`,
  `harness/grading_plugin.py`, and `harness/workspace.py` are read-only
  inputs. If a test fails, the fix belongs in the test or the fixture, not
  in the harness — a harness change means the cycle's premise was wrong
  and needs re-brainstorming, not patching.
- No changes to `examples/agentclinic/phase-1/{reference,broken,acceptance}`.
  The attacks are built in `tmp_path` at test time, never added as new
  directories under `examples/`.
- Both attacks build on `examples/agentclinic/phase-1/broken` — a solution
  that genuinely fails the acceptance suite — not on stub content, so each
  test demonstrates the attack laundering a real rejection into an
  apparent pass.
- The two tests assert exactly three things each: `returncode == 0` (a
  naive exit-code grader would accept), `accepted is False` (the verdict
  rejects), and `tests_executed == 0`.
- No new concepts. This cycle introduces no term not already spent by
  cycles 1–3.

---

### Task 1: `tests/test_subversion.py` — the two attacks and their proofs

**Files:**
- Create: `tests/test_subversion.py`

**Interfaces:**
- Consumes: `prepare_workspace(source_dir: Path) -> Iterator[Path]` from
  `harness.workspace` (cycle 2); `grade(workspace: Path, suite: Path, timeout: int = 30) -> GradeResult`
  from `harness.grading` (cycle 3). `GradeResult` carries `accepted: bool`,
  `tests_executed: int`, `tests_expected: int`, `returncode: int`,
  `stdout: str`, `stderr: str`.
- Produces: `_attack_with_collect_only(tmp_path: Path) -> Path` and
  `_attack_with_exit_at_import(tmp_path: Path) -> Path`, each returning a
  source directory ready to pass to `prepare_workspace`. Cycle 5 consumes
  both to prove config refusal.

**Note on TDD shape for this task.** These tests exercise cycle 3's
already-shipped grader, so there is no red step in the usual sense — they
pass on first run, and that is the correct outcome, not a warning sign.
Step 3 replaces the red step with a real non-vacuity check: deliberately
neuter each attack and confirm the corresponding test fails. Do not skip
it. A subversion fixture that silently fails to subvert would still leave
a green test, which is exactly the failure mode this cycle exists to rule
out.

- [ ] **Step 1: Write the test file**

```python
# tests/test_subversion.py
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
```

- [ ] **Step 2: Run the two tests**

Run: `uv run pytest tests/test_subversion.py -v`
Expected: 2 passed. (Both attacks are rejected by cycle 3's grader, which
already shipped — see the note above on why there is no red step here.)

If either test fails, stop and report. Do not modify anything under
`harness/` to make it pass.

- [ ] **Step 3: Non-vacuity check — confirm each test catches a no-op attack**

The `returncode == 0` assertion is what makes each test non-vacuous: if an
attack silently failed to fire, the underlying broken solution would run,
fail its four tests, and exit nonzero. Verify that directly.

First, neuter the collect-only attack by commenting out its `pytest.ini`
write:

```python
    # (source / "pytest.ini").write_text("[pytest]\naddopts = --collect-only\n")
```

Run: `uv run pytest tests/test_subversion.py::test_collect_only_attack_defeats_the_exit_code_but_not_the_verdict -v`
Expected: FAIL on `assert result.returncode == 0` (the unattacked broken
solution exits nonzero).

Restore that line, then neuter the exit-at-import attack by making its
write a no-op:

```python
    app.write_text(app.read_text())
```

Run: `uv run pytest tests/test_subversion.py::test_exit_at_import_attack_defeats_the_exit_code_but_not_the_verdict -v`
Expected: FAIL on `assert result.returncode == 0`.

Restore that line to:

```python
    app.write_text("import os\nos._exit(0)\n" + app.read_text())
```

- [ ] **Step 4: Re-run the two tests after restoring both attacks**

Run: `uv run pytest tests/test_subversion.py -v`
Expected: 2 passed

- [ ] **Step 5: Run the full test suite**

Run: `uv run pytest -q`
Expected: 21 passed (19 pre-existing + 2 new)

- [ ] **Step 6: Commit**

```bash
git add tests/test_subversion.py
git commit -m "test(subversion): the two attacks that defeat an exit-code grader, and proof the verdict survives them"
```

---

### Task 2: Record the results-file forge in the Backlog

**Files:**
- Modify: `ROADMAP.md` (the `## Backlog` section)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing consumed by later tasks. This is the spec's explicit
  commitment ("Recorded in `ROADMAP.md`'s Backlog at the end of this
  cycle") discharged in-cycle, so it cannot be lost to post-merge memory.

Marking cycle 4 itself Done is deliberately *not* part of this task — that
belongs to the post-merge re-plan, following cycle 3's precedent.

- [ ] **Step 1: Add the Backlog entry**

In `ROADMAP.md`, find the `## Backlog` section and append this bullet as
the last item in that list:

```markdown
- Acceptance grading still trusts a same-process signal a model can forge.
  A model-authored `app.py` can read the results-file path from the
  environment it shares with `harness/grading_plugin.py` and write forged
  `nodeid<TAB>outcome` lines and a completion marker straight into the
  results file. Cheap to do, and no in-process secret closes it — anything
  the plugin can read, model code sharing its process can read too. The
  real fix is running the suite out-of-process against a live app
  subprocess instead of in-process `TestClient(app)`, which is materially
  larger than the cycle that surfaced it. Scoped out of cycle 4 by
  explicit decision, not oversight — see that cycle's design doc, "Out of
  scope for this cycle".
```

- [ ] **Step 2: Verify the section still reads correctly**

Run: `git diff ROADMAP.md`
Expected: one added bullet at the end of the `## Backlog` list, no other
changes, and no disruption to the `## Prior work` heading that follows.

- [ ] **Step 3: Commit**

```bash
git add ROADMAP.md
git commit -m "docs(roadmap): backlog the results-file forge scoped out of cycle 4"
```
