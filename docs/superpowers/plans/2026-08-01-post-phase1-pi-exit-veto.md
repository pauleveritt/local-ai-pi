# Pi exit veto implementation plan

**Goal:** Reject a run when Pi exits nonzero, while preserving its diff and
hermetic grade as diagnostic evidence.

**Architecture:** Keep the decision at `RunResult.accepted`, where the runner
already combines Pi timeout state with the nested grading verdict. Add the
recorded `pi_returncode == 0` condition there; neither the grader nor the
checkpoint representation changes.

**Tech stack:** Python 3.14, pytest.

## Constraints

- A nonzero Pi exit does not skip staging, diffing, or grading.
- `GradeResult.accepted` remains a grading-only verdict.
- No live Pi/model invocation, changed flags, preflight behavior, timeout
  behavior, or checkpoint schema.
- The spec and this plan are committed before Python code changes.

## Tasks

### 1. Prove the Pi-return-code condition

**Files:** `tests/test_runner.py`

- Construct a `RunResult` with an accepted grade, no timeout, and a nonzero
  `pi_returncode`.
- Assert `result.accepted is False`.
- Retain the existing normal-Pi test as the zero-return-code control, proving
  the condition is specific rather than a blanket rejection.

### 2. Apply the run-level veto

**Files:** `harness/runner.py`

- Require `self.pi_returncode == 0` in `RunResult.accepted`, alongside the
  existing no-timeout and accepted-grade conditions.
- Do not alter the runner sequence: the existing code continues to collect
  diff and grade evidence after Pi has returned.

### 3. Verify and close

- Run the focused runner tests and the full non-live suite.
- Run Ruff lint/format checks, Pyrefly, and Sphinx with warnings as errors.
- Rewrite `ROADMAP.md`: record the corrective cycle, preserve Phase 1's
  completed 16/16 evidence as unaffected, and explicitly check the concept
  budget for changes.
- Commit the implementation, tests, and closing roadmap rewrite.
