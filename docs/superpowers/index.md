# Development record

Every feature cycle in this project produced a **design spec** (what we're
building and why) and an **implementation plan** (the task-by-task
decomposition). Both are committed rather than thrown away, so you can read
why the code looks the way it does — including the arguments that were
considered and rejected.

New here? Read [how we work](../sdd.md) first, then pick two or three of
these. Cycles 3, 6, and 9 are the most instructive: each one found a real
bug in the engine's own trustworthiness.

## Phase 1 — Reproduce AgentClinic Phase 1

Fourteen cycles, building a grading engine that can decide hermetically whether
a small local model succeeded at a real task. The order is deliberate:
cycles 3–7 build and prove the entire judging apparatus *before* a model
runs once, so that when a number finally arrives it measures the model
rather than the engine.

| # | Cycle | Spec | Plan |
|---|---|---|---|
| 1 | Accept/reject fixture pair | [spec](specs/2026-07-30-phase1-cycle1-fixture-pair-design.md) | [plan](plans/2026-07-30-phase1-cycle1-fixture-pair.md) |
| 2 | Workspace provisioning | [spec](specs/2026-07-30-phase1-cycle2-workspace-provisioning-design.md) | [plan](plans/2026-07-30-phase1-cycle2-workspace-provisioning.md) |
| 3 | Verdict from a hook-written results file | [spec](specs/2026-07-30-phase1-cycle3-verdict-file-design.md) | [plan](plans/2026-07-30-phase1-cycle3-verdict-file.md) |
| 4 | Subversion fixtures | [spec](specs/2026-07-30-phase1-cycle4-subversion-fixtures-design.md) | [plan](plans/2026-07-30-phase1-cycle4-subversion-fixtures.md) |
| 5 | Refusal of model-written config | [spec](specs/2026-07-30-phase1-cycle5-config-refusal-design.md) | [plan](plans/2026-07-30-phase1-cycle5-config-refusal.md) |
| 6 | AgentClinic task spec | [spec](specs/2026-07-30-phase1-cycle6-task-spec-design.md) | [plan](plans/2026-07-30-phase1-cycle6-task-spec.md) |
| 7 | Model-server liveness check | [spec](specs/2026-07-31-phase1-cycle7-liveness-check-design.md) | [plan](plans/2026-07-31-phase1-cycle7-liveness-check.md) |
| 8 | First real run | [spec](specs/2026-07-31-phase1-cycle8-first-real-run-design.md) | [plan](plans/2026-07-31-phase1-cycle8-first-real-run.md) |
| 9 | Source allowlist | [spec](specs/2026-07-31-phase1-cycle9-source-allowlist-design.md) | [plan](plans/2026-07-31-phase1-cycle9-source-allowlist.md) |
| 10 | Checkpoint recording | [spec](specs/2026-07-31-phase1-cycle10-checkpoint-recording-design.md) | [plan](plans/2026-07-31-phase1-cycle10-checkpoint-recording.md) |
| 11 | Corrective hardening | [spec](specs/2026-08-01-phase1-cycle11-corrective-hardening-design.md) | [plan](plans/2026-08-01-phase1-cycle11-corrective-hardening.md) |
| 12 | Hang tolerance | [spec](specs/2026-08-01-phase1-cycle12-hang-tolerance-design.md) | [plan](plans/2026-08-01-phase1-cycle12-hang-tolerance.md) |
| 13 | Batch contract | [spec](specs/2026-08-01-phase1-cycle13-batch-contract-design.md) | [plan](plans/2026-08-01-phase1-cycle13-batch-contract.md) |
| 14 | Sequential n=16 batch | [spec](specs/2026-08-01-phase1-cycle14-n16-batch-design.md) | [plan](plans/2026-08-01-phase1-cycle14-n16-batch.md) |

Phase 1 is complete. The supervised n=16 run accepted all 16 attempts; see
`ROADMAP.md` in this checkout for the Phase 2 backlog.

## Post-Phase 1 corrective closure

Three small corrections followed the completed Phase 1 feature sequence. They
preserve the 16/16 result, make future run acceptance stricter, retain a
compact evidence record, and keep local historical artifacts out of the new
repository.

| # | Cycle | Spec | Plan |
|---|---|---|---|
| 15 | Pi exit veto | [spec](specs/2026-08-01-post-phase1-pi-exit-veto-design.md) | [plan](plans/2026-08-01-post-phase1-pi-exit-veto.md) |
| 16 | n=16 batch evidence | [spec](specs/2026-08-01-post-phase1-batch-evidence-record-design.md) | [plan](plans/2026-08-01-post-phase1-batch-evidence-record.md) |
| 17 | Local workspace hygiene | [spec](specs/2026-08-01-post-phase1-local-workspace-hygiene-design.md) | [plan](plans/2026-08-01-post-phase1-local-workspace-hygiene.md) |
| 18 | Pages publication | [spec](specs/2026-08-01-post-phase1-pages-publication-design.md) | [plan](plans/2026-08-01-post-phase1-pages-publication.md) |

## Phase 2 — Measurement we can trust, cheaply enough to repeat

Phase 1 asked whether generated code can be trusted. Phase 2 asks what it
costs to measure that trustworthily and affordably — on hardware ranging
from the owner's Mac to a collaborator's much lower-powered machine, without
every question costing a supervised batch. Cycle 1 builds the instrument
and wires it to nothing — the same instrument-before-experiment order
Phase 1 used when it built the entire grading apparatus before a model ran
once.

*(An earlier framing named this phase "Measure the cost of orchestration"
and planned to build an orchestrator as its second and third steps. That
plan was withdrawn 2026-08-02 — see `ROADMAP.md`'s concept budget and "Now"
section for the full correction. The orchestration-cost claim that
motivated cycle 1's metric choices remains true and worth testing
eventually; building the orchestrator itself is deferred to the Backlog,
not scheduled within this phase.)*

| # | Cycle | Spec | Plan |
|---|---|---|---|
| 1 | Telemetry reader | [spec](specs/2026-08-02-phase2-cycle1-telemetry-reader-design.md) | [plan](plans/2026-08-02-phase2-cycle1-telemetry-reader.md) |

## Withdrawn

Designs that were approved and then withdrawn are kept, headed with a
banner explaining why. They're often more instructive than the ones that
shipped.

- [Cycle 14 — live-server suite execution](specs/2026-08-01-phase1-cycle14-live-server-execution-design.md)
  — approved, then withdrawn the same day when the owner challenged whether
  the threat it defended against was real. It wasn't. The research
  survives: notably, an empirical demonstration that running the model's
  app in a separate process does *not* close the forgery gap everyone
  assumed it would.

## Research

- [Cycle 1 fixture results](research/2026-07-30-phase1-cycle1-fixture-results.md)
- [Phase 1 n=16 batch evidence](research/2026-08-01-phase1-n16-batch-evidence.md)

```{toctree}
:hidden:
:maxdepth: 1
:caption: Specs

specs/2026-07-30-phase1-cycle1-fixture-pair-design
specs/2026-07-30-phase1-cycle2-workspace-provisioning-design
specs/2026-07-30-phase1-cycle3-verdict-file-design
specs/2026-07-30-phase1-cycle4-subversion-fixtures-design
specs/2026-07-30-phase1-cycle5-config-refusal-design
specs/2026-07-30-phase1-cycle6-task-spec-design
specs/2026-07-31-phase1-cycle7-liveness-check-design
specs/2026-07-31-phase1-cycle8-first-real-run-design
specs/2026-07-31-phase1-cycle9-source-allowlist-design
specs/2026-07-31-phase1-cycle10-checkpoint-recording-design
specs/2026-08-01-phase1-cycle11-corrective-hardening-design
specs/2026-08-01-phase1-cycle12-hang-tolerance-design
specs/2026-08-01-phase1-cycle13-batch-contract-design
specs/2026-08-01-phase1-cycle14-n16-batch-design
specs/2026-08-01-phase1-cycle14-live-server-execution-design
specs/2026-08-01-post-phase1-pi-exit-veto-design
specs/2026-08-01-post-phase1-batch-evidence-record-design
specs/2026-08-01-post-phase1-local-workspace-hygiene-design
specs/2026-08-01-post-phase1-pages-publication-design
specs/2026-08-02-phase2-cycle1-telemetry-reader-design
specs/2026-08-02-phase2-cycle2-precision-baseline-design
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Plans

plans/2026-07-30-phase1-cycle1-fixture-pair
plans/2026-07-30-phase1-cycle2-workspace-provisioning
plans/2026-07-30-phase1-cycle3-verdict-file
plans/2026-07-30-phase1-cycle4-subversion-fixtures
plans/2026-07-30-phase1-cycle5-config-refusal
plans/2026-07-30-phase1-cycle6-task-spec
plans/2026-07-31-phase1-cycle7-liveness-check
plans/2026-07-31-phase1-cycle8-first-real-run
plans/2026-07-31-phase1-cycle9-source-allowlist
plans/2026-07-31-phase1-cycle10-checkpoint-recording
plans/2026-08-01-phase1-cycle11-corrective-hardening
plans/2026-08-01-phase1-cycle12-hang-tolerance
plans/2026-08-01-phase1-cycle13-batch-contract
plans/2026-08-01-phase1-cycle14-n16-batch
plans/2026-08-01-post-phase1-pi-exit-veto
plans/2026-08-01-post-phase1-batch-evidence-record
plans/2026-08-01-post-phase1-local-workspace-hygiene
plans/2026-08-01-post-phase1-pages-publication
plans/2026-08-02-phase2-cycle1-telemetry-reader
plans/2026-08-02-phase2-cycle2-precision-baseline
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Research

research/2026-07-30-phase1-cycle1-fixture-results
research/2026-08-01-phase1-n16-batch-evidence
```
