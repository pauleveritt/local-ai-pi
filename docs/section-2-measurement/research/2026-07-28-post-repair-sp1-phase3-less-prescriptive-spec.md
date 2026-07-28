# Baseline: Phase 3 — Add Complaint

**Spec variant:** rewritten phase-3 spec, commit `9cb73f0` — no longer states
the answer to the redirect-status and `follow_redirects` traps
(`lessons.md` #13). See
[`docs/superpowers/specs/2026-07-27-next-phase-decision-design.md`](../../superpowers/specs/2026-07-27-next-phase-decision-design.md)
Decision 1.

**Date:** 2026-07-28
**Model:** omlx/gemma-4-12B-it-MLX-8bit
**Start state:** seeded: examples/reference/phase-2
**pi version:** `0.82.0`
**Runs:** n=16
**Success rate:** 16/16 (100%)

**Mean process wall time:** 205s (harness-side subprocess timing, not artifact task duration — this pi version's --mode json stream has no per-event timestamps to compute the latter; over success-eligible runs, timeout/no-delegation excluded)
**Mean turns:** 24.2
**Hang incidence:** 6/16 runs required a retry after a killed attempt (exited-with-hang)
**Drift incidence:** 1/16 runs (overreach=1)

| # | Outcome | Success | Turns | Wall Time | Changed Files | Artifact |
|---|---------|---------|-------|-----------|---------------|----------|
| 1 | exited-with-hang | ✅ | 23 | 300s | app.py, templates/complaints.html, tests/test_app.py | `2b9c7afba085` |
| 2 | exited-with-hang | ✅ | 31 | 300s | app.py, templates/complaints.html, tests/test_app.py | `5fd22df26b84` |
| 3 | exited-with-hang | ✅ | 30 | 300s | app.py, templates/complaints.html, tests/test_app.py (+3) | `fd6327377d6f` |
| 4 | exited-with-hang | ✅ | 34 | 300s | app.py, templates/complaints.html, tests/test_app.py | `622ee0732f63` |
| 5 | exited | ✅ | 9 | 82s | app.py, templates/complaints.html, tests/test_app.py | `6cb468c07a2b` |
| 6 | exited | ✅ | 37 | 246s | app.py, templates/complaints.html, tests/test_app.py | `1969bedb466c` |
| 7 | exited | ✅ | 10 | 91s | app.py, templates/complaints.html, tests/test_app.py | `e466a066a51b` |
| 8 | exited | ✅ | 9 | 89s | app.py, templates/complaints.html, tests/test_app.py | `d2df8c917873` |
| 9 | exited | ✅ | 28 | 235s | app.py, templates/complaints.html, tests/test_app.py | `d7d5e514ae79` |
| 10 | exited-with-hang | ✅ | 41 | 300s | app.py, templates/complaints.html, tests/test_app.py | `8462d9bdd446` |
| 11 | exited | ✅ | 9 | 87s | app.py, templates/complaints.html, tests/test_app.py | `e2183140572d` |
| 12 | exited-with-hang | ✅ | 37 | 300s | app.py, templates/complaints.html, tests/test_app.py | `9e7564a5461a` |
| 13 | exited | ✅ | 28 | 219s | app.py, templates/complaints.html, tests/test_app.py | `9470e7668755` |
| 14 | exited | ✅ | 10 | 95s | app.py, templates/complaints.html, tests/test_app.py | `88a39cef4eee` |
| 15 | exited | ✅ | 42 | 258s | app.py, templates/complaints.html, tests/test_app.py | `32b110b77eda` |
| 16 | exited | ✅ | 9 | 76s | app.py, templates/complaints.html, tests/test_app.py | `4d6fedb728e4` |

*Session transcripts are retained locally at `research/sessions/<id>.jsonl` and are not published — see [artifact retention](../../superpowers/policies/evidence.md#artifact-retention).*

## Subagent delegation metrics

No subagent delegations detected in any run.

## Behavioral instrumentation

**Inherited-file write attempts:** 6/16 runs
**Shared-file replace-vs-extend:** replace=6 extend=10 untouched=0
**False self-report:** 0/16 runs (model's own suite passed; harness acceptance disagreed)

## Evidence tier

- **Outcome mix:** 10 exited, 6 exited-with-hang.
- **Success rate:** artifact-backed — n=16 dated session files (GREEN per [evidence policy](../../superpowers/policies/evidence.md)).
- **Timing / turns:** real but noisy — n=16, single-model, single-provider (YELLOW). Compare deltas at n=4 with caution.

## Disposition

**Corroborates, does not supersede,** the standing
[2026-07-27 report](2026-07-27-post-repair-sp1-phase3.md) (16/16). Removing
the `RedirectResponse`/`follow_redirects` implementation and test-technique
hints did not reopen a ditch at n=16 — spec prescriptiveness was not
load-bearing for the original no-ditch result. Amendment 1 decision 4's
disposition (Section III proceeds, cost-equivalence framing) stands
unchanged.

**Success rate is not the whole story here, per evidence policy D2
(failure-mode incidence is the primary metric).** Two behavioral-incidence
numbers moved substantially between the two reports, at identical n=16,
same model, same seed, same acceptance suite — only the spec's wording
changed:

| Metric | 2026-07-27 (prescriptive spec) | 2026-07-28 (this report) |
|---|---|---|
| Success rate | 16/16 | 16/16 |
| Hang incidence | 0/16 | 6/16 |
| Mean turns | 10.8 | 24.2 |
| Mean wall time | 91s | 205s |

Removing the answer to the two traps did not cost the model the phase — it
cost it roughly 2.2x the turns and a 6/16 hang rate that was previously
zero. This is exactly the kind of signal D2 exists to capture: a chapter
here would report *this* incidence change, not a success-rate delta neither
report can distinguish from noise at n=16 (Rule 7). Whether this specific
delta is worth a Section 2 or Section 3 chapter — "what disappears when you
stop stating the answer to the trap" — is a call for whoever drafts Task 9's
prose, not decided here.
