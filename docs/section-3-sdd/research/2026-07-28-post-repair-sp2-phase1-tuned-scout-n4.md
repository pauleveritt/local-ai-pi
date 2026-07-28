# Baseline: Phase 1 — Tuned SP2 (scout)

**Date:** 2026-07-28
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Start state:** empty (no seed)
**pi version:** `0.82.0`
**Runs:** n=4
**Success rate:** 3/4 (75%)

**Mean process wall time:** 270s (harness-side subprocess timing, not artifact task duration — this pi version's --mode json stream has no per-event timestamps to compute the latter; over success-eligible runs, timeout/no-delegation excluded)
**Mean turns:** 11.0
**Drift incidence:** 1/4 runs (overreach=1)

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ✅ | 9 | 76s | app.py, templates/base.html, templates/home.html (+1) | `3d76ccb16bad` |
| 2 | exited | ✅ | 9 | 84s | app.py, templates/base.html, templates/home.html (+1) | `e02aaa94f45e` |
| 3 | exited | ❌ | 18 | 830s | uv.lock, app.py, models.py (+4) | `55dbfd2a5e44` |
| 4 | exited | ✅ | 8 | 90s | app.py, templates/base.html, templates/home.html (+1) | `0356c6a96ccd` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Subagent delegation metrics

| # | Subagent calls | Packet size (bytes) |
|---|---------------|---------------------|
| 1 | 1 | 1,369 |
| 2 | 1 | 1,315 |
| 3 | 7 | 6,915 |
| 4 | 1 | 1,315 |
| **Agg** | μ=2.5 (in 4/4 runs) | μ=2,728 |

*Packet fidelity (verbatim literal matching) and implementer self-report
vs harness verdict agreement are deferred to a future harness iteration.*

## Behavioral instrumentation

**Inherited-file write attempts:** 0/4 runs (no seed -- not applicable)
**Shared-file replace-vs-extend:** replace=0 extend=0 untouched=4 (no seed -- not applicable)
**False self-report:** 1/4 runs (model's own suite passed; harness acceptance disagreed)

## Evidence tier

- **Outcome mix:** 4 exited.
- **Success rate:** artifact-backed — n=4 dated session files (GREEN per [evidence policy](../../superpowers/policies/evidence.md)).
- **Delegation metrics:** artifact-backed — subagent call counts and packet sizes extracted from parent JSONLs (GREEN).
- **Timing / turns:** real but noisy — n=4, single-model, single-provider (YELLOW). Compare deltas at n=4 with caution.
- **Statistical note:** n=4 — per-run success-rate deltas of ±1 run are within noise at this sample size. Cite structural claims, not small-sample tuning deltas.
