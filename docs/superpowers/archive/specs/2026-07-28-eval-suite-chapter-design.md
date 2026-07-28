# "How to Write an Eval Suite" Chapter — Design

**Date:** 2026-07-28
**Status:** approved by project owner, pending write-up as an implementation plan
**Context:** extends Decision 2 of
[`docs/superpowers/specs/2026-07-27-next-phase-decision-design.md`](2026-07-27-next-phase-decision-design.md),
which renamed Section 2 to "How to Write an Eval Suite" but left its
suite-authoring sub-arc built entirely from retrospective artifacts (the
grading-path reboot's own Task 1–2 history, the oracle-invalid incident).
This design adds a concrete, hands-on case study to that sub-arc, surfaced
in conversation the same day as this document's date.

## What this adds

A new higher-level, business/user-story version of the AgentClinic roadmap,
targeting the identical app the existing detailed roadmap targets — per the
master spec's own framing
([`docs/superpowers/specs/2026-07-23-course-design.md`](../../specs/2026-07-23-course-design.md),
line 38-41): "the shift from detailed to higher-level framing is itself a
late-course subject, not a change of workload." The master spec named
oracle-derivation-from-a-vague-story as Part III's "central open question,"
previously assigned to an evidence-gated "planner" specialist that was never
built (line 226). This chapter resolves a disciplined version of that same
question by hand, as a teaching exercise, rather than waiting on that
specialist.

## Scope, deliberately kept small

Three explicit scope decisions, made in conversation before this doc was
written, each trading a larger, more "complete" version of this feature for
a smaller one:

1. **Add alongside, not replace.** `examples/agentclinic/specs/roadmap.md`
   (the existing detailed spec) is untouched — it's the evidence chain's
   baseline; every existing report cites it. The new file is
   `examples/agentclinic/specs/roadmap-user-story.md`, a second variant of
   the same three phases, phrased at business/user-story level instead of
   implementation-level instructions.
2. **No new phase, no new failure-mode engineering.** An earlier version of
   this design considered a new Phase 4 purpose-built to exercise
   preservation breakage and false self-report (both flagged thin/
   underpowered in the evidence policy's evidence triage). That was dropped
   in favor of a smaller step: rewrite Phases 1–3 to be functionally
   equivalent to the existing app, just less prescriptive. "This by itself
   will be an improvement" — the reframing is the whole exercise.
3. **No new acceptance suite, no new reference solution, no new batch.**
   Because the end app is functionally identical, the existing cumulative
   phase-3 suite (`examples/acceptance/phase-3/test_acceptance.py`) and the
   existing reference solutions already grade `roadmap-user-story.md`
   correctly. Nothing is authored, nothing is re-gated, and — because
   nothing measures anything in this pass — **no Rule 8 review applies
   here** (mirrors the phase-3 spec rewrite's own precedent: touching only
   the model-facing spec, not measurement code).

## What the chapter actually teaches

The chapter narrates deriving the acceptance contract from the higher-level
story — walking through the judgment calls a vaguer spec forces (what does
"agents can register a complaint" actually require observably?) — and then
reveals the suite that already exists, showing it matches. The point being
made: a vaguer spec doesn't change what's graded, it changes how much
judgment deriving the grade takes. This is D3's own discipline
("the acceptance suite is harness-owned and human-authored... because it is
what grades models") demonstrated by exercise rather than only stated as a
rule.

## Rule 6, deferred not skipped

Creating `roadmap-user-story.md` is, in evidence-policy terms, introducing a
new workload variant — but Rule 6 ("any change to the workload... re-
triggers oracle validation before the next published batch") binds
*batches*, and this pass runs none. **This is explicitly flagged, not
silently skipped:** whoever later runs a measured batch against
`roadmap-user-story.md` (see "Forward link" below) owns re-running
`tests/test_oracle.py` before trusting that batch, exactly as Decision 1 of
the prior design required for the phase-3 rewrite.

## Forward link to Section 3 (named, not built here)

`roadmap-user-story.md` becomes Section 3's packet source for a later
orchestrator+implementer measurement — a new evaluation axis (how the
mechanism performs with less precise hand-holding) alongside the
already-planned cost-equivalence work from Decision 1 of the prior design
doc. That measurement is out of scope for this document; this is the wiring
that makes it possible later, not the batch itself.

## The scheduled task

Per the project owner's explicit request: this needs to be a **scheduled**
task, not just a design left implicit in a spec file. Two edits, made
alongside this document:

1. [`docs/superpowers/plans/2026-07-24-grading-path-reboot.md`](../../plans/2026-07-24-grading-path-reboot.md)
   Task 9's Section 2 description now names this chapter and its case study
   explicitly, alongside the pre-existing three-arc description.
2. [`docs/superpowers/roadmap.md`](../../roadmap.md)'s "Next action" banner now
   names this chapter in its "what proceeds now" paragraph, so it's visible
   without opening the plan — matching the project's own convention that the
   roadmap header is where a fresh reader reaches every live constraint.

## What this design does not decide

- **The exact wording of `roadmap-user-story.md`.** That's implementation,
  covered in the follow-on implementation plan.
- **Whether Section 3's later measurement against this roadmap reopens any
  ditch, or what the degradation-budget metric set looks like for that
  comparison.** Both remain the open items named in the prior design doc's
  "What this design does not decide," untouched by this one.
