# Next-Phase Decision — Design

**Date:** 2026-07-27
**Status:** approved by project owner, pending write-up as an implementation plan
**Context:** Task 8's unsteered half is done (n=16 per phase, no ditch — see
[`plans/2026-07-24-grading-path-reboot.md`](../plans/2026-07-24-grading-path-reboot.md)
Task 8 addendum). This decides what happens next, resolving two threads that
surfaced in the same conversation but were not yet turned into a plan.

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

1. **(A) is cheap and reversible.** It reuses the harness Task 8 already
   validated, touches only the model-facing spec/prompt (not the acceptance
   suite, not grading-path or measurement code), so it needs no Rule 8 review.
   Rewrite → re-run n=16 → read the result is a same-day loop.
2. **(A) is upstream of (B)'s premise, not independent of it.** Section III's
   framing — "no improvement claim, only continuous-cost-equivalence, because
   the no-ditch contingency already fired" — depends on "no ditch" holding.
   The current phase-3 spec hands the model the answer to its own traps, which
   is a plausible explanation for why n=16 found no ditch. If the rewrite
   reopens a ditch, that changes what Section III would be measuring against,
   and would itself re-examine Amendment 1 decision 4 (the pre-registered
   move to the higher-level user-story roadmap).
3. **Apparent independence (different files, no merge conflict) is not the
   same as independence of evidence.** Section III's degradation budget needs
   a stable definition of "solved" on the workload it tests against; that
   definition is exactly what (A) is testing.

Section III's degradation-budget design is not blocked by this — it can be
drafted in parallel — but no steered batch runs until (A)'s result is in.

## Decision 2 — Course renumbering: Section 2 becomes suite-authoring

**Current structure** (per `docs/superpowers/roadmap.md`):

| Section | Content |
|---|---|
| I (SP0) | Scaffold + hello-world |
| II (SP1) | Measurement — telemetry reader, eval harness, evidence ledger |
| III (SP2) | SDD on Pi — orchestrator + implementer |
| IV (SP3) | Keeping the SLM on track — blocked on SPR |

Task 9 of the grading-path reboot plan already commits to rewriting Sections
2–4 from scratch against the reframe and final numbers, but had not yet
decided *what Section 2 teaches*.

**New structure:**

| Section | Content |
|---|---|
| 1 | Scaffold + hello-world — **unchanged** |
| 2 | **How to Write an Eval Suite** — replaces the Measurement framing |
| 3 | Orchestrator + Implementer, Measured — **absorbs** the measurement apparatus |
| 4 | Keeping the SLM on track — **unchanged**, still blocked on SPR |

**Section 2 — How to Write an Eval Suite.** Built from the grading-path
reboot's own history (SPR Tasks 1–2 and the oracle-invalid incident), not
invented content:

- Rule 3 (a passing smoke test is not a passing phase) as the opening claim.
- D3 (the acceptance suite is harness-owned, human-authored, overlaid after
  the model finishes) — taught through the incident where authoring was
  delegated to a model anyway and discarded: the concrete demonstration that
  "a human reviews it after" converts the judgment call into a rubber stamp.
- Non-vacuity gated in both directions (accepts a known-good solution, rejects
  a deliberately broken one) — the break matrix (isolated phase 1/2/3 breaks)
  as the worked example.
- D4 (the grader accepts no model-controlled input) — told through the two
  live defeats (`pytest.ini` + `--collect-only`, `os._exit(0)`) and why
  blacklisting an open category never closes it.
- Rule 8 (adversarial review by a different model) as standing discipline for
  anything that grades models.

**Section 3 — Orchestrator + Implementer, Measured.** Keeps the existing SP2
mechanism content (parent-as-orchestrator + implementer specialist,
packet/roadmap handoff) and absorbs the measurement apparatus (telemetry
reader, evidence ledger) that Section 2 no longer owns. Measurement is
interleaved with each mechanism claim (replace-vs-extend 8/8, cost-
equivalence) rather than front-loaded as a standalone chapter — this mirrors
D2 (failure-mode incidence is the primary metric, evidenced per claim, not
in aggregate). This ordering is a recommendation, not load-bearing to the
rest of this design; it can be revisited when Task 9 is actually drafted
without touching Decision 1 or the section boundaries above.

**Mechanical consequence.** SPR (the grading-path reboot) stops being a
standing "current phase" once Task 9 lands — its content becomes Section 2.
This simplifies Task 10's consolidation: one fewer phase for the roadmap
header to point at.

**Relationship to Decision 1.** The phase-3 spec rewrite (model-facing task
spec) and Section 2's suite-authoring content (acceptance suite, D3-protected)
are different artifacts on opposite sides of the D3 boundary — no conflict,
but Section 2's arc should note the adjacent lesson in one line: both are
instances of "a spec/oracle that leaks its own answer measures nothing."

## What this design does not decide

- **Section III's degradation-budget metric set and thresholds.** Deferred to
  its own design pass, gated on Decision 1's result.
- **The exact rewritten text of the phase-3 spec.** That's implementation,
  not design — covered in the follow-on implementation plan.
- **Whether Decision 1's spec rewrite reopens a ditch, and what happens if it
  does.** Genuinely unknown until the batch runs; the roadmap's own Amendment
  1 already names the fallback (the contingency stays open, not retired).

## Next step

Invoke `writing-plans` for the immediate actionable item: rewriting
`examples/agentclinic/specs/roadmap.md`'s Phase 3 section and re-running the
unsteered n=16 baseline. Decision 2 (renumbering) is recorded here for Task 9
to execute against later; it does not need its own implementation plan yet.
