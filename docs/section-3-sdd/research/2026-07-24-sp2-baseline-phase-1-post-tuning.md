# Baseline: Phase 1 — Home Page (post-tuning re-run)

```{warning}
**Superseded (2026-07-24).** The acceptance oracle behind this report was
invalid — it failed textbook-correct solutions — so these numbers measure an
unstated pytest-configuration workaround, not model competence. Kept for the
historical record. See the
[oracle-invalid incident report](../../section-2-measurement/research/2026-07-24-oracle-invalid-incident.md) and the
post-repair reports that replace this one.
```

**Date:** 2026-07-24
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Runs:** n=8
**Success rate:** 5/8 (62%)

**Mean task duration:** 0s (over success-eligible runs; timeout/no-delegation excluded)
**Mean turns:** 6.6
**Hang incidence:** 1/8 runs required a retry after a killed attempt (exited-with-hang)

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ❌ | 4 | 133s | app.py, templates/base.html, templates/home.html (+1) | `cd42f62601df` |
| 2 | exited | ✅ | 9 | 260s | app.py, templates/base.html, templates/home.html (+1) | `63ad907b08e0` |
| 3 | exited | ❌ | 4 | 316s | app.py, templates/base.html, templates/home.html (+1) | `f4a48bb64868` |
| 4 | exited | ✅ | 9 | 207s | app.py, templates/base.html, templates/home.html (+2) | `9050ba1ed8fc` |
| 5 | exited-with-hang | ❌ | 8 | 690s | app.py, templates/base.html, templates/home.html (+2) | `4e90a4ba4d35` |
| 6 | exited | ✅ | 5 | 340s | app.py, templates/base.html, templates/home.html (+2) | `871d212410c7` |
| 7 | exited | ✅ | 9 | 385s | app.py, templates/base.html, templates/home.html (+2) | `d1e8f551f274` |
| 8 | exited | ✅ | 5 | 186s | app.py, templates/base.html, templates/home.html (+2) | `0d1d54ee57ed` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Subagent delegation metrics

| # | Subagent calls | Packet size (bytes) |
|---|---------------|---------------------|
| 1 | 1 | 1,315 |
| 2 | 2 | 1,777 |
| 3 | 1 | 1,315 |
| 4 | 1 | 1,315 |
| 5 | 2 | 1,642 |
| 6 | 1 | 1,315 |
| 7 | 1 | 1,315 |
| 8 | 1 | 1,315 |
| **Agg** | μ=1.2 (in 8/8 runs) | μ=1,414 |

*Packet fidelity (verbatim literal matching) and implementer self-report
vs harness verdict agreement are deferred to a future harness iteration.*

## Evidence tier

- **Success rate:** artifact-backed — n=8 dated session files (GREEN per [evidence policy](../../superpowers/policies/evidence.md)).
- **Delegation metrics:** artifact-backed — subagent call counts and packet sizes extracted from parent JSONLs (GREEN).
- **Timing / turns:** real but noisy — n=8, single-model, single-provider (YELLOW). Compare deltas at n=4 with caution.
- **Statistical note:** n=8 — per-run success-rate deltas of ±1 run are within noise at this sample size. Cite structural claims, not small-sample tuning deltas.
