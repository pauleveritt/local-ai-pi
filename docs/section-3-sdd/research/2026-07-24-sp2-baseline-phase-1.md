# Baseline: Phase 1 — Home Page

**Date:** 2026-07-24
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Runs:** n=8
**Success rate:** 3/8 (38%)

**Mean wall time:** 483s
**Mean turns:** 9.9

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ✅ | 9 | 860s | app.py, models.py, templates/base.html (+4) | [947ed30c636b.jsonl](sessions/947ed30c636b.jsonl) |
| 2 | timeout | ❌ | 22 | 1396s | uv.lock, __init__.py, app.py (+7) | [11c78d4956d1.jsonl](sessions/11c78d4956d1.jsonl) |
| 3 | exited | ✅ | 7 | 508s | app.py, models.py, templates/base.html (+4) | [9e7cddfeaed6.jsonl](sessions/9e7cddfeaed6.jsonl) |
| 4 | exited | ❌ | 5 | 157s | app.py, templates/base.html, templates/home.html (+1) | [9fb6c2a64b64.jsonl](sessions/9fb6c2a64b64.jsonl) |
| 5 | exited | ❌ | 13 | 334s | app.py, templates/base.html, templates/home.html (+1) | [1d4fb2e033b0.jsonl](sessions/1d4fb2e033b0.jsonl) |
| 6 | exited | ✅ | 9 | 542s | app.py, models.py, templates/base.html (+4) | [b206d889c1e8.jsonl](sessions/b206d889c1e8.jsonl) |
| 7 | exited | ❌ | 9 | 778s | uv.lock, app.py, models.py (+5) | [c40312831cbf.jsonl](sessions/c40312831cbf.jsonl) |
| 8 | exited | ❌ | 5 | 205s | __init__.py, app.py, templates/base.html (+2) | [e3f2039e3fd4.jsonl](sessions/e3f2039e3fd4.jsonl) |

## Subagent delegation metrics

| # | Subagent calls | Packet size (bytes) |
|---|---------------|---------------------|
| 1 | 5 | 5,813 |
| 2 | 4 | 4,877 |
| 3 | 3 | 3,608 |
| 4 | 1 | 1,315 |
| 5 | 1 | 1,315 |
| 6 | 3 | 3,562 |
| 7 | 5 | 6,208 |
| 8 | 1 | 1,315 |
| **Agg** | μ=2.9 (in 8/8 runs) | μ=3,502 |

*Packet fidelity (verbatim literal matching) and implementer self-report
vs harness verdict agreement are deferred to a future harness iteration.*

## Evidence tier

- **Success rate:** artifact-backed — n=8 dated session files (GREEN per [evidence policy](../superpowers/policies/evidence.md)).
- **Delegation metrics:** artifact-backed — subagent call counts and packet sizes extracted from parent JSONLs (GREEN).
- **Timing / turns:** real but noisy — n=8, single-model, single-provider (YELLOW). Compare deltas at n=8 with caution.
- **Statistical note:** n=8 — per-run success-rate deltas of ±1 run are within noise (Fisher exact p≈1.0 at 3/8 vs 4/8). Cite the structural claim (0/8 → 3–4/8), not the tuning delta.
