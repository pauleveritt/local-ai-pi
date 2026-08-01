# Corrective Hardening Implementation Plan

**Goal:** Remove the four demonstrated pre-batch faults in checkpoint writing,
grading isolation, workspace setup, and their missing proofs.

**Architecture:** Keep the existing module boundaries. `checkpoint.py` repairs
only the terminal JSONL suffix in place; `grading.py` builds an explicit child
environment; `workspace.py` owns Git initialization isolation; `runner.py`
retains one-run orchestration but exposes the Pi return code needed to prove it
ran. Tests use temporary paths and mocks only.

**Tech stack:** Python 3.14 stdlib, pytest, Git, Ruff, Pyrefly, and Sphinx.

## Constraints

- No model invocation, batch loop, timeout behavior, or retry behavior.
- Do not rewrite existing specs or plans to conceal their history. The new spec
  is the authoritative corrective record.
- Commit the Cycle 11 spec and this plan before modifying Python code.
- Use tests that fail under the reviewed implementation before applying each
  repair.

## Tasks

### 1. Repair checkpoint suffix handling

**Files:** `harness/checkpoint.py`, `tests/test_checkpoint.py`

- Add a test where one complete line has no trailing newline, then append a
  second result; loading must return both in order.
- Add a test that simulates interruption while repairing a malformed final
  fragment and verifies all previous complete records remain readable.
- Change `append_checkpoint` to examine bytes at the final line, parse that
  final segment when necessary, and use `truncate()` only on a malformed
  suffix. For a complete no-newline record, append the missing separator.
- Flush and `fsync()` the repaired/appended file before returning.
- Retain the existing proof that malformed non-final data raises.

### 2. Construct the grading child environment

**Files:** `harness/grading.py`, `tests/test_grading.py`

- Add a regression test that sets `PYTEST_ADDOPTS=--collect-only` in the parent
  and proves the reference fixture is still accepted.
- Add a focused assertion that the child environment disables plugin autoload
  while still loading the explicit grading plugin.
- Replace `dict(os.environ)` with a helper that creates the minimal
  environment specified by the Cycle 11 design, including fresh home/XDG
  locations under the grading directory.
- Keep the results path private to the grader and preserve the existing
  allowlist/refusal behavior.

### 3. Make workspace initialization independent of user Git state

**Files:** `harness/workspace.py`, `tests/test_workspace.py`,
`examples/agentclinic/phase-1/empty/.gitkeep` (remove if no longer needed)

- Add a test that creates a source directory with no files, prepares it, and
  proves `HEAD` exists, the worktree is clean, and no placeholder was added.
- Add a test whose global Git hook would fail if executed; prove
  `prepare_workspace` still supplies its initial commit.
- Give the initial commit an explicit controlled Git environment,
  `--allow-empty`, and an overridden inert `core.hooksPath`; let callers use
  `prepare_workspace()` with no source directory for the tracked empty state.
- Remove the empty-fixture workaround only after the literal-empty test passes.

### 4. Close the proof gaps around counting, liveness, and the runner

**Files:** `tests/test_grading.py`, `tests/test_liveness.py`,
`harness/runner.py`, `harness/checkpoint.py`, `tests/test_runner.py`,
`tests/test_checkpoint.py`

- Add a module-level async test declaration to the `_test_count()` test and
  assert it contributes to the expected count.
- Make the liveness stub reject paths other than `/v1/models`; retain its
  positive case so it pins the real endpoint.
- Add `pi_returncode: int | None` to `RunResult` and checkpoint serialization;
  old records load with `None` rather than becoming unreadable.
- Replace the live, circular runner assertion with a mocked unit test that
  verifies ordered liveness, workspace, Pi, diff, and grading collaborators,
  plus the Pi output and return code in `RunResult`. Keep an optional live test
  only if it asserts actual model evidence and is clearly opt-in.

### 5. Validate and close the cycle

**Files:** `ROADMAP.md`, relevant docstrings and setup/onboarding documents

- Run focused tests after each task, then the full non-live test suite.
- Run Ruff check and formatter check, Pyrefly, and the Sphinx build with
  warnings treated as errors; repair only findings within this cycle's scope.
- Rewrite the Phase 1 table as Cycle 11 corrective hardening, Cycle 12 hang
  tolerance, Cycle 13 batch contract, and Cycle 14 sequential n=16 batch.
  Update the ordering rationale, concept budget, backlog, and onboarding
  wording that the review demonstrated stale.
- Record deferred work accurately; do not create an invented withdrawn Cycle
  15 artifact.
- Commit the implementation and documentation with the verification results.
