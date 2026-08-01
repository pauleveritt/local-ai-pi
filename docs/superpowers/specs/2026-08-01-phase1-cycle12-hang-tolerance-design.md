# Cycle 12 — Hang tolerance

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine  
**Status:** approved for implementation

## Why this cycle exists

Cycle 11 made the state a batch will depend on safe to create and record. A
timeout is still fatal: both Pi and pytest use `subprocess.run`, so a
`TimeoutExpired` escapes and aborts the caller. Worse, killing only a direct
child leaves its descendants alive; one can retain a pipe and keep the parent
blocked after the direct child has gone away.

A sequential batch must record one timed-out attempt and continue to the next.
This cycle makes that narrow promise. It does not decide the final Pi
invocation, perform a real-output preflight, add a batch loop, retry an
attempt, or collect telemetry.

## One bounded child-process contract

`harness/processes.py` supplies one internal helper for the two existing
subprocess users: Pi in `runner.py` and pytest in `grading.py`. It starts a
child with `stdin` disconnected and a new process session.

On ordinary completion, it returns the child's return code and captured
stdout/stderr. On timeout, it:

1. sends `SIGTERM` to the child's process group;
2. gives the group five seconds to exit and drain its pipes;
3. sends `SIGKILL` to survivors; and
4. waits at most another five seconds for pipe drain, returning partial output
instead of waiting forever if a descendant escaped the group.

The helper records a timeout as data. It does not retry, classify a model
response, or promise to clean up an intentionally daemonized process that has
escaped the process group. The supported Phase 1 host is macOS/POSIX; a direct
child fallback is sufficient outside that environment.

## Results after a timeout

`GradeResult` gains `timed_out: bool`, defaulting false for old checkpoint
records. A timed-out pytest process produces `accepted=False`,
`timed_out=True`, its partial captured output, and its known return code (or
`None`). It remains a grader verdict, not an exception.

`RunResult` gains `pi_timed_out: bool`, also defaulting false for old records.
Pi timeout does **not** skip diffing or grading: the partial workspace and
partial output are useful diagnostic evidence. But `RunResult.accepted` is
false whenever Pi timed out, even if the partial workspace happened to satisfy
the acceptance suite. This is the run-level rejection the future batch will
count.

`ModelServerDown` remains unchanged. It is an environment failure detected
before Pi starts, so it propagates rather than becoming a timed-out or rejected
run.

## Evidence

No Pi executable or model server is required.

- A small Python child writes output, spawns a delayed marker-writing child,
  then blocks. After the helper times out, the result is marked timed out,
  retains the early output, and the marker never appears. A companion ordinary
  completion proves the helper does not label every child as timed out.
- A deliberately sleeping acceptance suite proves `grade()` returns a
  timed-out rejection rather than raising.
- A mocked Pi timeout proves the runner records partial Pi output, still
  produces the diff and grade evidence, and reports `RunResult.accepted` as
  false. A normal mocked Pi remains accepted.
- Checkpoint round-trip tests prove the two new flags persist, while records
  made before this cycle load with both flags false.

## Deferred

Cycle 13 chooses the precise Pi invocation and real-output preflight. Cycle
14 owns checkpoint wiring, resume compatibility across a declared batch, and
the sixteen sequential attempts. Capturing richer partial process diagnostics,
retries, and timeout tuning from live data remain deferred until evidence asks
for them.
