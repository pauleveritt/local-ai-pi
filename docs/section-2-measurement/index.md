# Section II — Measurement

Three chapters that build the evaluation harness, run the n=4 baseline, and
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
research/2026-07-24-oracle-invalid-incident
research/2026-07-24-post-repair-sp1-phase1
research/2026-07-24-post-repair-sp1-phase2
research/2026-07-24-post-repair-sp1-phase2-pooled
research/2026-07-24-selfgrade-forensics
research/2026-07-24-write-vs-edit-experiment
```
