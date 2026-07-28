# Baseline: Phase 1 — Tuned SP2

**Date:** 2026-07-28
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Start state:** empty (no seed)
**pi version:** `0.82.0`
**Runs:** n=16
**Success rate:** 15/16 (94%)

**Mean process wall time:** 188s (harness-side subprocess timing, not artifact task duration — this pi version's --mode json stream has no per-event timestamps to compute the latter; over success-eligible runs, timeout/no-delegation excluded)
**Mean turns:** 8.8
**Drift incidence:** 2/16 runs (overreach=2)

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ✅ | 9 | 76s | app.py, templates/base.html, templates/home.html (+1) | `3d76ccb16bad` |
| 2 | exited | ✅ | 9 | 84s | app.py, templates/base.html, templates/home.html (+1) | `e02aaa94f45e` |
| 3 | exited | ❌ | 18 | 830s | uv.lock, app.py, models.py (+4) | `55dbfd2a5e44` |
| 4 | exited | ✅ | 8 | 90s | app.py, templates/base.html, templates/home.html (+1) | `0356c6a96ccd` |
| 5 | exited | ✅ | 8 | 72s | app.py, templates/base.html, templates/home.html (+1) | `9f90a4bf2282` |
| 6 | exited | ✅ | 5 | 142s | app.py, templates/base.html, templates/home.html (+1) | `cbffd1079025` |
| 7 | exited | ✅ | 5 | 95s | app.py, templates/base.html, templates/home.html (+1) | `e038a1042364` |
| 8 | exited | ✅ | 9 | 142s | app.py, templates/base.html, templates/home.html (+1) | `1051e12c3141` |
| 9 | exited | ✅ | 5 | 87s | app.py, templates/base.html, templates/home.html (+1) | `37f7e264cce3` |
| 10 | exited | ✅ | 8 | 96s | app.py, templates/base.html, templates/home.html (+1) | `3e656cd6443b` |
| 11 | exited | ✅ | 8 | 87s | app.py, templates/base.html, templates/home.html (+1) | `5cbbccc98173` |
| 12 | exited | ✅ | 13 | 826s | app.py, models.py, request_test.py (+7) | `aeea65f9f243` |
| 13 | exited | ✅ | 10 | 95s | app.py, templates/base.html, templates/home.html (+1) | `7e78495cae46` |
| 14 | exited | ✅ | 9 | 93s | app.py, templates/base.html, templates/home.html (+1) | `a2148a2cb677` |
| 15 | exited | ✅ | 8 | 90s | app.py, templates/base.html, templates/home.html (+1) | `4d5e02c690bb` |
| 16 | exited | ✅ | 9 | 103s | app.py, templates/base.html, templates/home.html (+1) | `e221aedce934` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Subagent delegation metrics

| # | Subagent calls | Packet size (bytes) |
|---|---------------|---------------------|
| 1 | 1 | 1,369 |
| 2 | 1 | 1,315 |
| 3 | 7 | 6,915 |
| 4 | 1 | 1,315 |
| 5 | 1 | 1,315 |
| 6 | 1 | 1,315 |
| 7 | 1 | 1,315 |
| 8 | 1 | 1,315 |
| 9 | 1 | 1,315 |
| 10 | 1 | 1,369 |
| 11 | 1 | 1,315 |
| 12 | 5 | 4,941 |
| 13 | 1 | 1,315 |
| 14 | 1 | 1,315 |
| 15 | 1 | 1,369 |
| 16 | 1 | 1,369 |
| **Agg** | μ=1.6 (in 16/16 runs) | μ=1,905 |

*Packet fidelity (verbatim literal matching) and implementer self-report
vs harness verdict agreement are deferred to a future harness iteration.*

## Behavioral instrumentation

**Inherited-file write attempts:** 0/16 runs (no seed -- not applicable)
**Shared-file replace-vs-extend:** replace=0 extend=0 untouched=16 (no seed -- not applicable)
**False self-report:** 1/16 runs (model's own suite passed; harness acceptance disagreed)

## Evidence tier

- **Outcome mix:** 16 exited.
- **Success rate:** artifact-backed — n=16 dated session files (GREEN per [evidence policy](../../superpowers/policies/evidence.md)).
- **Delegation metrics:** artifact-backed — subagent call counts and packet sizes extracted from parent JSONLs (GREEN).
- **Timing / turns:** real but noisy — n=16, single-model, single-provider (YELLOW). Compare deltas at n=4 with caution.
