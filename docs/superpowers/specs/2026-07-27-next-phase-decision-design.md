# Next-Phase Decision — Design

**Date:** 2026-07-27
**Status:** approved by project owner, pending write-up as an implementation plan
**Context:** Task 8's unsteered half is done (n=16 per phase, no ditch — see
[`plans/2026-07-24-grading-path-reboot.md`](../plans/2026-07-24-grading-path-reboot.md)
Task 8 addendum). This decides what happens next, resolving two threads that
surfaced in the same conversation but were not yet turned into a plan.

**Revision note (2026-07-27):** this design was reviewed adversarially by a
different model (Fable) per the spirit of evidence policy Rule 8 — Rule 8
itself only binds grading-path/acceptance-suite/measurement-code changes, and
this is a planning document, but the same discipline caught real defects here
too. Three findings were blocking and are folded in below: an unaddressed
spec/suite-contract mismatch, a skipped Rule 6 precondition, and a factual
misstatement about Task 9 that silently dropped two-thirds of its planned
Section 2 content. Two more sharpened the sequencing rationale and closed a
report-provenance gap. See the affected subsections for what changed.

## Decision 1 — Sequencing: spec rewrite before Section III

**The two candidate next actions:**

- **(A) Rewrite the phase-3 model-facing spec** to stop pre-defusing its own
  known traps — `examples/agentclinic/specs/roadmap.md` (Phase 3) currently
  tells the model to use `RedirectResponse` status 303 and test with
  `follow_redirects=False`, i.e. it states the answer to the two traps
  `lessons.md` #13 names. Re-run the unsteered n=16 baseline against the
  rewritten spec.
- **(B) Section III's cost-equivalence work** — pre-register a degradation
  budget (metric set + thresholds), then run the steered batches, per the
  disposition already recorded in
  [`plans/2026-07-24-oracle-repair.md`](../plans/2026-07-24-oracle-repair.md)
  Amendment 1's "triggered and dispositioned" note.

**Decision: (A) first, then (B). Not parallel.**

Rationale:

1. **(A) is cheap and reversible, with one hard precondition.** It reuses the
   harness Task 8 already validated and touches only the model-facing
   spec/prompt, not the acceptance suite — but the model-facing spec **is
   part of the workload** in evidence-policy terms, so Rule 6 applies:
   *"Any change to the workload... re-triggers this validation before the
   next published batch."* `tests/test_oracle.py` must be re-run (green)
   against the rewritten spec's reference solution before the new n=16 batch
   is trusted, even though nothing in `harness/` or the acceptance suite
   itself changes. This is a cheap check (the suite already exists and the
   Phase 3 reference solution already satisfies the contract — see rationale
   2 below for why that stays true) but it is not optional, and the original
   version of this doc omitted it.
2. **The rewrite removes the implementation hint, not the behavioral
   contract — and that distinction must hold or the batch is invalid.** The
   Phase 3 acceptance suite requires a 303 redirect with `Location:
   /complaints` and was deliberately built as "a `follow_redirects` trap
   detector" (grading-path reboot plan, Task 1). If the rewritten spec
   silently dropped the 303 **requirement** (not just the `RedirectResponse`
   class name and the `follow_redirects=False` testing instruction), a
   model returning a spec-compliant 200 re-render would fail acceptance
   against a contract its spec no longer stated — reproducing, inside this
   very project, the unstated-oracle-vs-workload mismatch the oracle-invalid
   incident exists to warn against. The implementation plan for (A) must
   preserve the 303 requirement as an explicit behavioral clause (e.g. "the
   POST redirects the browser to `GET /complaints` per the POST-redirect-GET
   pattern") while removing only the class name and the test-authoring hint.
   Because the contract is preserved, the acceptance suite itself does not
   change — no D3 re-authoring, no non-vacuity re-gating, no Rule 8 review
   is triggered by (A); only Rule 6's oracle-validation re-check (rationale
   1) is.
3. **(A) is upstream of (B)'s premise for Phase 3 specifically, not for the
   whole no-ditch result.** Section III's framing — "no improvement claim,
   only continuous-cost-equivalence, because the no-ditch contingency
   already fired" — rests on all three phases having no ditch. Only the
   Phase 3 spec pre-defuses its own traps (checked: Phases 1–2's spec
   sections carry no equivalent answer-leaking parenthetical). So (A) can at
   most reopen a Phase 3 ditch; Phases 1–2's 15/16 results are unaffected
   either way. That is enough to matter — Section III's "nothing left to
   improve on this workload" claim is about the workload as a whole, and a
   reopened Phase 3 ditch would falsify it — but the earlier draft's "no
   ditch found anywhere" framing over-stated which part of the premise is
   actually in question.
4. **Apparent independence (different files, no merge conflict) is not the
   same as independence of evidence.** Section III's degradation budget needs
   a stable definition of "solved" on the workload it tests against; that
   definition is exactly what (A) is testing for Phase 3.

**Report provenance.** The new batch's report must state, per Amendment 1's
existing "every report header states the starting state" requirement plus
one addition this design adds: which version of the Phase 3 spec produced
the reference solution and the batch (commit hash), and its explicit
relationship to the standing
[Phase 3 15/16 → 16/16 report](../../section-2-measurement/research/2026-07-27-post-repair-sp1-phase3.md)
— supersede it, or stand alongside it as a distinct workload variant. This
is not yet decided; it depends on the result (see "What this design does not
decide").

Section III's degradation-budget design is not blocked by this — it can be
drafted in parallel — but no steered batch runs until (A)'s result is in.
**Task 9's prose-writing is also sequenced after (A)'s result**, not only
after Section III's batches (see Decision 2's closing note) — Section 2's
planned "what the workload actually is" and Section 3's mechanism claims
would otherwise be written against a Phase 3 number that is still
provisional.

## Decision 2 — Course renumbering: Section 2 becomes suite-authoring

**Current structure** (per `docs/superpowers/roadmap.md`):

| Section | Content |
|---|---|
| I (SP0) | Scaffold + hello-world |
| II (SP1) | Measurement — telemetry reader, eval harness, evidence ledger |
| III (SP2) | SDD on Pi — orchestrator + implementer |
| IV (SP3) | Keeping the SLM on track — blocked on SPR |

Task 9 of the grading-path reboot plan already specifies a three-part arc for
Section 2: *validating the oracle · what the workload actually is · when
your metrics are fiction*. (An earlier version of this design incorrectly
stated Task 9 "had not yet decided what Section 2 teaches" and proposed a
Section 2 outline that silently dropped the latter two parts. That was a
factual error, caught on review — corrected below: all three parts are kept,
split across Sections 2 and 3 by subject matter rather than collapsed into
one.)

**New structure:**

| Section | Content |
|---|---|
| 1 | Scaffold + hello-world — **unchanged** |
| 2 | **How to Write an Eval Suite** — replaces the Measurement framing |
| 3 | Orchestrator + Implementer, Measured — **absorbs** the measurement apparatus |
| 4 | Keeping the SLM on track — **unchanged**, still blocked on SPR |

**Section 2 — How to Write an Eval Suite.** Two sub-arcs, both from Task 9's
original three, chosen because both concern *defining and grading the
contract* rather than watching a mechanism run:

- **What the workload actually is** (Task 9's second arc; D1/D2) — opens the
  section. A phase-N run is defined as starting from the seeded reference
  solution of phases 1..N−1, not empty (the lesson Amendment 1 recorded when
  "Phase 2: 0/8" turned out to mean "Phases 1+2 combined, from empty"); pooled
  decision thresholds (D2) as the rule for when a batch result is trustworthy.
  This comes first because suite-authoring only makes sense once the reader
  knows what a phase-N run is supposed to measure.
- **Suite-authoring** (Task 9's first arc; built from SPR Tasks 1–2 and the
  oracle-invalid incident):
  - Rule 3 (a passing smoke test is not a passing phase) as the opening claim.
  - D3 (the acceptance suite is harness-owned, human-authored, overlaid after
    the model finishes) — taught through the incident where authoring was
    delegated to a model anyway and discarded: the concrete demonstration
    that "a human reviews it after" converts the judgment call into a rubber
    stamp.
  - Non-vacuity gated in both directions (accepts a known-good solution,
    rejects a deliberately broken one) — the break matrix (isolated phase
    1/2/3 breaks) as the worked example.
  - D4 (the grader accepts no model-controlled input) — told through the two
    live defeats (`pytest.ini` + `--collect-only`, `os._exit(0)`) and why
    blacklisting an open category never closes it.
  - Rule 8 (adversarial review by a different model) as standing discipline
    for anything that grades models — the same discipline this design
    document was itself just put through.

**Section 3 — Orchestrator + Implementer, Measured.** Keeps the existing SP2
mechanism content (parent-as-orchestrator + implementer specialist,
packet/roadmap handoff) and absorbs two things Section 2 no longer owns:

- **The measurement apparatus** (telemetry reader, evidence ledger),
  interleaved with each mechanism claim (replace-vs-extend 8/8,
  cost-equivalence) rather than front-loaded as a standalone chapter — this
  mirrors D2 (failure-mode incidence is the primary metric, evidenced per
  claim, not in aggregate). This ordering is a recommendation, not
  load-bearing to the rest of this design.
- **"When your metrics are fiction"** (Task 9's third arc) — the catalog of
  fabricated metrics this project's own automation produced and its own
  agents cleared on self-review: a duration metric that always returned zero
  with a passing unit test pinning that as correct; evidence tiers stamped
  GREEN unconditionally; a status narrating "70–74 subagent calls" when the
  artifact recorded 1; an "Oracle validated" line that never ran the oracle
  (grading-path reboot plan, closing note). This belongs with Section 3, not
  Section 2, because it is specifically about whether the *report writer*
  watching the mechanism can be trusted — the same apparatus Section 3 now
  owns — not about the acceptance contract itself.

**Mechanical consequence.** SPR (the grading-path reboot) stops being a
standing "current phase" once Task 9 lands — its content becomes Sections 2
and 3. This simplifies Task 10's consolidation: one fewer phase for the
roadmap header to point at.

**Relationship to Decision 1.** The phase-3 spec rewrite (model-facing task
spec) and Section 2's suite-authoring content (acceptance suite,
D3-protected) are different artifacts on opposite sides of the D3 boundary —
no conflict, but Section 2's arc should note the adjacent lesson in one
line: both are instances of "a spec/oracle that leaks its own answer
measures nothing."

**Sequencing note.** Task 9's prose is not written until Decision 1's re-run
result is known (see Decision 1's closing paragraph) — both new sub-arcs in
Section 2 ("what the workload actually is," suite-authoring's worked
examples) and Section 3's mechanism claims would cite the Phase 3 number,
which is provisional until then.

## What this design does not decide

- **Section III's degradation-budget metric set and thresholds.** Deferred to
  its own design pass, gated on Decision 1's result.
- **The exact rewritten text of the phase-3 spec**, including the precise
  wording that preserves the 303 behavioral contract while removing the
  implementation hint. That's implementation, not design — covered in the
  follow-on implementation plan.
- **Whether Decision 1's spec rewrite reopens a Phase 3 ditch, and what
  happens if it does** — including whether the resulting report supersedes
  the standing 16/16 Phase 3 report or stands alongside it as a distinct
  workload variant. Genuinely unknown until the batch runs; the roadmap's own
  Amendment 1 already names the fallback for a reopened ditch (the
  higher-level user-story contingency stays open, not retired).

## Next step

Invoke `writing-plans` for the immediate actionable item: rewriting
`examples/agentclinic/specs/roadmap.md`'s Phase 3 section (preserving the 303
behavioral contract per Decision 1 rationale 2), re-validating the oracle
(Rule 6), and re-running the unsteered n=16 baseline. Decision 2
(renumbering) is recorded here for Task 9 to execute against later, sequenced
after this batch's result; it does not need its own implementation plan yet.
