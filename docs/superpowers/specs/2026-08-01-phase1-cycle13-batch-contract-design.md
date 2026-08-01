# Cycle 13 — Batch contract

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine  
**Status:** approved for implementation

## Goal

Make one run comparable to another before Cycle 14 invokes Pi sixteen times.
The runner must use the trusted noninteractive invocation shape, prove that
the model produces real output, and attach the conditions needed to reject a
resume from a different experiment.

## Invocation

The Pi command keeps Cycle 8's explicit isolation and direct task-spec prompt,
and adds the trusted session flags:

- `--print`
- `--mode json`
- `--no-session`
- the recorded model and explicit project extension
- disabled ambient extensions, skills, prompt templates, themes, and context
  files

The task spec remains prompt text; the preflight uses the same flags and model
but a short fixed prompt in a disposable workspace.

## Real-output preflight

Before any batch attempt or checkpoint record is created:

1. perform the existing model-server liveness check;
2. invoke Pi with the final invocation shape and the configured model;
3. require a zero exit and non-empty assistant content in its JSON output.

Failure is an environment failure and stops the batch. The preflight is not a
graded run and does not consume a checkpoint position. Its output is retained
only for the caller's diagnostic message; it is not mixed into the n=16
results.

## Conditions and resume

Each `RunResult` carries one immutable conditions record:

- model name;
- normalized Pi command (with the task text replaced by a stable prompt
  label, never storing secrets or the full task text);
- Pi version;
- SHA-256 of the transplanted task spec;
- harness Git revision;
- run and grading timeout values.

The same record is captured for the preflight and requested batch. Cycle 14
must refuse to resume when any existing checkpoint record has a different
conditions record. Older records without conditions are readable for
inspection, but are not eligible for a resumed batch.

## Boundaries

This cycle does not loop, append checkpoints, or run n=16. It does not choose
an alternate model server, retry a failed preflight, or add telemetry. The
server-down exception remains the environment boundary established in Cycle 7.

## Evidence

- A command-construction test pins every isolation and session flag and proves
  the task prompt is still passed as the final positional argument.
- A fake Pi JSON stream with no assistant content fails the preflight; a
  non-empty assistant message and zero exit succeeds. A nonzero exit fails.
- Conditions round-trip through checkpoints, compare by value, and exclude
  the full task text.
- A checkpoint compatibility test proves records missing conditions load but
  are refused by the future resume check.
