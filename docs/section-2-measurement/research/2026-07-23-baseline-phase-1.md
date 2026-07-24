# Baseline: Phase 1 — Home Page

```{warning}
**Superseded (2026-07-24).** The acceptance oracle behind this report was
invalid — it failed textbook-correct solutions — so these numbers measure an
unstated pytest-configuration workaround, not model competence. Kept for the
historical record. See the
[oracle-invalid incident report](2026-07-24-oracle-invalid-incident.md) and the
post-repair reports that replace this one.
```

**Date:** 2026-07-23
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Runs:** n=8
**Success rate:** 0/8 (0%)

**Mean wall time:** 45s
**Mean turns:** 6.4

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ❌ | 6 | 43s | app.py, templates/base.html, templates/home.html (+1) | `e7b32440f47e` |
| 2 | exited | ❌ | 6 | 38s | app.py, templates/base.html, templates/home.html (+1) | `6fb41cb953ce` |
| 3 | exited | ❌ | 6 | 39s | app.py, templates/base.html, templates/home.html (+1) | `2412dba6e110` |
| 4 | exited | ❌ | 6 | 39s | app.py, templates/base.html, templates/home.html (+1) | `bc85c2e72a25` |
| 5 | exited | ❌ | 6 | 43s | app.py, templates/base.html, templates/home.html (+1) | `106a89faa42a` |
| 6 | exited | ❌ | 9 | 52s | app.py, templates/base.html, templates/home.html (+1) | `c4a30fee6a04` |
| 7 | exited | ❌ | 6 | 64s | app.py, templates/base.html, templates/home.html (+1) | `eef6ba17f259` |
| 8 | exited | ❌ | 6 | 45s | app.py, templates/base.html, templates/home.html (+1) | `b53e9a5132cc` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Evidence tier

- **Success rate:** GREEN — n=8 artifact-backed runs
- **Timing / turns:** YELLOW — real but noisy (n=8, single-model, single-provider)
