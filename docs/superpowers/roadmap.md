# local-ai-pi Roadmap

The master design is [`specs/2026-07-23-course-design.md`](specs/2026-07-23-course-design.md).
Per-phase specs in `specs/` and plans in `plans/` are the source of truth for
*what* each phase does. This file is the cross-phase index: sequence, status, and
links. It is built the way the course teaches — each phase is evidence-gated, and
a later phase is not queued just because an earlier one landed.

**Next phase:** Sub-project 1 — Part II (Measurement). Brainstorm → spec → plan →
build. It is next because Parts III and IV cannot be evaluated without the harness
and baseline it produces.

## Phases

| ID | Phase | Status | Spec | Plan | Evidence |
|----|-------|--------|------|------|----------|
| SP0 | Scaffold + Part I (repo skeleton, docs toolchain, roadmap, LESSONS, example spec triple, hello-world extension) | **In progress** (handed off from brainstorming) | [course-design](specs/2026-07-23-course-design.md) | — | — |
| SP1 | Part II — Measurement (telemetry reader, minimal eval harness, evidence ledger, the smoking-gun baseline) | Queued (next) | — | — | — |
| SP2 | Part III — SDD on Pi (roadmap/packet method, orchestrator subagent; planner + fleet are evidence-gated, see backlog). Guardrail inheritance is taught as a forward promise, demonstrated in SP3. | Blocked on SP1 | — | — | — |
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
  First step is confirmation, not implementation: `pi-lsp` is **not** a package
  in the Pi checkout at `~/PycharmProjects/pi` — establish what it actually is
  (a real component? external? planned?) and whether it can be wired through a
  built-in Pi extension seam (e.g. a tool that shells to a language server, or
  `before_agent_start` orientation fed from LSP symbols) without violating the
  course's "built-in Pi only, no forks" constraint. If wiring it needs a runtime
  patch, it stays out of scope and the item records that finding. Evidence-gated
  like every other improvement: taught only if a measured run shows it helps the
  SLM on the example workload.

## Conventions

- Completed specs/plans move to `archive/{specs,plans}/`; the row here keeps the
  archived link.
- Every "this helps" claim links to a dated report in `research/`.
- Status vocabulary: Queued, In progress, Blocked on <ID>, Done, Backlog.
