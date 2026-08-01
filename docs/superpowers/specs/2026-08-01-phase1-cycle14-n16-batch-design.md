# Cycle 14 — Sequential n=16 batch

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine  
**Status:** approved for implementation

## Goal

Run the same AgentClinic Phase 1 task sixteen times against the shared local
model, recording every completed attempt so an interrupted batch can resume.
The result is the evidence for Phase 1's target of approximately 15 accepted
runs out of 16.

## Interface

```python
def run_batch(
    checkpoint_path: Path,
    *,
    target: int = 16,
    model: str = DEFAULT_MODEL,
) -> list[RunResult]: ...
```

The checkpoint path is explicit. There is no project-wide default and no
parallel mode. `target` is a seam for small fixture tests; the Phase 1 run uses
the default 16.

## Sequence

1. Load existing records.
2. Refuse before Pi if any existing record lacks conditions or differs from the
   requested model/conditions.
3. If records already reach the target, return them without invoking Pi.
4. Run Cycle 13's liveness and real-output preflight once before remaining
   attempts.
5. Run one fresh workspace at a time. Append its `RunResult` immediately,
   including rejected and timed-out attempts.
6. Return records in checkpoint order after reaching the target.

`ModelServerDown` remains an environment failure and propagates. It creates no
record and does not advance the resume position. A bounded Pi or pytest
timeout is already a recorded rejected result from Cycle 12, so the next
attempt continues.

## Evidence

- A fake runner and temporary checkpoint prove exactly one preflight occurs,
  attempts are sequential, and every completed attempt is appended before the
  next begins.
- A pre-populated checkpoint proves resume starts at its length and does not
  repeat earlier records.
- A mismatched or condition-less record proves refusal before any Pi call.
- A preflight/model-server failure proves no checkpoint record is appended.
- A target already reached proves the batch is a no-op and does not require a
  live server.

## Non-goals

No statistics package, confidence interval, retry policy, concurrency, live
model run in the test suite, or Phase 2 telemetry is added. The caller can
count `RunResult.accepted` values in the returned list.
