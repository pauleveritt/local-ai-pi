# Sequential n=16 Batch Implementation Plan

**Goal:** Add the smallest resumable sequential batch loop that consumes
Cycles 10–13's checkpoint, run, timeout, and condition contracts.

## Constraints

- Default target is exactly 16; no parallelism or retries.
- Checkpoint after each completed attempt.
- Refuse mismatched/missing conditions before Pi.
- Propagate `ModelServerDown` without writing a result.
- Commit this spec and plan before modifying Python code.

## Tasks

### 1. Add the batch loop

**Files:** `harness/runner.py`, `tests/test_runner.py`

- Add `run_batch` with an explicit checkpoint path and target seam.
- Load records, derive requested conditions without invoking the model, and
  compare existing conditions before doing any work.
- No-op when the target is already reached; otherwise run preflight once and
  call `run_agentclinic_phase1` sequentially for each remaining position.
- Append immediately after each completed run and return ordered records.

### 2. Prove resume and failure boundaries

**Files:** `tests/test_runner.py`

- Use fakes to prove order, preflight count, append timing, and resume length.
- Prove condition mismatch and missing condition refuse before Pi.
- Prove server/preflight failure leaves the checkpoint unchanged.
- Prove a timed-out/rejected result is still appended and the next attempt
  runs.

### 3. Close Phase 1

- Run full tests, Ruff, Pyrefly, and Sphinx with warnings as errors.
- Rewrite `ROADMAP.md` and the design index to mark Cycle 14 done and Phase 1
  complete; record the actual live n=16 result after the owner runs it.
- Harvest any changed/deferred terms and leave Phase 2 Backlog coherent.
- Commit the implementation and documentation.
