# Baseline: Phase 1 — Home Page

**Date:** 2026-07-24
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Runs:** n=4
**Success rate:** 4/4 (100%)

**Mean task duration:** 0s (over success-eligible runs; timeout/no-delegation excluded)
**Mean turns:** 7.5

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ✅ | 6 | 36s | app.py, templates/base.html, templates/home.html (+1) | [36c9ba2307c0.jsonl](sessions/36c9ba2307c0.jsonl) |
| 2 | exited | ✅ | 9 | 47s | app.py, templates/base.html, templates/home.html (+1) | [ff6bd301caea.jsonl](sessions/ff6bd301caea.jsonl) |
| 3 | exited | ✅ | 9 | 46s | app.py, templates/base.html, templates/home.html (+1) | [18f6ba307774.jsonl](sessions/18f6ba307774.jsonl) |
| 4 | exited | ✅ | 6 | 43s | app.py, templates/base.html, templates/home.html (+1) | [70ba2af68613.jsonl](sessions/70ba2af68613.jsonl) |

## Subagent delegation metrics

No subagent delegations detected in any run.

## Evidence tier

- **Success rate:** artifact-backed — n=4 dated session files (GREEN per [evidence policy](../../superpowers/policies/evidence.md)).
- **Timing / turns:** real but noisy — n=4, single-model, single-provider (YELLOW). Compare deltas at n=4 with caution.
- **Statistical note:** n=4 — per-run success-rate deltas of ±1 run are within noise at this sample size. Cite structural claims, not small-sample tuning deltas.
