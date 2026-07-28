# Section III Cost-Equivalence — Pre-Registered Metrics and Degradation Budget

**Date:** 2026-07-28
**Status:** approved by the project owner, 2026-07-28 — metric set, data
sources, and the 3x-turns / +2-hangs degradation thresholds are all locked.
Pre-registration is closed; no threshold in this document may change after a
steered batch has been seen, per the point of pre-registering at all.
**Context:** [`plans/2026-07-24-oracle-repair.md`](../plans/2026-07-24-oracle-repair.md)
Amendment 1 decision 4 (dispositioned 2026-07-27) commits Section III to a
single empirical claim — **continuous-cost equivalence**: does adopting the
orchestrator+implementer mechanism cost materially more (turns, packet/token
size; wall time is context only) without degrading below Amendment 2's solved
line. This document fixes what that means in numbers, *before* any steered
batch runs — per the same discipline the roadmap's banner already states
("so the claim can't be set after seeing the data").

**Precondition satisfied:** this pre-registration was gated on
[Decision 1](2026-07-27-next-phase-decision-design.md)'s Phase 3 spec-rewrite
result. That result is in — 16/16, corroborating, no ditch reopened
(`evidence: post-repair phase-3 baseline, rewritten spec (n=16)`,
[report](../../section-2-measurement/research/2026-07-28-post-repair-sp1-phase3-less-prescriptive-spec.md)) —
so this document proceeds against the **rewritten** Phase 3 spec, since that
is the spec Section III's steered batches will actually run against.

## Why success-rate delta is not the metric (Rule 7)

Evidence policy Rule 7 forbids any chapter claiming a success-rate delta —
detecting a realistic effect needs ~100 runs/arm, which this project cannot
afford. Section III's claim is explicitly *not* "the mechanism improves
success" (Amendment 1 decision 4: "there is nothing left to improve on this
workload"). It is a **floor check** (did the mechanism make things worse) plus
a **cost comparison** (does the mechanism cost more turns/tokens for the same
outcome) — categorically different claim shapes, each with its own rule.

## Metric set

| # | Metric | Data source | Claim shape (Rule 7) |
|---|--------|--------------|----------------------|
| 1 | **Solved-line floor** | `SessionResult` success bit, aggregated per phase | Gate, not a claim — binary pass/fail against a pre-registered floor |
| 2 | **Turns (parent)** | `RunTelemetry.turns` (`harness/telemetry.py`, already implemented) | YELLOW context, reported with noise caveat (Rule 4) — not a pass/fail claim by itself |
| 3 | **Hang incidence** | `outcome == "exited-with-hang"` (already recorded in every SP1/SPR report table) | Behavioral-incidence change — Rule 7's countable-per-run-signal category |
| 4 | **Packet size (bytes)** | `SubagentStats.packet_size_total` / `invocations` (`harness/telemetry.py::subagent_stats_from`, already implemented) | Absolute number, reported against the shipped 50KB per-task result cap (SP2 spec) as a structural-risk check, not a delta (no unsteered equivalent exists) |
| 5 | **Wall time** | subprocess timing | Context only, never a claim — per the Fable review of the Task 8 results, already stated in Amendment 1 decision 4 |

Token counts (input/cache) are **not** in this metric set. `harness/telemetry.py`'s
own header documents that `--mode json` carries no token-usage data; that path
is `get_session_stats` over `--mode rpc`, explicitly deferred, and picking it
up is not a precondition for this pre-registration — packet size in bytes is
the load-bearing proxy Amendment 1 already named ("turns, packet/**token**
size" is written loosely; the only size figure the harness actually produces
today is packet bytes).

## Pre-registered unsteered baselines (GREEN, artifact-backed)

The comparison arm for every steered batch. All three come from the
rebuilt grading path, n=16, using the spec Section III will actually dispatch
(rewritten Phase 3):

| Phase | Report | n | Success | Mean turns | Hang incidence |
|-------|--------|---|---------|-----------|-----------------|
| 1 | [2026-07-27](../../section-2-measurement/research/2026-07-27-post-repair-sp1-phase1.md) | 16 | 15/16 | 12.8 | 0/16 post-fix* |
| 2 | [2026-07-27](../../section-2-measurement/research/2026-07-27-post-repair-sp1-phase2.md) | 16 | 15/16 | 8.6 | 0/16 |
| 3 (rewritten spec) | [2026-07-28](../../section-2-measurement/research/2026-07-28-post-repair-sp1-phase3-less-prescriptive-spec.md) | 16 | 16/16 | 24.2 | 6/16 |

\* Phase 1's report recorded 2/16 hangs, but flags them explicitly as an
artifact of a harness bug fixed mid-batch (`1883a9c`, the process-group kill
fix), not model behavior — the report's own header excludes those two runs
from the citable numbers. Treated here as 0/16 clean.

**Note the natural variance already in this table**: Phase 3's mean turns
moved 10.8→24.2 (2.2x) and hang incidence moved 0/16→6/16 from a
*spec-wording change alone*, no steering involved. Any degradation budget
that doesn't sit comfortably above that swing would flag workload noise as a
mechanism cost.

## Degradation budget (decision rule, pre-registered)

A steered batch (orchestrator + implementer, n=16 per phase) is compared to
its matching unsteered baseline above. Two independent gates — either one
tripping is reported as a real degradation, not averaged away:

1. **Solved-line floor.** Per Amendment 2's revised threshold (n=16), a phase
   is "solved" at ≥15/16. If a steered phase batch scores below 15/16 while
   its unsteered baseline is ≥15/16, that is a degradation: the mechanism
   made a solved phase unsolved. Report plainly and stop — do not proceed to
   the next phase's steered batch on the assumption the mechanism is safe,
   mirroring how Decision 1 treated a reopened ditch as a stop-and-report
   condition returning to the project owner, not a thing to unilaterally
   route around.
2. **Cost budget.** Either sub-condition is a material-cost flag:
   - **Turns:** steered mean turns exceeds **3x** the matching unsteered
     mean turns. (Recommendation, see "Open decision" — chosen to sit clearly
     above the 2.2x swing already observed from spec wording alone at n=16,
     so the bar isn't tripped by ordinary workload noise.)
   - **Hang incidence:** steered hang count exceeds the unsteered baseline's
     hang count by more than 2 runs at n=16 (a countable, Rule-7-compliant
     behavioral-incidence signal — e.g. Phase 2's 0/16 baseline would flag at
     steered ≥3/16; Phase 3's 6/16 baseline would flag at steered ≥9/16).

Turns and hang incidence are each reported as YELLOW (n=16, single-model,
single-provider) per Rule 4, with the raw numbers shown — the budget is a
pre-registered trigger for calling out "this is materially more," not a
license to hide the raw comparison.

Packet size is reported per delegation (mean bytes, min/max) against the
shipped 50KB cap as a structural ceiling check — flagged only if any single
packet approaches that cap, not compared against an unsteered number that
doesn't exist.

## Decision (approved 2026-07-28)

The **3x-turns / +2-hangs** thresholds above are approved by the project
owner as pre-registered, before any steered batch has run. They were derived
from the observed baseline variance (the 2.2x, 0→6 swing seen from a
spec-wording change alone) rather than handed down from an existing project
decision the way Amendment 2's 15/16 floor was — recorded here for the same
reason Amendment 1, Amendment 2, and Decision 1 each record who decided and
when.

## What this does not decide

- **Whether to add child-turn telemetry** (the child's turn count inside a
  delegation, distinct from the parent's turn count). Listed as a metric in
  the SP2 spec's "Additional metrics" but not implemented in
  `harness/telemetry.py` today — same backlog gap as "capture child session
  JSONL" (roadmap backlog, gap 1). Not a precondition for this pre-registration:
  parent turns and packet size are sufficient to evaluate the two degradation
  gates above.
- **Token-count telemetry** (the `--mode rpc` / `get_session_stats` path).
  Explicitly out of scope here — see "Metric set" above.
- **The actual steered batch runs.** This document only fixes what will be
  measured and the decision rule for interpreting it; running the batches is
  the next step once this is confirmed.
