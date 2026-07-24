# Baseline: Phase 2 — Complaints Board (pooled n=8, SP1)

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
**Runs:** n=8
**Success rate:** 0/8 (0%)

**Mean task duration:** 0s (over success-eligible runs; timeout/no-delegation excluded)
**Mean turns:** 11.0
**Oracle validated:** `tests/test_oracle.py` green at commit `083dbd7`

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ❌ | 16 | 139s | app.py, models.py, templates/base.html (+2) | `190e436e3787` |
| 2 | exited | ❌ | 13 | 107s | app.py, models.py, templates/base.html (+2) | `34941389a337` |
| 3 | exited | ❌ | 9 | 63s | app.py, models.py, templates/base.html (+2) | `686faff788f2` |
| 4 | exited | ❌ | 10 | 68s | app.py, models.py, templates/base.html (+2) | `46419db43a9f` |
| 5 | exited | ❌ | 11 | 69s | app.py, models.py, templates/base.html (+2) | `4ef829bc0a4a` |
| 6 | exited | ❌ | 10 | 92s | app.py, models.py, templates/base.html (+2) | `0dbacb285f03` |
| 7 | exited | ❌ | 8 | 63s | app.py, models.py, templates/base.html (+2) | `4a9913015eee` |
| 8 | exited | ❌ | 11 | 92s | app.py, models.py, templates/base.html (+2) | `de059e8b9351` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Subagent delegation metrics

No subagent delegations detected in any run.

## Evidence tier

- **Success rate:** artifact-backed — n=8 dated session files (GREEN per [evidence policy](../../superpowers/policies/evidence.md)).
- **Timing / turns:** real but noisy — n=8, single-model, single-provider (YELLOW). Compare deltas at n=4 with caution.
- **Statistical note:** n=8 — per-run success-rate deltas of ±1 run are within noise at this sample size. Cite structural claims, not small-sample tuning deltas.
