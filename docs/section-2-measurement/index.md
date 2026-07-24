# Section II — Measurement

Three chapters that build the evaluation harness, run the n=8 baseline, and
produce the smoking-gun evidence report. The harness drives Pi headless via
`subprocess`, provisions disposable git-tracked workspaces, captures diffs, and
runs pytest as the acceptance oracle.

**Status:** ✅ Complete ([spec](spec.md), [plan](plan.md))

**Evidence:** [0/8 baseline](research/2026-07-23-baseline-phase-1.md) —
the unsteered SLM cannot reliably complete Phase 1.

```{toctree}
:hidden:

telemetry-reader
eval-session
smoking-gun
spec
plan
research/2026-07-23-baseline-phase-1
```
