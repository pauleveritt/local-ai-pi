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

**One correction, added 2026-08-02.** Cycle 2 is titled *workspace
provisioning* and cycle 11 *corrective hardening*, and it is easy to read
those as having provisioned the model a working environment. They did not.
Cycle 2 provisioned a disposable **git repository**; cycle 11's controlled
environment covers the *pytest grading child* only, while `runner.py` passes
`env=None`, so Pi inherits whatever ambient environment it was launched in.
The model's own working conditions were never in any Phase 1 cycle's scope —
and Phase 2 cycle 3 found that this cost ~95% of the measured variance in
turn count, and that the cleanest-looking runs were the ones that skipped
testing. If you are copying this pattern, provision the environment too, or
state it in the task. See
[Phase 2, cycle 3 — clean baseline](research/2026-08-02-phase2-cycle3-clean-baseline.md).

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

Phase 1 asked whether generated code can be trusted. Phase 2 asked what it
costs to measure that trustworthily — on hardware ranging from the owner's
Mac to a collaborator's much lower-powered machine, without every question
costing a supervised batch. Cycle 1 builds the instrument and wires it to
nothing, the same instrument-before-experiment order Phase 1 used when it
built the entire grading apparatus before a model ran once.

**Four cycles, and the most instructive thing they found was about
themselves.** Cycle 2 characterized the instrument's precision against 48
real runs. Cycle 3 then discovered what that instrument had been measuring:
the variance was ~95% environment friction, and every run that showed no
friction had avoided it by never running a test. Cycle 4 responded to a
different problem the same session exposed — six wrong numbers in published
prose, none reachable by any test — with four checks and one gate. Phase 2
is complete; see `ROADMAP.md` for why its original affordability target was
retired rather than met.

*(An earlier framing named this phase "Measure the cost of orchestration"
and planned to build an orchestrator as its second and third steps. That
plan was withdrawn 2026-08-02 — see `ROADMAP.md`'s concept budget and "Now"
section for the full correction. The orchestration-cost claim that
motivated cycle 1's metric choices remains true and worth testing
eventually; building the orchestrator itself is deferred to the Backlog,
not scheduled within this phase.)*

*("Eventually" arrived on 2026-08-04: the claim is scheduled as **Phase 5**,
which is named for it. This paragraph stays as written because it records
what Phase 2 decided and why, and that decision was right for Phase 2. Only
the last clause has gone out of date — the orchestrator is no longer sitting
in the Backlog.)*

| # | Cycle | Spec | Plan |
|---|---|---|---|
| 1 | Telemetry reader | [spec](specs/2026-08-02-phase2-cycle1-telemetry-reader-design.md) | [plan](plans/2026-08-02-phase2-cycle1-telemetry-reader.md) |
| 2 | Precision baseline | [spec](specs/2026-08-02-phase2-cycle2-precision-baseline-design.md) | [plan](plans/2026-08-02-phase2-cycle2-precision-baseline.md) |
| 3 | Honest environment, clean baseline | [spec](specs/2026-08-02-phase2-cycle3-honest-environment-design.md) | [plan](plans/2026-08-02-phase2-cycle3-honest-environment.md) |
| 4 | Claim discipline | [spec](specs/2026-08-02-phase2-cycle4-claim-discipline-design.md) | [plan](plans/2026-08-02-phase2-cycle4-claim-discipline.md) |

## Withdrawn

Designs that were approved and then withdrawn are kept, headed with a
banner explaining why. They're often more instructive than the ones that
shipped.

- [Phase 3, cycle 2 — specialized subagent](specs/2026-08-03-phase3-cycle2-specialized-subagent-design.md)
  — approved and withdrawn the same day, when the owner challenged whether
  Phase 3 should be getting into orchestration. It should not have been, and
  the roadmap had already said so in a Backlog entry nobody reconciled it
  against. The research survives: how Pi spawns a subagent child, what that
  child does and does not inherit, and the environment lever that isolates
  it.

- [Cycle 14 — live-server suite execution](specs/2026-08-01-phase1-cycle14-live-server-execution-design.md)
  — approved, then withdrawn the same day when the owner challenged whether
  the threat it defended against was real. It wasn't. The research
  survives: notably, an empirical demonstration that running the model's
  app in a separate process does *not* close the forgery gap everyone
  assumed it would.

## Chapters

Teaching material, written for contributors rather than as a record of a
cycle's argument.

- [Hello, agent](chapters/hello-agent.md) — what a Pi extension is, the
  lifecycle the project's own extension tours, and why *where* you emit
  decides whether anything hears it.

- [Extension mechanics](chapters/pi-extension-mechanics.md) — how Pi finds an
  extension, how `registerTool` works taught from a twenty-line example you can
  run, and Pi's own shipped subagent extension read as a worked example rather
  than adopted.

## Research

- [Cycle 1 fixture results](research/2026-07-30-phase1-cycle1-fixture-results.md)
- [Phase 1 n=16 batch evidence](research/2026-08-01-phase1-n16-batch-evidence.md)
- [Phase 2 cycle 2 — precision baseline](research/2026-08-02-phase2-cycle2-precision-baseline.md)
- [Phase 2 cycle 3 — clean baseline](research/2026-08-02-phase2-cycle3-clean-baseline.md)
- [Phase 2 — plan for the remainder](research/2026-08-02-phase2-remaining-plan.md)
- [Phase 3, cycle 1 — the event vocabulary](research/2026-08-02-phase3-cycle1-event-vocabulary.md)
  — what an extension can and cannot emit under
  `--print --mode json --no-session --no-themes`, and the corrected cause of
  48 inert runs.
- [Phase 3, cycle 2 — the Pi gotchas record](research/2026-08-03-phase3-cycle2-pi-gotchas.md)
  — ten findings this project paid to discover, each with a checked citation
  into the installed package, each labelled **read** or **run**, and each with
  what it cost.
- [Phase 5, cycle 1 — what one live delegation showed](research/2026-08-04-phase5-cycle1-delegation-spike.md)
  — `--extension` needs the entry-point file, not the extension's
  directory; pointed at the directory it fails silently and the run still
  grades accepted.
- [Phase 4, cycle 1 — what the second suite cost](research/2026-08-04-phase4-cycle1-what-the-second-suite-cost.md)
  — every `harness/` change a second workload forced, labelled *seam
  extraction* or *genuine gap*; what was already general; and what is still
  not.

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
specs/2026-08-02-phase2-cycle3-honest-environment-design
specs/2026-08-02-phase2-cycle4-claim-discipline-design
specs/2026-08-02-phase3-cycle1-observable-extension-design
specs/2026-08-03-phase3-cycle2-specialized-subagent-design
specs/2026-08-03-phase3-cycle2-extension-mechanics-design
specs/2026-08-03-pi-version-pin-design
specs/2026-08-04-phase4-cycle1-second-suite-design
specs/2026-08-04-phase5-cycle1-improvement-mechanism-design
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
plans/2026-08-02-phase2-cycle3-honest-environment
plans/2026-08-02-phase2-cycle4-claim-discipline
plans/2026-08-02-phase3-cycle1-observable-extension
plans/2026-08-03-phase3-cycle2-specialized-subagent
plans/2026-08-03-phase3-cycle2-extension-mechanics
plans/2026-08-03-pi-version-pin
plans/2026-08-04-phase4-cycle1-second-suite
plans/2026-08-04-phase5-cycle1-improvement-mechanism
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Chapters

chapters/hello-agent
chapters/pi-extension-mechanics
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Research

research/2026-07-30-phase1-cycle1-fixture-results
research/2026-08-01-phase1-n16-batch-evidence
research/2026-08-02-phase2-cycle2-precision-baseline
research/2026-08-02-phase2-cycle3-clean-baseline
research/2026-08-02-phase2-remaining-plan
research/2026-08-02-phase3-cycle1-event-vocabulary
research/2026-08-03-phase3-cycle2-pi-gotchas
research/2026-08-04-phase4-cycle1-what-the-second-suite-cost
research/2026-08-04-phase5-cycle1-delegation-spike
```
