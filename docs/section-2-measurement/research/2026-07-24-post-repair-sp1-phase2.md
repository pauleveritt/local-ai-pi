# Baseline: Phase 2 — Complaints Board

```{warning}
**Non-canonical start state (Amendment 1, 2026-07-24).** These runs started
from an EMPTY workspace, so they measured "build Phases 1+2 combined from
nothing," not Phase 2. The canonical phase-2 workload seeds the phase-1
reference solution (see the oracle-repair plan, Amendment 1). Kept as an
exploratory combined-workload data point; not citable as the Phase 2
baseline. Superseded by the seeded phase-2 reports.
```


**Date:** 2026-07-24
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Runs:** n=4
**Success rate:** 0/4 (0%)

**Mean task duration:** 0s (over success-eligible runs; timeout/no-delegation excluded)
**Mean turns:** 11.8
**Oracle validated:** `tests/test_oracle.py` green at commit `760197c`

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ❌ | 13 | 63s | app.py, models.py, templates/base.html (+2) | [8c9e54401325.jsonl](sessions/8c9e54401325.jsonl) |
| 2 | exited | ❌ | 12 | 63s | app.py, models.py, templates/base.html (+2) | [e5e447a20181.jsonl](sessions/e5e447a20181.jsonl) |
| 3 | exited | ❌ | 12 | 68s | app.py, models.py, templates/base.html (+2) | [960f3cd5753d.jsonl](sessions/960f3cd5753d.jsonl) |
| 4 | exited | ❌ | 10 | 72s | app.py, models.py, templates/base.html (+2) | [d7e713bd071f.jsonl](sessions/d7e713bd071f.jsonl) |

## Subagent delegation metrics

No subagent delegations detected in any run.

## Evidence tier

- **Success rate:** artifact-backed — n=4 dated session files (GREEN per [evidence policy](../superpowers/policies/evidence.md)).
- **Timing / turns:** real but noisy — n=4, single-model, single-provider (YELLOW). Compare deltas at n=4 with caution.
- **Statistical note:** n=4 — per-run success-rate deltas of ±1 run are within noise at this sample size. Cite structural claims, not small-sample tuning deltas.
