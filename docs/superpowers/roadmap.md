# local-ai-pi Roadmap

The master design is [`specs/2026-07-23-course-design.md`](specs/2026-07-23-course-design.md).
Per-phase specs and plans are co-located in `docs/section-*/` directories.
This file is the cross-phase index: sequence, status, and links. It is built the way the course teaches — each phase is evidence-gated, and
a later phase is not queued just because an earlier one landed.

**Current phase:** Sub-project 3 — Part IV (Keeping the SLM on track). SP0, SP1,
and SP2 are complete. SP3 is unblocked — the SP2 baseline (4/8) is the
before-picture for every guardrail.

## Phases

| ID | Phase | Status | Spec | Plan | Evidence |
|----|-------|--------|------|------|----------|
| SP0 | Scaffold + Section I (repo skeleton, docs toolchain, roadmap, LESSONS, example spec triple, hello-world extension) | **Done** | [spec](../section-1-hello-agent/spec.md) | [plan](../section-1-hello-agent/plan.md) | — |
| SP1 | Section II — Measurement (telemetry reader, minimal eval harness, evidence ledger, the smoking-gun baseline) | **Done** | [spec](../section-2-measurement/spec.md) | [plan](../section-2-measurement/plan.md) | [0/8 baseline](../section-2-measurement/research/2026-07-23-baseline-phase-1.md) |
| SP2 | Section III — SDD on Pi (roadmap/packet method, parent-as-orchestrator + implementer specialist) | **Done** | [spec](../section-3-sdd/spec.md) | [plan](../section-3-sdd/plan.md) | [3/8 pre](../section-3-sdd/research/2026-07-24-sp2-baseline-phase-1.md), [5/8 post](../section-3-sdd/research/2026-07-24-sp2-baseline-phase-1-post-tuning.md), [deep-dive](../section-3-sdd/research/2026-07-24-sp2-deep-dive.md) |
| SP3 | Section IV — Keeping the SLM on track (orientation, tool restriction, output cap, path guard, repeat breaker, turn cap, model tuning, context budgeting) | Queued (next, unblocked by corrected SP2 baselines) | — | — | — |

## Backlog (evidence-gated, not queued)

Items held to a recurrence bar or a trigger, not scheduled just because a
neighbor shipped:

- **Harness telemetry improvements** (triggered by SP2 deep-dive, 2026-07-24).
  Five gaps identified in [`research/2026-07-24-sp2-deep-dive.md`](../section-3-sdd/research/2026-07-24-sp2-deep-dive.md):
  1. **Capture child session JSONL** — the highest-value gap. The parent JSONL
     shows the subagent tool call and its summary result, but the child's
     detailed event stream (every tool call, every message, full pytest output
     at each step) is not captured. Fix: run the child with `--session <path>` so
     pi writes its own JSONL, then parse it alongside the parent's.
  2. **Capture harness pytest output on failure** ✅ (fixed in SP2 cleanup,
     2026-07-24). `SessionResult` now stores `pytest_stdout` and `pytest_stderr`.
     Old fix text: store in `SessionResult` and include in the report.
  3. **Packet fidelity metric** — mechanically check whether the packet's
     acceptance strings and allowed-files list match the roadmap verbatim.
     Directly measures the spec's "handoff drift" commitment.
  4. **Validation command drift detection** — the implementer runs a narrower
     pytest (`tests/test_app.py`) than the packet specifies (`uv run pytest -q`).
     Parse the child's result for the exact command and flag disagreement.
  5. **Self-report vs harness verdict agreement** — compare the implementer's
     claimed pass/fail to the harness verdict, record disagreement as a metric.

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

- Specs and plans are co-located with section content in `docs/section-*/`.
- Every "this helps" claim links to a dated report in `research/`.
- Status vocabulary: Queued, In progress, Blocked on <ID>, Done, Backlog.
