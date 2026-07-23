# local-ai-pi Roadmap

The master design is [`specs/2026-07-23-course-design.md`](specs/2026-07-23-course-design.md).
Per-phase specs in `specs/` and plans in `plans/` are the source of truth for
*what* each phase does. This file is the cross-phase index: sequence, status, and
links. It is built the way the course teaches — each phase is evidence-gated, and
a later phase is not queued just because an earlier one landed.

**Current phase:** Sub-project 2 — Part III (SDD on Pi). This is unblocked
now that SP1's measurement harness and baseline exist. SP0 and SP1 are
complete.

## Phases

| ID | Phase | Status | Spec | Plan | Evidence |
|----|-------|--------|------|------|----------|
| SP0 | Scaffold + Part I (repo skeleton, docs toolchain, roadmap, LESSONS, example spec triple, hello-world extension) | **Done** | [course-design](specs/2026-07-23-course-design.md), [sp0-hello-agent](specs/2026-07-23-sp0-hello-agent-design.md) | [sp0-plan](plans/2026-07-23-sp0-hello-agent.md) | — |
| SP1 | Part II — Measurement (telemetry reader, minimal eval harness, evidence ledger, the smoking-gun baseline) | **Done** | [sp1-measurement-design](specs/2026-07-24-sp1-measurement-design.md) | [sp1-plan](plans/2026-07-24-sp1-measurement.md) | [baseline-phase-1](research/2026-07-23-baseline-phase-1.md) — 0/8 |
| SP2 | Part III — SDD on Pi (roadmap/packet method, subagent specialist; planner + fleet are evidence-gated, see backlog). Reframed around the *shipped* Pi subagent example — the course specializes it rather than rebuilding it. Guardrail inheritance is taught as a forward promise, demonstrated in SP3. | Queued (next) | — | — | — |
| SP3 | Part IV — Improvements catalog (orientation, tool restriction, output cap, path guard, repeat breaker, turn cap, model tuning, context budgeting) | Blocked on SP1 | — | — | — |

## Backlog (evidence-gated, not queued)

Items held to a recurrence bar or a trigger, not scheduled just because a
neighbor shipped:

- **Specialized subagent fleet beyond the orchestrator** (SP2). Each of
  planner / implementer / verifier is admitted only if a measured run shows it
  beats the simpler shape. Prior evidence (`LESSONS.md #4`) is *against* the hop;
  this course re-tests it.
- **Planner specialist + oracle derivation** (SP2). The reserved "galaxy-brain"
  role: a bigger-model, hybrid deterministic+model tool-agent that turns
  business/user-story phases into right-sized packets *and derives their
  acceptance oracles*. Oracle derivation is the risky part; the planner ships
  only if measured runs show its derived oracles hold. Hypothesis under test, not
  a scheduled deliverable.
- **Improvements whose motivating failure the baseline does not actually
  reproduce** (SP3). If Part II's baseline never triggers, say, the 48KB
  tool-output blowup on this model, the output-cap chapter is demoted to backlog
  with a note rather than taught as if the failure were live.
- **Investigate teaching how to wire `pi-lsp` into the setup** (candidate for
  SP3/SP4). Motivated by `LESSONS.md #5` (orient the model with structure, not
  repo-wide exploration) and `#4` (let an independent checker — LSP, type checker
  — establish whether an edit worked). An LSP gives structural orientation
  (symbols, imports, references) up front and a verification signal after, both
  named as high-value in the lessons but out of scope in the prior course.
  The candidate is the published package **`@spences10/pi-lsp`**
  (`pi install npm:@spences10/pi-lsp`, https://pi.dev/packages/@spences10/pi-lsp):
  a Pi **extension** that registers LSP-backed tools (diagnostics, hover,
  definitions, references, document symbols) and injects a small system-prompt
  reminder, covering `python-lsp-server` among others. Per its page it installs
  as a standard Pi package and **requires no fork** — so it sits inside the
  course's "built-in Pi only" constraint and is a real starting point rather than
  a research unknown. Open questions the investigation answers: does a Gemma-class
  SLM actually *use* the LSP tools when offered, or ignore them; is the
  orientation better delivered as tools the model must choose or as
  `before_agent_start` context injected deterministically (the "structure beats
  strings" tension from `LESSONS.md #1`); and does its Python path help the
  AgentClinic workload. Evidence-gated like every other improvement: taught only
  if a measured run shows it helps the SLM on the example workload. (Installing
  it is a normal package install for the reader; it does not touch the pinned
  global `pi` runtime.)

## Conventions

- Completed specs/plans move to `archive/{specs,plans}/`; the row here keeps the
  archived link.
- Every "this helps" claim links to a dated report in `research/`.
- Status vocabulary: Queued, In progress, Blocked on <ID>, Done, Backlog.
