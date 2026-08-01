# Batch Contract Implementation Plan

**Goal:** Establish the final single-run invocation, real-output preflight,
and immutable conditions record that Cycle 14's batch will consume.

**Architecture:** Keep one-run orchestration in `runner.py`. Add a small
conditions value object and a preflight function; do not add the batch loop.
Use the existing bounded process helper and checkpoint serializer.

## Constraints

- No n=16 loop, checkpoint append, retry, or telemetry.
- Liveness and preflight failures propagate as environment failures.
- The preflight uses the exact final Pi flags and model but never becomes a
  graded run.
- Commit this spec and plan before modifying Python code.

## Tasks

### 1. Pin the final Pi invocation

**Files:** `harness/runner.py`, `tests/test_runner.py`

- Add `--mode json` and `--no-session` to the existing isolated command.
- Keep the direct task-spec positional argument and explicit project extension.
- Make a command-capture test assert the complete ordered command.

### 2. Implement and prove real-output preflight

**Files:** `harness/runner.py`, `tests/test_runner.py`

- Parse the bounded process result as JSON lines and require assistant content,
  zero exit, and no timeout.
- Add success, empty-output, and nonzero-exit tests with fake process results.
- Ensure liveness is called before preflight and the preflight before any run.

### 3. Add conditions and checkpoint compatibility

**Files:** `harness/runner.py`, `harness/checkpoint.py`,
`tests/test_runner.py`, `tests/test_checkpoint.py`

- Add the immutable conditions value to `RunResult` and JSONL serialization.
- Hash the task spec, obtain Pi version and harness revision through explicit
  seams, and normalize the command so prompt content is not stored.
- Add value-equality, round-trip, and missing-conditions compatibility tests.
- Expose a small resume-compatibility predicate for Cycle 14; it must reject
  missing or mismatched conditions.

### 4. Close the cycle

- Run focused and full tests, Ruff, Pyrefly, and Sphinx with warnings as
  errors.
- Rewrite `ROADMAP.md` and the design index to mark Cycle 13 done and Cycle
  14 as the final n=16 batch.
- Update the concept budget only for terms that remain in the live design.
- Commit the implementation and documentation.
