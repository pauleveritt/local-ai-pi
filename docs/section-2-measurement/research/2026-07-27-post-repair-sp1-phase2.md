# Baseline: Phase 2 — Complaints Board

**Date:** 2026-07-27
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Start state:** seeded: examples/reference/phase-1
**pi version:** `0.82.0`
**Runs:** n=16
**Success rate:** 15/16 (94%)

**Mean process wall time:** 56s (harness-side subprocess timing, not artifact task duration — this pi version's --mode json stream has no per-event timestamps to compute the latter; over success-eligible runs, timeout/no-delegation excluded)
**Mean turns:** 8.6

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ✅ | 6 | 34s | app.py, tests/test_app.py, models.py (+1) | `316b73bf5bc4` |
| 2 | exited | ✅ | 8 | 46s | app.py, tests/test_app.py, models.py (+1) | `b9d2d8e3c5be` |
| 3 | exited | ✅ | 7 | 40s | app.py, tests/test_app.py, models.py (+1) | `d3ad56067688` |
| 4 | exited | ✅ | 9 | 55s | app.py, tests/test_app.py, models.py (+1) | `b9daaecf1280` |
| 5 | exited | ✅ | 10 | 57s | app.py, tests/test_app.py, models.py (+1) | `8046bf51642c` |
| 6 | exited | ✅ | 8 | 62s | app.py, tests/test_app.py, models.py (+1) | `f0a1f32a2df1` |
| 7 | exited | ❌ | 7 | 42s | app.py, tests/test_app.py, models.py (+1) | `ae104e39493e` |
| 8 | exited | ✅ | 9 | 64s | app.py, tests/test_app.py, models.py (+1) | `72594c7a0e75` |
| 9 | exited | ✅ | 9 | 63s | app.py, tests/test_app.py, models.py (+1) | `34c85edb5947` |
| 10 | exited | ✅ | 9 | 61s | app.py, tests/test_app.py, models.py (+1) | `ea97ef3dd0fb` |
| 11 | exited | ✅ | 9 | 58s | app.py, tests/test_app.py, models.py (+1) | `4a543bec346b` |
| 12 | exited | ✅ | 10 | 64s | app.py, tests/test_app.py, models.py (+1) | `44937d887d2f` |
| 13 | exited | ✅ | 8 | 62s | app.py, tests/test_app.py, models.py (+1) | `a2ee7a909798` |
| 14 | exited | ✅ | 12 | 80s | app.py, tests/test_app.py, models.py (+1) | `5e59b238707a` |
| 15 | exited | ✅ | 8 | 54s | app.py, tests/test_app.py, models.py (+1) | `f1de75f7812b` |
| 16 | exited | ✅ | 9 | 62s | app.py, tests/test_app.py, models.py (+1) | `9d7a7d67da2d` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Subagent delegation metrics

No subagent delegations detected in any run.

## Behavioral instrumentation

**Inherited-file write attempts:** 5/16 runs
**Shared-file replace-vs-extend:** replace=5 extend=11 untouched=0
**False self-report:** 0/16 runs (model's own suite passed; harness acceptance disagreed)

## Evidence tier

- **Outcome mix:** 16 exited.
- **Success rate:** artifact-backed — n=16 dated session files (GREEN per [evidence policy](../../superpowers/policies/evidence.md)).
- **Timing / turns:** real but noisy — n=16, single-model, single-provider (YELLOW). Compare deltas at n=4 with caution.
