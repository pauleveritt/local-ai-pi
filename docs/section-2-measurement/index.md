# Section II — Measurement

The evaluation harness: it drives Pi headless via `subprocess`, provisions
disposable git-tracked workspaces, captures diffs, and runs pytest as the
acceptance oracle.

**Status:** evidence finalized 2026-07-27, chapter prose still pending
(Task 9). Every earlier number below (the n=4 0/8 baseline, the pre-repair
post-repair reports) was measured under an invalid or self-graded oracle
and is superseded — kept as historical record, bannered where applicable.
The grading path was rebuilt under the grading-path reboot (see
[`docs/superpowers/plans/2026-07-24-grading-path-reboot.md`](../superpowers/plans/2026-07-24-grading-path-reboot.md)),
and the 2026-07-27 unsteered n=16 reports below are the first trustworthy
numbers this project has produced. New chapter prose is written against
these final numbers next (Task 9's rewrite half).

**Evidence:** unsteered n=16 per phase, no ditch —
[Phase 1](research/2026-07-27-post-repair-sp1-phase1.md) 15/16,
[Phase 2](research/2026-07-27-post-repair-sp1-phase2.md) 15/16,
[Phase 3](research/2026-07-27-post-repair-sp1-phase3.md) 16/16,
[Phase 3, less-prescriptive spec](research/2026-07-28-post-repair-sp1-phase3-less-prescriptive-spec.md) 16/16.

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
research/2026-07-27-post-repair-sp1-phase1
research/2026-07-27-post-repair-sp1-phase2
research/2026-07-27-post-repair-sp1-phase3
research/2026-07-28-post-repair-sp1-phase3-less-prescriptive-spec
```
