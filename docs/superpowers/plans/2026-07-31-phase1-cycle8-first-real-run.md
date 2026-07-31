# First Real Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `run_agentclinic_phase1()`, the first function that invokes
`pi` for real against a fresh, empty workspace, and grades the result with
the existing hermetic grader.

**Architecture:** One new fixture (`examples/agentclinic/phase-1/empty/`),
one transplanted `pi` extension (`.pi/extensions/hello-world.ts`), and one
new module (`harness/runner.py`) that composes four already-proven pieces —
`check_model_server_alive` (cycle 7), `prepare_workspace` (cycle 2), a
`subprocess.run` call to `pi`, and `grade()` (cycles 3–6) — into a single
`RunResult`.

**Tech Stack:** Python 3.14 stdlib (`subprocess`, `dataclasses`, `pathlib`)
plus the existing `harness` modules. `pi` 0.82.0 on `PATH`. pytest 8.3.4.

## Global Constraints

- `run_agentclinic_phase1(model: str = "omlx/gemma-4-12B-it-MLX-8bit",
  timeout: int = 600) -> RunResult` is the exact signature — both
  parameters are seams with defaults, not hardcodes.
- `ModelServerDown` (cycle 7) and `subprocess.TimeoutExpired` both
  propagate uncaught. Neither is wrapped or swallowed in this cycle.
- The empty fixture is not literally zero files: it contains one
  `.gitkeep` placeholder, because `prepare_workspace` runs `git add -A`
  then `git commit` with no `--allow-empty`, and a directory with nothing
  in it stages nothing (`ROADMAP.md`'s open cycle-9 note). This plan does
  not modify `harness/workspace.py` — that fix, if needed, is cycle 9's.
- `.pi/extensions/hello-world.ts` is transplanted verbatim (byte-identical
  to `main`'s copy) — no edits, no added commentary.
- The task spec (`examples/agentclinic/specs/roadmap.md`) is passed as
  `pi`'s prompt text. It is never copied into the workspace.
- `pi` runs with the harness's own Python environment (`sys.executable`'s
  environment) so `fastapi`/`turbohtml`/`pytest` are already importable.

---

## File Structure

```
.pi/
  extensions/
    hello-world.ts              # CREATE: transplanted verbatim from main
examples/agentclinic/phase-1/
  empty/
    .gitkeep                    # CREATE: empty fixture placeholder
harness/
  runner.py                     # CREATE: RunResult, run_agentclinic_phase1()
tests/
  test_workspace.py             # MODIFY: add empty-fixture provisioning test
  test_runner.py                # CREATE: skipped integration test
```

---

### Task 1: The empty fixture and the transplanted extension

**Files:**
- Create: `examples/agentclinic/phase-1/empty/.gitkeep`
- Create: `.pi/extensions/hello-world.ts`
- Modify: `tests/test_workspace.py`

**Interfaces:**
- Consumes: `harness.workspace.prepare_workspace(source_dir: Path) ->
  Iterator[Path]` (cycle 2, unchanged).
- Produces: `PHASE_1 / "empty"` — a fixture directory later tasks pass to
  `prepare_workspace`.

**Purpose:** Prove, with no `pi` and no model involved, that
`prepare_workspace` can actually provision from this fixture — the exact
case that fails without the `.gitkeep` placeholder (self-review caught
this while writing the design: `git add -A` stages nothing from a directory
with zero files, and `prepare_workspace`'s `git commit` has no
`--allow-empty`).

- [ ] **Step 1: Write the failing test**

Add to `tests/test_workspace.py` (after the existing tests):

```python
def test_prepare_workspace_provisions_the_empty_fixture():
    with prepare_workspace(PHASE_1 / "empty") as workspace:
        log = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        )
        assert log.stdout.strip() != ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workspace.py::test_prepare_workspace_provisions_the_empty_fixture -v`
Expected: FAIL — `FileNotFoundError` or similar, because
`examples/agentclinic/phase-1/empty/` does not exist yet.

- [ ] **Step 3: Create the empty fixture**

```bash
mkdir -p examples/agentclinic/phase-1/empty
touch examples/agentclinic/phase-1/empty/.gitkeep
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workspace.py::test_prepare_workspace_provisions_the_empty_fixture -v`
Expected: PASS

- [ ] **Step 5: Transplant the pi extension**

Create `.pi/extensions/hello-world.ts` with this exact content (verbatim
from `main`'s copy — no edits):

```typescript
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // ── session_start: the session comes to life ──────────────────────
  pi.on("session_start", async (_event, ctx) => {
    ctx.ui.notify("Session started!", "info");

    // Write an evidence entry into the session.
    // pi.appendEntry(customType, data?) — first arg is a string type ID.
    pi.appendEntry("evidence", { event: "session_start", timestamp: Date.now() });
  });

  // ── agent_start: the LLM wakes up ─────────────────────────────────
  pi.on("agent_start", async (_event, ctx) => {
    ctx.ui.notify("Agent started — LLM turn beginning", "info");
  });

  // ── tool_call: a tool is about to execute (can block here) ────────
  pi.on("tool_call", async (event, ctx) => {
    ctx.ui.notify(`Tool called: ${event.toolName}`, "info");
  });

  // ── tool_execution_start: execution begins ────────────────────────
  pi.on("tool_execution_start", async (event, ctx) => {
    ctx.ui.notify(`Executing: ${event.toolName}`, "info");
  });

  // ── tool_execution_end: execution finished ────────────────────────
  pi.on("tool_execution_end", async (event, ctx) => {
    const status = event.isError ? " (FAILED)" : "";
    ctx.ui.notify(`Done: ${event.toolName}${status}`, "info");
  });

  // ── turn_end: the LLM pauses between tool loops ───────────────────
  pi.on("turn_end", async (event, ctx) => {
    ctx.ui.notify(`Turn ${event.turnIndex + 1} complete`, "info");
  });

  // ── agent_end: the LLM rests ──────────────────────────────────────
  pi.on("agent_end", async (_event, ctx) => {
    ctx.ui.notify("Agent finished", "info");
  });
}
```

- [ ] **Step 6: Commit**

```bash
git add examples/agentclinic/phase-1/empty/.gitkeep tests/test_workspace.py .pi/extensions/hello-world.ts
git commit -m "feat(fixtures): empty-workspace fixture and transplanted pi isolation extension"
```

---

### Task 2: `run_agentclinic_phase1()`

**Files:**
- Create: `harness/runner.py`
- Create: `tests/test_runner.py`

**Interfaces:**
- Consumes:
  - `harness.liveness.check_model_server_alive(base_url: str =
    "http://127.0.0.1:8001") -> None`, raises `ModelServerDown` (cycle 7)
  - `harness.workspace.prepare_workspace(source_dir: Path) ->
    Iterator[Path]` (cycle 2)
  - `harness.grading.grade(workspace: Path, suite: Path, timeout: int =
    30) -> GradeResult` (cycles 3–6)
  - `harness.grading.GradeResult` fields: `accepted: bool,
    tests_executed: int, tests_expected: int, returncode: int | None,
    stdout: str, stderr: str, refused_config: tuple[str, ...]`
  - `PHASE_1 / "empty"` fixture and `.pi/extensions/hello-world.ts` from
    Task 1
- Produces: `harness.runner.RunResult` (fields: `diff: str, grade:
  GradeResult`); `harness.runner.run_agentclinic_phase1(model: str =
  "omlx/gemma-4-12B-it-MLX-8bit", timeout: int = 600) -> RunResult`

- [ ] **Step 1: Write the failing test**

Create `tests/test_runner.py`:

```python
import shutil

import pytest

from harness.runner import RunResult, run_agentclinic_phase1


def _pi_and_server_available() -> bool:
    if shutil.which("pi") is None:
        return False
    try:
        from harness.liveness import check_model_server_alive

        check_model_server_alive()
    except Exception:
        return False
    return True


@pytest.mark.skipif(
    not _pi_and_server_available(),
    reason="requires pi on PATH and a live model server",
)
def test_run_agentclinic_phase1_returns_a_graded_result():
    result = run_agentclinic_phase1()

    assert isinstance(result, RunResult)
    assert result.grade.tests_expected == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_runner.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'harness.runner'`
(if `pi`/the server aren't available on this machine, this import error
still surfaces during collection, before the skip is evaluated — so the
failure is visible either way).

- [ ] **Step 3: Write the implementation**

Create `harness/runner.py`:

```python
import subprocess
from dataclasses import dataclass
from pathlib import Path

from harness.grading import GradeResult, grade
from harness.liveness import check_model_server_alive
from harness.workspace import prepare_workspace

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_1 = REPO_ROOT / "examples" / "agentclinic" / "phase-1"
TASK_SPEC = REPO_ROOT / "examples" / "agentclinic" / "specs" / "roadmap.md"
EXTENSION = REPO_ROOT / ".pi" / "extensions" / "hello-world.ts"


@dataclass(frozen=True)
class RunResult:
    diff: str
    grade: GradeResult


def run_agentclinic_phase1(
    model: str = "omlx/gemma-4-12B-it-MLX-8bit",
    timeout: int = 600,
) -> RunResult:
    check_model_server_alive()

    with prepare_workspace(PHASE_1 / "empty") as workspace:
        prompt = TASK_SPEC.read_text()
        subprocess.run(
            [
                "pi",
                "--model", model,
                "--no-extensions",
                "--extension", str(EXTENSION),
                "--no-skills",
                "--no-prompt-templates",
                "--no-themes",
                "--no-context-files",
                "--approve",
                "--",
                prompt,
            ],
            cwd=workspace,
            timeout=timeout,
            check=False,
        )

        diff = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        ).stdout

        grade_result = grade(workspace, PHASE_1 / "acceptance" / "test_acceptance.py")

    return RunResult(diff=diff, grade=grade_result)
```

- [ ] **Step 4: Run test to verify it passes (or skips)**

Run: `uv run pytest tests/test_runner.py -v`
Expected: PASS if `pi` is on `PATH` and the model server is alive;
otherwise SKIPPED with reason "requires pi on PATH and a live model
server". Either outcome is correct — do not force a real run to make this
step "pass" if the environment isn't ready.

- [ ] **Step 5: Run the whole suite to confirm no regressions**

Run: `uv run pytest -q`
Expected: all previously-passing tests still pass; `test_runner.py`'s test
is either 1 passed or 1 skipped depending on the machine.

- [ ] **Step 6: Commit**

```bash
git add harness/runner.py tests/test_runner.py
git commit -m "feat(runner): run_agentclinic_phase1 invokes pi and grades the result"
```

---

## Plan Self-Review Notes

- **Spec coverage:** empty fixture + `.gitkeep` fix — Task 1. Transplanted
  extension — Task 1. `RunResult`/`run_agentclinic_phase1` interface,
  liveness-first ordering, prompt-as-text delivery, harness environment,
  diff capture, `grade()` call — Task 2. Skip-when-unavailable integration
  test, asserting shape not acceptance — Task 2. Non-goals (batch,
  checkpoint, allowlist) — untouched by both tasks.
- **Type consistency:** `RunResult(diff: str, grade: GradeResult)` and
  `run_agentclinic_phase1(model: str = "omlx/gemma-4-12B-it-MLX-8bit",
  timeout: int = 600) -> RunResult` match the spec's Interface section
  exactly; `GradeResult`'s fields as used in the test (`tests_expected`)
  match `harness/grading.py`'s actual dataclass.
- **No placeholders:** every step shows complete, runnable code and an
  exact command with an expected result.
