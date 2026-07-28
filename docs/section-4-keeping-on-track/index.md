# Section IV — Keeping the SLM on Track

**Status: not yet written.** This page is a framing placeholder, not a chapter
catalog — read it as "here's what we know and what we're waiting on," not "here's
what Section IV teaches." Current status always lives in
[the roadmap](../superpowers/roadmap.md); this page will be rewritten once that
status changes.

## Why there's no chapter catalog yet

An earlier version of this page named four chapters (Terminal Validation, Path
Guard, Turn Cap, Repeat Breaker), each measured against a Section III baseline
of 5/8 (62%) success on Phase 1. That baseline no longer exists: a grading-path
rebuild found the acceptance oracle was accepting broken solutions, and under
the rebuilt, validated oracle the unsteered model clears Phases 1–3 at
15–16/16 — see the roadmap's "Consequences" note. The four chapters' motivating
failures don't reproduce against the current baseline, so they're retired, not
rewritten in place. Building them anyway would mean teaching guardrails against
a ditch that no longer exists.

Their original design docs (`terminal-validation/spec.md`,
`terminal-validation/plan.md`) are left in the repo as historical record but
pulled from this page's navigation — they describe a chapter that isn't being
built as specified.

## What we're waiting on before deciding a new catalog

Two preconditions, neither satisfied yet:

1. **Section III's final baseline.** Section III's cost-equivalence batches
   (does the orchestrator+implementer mechanism cost materially more than
   unsteered, without dropping below the current solved line) are running now
   — see the roadmap for progress. Until that's in, there's no settled
   "current mechanism" to build Section IV's guardrails on top of.
2. **The mechanism to develop against.** Section IV's guardrails need to sit
   somewhere structurally — on the bare unsteered flow, on the Section III
   orchestrator+implementer flow, or both. Which one (or both) isn't decidable
   until Section III's shape is final, since a guardrail built against the
   wrong base is a guardrail that has to be rebuilt.

Until both land, nothing below should be read as decided.

## Candidate subject (evidence-backed, not yet a chapter plan)

Section II's current, valid, n=16 unsteered data shows two failure modes still
live, independent of Section III's outcome:

- **Speed/reliability.** Hang incidence and turn count are real — e.g. the
  rewritten Phase 3 spec: 6/16 runs (37.5%) hit the timeout, mean turns
  10.8→24.2 from a spec-wording change alone. The model finishes, but it
  thrashes.
- **Preservation breakage (replace-vs-extend).** Destructive rewrites of
  shared/inherited files at a real rate even while acceptance still passes —
  e.g. Phase 2: replace=5/16, Phase 3: replace=4–6/16 depending on spec
  variant. A run can pass the contract while silently damaging prior work.

These are named here as the leading candidates for what Section IV ends up
about, backed by evidence that already exists and doesn't depend on Section
III. But per the precondition above, no mechanism, chapter, or measurement
plan is committed against them yet — that requires the new orchestrator
machinery Section III is establishing to actually surface these issues live,
not just cite the raw counts. Treat this section as "what we'd start from,"
not "what we'll build."

## Reference material, not a plan

Several mechanisms (output cap, path guard, repeat breaker, turn cap) were
previously designed and implemented in a reference repo (`local-ai-gemma`,
branch `slm-guardrails`, 75 passing tests). That work remains available as raw
material — design decisions, adversarial-review findings, live-verification
evidence — but it targeted the retired catalog above, and nothing about it is
assumed to carry forward. Whatever Section IV becomes should be evaluated
against the current evidence, not backfilled from what was built once before.

The method that governed the retired catalog is still expected to govern
whatever replaces it: show the failure with recorded telemetry, apply one Pi
mechanism, measure whether it helped, record evidence in a dated report. No
technique adopted on faith. That much doesn't need to be redecided — only the
subject and the mechanism do.
