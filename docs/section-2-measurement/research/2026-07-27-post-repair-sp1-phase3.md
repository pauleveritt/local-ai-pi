# Baseline: Phase 3 — Add Complaint

**Date:** 2026-07-27
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Start state:** seeded: examples/reference/phase-2
**pi version:** `0.82.0`
**Runs:** n=16
**Success rate:** 16/16 (100%)

**Mean process wall time:** 91s (harness-side subprocess timing, not artifact task duration — this pi version's --mode json stream has no per-event timestamps to compute the latter; over success-eligible runs, timeout/no-delegation excluded)
**Mean turns:** 10.8

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ✅ | 17 | 73s | app.py, templates/complaints.html, tests/test_app.py | `806c4e41be94` |
| 2 | exited | ✅ | 10 | 64s | app.py, templates/complaints.html, tests/test_app.py | `1452e91efe96` |
| 3 | exited | ✅ | 10 | 74s | app.py, templates/complaints.html, tests/test_app.py | `a11cdd5d6b20` |
| 4 | exited | ✅ | 10 | 90s | app.py, templates/complaints.html, tests/test_app.py | `9deb8d614c4e` |
| 5 | exited | ✅ | 10 | 96s | app.py, templates/complaints.html, tests/test_app.py | `6a37226dda9c` |
| 6 | exited | ✅ | 11 | 108s | app.py, templates/complaints.html, tests/test_app.py | `147a45f8c5f1` |
| 7 | exited | ✅ | 16 | 194s | app.py, templates/complaints.html, tests/test_app.py | `6b04a483aa8a` |
| 8 | exited | ✅ | 10 | 85s | app.py, templates/complaints.html, tests/test_app.py | `c08c882d3fc9` |
| 9 | exited | ✅ | 10 | 81s | app.py, templates/complaints.html, tests/test_app.py | `323a56fe2447` |
| 10 | exited | ✅ | 10 | 84s | app.py, templates/complaints.html, tests/test_app.py | `d20fd053a468` |
| 11 | exited | ✅ | 10 | 78s | app.py, templates/complaints.html, tests/test_app.py | `ddf3be1ca578` |
| 12 | exited | ✅ | 10 | 78s | app.py, templates/complaints.html, tests/test_app.py | `a2ab852c4fa7` |
| 13 | exited | ✅ | 10 | 92s | app.py, templates/complaints.html, tests/test_app.py | `9baefe173c4a` |
| 14 | exited | ✅ | 10 | 84s | app.py, templates/complaints.html, tests/test_app.py | `62f497432fd2` |
| 15 | exited | ✅ | 9 | 87s | app.py, templates/complaints.html, tests/test_app.py | `c0bd5339ab26` |
| 16 | exited | ✅ | 10 | 90s | app.py, templates/complaints.html, tests/test_app.py | `1312b5272a65` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Subagent delegation metrics

No subagent delegations detected in any run.

## Behavioral instrumentation

**Inherited-file write attempts:** 4/16 runs
**Shared-file replace-vs-extend:** replace=4 extend=12 untouched=0
**False self-report:** 0/16 runs (model's own suite passed; harness acceptance disagreed)

## Evidence tier

- **Outcome mix:** 16 exited.
- **Success rate:** artifact-backed — n=16 dated session files (GREEN per [evidence policy](../../superpowers/policies/evidence.md)).
- **Timing / turns:** real but noisy — n=16, single-model, single-provider (YELLOW). Compare deltas at n=4 with caution.
