# local-ai-pi Roadmap

The master design is [`specs/2026-07-23-course-design.md`](specs/2026-07-23-course-design.md).
Per-phase specs and plans are co-located in `docs/section-*/` directories.
This file is the cross-phase index: sequence, status, and links. It is built the way the course teaches — each phase is evidence-gated, and
a later phase is not queued just because an earlier one landed.

**Current phase:** Sub-project 3 — Part IV (Keeping the SLM on track). SP0, SP1,
and SP2 are complete. SP3 is unblocked — the SP2 baseline (5/8) is the
before-picture for every guardrail.

## Phases

| ID | Phase | Status | Spec | Plan | Evidence |
|----|-------|--------|------|------|----------|
| SP0 | Scaffold + Section I (repo skeleton, docs toolchain, roadmap, LESSONS, example spec triple, hello-world extension) | **Done** | [spec](../section-1-hello-agent/spec.md) | [plan](../section-1-hello-agent/plan.md) | — |
| SP1 | Section II — Measurement (telemetry reader, minimal eval harness, evidence ledger, the smoking-gun baseline) | **Done** | [spec](../section-2-measurement/spec.md) | [plan](../section-2-measurement/plan.md) | [0/8 baseline](../section-2-measurement/research/2026-07-23-baseline-phase-1.md) |
| SP2 | Section III — SDD on Pi (roadmap/packet method, parent-as-orchestrator + implementer specialist) | **Done** | [spec](../section-3-sdd/spec.md) | [plan](../section-3-sdd/plan.md) | [3/8 pre](../section-3-sdd/research/2026-07-24-sp2-baseline-phase-1.md), [5/8 post](../section-3-sdd/research/2026-07-24-sp2-baseline-phase-1-post-tuning.md), [deep-dive](../section-3-sdd/research/2026-07-24-sp2-deep-dive.md) |
| SP3 | Section IV — Keeping the SLM on track (orientation, tool restriction, output cap, path guard, repeat breaker, turn cap, model tuning, context budgeting) | Queued (next, unblocked by corrected SP2 baselines) | — | — | — |


## Narrative reframe (adopted 2026-07-24)

The course's original hook — "an unsteered SLM goes 0/8; here is the ditch" —
is dead. That 0/8 was an oracle artifact (see the oracle-invalid incident), and
under a valid oracle the model clears seeded Phase 1 and Phase 2 comfortably.

**The course is now about a different and more interesting failure: the model
succeeds at the task and damages the repository.** Every element of this is
artifact-backed as of 2026-07-24:

- it silently destroys inherited work when files are shared (preservation
  breakage; `lessons.md` #12 clause 2, reachable for the first time under the
  seeded incremental workload);
- it rewrites its own grader (2/8 seeded runs replaced the inherited test
  suite wholesale);
- it reports success while the contract is broken (false self-report in both
  observed failures).

The thesis this serves: **determinism, not persuasion.** The move from OpenCode
to Pi is worth making precisely because Pi's extension points let these be
handled mechanically — a `tool_call` block makes a failure structurally
impossible — rather than by prompt wording, which `lessons.md` #16 already
recorded as insufficient. Expect a long tail of places where the model still
needs help at generation time; the mechanisms are the floor, not the ceiling.

This reframe governs the Section 2-4 rewrite pass and has not yet been
propagated into chapter prose.

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

- **Investigate putting git to work: change visibility, pseudo-transactions,
  and an atomic-overlay equivalent.** Both predecessor efforts converged on git
  as the substrate for making agent work *inspectable and reversible*, and Pi
  ships more machinery for it than either used.

  **Prior art.** `local-ai-gemma`'s medium tier had the controller record a
  `git status --short` baseline before delegating and diff it after, so scope
  violations were mechanical rather than self-reported (`lessons.md` #15, #16).
  This course's harness already goes further: every eval workspace is a git repo
  with a pristine commit, and `capture_diff` reduces a run to changed-files plus
  a diff — that is what makes the acceptance oracle independent of the model's
  claims. The Tainie Pi spike hit the limit from the other side: a model `rm`'d a
  file via bash, write/edit dirty-tracking missed it, and the spike concluded
  verify extensions are *unsound against bash mutations*, proposing a
  workspace-diff event that makes the `git-checkpoint.ts` pattern first-class
  (`VERIFY-LOOP-SLM-SUPPORT.md`, item 4, status TBD upstream).

  **What Pi actually ships** (all in the installed package's
  `examples/extensions/`, no fork required): `git-checkpoint.ts` creates a
  `git stash create` checkpoint on every `turn_start` and restores it on
  `session_before_fork` — per-turn rollback points; `dirty-repo-guard.ts` blocks
  session changes when the tree is dirty; `auto-commit-on-exit.ts`;
  `git-merge-and-resolve.ts` merges upstream after each turn and feeds conflict
  blocks back to the model as follow-ups. Plus `pi.exec` for arbitrary git from
  any extension.

  **The three things worth teaching, in ascending ambition:**
  1. *See the changes.* A per-turn workspace diff surfaced as evidence —
     closing the bash-mutation blind spot the spike identified, and the natural
     mechanism for the newly-admitted **preservation breakage** chapter (a
     Phase 1 file rewritten during Phase 2 is exactly a diff-detectable event).
  2. *Pseudo-transactions.* Checkpoint before a delegation, roll back on a
     failed acceptance run — bounding a bad turn's blast radius mechanically
     instead of asking the model to be careful (`lessons.md` #1).
  3. *The atomic-overlay equivalent.* Tainie's pyrefly fork verified edits in an
     in-memory overlay and wrote only on success. The built-in-only analogue is
     write → verify → keep-or-revert on a checkpoint, i.e. a transaction where
     the acceptance oracle is the commit gate. This is the most interesting and
     the least proven; it may also subsume the "verify gate" idea the master
     spec has carried as out-of-scope since SP0.

  **Open questions.** Does per-turn stashing cost enough wall-clock to matter at
  the batch sizes Amendment 2 sets? Does rollback confuse a small model that
  sees its own edits vanish (a real risk — this is state changing under it
  between turns)? And does any of it beat simply *reporting* the diff, which the
  harness already does? Evidence-gated like everything else: taught only if a
  measured run shows it helps the SLM on the example workload. Candidate for
  Section 4 once the preservation-breakage chapter has its before-picture.


- **Coverage (or an equivalent) as an anti-neutralization mechanism for the
  acceptance suite.** A model-written `tests/conftest.py` can skip-mark every
  collected test; pytest exits 0 on all-skipped, so the oracle returns
  "passed" with the contract entirely unenforced (verified defeat,
  2026-07-24). The harness now removes conftest files and re-stamps
  `pyproject.toml` before grading, but that is a blacklist — it closes two
  known vectors, not the category. A positive check would be stronger:
  require the acceptance run to report a minimum number of *executed*
  assertions, or measure coverage of the app under the acceptance suite and
  fail below a floor. Open question: coverage adds a dependency to the
  workspace (against the thin-workload preference) and measures the wrong
  thing (lines executed, not contract satisfied) — an executed-test-count
  floor from pytest's own summary may be the cheaper 80%. Evidence-gated:
  build it when a run actually neutralizes the suite, or when authoring the
  phase-2/3 suites shows the blacklist is insufficient.

- **The long tail: where the model needs help at generation time.** The
  mechanisms in Section 4 are a floor — they make specific failures
  structurally impossible. They do not make the model *good*. Expect a
  residue of failures that no `tool_call` block can prevent because they are
  failures of generation, not of tool discipline (wrong logic, misread
  contract, plausible-but-incorrect template). Worth cataloguing as it
  emerges from measured runs rather than speculating now; the honest course
  ends by naming what mechanism cannot fix.

## Conventions

- Specs and plans are co-located with section content in `docs/section-*/`.
- Every "this helps" claim links to a dated report in `research/`.
- Status vocabulary: Queued, In progress, Blocked on <ID>, Done, Backlog.
