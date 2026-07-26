# Section II — Measurement

The evaluation harness: it drives Pi headless via `subprocess`, provisions
disposable git-tracked workspaces, captures diffs, and runs pytest as the
acceptance oracle.

**Status:** withdrawn pending rewrite. The chapter prose that narrated the
n=4 0/8 baseline is discarded — the grading path it described was rebuilt
under the grading-path reboot (see
[`docs/superpowers/plans/2026-07-24-grading-path-reboot.md`](../superpowers/plans/2026-07-24-grading-path-reboot.md),
Task 9), and the numbers below predate that fix. Spec and plan are kept as
historical record; the research reports below are superseded/bannered
where applicable. New chapter prose is written against the reframe and
final numbers, not before.

**Evidence:** [0/8 baseline](research/2026-07-23-baseline-phase-1.md) —
the unsteered SLM cannot reliably complete Phase 1.

```{toctree}
:hidden:

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
