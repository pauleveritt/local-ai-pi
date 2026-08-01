# Hang Tolerance Implementation Plan

**Goal:** Make Pi and pytest timeouts bounded, process-tree-safe recorded
results rather than uncaught exceptions.

**Architecture:** A compact `harness/processes.py` helper owns process-session
creation, group teardown, bounded pipe draining, and captured output.
`grading.py` maps its result to `GradeResult`; `runner.py` maps Pi timeout to
run-level acceptance while still preserving diagnostic grade and diff data.

**Tech stack:** Python 3.14 stdlib (`subprocess`, `os`, `signal`), pytest.

## Constraints

- Five seconds for graceful group shutdown and five seconds for forced-drain
  completion; no unbounded `communicate()` after a timeout.
- No retry loop, batch loop, real model invocation, changed Pi flags, or
  telemetry.
- `ModelServerDown` continues to propagate before any child starts.
- Commit this spec and plan before modifying Python code.

## Tasks

### 1. Prove and implement bounded process-group teardown

**Files:** `harness/processes.py`, `tests/test_processes.py`

- Write a child-process test that emits early output, starts a delayed marker
  writer, and blocks. It must fail under direct-child timeout behavior because
  the marker appears after the parent returns.
- Write an ordinary completion control.
- Implement a frozen result value with return code, stdout, stderr, and a
  timeout flag. Start new sessions, terminate the group, escalate to kill,
  decode partial output safely, and bound both drain windows.

### 2. Return a timeout verdict from grading

**Files:** `harness/grading.py`, `tests/test_grading.py`

- Add `timed_out: bool = False` to `GradeResult` and use the process helper.
- Write a sleeping-suite test that fails under the current uncaught
  `TimeoutExpired` behavior, then proves a returned timed-out rejection with
  partial output.
- Preserve all refusal and ordinary-grade behavior.

### 3. Record Pi timeout without losing diagnostic evidence

**Files:** `harness/runner.py`, `tests/test_runner.py`,
`harness/checkpoint.py`, `tests/test_checkpoint.py`

- Add `pi_timed_out: bool = False` and a run-level `accepted` property.
- Change the runner to use the process helper, continue through diff and grade
  after a Pi timeout, and preserve partial Pi output/return code.
- Add mocked normal and timed-out Pi tests. The latter proves liveness still
  happens first, grading still runs, and the run is not accepted.
- Round-trip new flags and load old records with false flags.

### 4. Close the cycle

- Run the focused tests and then the complete non-live test suite.
- Run Ruff lint and formatting checks, Pyrefly, and Sphinx with warnings as
  errors. Do not broaden formatting-only changes beyond touched files.
- Rewrite `ROADMAP.md` to mark Cycle 12 done, retain only genuinely deferred
  timeout work, and update the concept budget only if a new durable term was
  necessary.
- Commit the implementation and cycle-close documentation.
