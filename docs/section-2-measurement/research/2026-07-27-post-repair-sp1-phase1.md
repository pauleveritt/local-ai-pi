# Baseline: Phase 1 — Home Page

**Provenance note (added 2026-07-27, Rule 8 review — Fable).** This batch
was interrupted twice mid-run (a killed harness session at run 5, then a
genuine subprocess hang at run 13 — a `pi`-spawned grandchild holding a
pipe open past `proc.kill()`) and resumed both times from the checkpoint
introduced for exactly this purpose; no completed run was lost or
re-run. All 16 runs in this report — including runs 13–16 — completed
**before** the process-group hang fix (commit `1883a9c`) landed; Phases 2
and 3's reports ran under the fixed harness. This does not affect
grading (the acceptance path was already fully rebuilt and unaffected by
either issue), but it does mean runs 9 and 10's wall-time figures (658s,
882s) reflect hang-and-retry overhead specific to the pre-fix harness,
not model behavior, and are not comparable to Phase 2/3's timing.

**Date:** 2026-07-27
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Start state:** empty (no seed)
**pi version:** `0.82.0`
**Runs:** n=16
**Success rate:** 15/16 (94%)

**Mean process wall time:** 149s (harness-side subprocess timing, not artifact task duration — this pi version's --mode json stream has no per-event timestamps to compute the latter; over success-eligible runs, timeout/no-delegation excluded)
**Mean turns:** 12.8
**Hang incidence:** 2/16 runs required a retry after a killed attempt (exited-with-hang)

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited | ✅ | 19 | 205s | app.py, templates/base.html, templates/home.html (+1) | `80780db96d93` |
| 2 | exited | ✅ | 6 | 41s | app.py, templates/base.html, templates/home.html (+1) | `b0cf17e3ce0b` |
| 3 | exited | ✅ | 6 | 44s | app.py, templates/base.html, templates/home.html (+1) | `aca9d75a1bf1` |
| 4 | exited | ✅ | 6 | 43s | app.py, templates/base.html, templates/home.html (+1) | `7e4a878f0144` |
| 5 | exited | ✅ | 6 | 54s | app.py, templates/base.html, templates/home.html (+1) | `b1fd1a59deef` |
| 6 | exited | ✅ | 6 | 61s | app.py, templates/base.html, templates/home.html (+1) | `4fe2595f9206` |
| 7 | exited | ✅ | 6 | 67s | app.py, templates/base.html, templates/home.html (+1) | `cef5836d195e` |
| 8 | exited | ✅ | 6 | 86s | app.py, templates/base.html, templates/home.html (+1) | `915f845abb6c` |
| 9 | exited-with-hang | ❌ | 55 | 658s | app.py, templates/base.html, templates/home.html (+1) | `2cb78c0b8e53` |
| 10 | exited-with-hang | ✅ | 52 | 882s | app.py, templates/base.html, templates/home.html (+1) | `7d6d3eba87e8` |
| 11 | exited | ✅ | 6 | 53s | app.py, templates/base.html, templates/home.html (+1) | `ccd79336a0e8` |
| 12 | exited | ✅ | 6 | 49s | app.py, templates/base.html, templates/home.html (+1) | `8313a6dd6203` |
| 13 | exited | ✅ | 6 | 32s | app.py, templates/base.html, templates/home.html (+1) | `737fc6ae517b` |
| 14 | exited | ✅ | 6 | 34s | app.py, templates/base.html, templates/home.html (+1) | `c949495e2b9e` |
| 15 | exited | ✅ | 6 | 39s | app.py, templates/base.html, templates/home.html (+1) | `151caef34f7b` |
| 16 | exited | ✅ | 6 | 40s | app.py, templates/base.html, templates/home.html (+1) | `719873a1c232` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Subagent delegation metrics

No subagent delegations detected in any run.

## Behavioral instrumentation

**Inherited-file write attempts:** 0/16 runs (no seed -- not applicable)
**Shared-file replace-vs-extend:** replace=0 extend=0 untouched=16 (no seed -- not applicable)
**False self-report:** 1/16 runs (model's own suite passed; harness acceptance disagreed)

## Evidence tier

- **Outcome mix:** 14 exited, 2 exited-with-hang.
- **Success rate:** artifact-backed — n=16 dated session files (GREEN per [evidence policy](../../superpowers/policies/evidence.md)).
- **Timing / turns:** real but noisy — n=16, single-model, single-provider (YELLOW). Compare deltas at n=4 with caution.
