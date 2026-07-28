# local-ai-pi Roadmap

The master design is [`specs/2026-07-23-course-design.md`](specs/2026-07-23-course-design.md).
Per-phase specs and plans are co-located in `docs/section-*/` directories.
This file is the cross-phase index: sequence, status, and links. It is built the way the course teaches — each phase is evidence-gated, and
a later phase is not queued just because an earlier one landed.

## Read this first, in order

1. [Evidence policy](policies/evidence.md) — the rules and doctrine every
   measured claim must satisfy. Read this before trusting any number below.
2. **This file's "Next action" banner, immediately below** — the current
   plan and where it stands. If you only read one section, read this one.
3. Everything else is either current supporting material (linked from the
   "Next action" banner or the [Phases](#phases) table) or superseded —
   see the [Archive](#archive) section near the bottom before assuming a
   `specs/` or `plans/` file still describes live work. A doc's existence in
   `docs/superpowers/specs/` or `plans/` does not by itself mean it's current
   — check the Archive list first.

**Current phase: GRADING-PATH REBOOT** — see
[`plans/2026-07-24-grading-path-reboot.md`](plans/2026-07-24-grading-path-reboot.md).

> ## ▶ Next action — Section 3 editorial pass (the "Section 2 treatment")
>
> **Sections I–III merged to `main`, 2026-07-28** (commit `e1e12d3`).
> Tasks 1–10 of the grading-path reboot are all done. Section II's
> eval-suite chapter and the user-story roadmap shipped in final form;
> Section III's cost-equivalence evidence (all three pre-registered phases,
> n=16 each) cleared every degradation gate and is written up as Claim 2
> in [`docs/section-3-sdd/index.md`](../section-3-sdd/index.md). Section
> IV's placeholder page also shipped — honest about being unwritten, not
> blocking Sections I–III.
>
> **What proceeds now: a prose/structure editing pass on Section 3**
> (`docs/section-3-sdd/index.md`) to give it the same treatment Section 2
> received — restructuring, trimming (~30% word cut on dense paragraphs),
> fact-checking every number against its source report, voice consistency.
> Claim 2 ("cost-equivalence, measured") is the section most in need: it
> was written in one pass and committed straight through without the
> multi-round review Section 2 got. The rest of the chapter ("Measuring the
> mechanism" and "When your metrics are fiction") gets the same scrutiny
> but is lower priority.
>
> **Section IV remains a framing placeholder** until its two preconditions
> land: (a) Section III's final baseline and (b) knowing which mechanism —
> bare unsteered, the orchestrator+implementer flow, or both — Section IV's
> guardrails need to sit on top of. Its two evidence-backed candidates —
> speed/reliability (hang incidence, turn count) and preservation breakage
> (replace-vs-extend) — are named but not adopted. *False self-report* was
> considered and dropped: current n=16 data doesn't support it at the weight
> the pre-repair narrative claimed (0/16 in Phase 2/3, 1/16 in Phase 1) —
> kept as a watched metric, not a candidate.

A deep review (Fable, 2026-07-24) found five further integrity failures, two of
which **defeat the hardened oracle** (a model-written `pytest.ini` with
`addopts = --collect-only`, and an import-time `os._exit(0)`, each producing
exit 0 on a deliberately broken app). Root cause: every fix so far has been a
blacklist against an open category. The grading path is being rebuilt so
model-controlled input cannot reach the grader at all.

Consequences: **SP1 and SP2 status is withdrawn** — their chapter prose is
discarded (it narrates the dead 0/8 arc) and their post-repair numbers are
superseded. SP3 is **blocked** until the reboot's gates pass. Success-rate
before/after is abandoned as a claim structure (evidence policy Rule 7). The
strongest surviving evidence is oracle-independent: replace-vs-extend on the
inherited **test suite specifically** was 8/8 predictive (Rule 8 review,
2026-07-26 — Fable: the run-level any-inherited-file classification now
standing in `harness/telemetry.py` gives 6/8 on the same sample; see that
module's docstring for the distinction).

## Phases

| ID | Phase | Status | Spec | Plan | Evidence |
|----|-------|--------|------|------|----------|
| SP0 | Scaffold + Section I (repo skeleton, docs toolchain, roadmap, LESSONS, example spec triple, hello-world extension) | **Done** | [spec](../section-1-hello-agent/spec.md) | [plan](../section-1-hello-agent/plan.md) | — |
| SP1 | Section II — Measurement *(harness kept; prose discarded, numbers superseded)* (telemetry reader, minimal eval harness, evidence ledger, the smoking-gun baseline) | **Done** | [spec](../section-2-measurement/spec.md) | [plan](../section-2-measurement/plan.md) | [0/8 baseline](../section-2-measurement/research/2026-07-23-baseline-phase-1.md) |
| SP2 | Section III — SDD on Pi *(mechanism kept; prose discarded, numbers superseded)* (roadmap/packet method, parent-as-orchestrator + implementer specialist) | **Done** | [spec](../section-3-sdd/spec.md) | [plan](../section-3-sdd/plan.md) | [3/8 pre](../section-3-sdd/research/2026-07-24-sp2-baseline-phase-1.md), [5/8 post](../section-3-sdd/research/2026-07-24-sp2-baseline-phase-1-post-tuning.md), [deep-dive](../section-3-sdd/research/2026-07-24-sp2-deep-dive.md) |
| SPR | **Grading-path reboot** — rebuild the grader so model-controlled input cannot reach it, restore honest reporting, then re-run the evidence chain | **Tasks 1–10 done; Sections I–III merged to `main` (2026-07-28). Section III now receiving editorial pass (the "Section 2 treatment").** | — | [plan](plans/2026-07-24-grading-path-reboot.md) | [Phase 1](../section-2-measurement/research/2026-07-27-post-repair-sp1-phase1.md), [Phase 2](../section-2-measurement/research/2026-07-27-post-repair-sp1-phase2.md), [Phase 3](../section-2-measurement/research/2026-07-27-post-repair-sp1-phase3.md) |
| SP3 | Section IV — Keeping the SLM on track *(old catalog — orientation, tool restriction, output cap, path guard, repeat breaker, turn cap, model tuning, context budgeting — retired)* | **Framing placeholder only (revised 2026-07-28) — gated on (a) Section III's final baseline and (b) which mechanism to build atop. Two evidence-backed candidates named, not decided: speed/reliability, preservation breakage. Merges to `main` *after* Sections I–III, not blocking them.** | — | — | [Phase 2](../section-2-measurement/research/2026-07-27-post-repair-sp1-phase2.md), [Phase 3 rewritten spec](../section-2-measurement/research/2026-07-28-post-repair-sp1-phase3-less-prescriptive-spec.md) |


## Narrative reframe (adopted 2026-07-24)

The course's original hook — "an unsteered SLM goes 0/8; here is the ditch" —
is dead. That 0/8 was an oracle artifact (see the oracle-invalid incident), and
under a valid oracle the model clears seeded Phase 1 and Phase 2 comfortably.

**The course is now about a different and more interesting failure: the model
succeeds at the task and damages the repository.** As originally adopted
2026-07-24, three elements were cited, at 2/8-scale, pre-repair evidence.
**Reconciled against the current, valid, n=16 data (2026-07-28) — two hold,
one is demoted:**

- it silently destroys inherited work when files are shared (preservation
  breakage; `lessons.md` #12 clause 2, reachable for the first time under the
  seeded incremental workload) — **holds**, and at a similar rate under
  clean n=16 data (Phase 2 replace=5/16, Phase 3 replace=4–6/16, see Section
  IV's decision above);
- it rewrites its own grader (2/8 seeded runs replaced the inherited test
  suite wholesale) — **folds into preservation breakage** above; the current
  harness's replace-vs-extend metric classifies all shared-file rewrites
  together and does not currently break out the test suite specifically at
  n=16 (the 8/8-predictive, test-suite-specific figure two paragraphs up is
  itself from the earlier, smaller sample);
- ~~it reports success while the contract is broken (false self-report in
  both observed failures)~~ — **demoted.** Current n=16 unsteered data does
  not support this at the cited weight: 0/16 in Phase 2 and Phase 3, 1/16 in
  Phase 1. Kept as a metric worth continuing to watch, not treated as live
  evidence for Section IV.

The thesis this serves: **determinism, not persuasion.** The move from OpenCode
to Pi is worth making precisely because Pi's extension points let these be
handled mechanically — a `tool_call` block makes a failure structurally
impossible — rather than by prompt wording, which `lessons.md` #16 already
recorded as insufficient. Expect a long tail of places where the model still
needs help at generation time; the mechanisms are the floor, not the ceiling.

This reframe governs the Section 2-4 rewrite pass. It has been propagated
into Section II and III chapter prose (Task 9, done 2026-07-28). Section IV
is a framing placeholder only (revised 2026-07-28, see "Next action" above) —
the two surviving pillars are named as candidates, not adopted, pending
Section III's final baseline and a decision on which mechanism they build
atop.

## Backlog (evidence-gated, not queued)

Items held to a recurrence bar or a trigger, not scheduled just because a
neighbor shipped:

- **Harness telemetry improvements** (triggered by SP2 deep-dive, 2026-07-24;
  status reconciled 2026-07-24). Five gaps identified in
  [`research/2026-07-24-sp2-deep-dive.md`](../section-3-sdd/research/2026-07-24-sp2-deep-dive.md).
  Two shipped, one was promoted out of the backlog, two remain:
  1. **Capture child session JSONL** — OPEN, and now the highest-value
     remaining gap. The parent JSONL shows the subagent tool call and its
     summary result, but the child's detailed event stream (every tool call,
     every message, full pytest output at each step) is not captured. Fix: run
     the child with `--session <path>` so pi writes its own JSONL, then parse
     it alongside the parent's.
  2. **Capture harness pytest output on failure** — ✅ **shipped** (SP2
     cleanup). `SessionResult` stores `pytest_stdout` and `pytest_stderr`.
  3. **Packet fidelity metric** — OPEN. Mechanically check whether the
     packet's acceptance strings and allowed-files list match the roadmap
     verbatim. Directly measures the spec's "handoff drift" commitment.
     Reports currently state this as deferred, in text
     (`runner.py`) — keep that line honest until it ships.
  4. **Validation command drift detection** — ✅ **shipped**.
     `telemetry.detect_validation_drift` flags a narrower pytest than the
     packet specifies; `BaselineReport.validation_drift_count` reports it.
  5. **Self-report vs harness verdict agreement** — **promoted out of the
     backlog** into [grading-path reboot Task 7](plans/2026-07-24-grading-path-reboot.md),
     where it is one of three standing behavioral metrics that evidence policy
     Rule 7 now depends on. The per-run field (`SessionResult.model_tests_pass`)
     already exists; the aggregate is what Task 7 owes.

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
- **Roadmap explainer doc** (docs). A new top-level Sphinx doc file explaining
  this roadmap and its contents — what the phase table and backlog mean, the
  evidence-gated convention, and how to navigate to per-phase specs/plans —
  for readers landing on the docs site without prior context.

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


- **Coverage as an anti-neutralization mechanism** — *residual only; the
  main item was scheduled.* Three verified defeats (a skip-marking
  `conftest.py`, a `pytest.ini` with `addopts = --collect-only`, and an
  import-time `os._exit(0)`) each produced exit 0 on an unenforced contract.
  The cheaper 80% — **an executed-test-count floor read from pytest's own
  summary** — is no longer speculative: it is
  [reboot Task 2, step 5](plans/2026-07-24-grading-path-reboot.md), gated by
  two regression tests, and its doctrine is evidence policy **D4**. What stays
  in the backlog is only the stronger form: measuring *coverage of the app
  under the acceptance suite* and failing below a floor. Open question
  unchanged — coverage adds a workspace dependency (against the thin-workload
  preference) and measures the wrong thing (lines executed, not contract
  satisfied). Trigger: a run that satisfies the executed-count floor while
  still leaving the contract unenforced.

- **Replace the acceptance-suite HTML text-extraction with a real parser.**
  — ✅ **shipped** (oracle-repair worktree, 2026-07-26). The stdlib
  `html.parser`-based `_RenderedTextParser` — which did not implement HTML5's
  optional-tag auto-closing rules, so an unclosed `<p>` before a block sibling
  (valid, browser-renders-identically markup) could be misjudged — is removed
  from both
  [`examples/acceptance/phase-2/test_acceptance.py`](../../examples/acceptance/phase-2/test_acceptance.py)
  and
  [`examples/acceptance/phase-3/test_acceptance.py`](../../examples/acceptance/phase-3/test_acceptance.py),
  replaced by [TurboHTML](https://turbohtml.readthedocs.io/en/stable/)
  (`turbohtml==1.5.0`), a WHATWG-spec-compliant parser with CSS-selector
  querying. Kept out of the model-visible workspace stamp per D4 — it is
  declared only in the isolated grader's own harness-authored
  `pyproject.toml`, written by `harness/grading.py::grade_acceptance()`
  into a directory the model never controls, pinned by
  `tests/test_session.py::test_turbohtml_stays_out_of_model_visible_workspace_stamp`.

- **Acceptance grading still trusts a same-process signal a model can
  forge.** `harness/grading.py`'s executed-test-count floor previously
  regex-scanned pytest's captured stdout/stderr (Rule 8, Fable,
  2026-07-26, round 1: a model-imported `app.py` writing a fake summary
  line into a captured fd, then `os._exit(0)`, forged `tests_pass=True`
  for a solution that does not exist). Fixed by
  `harness/grading_plugin.py`, a pytest plugin recording real per-test
  hook events to a results file instead of trusting captured text —
  closes that specific attack, pinned in `tests/test_grading.py`. A
  second Rule 8 round (Fable, same day) found the fix moved the forge,
  not closed it: model-imported code can read the results-file path from
  its own `os.environ` and write directly-formatted fake lines into it,
  comparably cheap (~7 lines) to the first attack. No in-process secret
  can close this — anything the plugin can read, model-imported code
  sharing its process and memory can read too. The real fix requires
  moving model-authored code out of the grading process entirely: launch
  the model's app as a server subprocess and drive the acceptance suite
  against it over HTTP, instead of today's in-process
  `TestClient(app)` (`examples/acceptance/phase-{1,2,3}/test_acceptance.py`).
  That is a materially larger change than the plugin and was deliberately
  deferred rather than done under Task 2. Documented on
  `harness/grading_plugin.py`'s module docstring, which links back here.
  Trigger: before this project publishes any success/failure claim that
  depends on `tests_pass` being resistant to a deliberately adversarial
  solution, or the grading path needs another capability anyway.

- **The long tail: where the model needs help at generation time.** The
  mechanisms in Section 4 are a floor — they make specific failures
  structurally impossible. They do not make the model *good*. Expect a
  residue of failures that no `tool_call` block can prevent because they are
  failures of generation, not of tool discipline (wrong logic, misread
  contract, plausible-but-incorrect template). Worth cataloguing as it
  emerges from measured runs rather than speculating now; the honest course
  ends by naming what mechanism cannot fix.

## Archive

Specs and plans whose work is fully executed, moved to
`docs/superpowers/archive/{specs,plans}/` so their status is visible without
opening them. Kept as historical record — cited from chapter prose and other
docs where their content is still relevant, but not describing live work.

| Doc | What it decided/built | Executed as |
|-----|------------------------|-------------|
| [archive/specs/2026-07-27-next-phase-decision-design.md](archive/specs/2026-07-27-next-phase-decision-design.md) | Decision 1 (Phase 3 spec rewrite, re-validate) + Decision 2 (Section renumbering: 2→suite-authoring, 3→orchestrator+measurement) | Decision 1: [16/16 report](../section-2-measurement/research/2026-07-28-post-repair-sp1-phase3-less-prescriptive-spec.md). Decision 2: Task 9 (below) |
| [archive/specs/2026-07-28-eval-suite-chapter-design.md](archive/specs/2026-07-28-eval-suite-chapter-design.md) | The user-story roadmap case study design for Section 2's suite-authoring arc | `examples/agentclinic/specs/roadmap-user-story.md` + Task 9's Section 2 rewrite |
| [archive/plans/2026-07-28-phase3-spec-rewrite.md](archive/plans/2026-07-28-phase3-spec-rewrite.md) | Task-by-task plan for the Phase 3 spec rewrite + re-validation | Commit `122d46d`, all steps checked |
| [archive/plans/2026-07-28-task9-sections-2-3-rewrite.md](archive/plans/2026-07-28-task9-sections-2-3-rewrite.md) | Task-by-task plan for Section 2 and Section 3 chapter prose (Section 4 explicitly out of scope of this plan) | Section 2/3 prose commits, `78ece8f`/`22a923f` review fixes |

**Not archived, still current** (do not archive without re-checking this
table first): `plans/2026-07-24-grading-path-reboot.md` (the active master
plan — Task 10, this consolidation, is still open), `plans/2026-07-24-oracle-repair.md`
(Amendments 1–2 are standing decisions actively cited above, not a completed
one-shot plan), `specs/2026-07-23-course-design.md` (the master spec, never
archived), `specs/2026-07-28-section3-cost-equivalence-metrics.md` (actively
governing the in-progress steered batches).

## Conventions

- Specs and plans are co-located with section content in `docs/section-*/`.
- Every "this helps" claim links to a dated report in `research/`.
- Status vocabulary: Queued, In progress, Blocked on <ID>, Done, Backlog.
- Cross-phase specs/plans that are fully executed move to `archive/` (see
  above) — don't leave a completed plan sitting alongside live ones.
