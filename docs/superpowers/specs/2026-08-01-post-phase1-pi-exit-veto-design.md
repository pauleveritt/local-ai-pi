# Post-Phase 1 corrective cycle — Pi exit veto

**Status:** approved for implementation

## Why this correction exists

`RunResult.accepted` currently rejects a Pi timeout but can accept a run whose
Pi process exited nonzero if the resulting workspace passes the hermetic
acceptance suite. That makes a failed agent invocation indistinguishable from
a successful one in the batch count.

The completed Phase 1 checkpoint is unaffected: every recorded Pi process
exited with code zero. This correction defines the contract for every future
run; it does not reinterpret or rerun that evidence.

## Contract

A run is accepted only if all of the following hold:

1. Pi did not time out.
2. Pi exited with code zero.
3. The hermetic grade is accepted.

Pi's diff, stdout, stderr, return code, and grade remain recorded when Pi
exits nonzero. The harness still stages, diffs, and grades that partial
workspace after Pi returns. Those details are diagnostic evidence, but the
run is rejected.

This stays a run-level rule. `GradeResult.accepted` continues to answer only
whether the workspace passed hermetic grading; it does not learn about Pi.
`ModelServerDown` remains an environment failure before Pi starts and still
propagates instead of becoming a rejected run.

## Evidence

One hermetic `RunResult` test constructs an accepted grade with a nonzero Pi
return code and asserts that the run is rejected. The existing ordinary Pi
test remains the control: an accepted grade with return code zero and no
timeout is accepted. Together they prove the return-code condition rather
than merely proving that runs can be rejected.

No model, Pi executable, or live model server is needed.

## Non-goals

- Do not change Pi invocation flags, preflight, timeout handling, checkpoint
  format, batch resume semantics, or grading.
- Do not add a new concept-budget term: this uses the existing *run*,
  *verdict*, and recorded Pi return-code fields.
