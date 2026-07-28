# Baseline: Phase 3 — Tuned SP2

**Date:** 2026-07-28
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Start state:** seeded: examples/reference/phase-2
**pi version:** `0.82.0`
**Runs:** n=16
**Success rate:** 16/16 (100%)

**Mean process wall time:** 407s (harness-side subprocess timing, not artifact task duration — this pi version's --mode json stream has no per-event timestamps to compute the latter; over success-eligible runs, timeout/no-delegation excluded)
**Mean turns:** 8.1
**Hang incidence:** 4/16 runs required a retry after a killed attempt (exited-with-hang)
**Drift incidence:** 1/16 runs (overreach=1)

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ✅ | 6 | 251s | app.py, templates/complaints.html, tests/test_app.py | `84fab024c747` |
| 2 | exited | ✅ | 9 | 349s | app.py, templates/complaints.html, tests/test_app.py | `97fe1d3e5934` |
| 3 | exited | ✅ | 7 | 232s | app.py, templates/complaints.html, tests/test_app.py | `bc460d027023` |
| 4 | exited-with-hang | ✅ | 2 | 900s | app.py, templates/complaints.html, tests/test_app.py | `0e8057a50162` |
| 5 | exited | ✅ | 6 | 134s | app.py, templates/complaints.html, tests/test_app.py | `cfaa4f5d938a` |
| 6 | exited | ✅ | 8 | 377s | app.py, templates/complaints.html, tests/test_app.py | `ddc5e64df7ca` |
| 7 | exited | ✅ | 8 | 315s | app.py, templates/complaints.html, tests/test_app.py (+3) | `c1e932ab390f` |
| 8 | exited-with-hang | ✅ | 31 | 900s | app.py, templates/complaints.html, tests/test_app.py | `1549ed13a963` |
| 9 | exited-with-hang | ✅ | 3 | 900s | app.py, templates/complaints.html, tests/test_app.py | `22d0bd36d34b` |
| 10 | exited | ✅ | 7 | 209s | app.py, templates/complaints.html, tests/test_app.py | `80953b947b1e` |
| 11 | exited-with-hang | ✅ | 2 | 900s | app.py, templates/complaints.html, tests/test_app.py | `1cfed3cd58c5` |
| 12 | exited | ✅ | 7 | 367s | app.py, templates/complaints.html, tests/test_app.py | `6408506cd686` |
| 13 | exited | ✅ | 9 | 198s | app.py, templates/complaints.html, tests/test_app.py | `858cb779d299` |
| 14 | exited | ✅ | 8 | 160s | app.py, templates/complaints.html, tests/test_app.py | `ddb6a79861e8` |
| 15 | exited | ✅ | 8 | 155s | app.py, templates/complaints.html, tests/test_app.py | `6de8b24c566f` |
| 16 | exited | ✅ | 8 | 163s | app.py, templates/complaints.html, tests/test_app.py | `e48abae6f280` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Subagent delegation metrics

| # | Subagent calls | Packet size (bytes) |
|---|---------------|---------------------|
| 1 | 1 | 796 |
| 2 | 2 | 2,192 |
| 3 | 1 | 765 |
| 4 | 1 | 734 |
| 5 | 1 | 712 |
| 6 | 1 | 734 |
| 7 | 1 | 734 |
| 8 | 1 | 792 |
| 9 | 1 | 765 |
| 10 | 1 | 762 |
| 11 | 1 | 746 |
| 12 | 1 | 719 |
| 13 | 1 | 712 |
| 14 | 1 | 734 |
| 15 | 1 | 734 |
| 16 | 1 | 734 |
| **Agg** | μ=1.1 (in 16/16 runs) | μ=835 |

*Packet fidelity (verbatim literal matching) and implementer self-report
vs harness verdict agreement are deferred to a future harness iteration.*

## Behavioral instrumentation

**Inherited-file write attempts:** 0/16 runs
**Shared-file replace-vs-extend:** replace=0 extend=1 untouched=15
**False self-report:** 0/16 runs (model's own suite passed; harness acceptance disagreed)

## Evidence tier

- **Outcome mix:** 12 exited, 4 exited-with-hang.
- **Success rate:** artifact-backed — n=16 dated session files (GREEN per [evidence policy](../../superpowers/policies/evidence.md)).
- **Delegation metrics:** artifact-backed — subagent call counts and packet sizes extracted from parent JSONLs (GREEN).
- **Timing / turns:** real but noisy — n=16, single-model, single-provider (YELLOW). Compare deltas at n=4 with caution.
