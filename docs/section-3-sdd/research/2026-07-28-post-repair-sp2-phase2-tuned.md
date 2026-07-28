# Baseline: Phase 2 — Tuned SP2

**Date:** 2026-07-28
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Start state:** seeded: examples/reference/phase-1
**pi version:** `0.82.0`
**Runs:** n=16
**Success rate:** 16/16 (100%)

**Mean process wall time:** 150s (harness-side subprocess timing, not artifact task duration — this pi version's --mode json stream has no per-event timestamps to compute the latter; over success-eligible runs, timeout/no-delegation excluded)
**Mean turns:** 8.1

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ✅ | 9 | 134s | app.py, tests/test_app.py, models.py (+1) | `75869424f9e4` |
| 2 | exited | ✅ | 9 | 150s | app.py, tests/test_app.py, models.py (+1) | `4380b3d892bb` |
| 3 | exited | ✅ | 5 | 130s | app.py, tests/test_app.py, models.py (+1) | `d56de1ac0b65` |
| 4 | exited | ✅ | 8 | 140s | app.py, tests/test_app.py, models.py (+1) | `abd78085f450` |
| 5 | exited | ✅ | 8 | 145s | app.py, tests/test_app.py, models.py (+1) | `5efd03f83d56` |
| 6 | exited | ✅ | 10 | 238s | app.py, tests/test_app.py, models.py (+1) | `c05ad7d592ae` |
| 7 | exited | ✅ | 8 | 158s | app.py, tests/test_app.py, models.py (+1) | `f2c94537d8c9` |
| 8 | exited | ✅ | 9 | 150s | app.py, tests/test_app.py, models.py (+1) | `e78c07bb842a` |
| 9 | exited | ✅ | 6 | 150s | app.py, tests/test_app.py, models.py (+1) | `a6d7b9ce9cbd` |
| 10 | exited | ✅ | 10 | 156s | app.py, tests/test_app.py, models.py (+1) | `c2dcec111a02` |
| 11 | exited | ✅ | 9 | 142s | app.py, tests/test_app.py, models.py (+1) | `8f978d397f99` |
| 12 | exited | ✅ | 9 | 157s | app.py, tests/test_app.py, models.py (+1) | `f11de34cd1c1` |
| 13 | exited | ✅ | 8 | 133s | app.py, tests/test_app.py, models.py (+1) | `304d7c65fddb` |
| 14 | exited | ✅ | 9 | 147s | app.py, tests/test_app.py, models.py (+1) | `27b4ea1fa062` |
| 15 | exited | ✅ | 5 | 141s | app.py, tests/test_app.py, models.py (+1) | `9f636de41276` |
| 16 | exited | ✅ | 8 | 137s | app.py, tests/test_app.py, models.py (+1) | `b5e7005ac55d` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Subagent delegation metrics

| # | Subagent calls | Packet size (bytes) |
|---|---------------|---------------------|
| 1 | 1 | 1,365 |
| 2 | 1 | 1,365 |
| 3 | 1 | 1,365 |
| 4 | 1 | 1,365 |
| 5 | 1 | 1,365 |
| 6 | 2 | 2,838 |
| 7 | 1 | 1,365 |
| 8 | 1 | 1,365 |
| 9 | 1 | 1,344 |
| 10 | 1 | 1,365 |
| 11 | 1 | 1,344 |
| 12 | 1 | 1,365 |
| 13 | 1 | 1,365 |
| 14 | 1 | 1,387 |
| 15 | 1 | 1,380 |
| 16 | 1 | 1,426 |
| **Agg** | μ=1.1 (in 16/16 runs) | μ=1,461 |

*Packet fidelity (verbatim literal matching) and implementer self-report
vs harness verdict agreement are deferred to a future harness iteration.*

## Behavioral instrumentation

**Inherited-file write attempts:** 0/16 runs
**Shared-file replace-vs-extend:** replace=0 extend=0 untouched=16
**False self-report:** 0/16 runs (model's own suite passed; harness acceptance disagreed)

## Evidence tier

- **Outcome mix:** 16 exited.
- **Success rate:** artifact-backed — n=16 dated session files (GREEN per [evidence policy](../../superpowers/policies/evidence.md)).
- **Delegation metrics:** artifact-backed — subagent call counts and packet sizes extracted from parent JSONLs (GREEN).
- **Timing / turns:** real but noisy — n=16, single-model, single-provider (YELLOW). Compare deltas at n=4 with caution.
