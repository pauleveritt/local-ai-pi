# Baseline: Phase 2 — Complaints Board

**Date:** 2026-07-24
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Start state:** seeded: examples/reference/phase-1
**Runs:** n=4
**Success rate:** 2/4 (50%)

**Mean process wall time:** 60s (harness-side subprocess timing, not artifact task duration — this pi version's --mode json stream has no per-event timestamps to compute the latter; over success-eligible runs, timeout/no-delegation excluded)
**Mean turns:** 10.0
**Oracle validated:** `tests/test_oracle.py` green at commit `d5c294b`

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ✅ | 8 | 42s | app.py, tests/test_app.py, models.py (+1) | `f638e3d0088a` |
| 2 | exited | ❌ | 11 | 49s | app.py, templates/base.html, tests/test_app.py (+2) | `aa7a0ac8980b` |
| 3 | exited | ✅ | 10 | 59s | app.py, tests/test_app.py, models.py (+1) | `5d6c176ddda3` |
| 4 | exited | ❌ | 11 | 91s | app.py, tests/test_app.py, models.py (+1) | `c1acd1f2b533` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Subagent delegation metrics

No subagent delegations detected in any run.

## Evidence tier

- **Success rate:** artifact-backed — n=4 dated session files (GREEN per [evidence policy](../../superpowers/policies/evidence.md)).
- **Timing / turns:** real but noisy — n=4, single-model, single-provider (YELLOW). Compare deltas at n=4 with caution.
- **Statistical note:** n=4 — per-run success-rate deltas of ±1 run are within noise at this sample size. Cite structural claims, not small-sample tuning deltas.
