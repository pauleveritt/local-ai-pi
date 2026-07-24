# Baseline: Phase 1 — Home Page

```{warning}
**Superseded (2026-07-24).** The acceptance oracle behind this report was
invalid — it failed textbook-correct solutions — so these numbers measure an
unstated pytest-configuration workaround, not model competence. Kept for the
historical record. See the
[oracle-invalid incident report](../../section-2-measurement/research/2026-07-24-oracle-invalid-incident.md) and the
post-repair reports that replace this one.
```

**Date:** 2026-07-23
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Runs:** n=8
**Success rate:** 3/8 (38%)

**Mean wall time:** 329s
**Mean turns:** 7.8

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ✅ | 5 | 243s | uv.lock, app.py, templates/base.html (+3) | `59a7953f99c2` |
| 2 | exited | ❌ | 5 | 354s | app.py, templates/base.html, templates/home.html (+1) | `2f2cd6290a07` |
| 3 | exited | ❌ | 14 | 447s | app.py, models.py, templates/base.html (+3) | `fbb1228e0b31` |
| 4 | exited | ✅ | 5 | 145s | app.py, templates/base.html, templates/home.html (+2) | `c5c3aaef9664` |
| 5 | exited | ❌ | 7 | 619s | app.py, models.py, templates/base.html (+3) | `27b6a8cb533a` |
| 6 | exited | ✅ | 5 | 166s | app.py, templates/base.html, templates/home.html (+2) | `03fbeae3549d` |
| 7 | timeout | ❌ | 9 | 1426s | app.py, models.py, templates/base.html (+4) | `2d6a552cfdcf` |
| 8 | timeout | ❌ | 12 | 1609s | uv.lock, app.py, models.py (+4) | `b31afcf6dc58` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Subagent delegation metrics

| # | Subagent calls | Packet size (bytes) |
|---|---------------|---------------------|
| 1 | 1 | 1,315 |
| 2 | 1 | 1,315 |
| 3 | 3 | 3,632 |
| 4 | 1 | 1,315 |
| 5 | 3 | 3,606 |
| 6 | 1 | 1,315 |
| 7 | 4 | 4,950 |
| 8 | 4 | 5,248 |
| **Agg** | μ=2.2 (in 8/8 runs) | μ=2,837 |

*Packet fidelity (verbatim literal matching) and implementer self-report
vs harness verdict agreement are deferred to a future harness iteration.*

## Evidence tier

- **Success rate:** GREEN — n=8 artifact-backed runs
- **Timing / turns:** YELLOW — real but noisy (n=8, single-model, single-provider)
