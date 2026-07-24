# Experiment: inherited-file write guard (write-vs-edit causality probe)

**Date:** 2026-07-24
**Model:** omlx/gemma-4-12B-it-MLX-8bit · **pi:** 0.82.0
**Workload:** seeded Phase 2 (start state: `examples/reference/phase-1`)
**Oracle:** the **Phase 1** acceptance suite, run after Phase 2 work — so
"preserved" means exactly: does Phase 1 still function afterwards.
**Arms:** n=4 each. CONTROL = current tool surface. GUARDED = plus
`.pi/extensions/inherited-file-guard.ts`, which blocks `write` to files that
existed at session start while allowing `write` to new files and `edit`
everywhere.

## Result

| Arm | Preservation broken | Did Phase 2 work | Guard fired |
|-----|--------------------|------------------|-------------|
| CONTROL | 1/4 | 4/4 | n/a |
| GUARDED | 0/4 | 4/4 | **1/4 runs** |

## What this does and does not show

**Does NOT show a measured effect on preservation.** 1/4 vs 0/4 is
statistically indistinguishable (Fisher p = 1.0). More importantly, **the
guard only fired in 1 of the 4 guarded runs** — in the other three the model
never attempted a write to an inherited file, so those runs were identical to
control by construction. The arms are therefore not really 4-vs-4; they are
1 intervention against a ~25% base rate. **Tier: RED for any effect claim.**

**Does show the mechanism behaves exactly as designed.** GREEN, deterministic,
artifact-backed, from the one run where it fired (`e2e126110318`):

```
write models.py                  (new file — allowed)
edit  app.py
write app.py                     ← BLOCKED by the guard
edit  app.py                     ← model recovered
write templates/complaints.html  (new file — allowed)
edit  tests/test_app.py
```

Three properties confirmed in that trace:

1. **It discriminates correctly.** `write` to new files (`models.py`,
   `templates/complaints.html`) passed untouched; only the inherited `app.py`
   was refused. A blunt "no write" rule would have broken the task.
2. **The model recovers gracefully.** Blocked once, it switched to `edit` on
   the same file and continued — no repair spiral, no repeated identical
   failing call, no abandonment.
3. **It does not break the task.** 4/4 guarded runs completed Phase 2 work,
   identical to control.

## The measurement problem this exposes

The motivating failure's base rate is roughly 25% (forensics: 2/8; this
experiment's control: 1/4; pooled 3/12). Detecting a reduction from 25% to
near-zero with conventional power needs on the order of **n≈50 per arm**, not
4. At ~60s per unsteered run that is ~1 hour per arm — affordable, but it must
be budgeted deliberately rather than assumed.

Two options for the real measurement, to decide before spending the time:

- **Raise n** to ~50/arm and measure the rate directly.
- **Raise the base rate** by making the workload more preservation-hostile
  (e.g. a phase whose contract forces edits to a file with more inherited
  behavior), so a smaller n suffices. This risks measuring an artificial
  workload rather than the real one.

## Standing metric this justifies

Independent of effect size, **inherited-file write attempts** are now worth
recording on every run: they are per-run, deterministic, and cheap
(`inherited_write_blocked` entries, or `write` calls against the seed's file
list). That converts a rare outcome failure into a frequent, countable
behavioral signal — which is exactly what Amendment 2's failure-mode-incidence
metric is for, and a far better basis for a Section 4 chapter than a success
rate at n=4.

## Provenance caveat

Reports do not yet record the pi version; this one states it by hand
(0.82.0). The 0.81.1 → 0.82.0 skew already changed the event-timestamp schema
mid-project. Adding it to the report header is outstanding.
