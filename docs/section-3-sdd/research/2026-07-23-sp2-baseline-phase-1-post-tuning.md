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
**Success rate:** 4/8 (50%)

**Mean wall time:** 213s
**Mean turns:** 7.6

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ✅ | 8 | 236s | app.py, templates/base.html, templates/home.html (+1) | `03b60d2ee8b9` |
| 2 | exited | ✅ | 7 | 305s | uv.lock, app.py, templates/base.html (+2) | `1929617fa8dd` |
| 3 | timeout | ❌ | 12 | 947s | app.py, templates/base.html, templates/home.html (+1) | `0c4cb9e51290` |
| 4 | exited | ✅ | 9 | 195s | app.py, templates/base.html, templates/home.html (+2) | `44a9f34c51a5` |
| 5 | timeout | ❌ | 6 | 913s | app.py, models.py, templates/base.html (+3) | `c2d816c525ac` |
| 6 | exited | ✅ | 9 | 167s | app.py, templates/base.html, templates/home.html (+2) | `65a74c4b7498` |
| 7 | exited | ❌ | 5 | 173s | __init__.py, app.py, templates/base.html (+3) | `b017a8b1dc2b` |
| 8 | exited | ❌ | 5 | 200s | app.py, templates/base.html, templates/home.html (+1) | `8527dc8c3d4d` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Subagent delegation metrics

| # | Subagent calls | Packet size (bytes) |
|---|---------------|---------------------|
| 1 | 2 | 2,075 |
| 2 | 2 | 1,748 |
| 3 | 1 | 1,315 |
| 4 | 1 | 1,315 |
| 5 | 3 | 3,562 |
| 6 | 1 | 1,315 |
| 7 | 1 | 1,315 |
| 8 | 1 | 1,315 |
| **Agg** | μ=1.5 (in 8/8 runs) | μ=1,745 |

*Packet fidelity (verbatim literal matching) and implementer self-report
vs harness verdict agreement are deferred to a future harness iteration.*

## Evidence tier

- **Success rate:** GREEN — n=8 artifact-backed runs
- **Timing / turns:** YELLOW — real but noisy (n=8, single-model, single-provider)
