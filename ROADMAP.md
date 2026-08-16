# Roadmap

> **Planning surface, not the front door.** Current phase (7), the concept
> budget, deferred candidates, and the backlog. Completed Phases 1–5 —
> narratives, cycle tables, and the withdrawn framings and retracted figures
> recorded along the way — moved verbatim to
> [`docs/superpowers/phase-history.md`](docs/superpowers/phase-history.md)
> on 2026-08-12.
>
> Not where a new contributor should start. For what's usable now, see
> [`README.md`](README.md); for the supported architecture,
> [`docs/engine/deliver-candidate.md`](docs/engine/deliver-candidate.md); for starter tasks,
> [`docs/contributing.md`](docs/contributing.md).

*Phases group feature cycles. One direction at a time. Tangents go to the
Backlog, not into the current phase.*

## Now

**Phases 1–5 — complete.** Reproduce AgentClinic Phase 1 with a trustworthy
engine; measurement we can trust; build the extension half; prove the engine
generalizes beyond one workload; the improvement loop. Their full narratives,
feature-cycle tables, and — importantly — the withdrawn framings, retracted
figures, and corrections recorded along the way are in
[`docs/superpowers/phase-history.md`](docs/superpowers/phase-history.md),
moved there verbatim on 2026-08-12 rather than summarized away.

The two findings from those phases that still govern current work:

- **Facts work, rules of conduct do not.** Across five prompt interventions,
  the three that supplied a fact the model lacked worked; the two that
  supplied a rule of conduct did not. This is what Phase 6 is a response to.
- **No trustworthy wall-clock number exists.** Two published figures were
  retracted in one night, both for the same reason: arms run as contiguous
  blocks on a machine whose load varies. Counts (turns, `context_processed`,
  tool calls) survive; seconds do not. Interleaving arms is a precondition
  for any future timing claim — first actually done in Phase 7's Cycle 7
  batch, though via a purpose-built driver rather than by fixing `run_batch`
  (see the Backlog item, still open for that reason).


**Phase 6 — Enforcement over persuasion. Complete.** Phase 5 found the
persuasion ceiling: of five prompt interventions, the three that supplied a
*fact* worked and the two that supplied a *rule of conduct* did not. That is a
re-derivation of `LESSONS.md` §1 from the prior project — "a rule such as
'repair at most twice' still relies on the SLM to count its own loop; a
mechanical stop does not" — and of Tainie's first principle, that the model
never decides scope. This project left OpenCode for Pi because Pi offers
machinery to control operations rather than prose to persuade with, and four
phases of harness plus one of prose have under-used it. So: one at a time, add
a guard to the extension, each drawn from prior experience and each proven
against a recorded failure before it ships.

Two things this phase deliberately does **not** do, stated once so no cycle
re-litigates them. It does not try to raise acceptance — the user-story suite
is at 15/16 facts-only and has no headroom, so a guard measured there can only
fail to show anything. And it publishes no wall-clock number, because Phase 5
retracted two figures in one night and filed interleaved arms as the
precondition for any timing claim. A guard's claim is *what it prevents*,
proven by replay fixture at zero model cost.

Hypotheses are allowed and bounded. A cycle may propose a guard with no banked
failure behind it, if the prediction is pre-registered; it ends either with the
failure recorded (and the guard then earning its fixtures like any other) or
falsified and dropped, written up the way cycle 8's 3/3 falsification was.
**Nothing enters the shipped extension on a hypothesis alone** — a phase whose
unit of work is "add a feature" walks toward `BRIEF.md`'s trap by construction,
and that rule is what keeps speculation costing a cycle rather than a permanent
line of code. [spec](docs/superpowers/specs/2026-08-05-phase6-guards-design.md)

**Two roadmap flavors, because they ask different questions.** On
AgentClinic's detailed roadmap the success rate is saturated — bare Pi
scored 16/16 in Phase 1, and the prior project's orchestrated arm also
scored 16/16 — so nothing about *benefit* is observable there and the only
things that can move are turns and `context_processed`. That makes it the
clean control for what orchestration **costs**, which is the handoff-packet
claim `harness/telemetry.py` was built for and has never been used on. The
user-story variant of the same roadmap ranges 1/16 to 15/16 in that prior
series, so it is where an improvement's **benefit** is visible. Every number
in that series is a *prediction to be replicated, not a result*: its source
carries a `PENDING RULE 8 REVIEW` banner and is explicitly not citable.

**The long-term goal this phase serves, stated so it is not confused with
what any one cycle measures.** The hope is that steering keeps a small model
*on track* — not repeating work, not spiralling into loops — rather than that
it is cheaper. Those two can come apart: an arm can cost more per run and
still be the one worth shipping, because it finishes instead of hanging. Cost
is what cycle 2 measures because the Backlog owed that debt and the
instrument exists for it; staying on track is the direction the phase is
walking toward, over more cycles than this phase contains. Neither cycle 2's
ratio nor cycle 3's success rate should be read as evidence for or against it.

**This reverses two recorded decisions, deliberately.** The orchestrator was
withdrawn from Phase 2 on 2026-08-02 ("**the orchestrator is not being built
in this phase**") and its cycles were withdrawn from Phase 3 on 2026-08-03 as
work the Backlog had already deferred. Both withdrawals were right at the
time and neither was a promise never to schedule it. What changed is that the
debt is now nameable and payable: the cost arm runs on a workload already in
the repository with its grader floor already proven, so testing the claim
costs a batch rather than a construction project. The Backlog's own condition
survives intact — the experiment is proved against small disposable arms, one
improvement at a time, with comparison done by hand. Automated comparison is
deliberately **not** in this phase; running the loop manually twice is how we
learn what a comparison must refuse, and building the refusal first is the
machinery-ahead-of-its-contract move `BRIEF.md` warns against.

*(Closed 2026-08-12, recorded late. The phase's guard harness shipped —
`extensions/guards/` with `types.ts`, the loop breaker moved in unchanged,
and `guards.test.ts` exercising the shipped TypeScript against recorded
sequences. The candidate well below was never worked through one guard at a
time as planned: Phase 7's re-plan overtook it, and the mutation engine
absorbed the enforcement job wholesale instead — a revision-checked engine
that refuses stale writes and undeclared destructive edits is the same
"mechanical stop, not prose" principle applied at a different layer. One
guard from that well is worth naming as **falsified rather than deferred**:
`preserve-symbols.ts` was written, wired into the implementer, and then
**removed** in Phase 7 on 2026-08-11, because a contract-blind pre-edit
guard refuses contract-authorized renames the engine would admit. The
module survives for its `symbolsIn()` helper. The lesson is a real one for
anything else drawn from this well: a guard that duplicates a check the
authoritative layer already makes, with less information, is not defense in
depth.)*

## Concept budget

*Every term below is a cost against a 5–10 h/wk volunteer's ability to hold
the design in mind — see `BRIEF.md`. Checked and updated at the end of each
cycle; a term earns its place by naming something the design actually needs,
not by being convenient shorthand.*

| Term | Means | Introduced |
|---|---|---|
| feature cycle | the unit of work within a phase — one small, provable thing | kickoff |
| phase | groups feature cycles; one direction at a time | kickoff |
| suite | one workload the harness can run: its prompt, its acceptance contract, and its source allowlist (`harness.runner.Suite`) | cycle 1; **redefined phase 4 cycle 1** — it previously meant only the acceptance test suite a solution is graded against, which is now called the *acceptance* (the parameter name in `grade()`) |
| fixture | a known-good or known-broken example solution, used to prove the grader itself | cycle 1 |
| workspace | a disposable, git-initialized directory the model writes into. Read by the grader, never graded directly — see *grading directory* | cycle 2 |
| grading directory | a fresh directory holding only allowlisted files copied out of the workspace, plus the acceptance file; what pytest actually runs against | cycle 9 |
| hermetic | graded with controlled model-written files and caller configuration, so those inputs cannot affect the verdict | cycle 2 |
| grader | the code that turns a workspace into a verdict (`harness/grading.py`) | cycle 1 |
| harness | the eval harness as a whole (`harness/` package) | kickoff |
| verdict | the accept/reject/refuse outcome of grading one workspace (`GradeResult`) | cycle 3 |
| hook | the pytest hook that writes the real per-test outcomes to a results file | cycle 3 |
| vacuous / non-vacuity | a test that passes without testing what it claims to — this project's recurring hazard | cycle 3 |
| refusal | the grader declines to certify a run before pytest ever executes | cycle 5 |
| task spec | the document a model builds a solution from — AgentClinic's roadmap, the duration suite's `spec.md` | cycle 6; generalized phase 4 cycle 1 |
| seam | a parameter standing in for a value that could change, so nothing has to change if it does — not a hardcode | `BRIEF.md`, reused cycle 7 |
| liveness (check) | confirming the model server responds before a run is even attempted | cycle 7 |
| allowlist | which model-written paths get copied into a fresh directory and graded at all; per-suite, and required rather than defaulted since phase 4 cycle 1 | cycle 5's close, implemented cycle 9 |
| checkpoint | an append-only JSONL record of completed runs; resumes by counting valid lines, tolerant of a truncated last line on both read and write | cycle 2's deferrals, implemented cycle 10 |
| run | one invocation of Pi against one fresh workspace, followed by its grade | cycle 8 |
| batch | a fixed, sequential set of runs under one declared set of conditions | cycle 11's re-plan |
| extension | the fixed project-supplied Pi addition loaded for each run, distinct from Pi's ambient extensions | cycle 8 |
| process group | one Pi or pytest child plus descendants, terminated together if that child times out | cycle 12 |
| telemetry | structured measurements derived from a run's captured output (`harness/telemetry.py`); a recomputable view, never storage | phase 2 cycle 1 |
| turn | one `turn_end` event in Pi's JSON stream — borrowed from Pi's vocabulary, not coined. Pinned: any redefinition invalidates every number already produced | phase 2 cycle 1 |
| tool call | one tool Pi invoked during a run, correlated start-to-end by `toolCallId` — borrowed from Pi's vocabulary, not coined | phase 2 cycle 1 |
| context processed | `input + cacheRead + cacheWrite` — a cumulative *workload* measure, not a context-window size, and not latency or cost. Adopted from the prior effort's metrics report rather than invented, so its numbers stay comparable | phase 2 cycle 1 |
| gotcha | a non-obvious Pi behavior, found by this project, costing time and frustration to discover, and invisible in Pi's own documentation — recorded with its price and a citation so it is remembered | phase 3 cycle 2 |
| improvement | a named, optional change to how a run is steered — agent files, prompts, supporting spec documents — applied to a run as one unit and digested into its conditions. A run has exactly one improvement or none | phase 5 cycle 1 |
| orchestrator | the parent Pi session that reads a task spec and delegates to a specialist child instead of writing the solution itself | phase 2 cycle 1; retired 2026-08-02 unspent, **revived phase 5** |
| handoff packet | the structured brief an orchestrator hands a specialist — task, allowed files, acceptance strings, validation command. What the cost claim is about | phase 2 cycle 1; retired 2026-08-02 unspent, **revived phase 5** |
| arm | one batch run under one improvement, named for comparison — *bare*, *facts-only*, *orchestrated*. **Spent against cycle 1's explicit decision not to**; see below | phase 5 cycle 2 in practice, admitted cycle 13 |
| delegation | one parent run handing a subtask to a child `pi` process, via Pi's shipped subagent extension. Countable: cycle 10's arm made exactly one per run | phase 5 cycle 3 |
| delegated child | the separate `pi` process a delegation spawns. Its stdout is never seen directly — the parent's stream carries its transcript, which is the only view of it | phase 5 cycle 3 |
| loop breaker | the project's Pi extension: refuses a tool call already made unchanged `THRESHOLD` times within a window of `WINDOW`. The phase's installable artifact | phase 5 cycle 6 |
| agent dir | the directory `PI_CODING_AGENT_DIR` points a run at, holding its settings, models and user-scope extensions. **The only seam that reaches a delegated child**, since the subagent extension passes no environment of its own | phase 5 cycle 9 |
| runaway | a run repeating one *identical* call — 245 `ls -R`, 77 identical `pytest`. What the loop breaker detects, because the key includes the arguments | phase 5 cycle 8 |
| churn | a run rewriting the *same target* repeatedly with differing content — 27 versions of one template. **Not a runaway**, and the loop breaker mostly does not catch it, which is why the two are separate words | phase 5 cycle 11 |
| guard | one enforcement rule in the extension, with its own replay fixtures. The loop breaker is guard #1 and keeps its own row above, because the published records cite it by name | phase 6 cycle 1 |
| replay fixture | a recorded tool-call sequence a guard is run against offline, paired — one it must fire on, one it must stay silent on. The evidence bar for a guard, as the known-good/known-broken pair is for a grader | phase 6 cycle 1 |

**Spent, phase 5 cycles 2–13 — seven terms, recorded late.** The table's
newest entry stood at cycle 1 while twelve cycles ran. That is the failure
this budget exists to prevent, so it is recorded as a lapse rather than
backfilled silently: terms entered the working vocabulary by use, and were
load-bearing in published records, before anyone weighed whether they earned
their place.

**`arm` was rejected at cycle 1 and then spent anyway.** The note below
argues against it — it "arrives carrying the fourth-attempt story `BRIEF.md`
tells" — and chooses `improvement` instead. Cycles 11 and 13 then use *arm*
in nearly every sentence, because the two words are not synonyms and the
cycles needed the one that was refused: an *improvement* is the change, an
*arm* is a batch run under it. Cycle 11 compares three arms of two
improvements plus a bare baseline, which cannot be said in the cycle-1
vocabulary at all. The word is admitted rather than the usage corrected,
and cycle 1's concern stands as a caution: **one improvement at a time,
comparison by hand**, no matrix.

**`runaway` and `churn` are kept apart deliberately.** They looked like one
concept for four cycles and are not. A runaway repeats an identical call and
the loop breaker stops it; churn rewrites one target with differing content
and mostly slips past, because the extension keys on arguments. Cycle 11
found churn in *both* arms at comparable amplitude with every churning run
still accepted — so the distinction is what keeps the phase from claiming a
guard for a problem it does not address.

**Redefined, phase 4 cycle 1.** Three terms above were narrowed to the
first workload without anyone noticing: *suite* meant an acceptance file,
*task spec* meant AgentClinic's roadmap specifically, and *allowlist*
named `app.py` and `templates` in its own definition. A second workload
made all three read as wrong. A redefinition costs a contributor *more*
than a new term — they must unlearn something — so it is recorded here
rather than quietly edited. The count of terms is unchanged.

**Retired, not currently spent:** `oracle` — dropped from the engine's
vocabulary, since "grader"/"verdict" cover the same ground without a term
borrowed from testing theory. It survives in `BRIEF.md` only as a
reference to the old branch's suite, which is a historical citation rather
than live usage; don't "fix" that occurrence. `conjunct` — renamed to
`condition`; cycle 5's audit caught that the rename hadn't reached every
test name.

`orchestrator` and `handoff packet` — spent at cycle 1's close and
**retired 2026-08-02, unspent**, when the orchestrator experiment was
withdrawn from Phase 2. The budget's rule is present-tense: a term earns
its place by naming something the design *actually needs*. With the
experiment deferred to the Backlog, no current or next cycle needs either
word — they name a backlog item, and carrying them would make the table a
record of things once said rather than a measure of what a 5-h/wk
contributor must currently hold. They survive as historical citations in
cycle 1's spec and in the Backlog entries that describe the deferred
experiment; that is the same status `oracle` has, so don't "fix" those
occurrences either. Both revive if and when the experiment is scheduled.

**Revived 2026-08-04, on that note's own terms.** Phase 5 schedules the
experiment, so `orchestrator` and `handoff packet` move back into the table
above. The retirement note anticipated exactly this — "Both revive if and
when the experiment is scheduled" — which is why the revival is a
restoration rather than a reversal. Their definitions are unchanged from
what phase 2 cycle 1 spent them on; nothing was redefined in absentia.

**Phase 5 spends one genuinely new term: `improvement`.** It earns its place
by naming the thing the phase exists to make measurable, and the alternatives
were both worse. *Intervention* is more precise and less legible to a 5-h/wk
contributor. *Arm* is the prior project's word and would be honest, but it
arrives carrying the fourth-attempt story `BRIEF.md` tells — six arms in a
single day — and the discipline this phase binds itself to (one improvement
at a time, comparison by hand) is easier to hold under a word that does not
already mean a matrix. Recorded so the choice is visible rather than
defaulted.

## Phases

| # | Phase | Direction (one sentence) | Status |
|---|-------|--------------------------|--------|
| 1 | Reproduce AgentClinic Phase 1 | One trustworthy, hermetically-graded run; n=16 reproducing ~15/16 | complete |
| 2 | Measurement we can trust, cheaply enough to repeat | Instrument a run, characterize its precision, make the environment honest, and impose a discipline on published numbers | complete; the n=100 affordability target was retired 2026-08-02 by the phase's own findings — see "Now" |
| 3 | Build the extension half | The product is "a Pi extension plus an eval harness"; two phases built the harness. Make the extension observable, then teach the mechanics and record the gotchas. *(This row previously read "Specialize Pi's shipped subagent, then test the handoff-packet cost claim" — withdrawn 2026-08-03 as orchestration work the Backlog had already deferred.)* | complete |
| 4 | Prove the engine generalizes beyond one workload | A second, differently-shaped suite runs through the same harness, each grader having accepted a known-good and rejected a known-broken solution | complete; closed at one cycle 2026-08-04 — see "Now" |
| 5 | The improvement loop | Make an improvement a named artifact the harness digests, then run the loop once end to end — what orchestration costs on a saturated workload, what it buys on one with headroom — and finish pointed at something installable | complete |
| 6 | Enforcement over persuasion | One at a time, add a guard to the extension, each drawn from prior experience and each proven against a recorded failure before it ships | complete; the guard harness shipped, but the candidate well was overtaken by Phase 7's re-plan and the mutation engine absorbed the enforcement job — see "Now" |
| 7 | Workload first, envelope to candidate commit | Credible evidence for a small local model doing routine, pre-chewed coding work, and the smallest useful repository-safe executor: task → typed handoff → bounded implementer → validated candidate ref | in progress — the current phase; [execution plan](docs/superpowers/plans/2026-08-09-phase7-workload-first-roadmap.md) |
| 8 | An eval you can type, not one you paste | Give the harness a documented entry point — a small, stdlib-only CLI (names not symbols, friendly preflight, a checkpoint summary) — and move the why/what/how into `docs/evals.md` | complete; five cycles shipped 2026-08-13 — see the Phase 8 section below |
| 9 | An engine you can install | Make the engine adoptable by a Python developer running a small local model in Pi: a one-file install that puts the guards in every session, a README whose setup section serves both the engine and the evals, and an honest pilot number for what the guards change | complete |
| 10 | Name the engine | Land the end-user vocabulary — engine as the package, orchestrator and implementer as the roles, guards as passive steering — in the docs and user-facing code, after the scheduled evidence run, so collaborators onboard to a naming regime that is not about to change | complete |
| 11 | The contract-authoring bridge | The orchestrator pre-chews a real `HandoffContract` from a roadmap/manifest (`tools/author_contract.py` → `HandoffContract` JSON, `inspectContract` as the admission gate), driving `/implement`'s structured flavor | planned |
| 12 | The engine, packaged | Make the engine a real pi package — `pi install` from a git repo or npm — so the two-file copy becomes a one-line install, and land the deferred re-org (directory rename, orchestration consolidation, closure unfreeze) at the same time | planned |


**Phase 7 — Workload first, envelope to candidate commit. In progress; the
current phase.** Produce credible evidence for a small local model doing
routine, pre-chewed coding work, and turn the coherent envelope into the
smallest useful repository-safe executor. The full execution plan is
[`docs/superpowers/plans/2026-08-09-phase7-workload-first-roadmap.md`](docs/superpowers/plans/2026-08-09-phase7-workload-first-roadmap.md)
— it is a separate document because it was written as a re-plan mid-phase,
and it, not this section, is the authority on cycle ordering.

Where it stands as of 2026-08-12:

- **The svcs workload is qualified and frozen** — ten candidate tasks
  curated, nine qualified, a cohort file that fails loudly on drift.
- **Candidate delivery exists and is the product path.** A task becomes a
  typed handoff; a Pi child bounded to `read`/`write`/`edit` implements it
  under a revision-checked mutation engine; the result is validated and
  lands as a reviewable `refs/satyrn/candidates/<task>` ref or a receipt
  saying why not. Traced end to end in
  [`docs/engine/deliver-candidate.md`](docs/engine/deliver-candidate.md).
- **Cycle 7's pre-registered comparison ran** — 64 attempts, two arms
  (concise brief vs. complete locating contract) across four tasks, n=8.
  The locating contract wins on one task of four; two are ceiling-tied and
  one is floor-tied. Result and its limits:
  [`docs/superpowers/research/2026-08-11-phase7-cycle7-confirmatory-result.md`](docs/superpowers/research/2026-08-11-phase7-cycle7-confirmatory-result.md).
  Every claim's evidence category is indexed in
  [`docs/evidence-index.md`](docs/evidence-index.md).
- **Distribution work is done** — evidence archived and checksummed, tests
  decoupled from historical artifacts, the front door rewritten, a
  clean-machine rehearsal run, and a curated `collaborator-export` branch
  built and verified against a live model.

**Not established, and not to be claimed:** that locating contracts help
generally (one task of four discriminated), that the typed bridge is a
planner (it is scoped to exactly four tasks and refuses the rest at the
CLI), or anything about wall-clock cost.

**Phase 8 — An eval you can type, not one you paste. Complete.** All five
cycles shipped 2026-08-13. The harness has a documented entry point:
`uv run python -m harness.cli` with `one`, `batch`, `preflight`, `suites`,
`improvements`, and `summarize`; suites and improvements are addressed by
name from the `SUITES`/`IMPROVEMENTS` registries rather than by symbol; the
known refusals (dead server, wrong Pi version, checkpoint mismatch) render
as fixable sentences with exit 2 instead of tracebacks; and the longer
treatment lives in `docs/evals.md`, with the README pointing at it. The
phase's standing limits held: no new dependency (argparse only), no
manifest and no Makefile, and comparison stays manual — `summarize` reads
a checkpoint and compares nothing. The manifest remains parked where the
`Improvement` docstring put it ("that is the cycle that adds the
manifest"). A review pass after the five cycles added the
rejection-signal fix and closed several test gaps; the deviations from the
plan, each recorded rather than quietly absorbed, are in the
[execution plan](docs/superpowers/plans/2026-08-13-phase8-eval-cli.md)'s
execution notes.

The phase's plan, kept as written:

Every number
this project publishes was produced by `run_suite` and `run_batch`, and the
only interface to them is Python: the `AGENTCLINIC_PHASE_1_USER_STORY`
constant, the `tech_stack_only()` factory, a `pathlib.Path.home() /
'evidence' / …` default. A contributor who wants to check a technique must
read `harness/runner.py` to reconstruct the invocation; there is no
`--help`, no way to discover what suites or improvements exist, and a dead
server or wrong Pi version surfaces as a traceback. The machinery is done —
this phase is about the entry point. It replaces that friction with a small,
stdlib-only command, `uv run python -m harness.cli`, with one subcommand per
step of the workflow (`one`, `batch`, `preflight`, `summarize`), suites and
improvements addressed by name rather than symbol, and failures that say
what to fix.

Three things it deliberately does **not** do. It adds **no dependency** —
`argparse` ships with Python, so there is nothing to install and nothing to
version-pin. It is **not a manifest and not a Makefile** — the `Improvement`
docstring already names the cycle that adds a manifest if one is ever
needed, and the Justfile is this machine's unrelated local tooling, not a
pattern to extend. And it does **not automate comparison** — `summarize`
reports what a checkpoint holds and compares nothing, keeping the "one
improvement at a time, comparison by hand" binding intact.

**Phase 9 — An engine you can install. Complete.** The engine works but has
no user-facing front door. The loop breaker is one installable file and one
documented page; the other guard sits next to research machinery; the
bounded executor is reachable only from a checkout; and the pitch —
*install the engine and your small model behaves better* — has no number of
its own. This phase gives the engine a user-facing install: the two guards
bundled into one self-contained `engine.ts` a developer copies into user
scope (`cp .pi/extensions/engine.ts ~/.pi/agent/extensions/`), a README
rebuilt around four parts (why; the engine; a setup section shared by
engine and evals — uv, ruff/pyrefly/pytest, local model and server; the
evals), a new `docs/engine/` section (why/how/what, problems and
architecture, shootout), and one pilot comparison of with-engine versus
without on a suite, indexed as pilot.
[spec](docs/superpowers/specs/2026-08-13-phase9-engine-onboarding-design.md)

Three things it deliberately does **not** do. It adds **no dependency** and
**no new guard** — Pi loads extensions through jiti (no compile step), so
the bundle is a self-contained file with no bundler, and it ships the two
guards that already exist. It does **not** touch the executor —
`deliver_candidate`'s digest-pinned closure and its tests stay as they
are, and bundling the bounded implementer into `engine.ts` is deferred to
the npm-packaging effort that will follow. And it is **not** the eval CLI
or confirmatory evidence — Phase 8 owns the harness entry point, and the
shootout is a pilot with its non-claims written down.

**Phase 10 — Name the engine. Complete.** Phase 9 shipped the engine bundle
and its docs, and the product's second face is called "the bounded
executor" — mechanism-speak that must go before collaborators onboard. The
intended vocabulary is the one the project has used internally all along:
the **engine** is what you install; the **orchestrator** is the front you
invoke — it pre-chews a task into a handoff packet and keeps the
implementer's context small; the **implementer** is the bounded worker it
drives; the **guards** steer passively. This phase ran the scheduled
guards-baseline evidence first (under the current names), then landed the
vocabulary in the docs and the user-facing code, registered `/implement` as
the orchestrator's session front (a thin shell-out to the existing CLI),
and shaped Phase 11 — the contract-authoring bridge — at the roadmap
level.
[spec](docs/superpowers/specs/2026-08-14-phase10-name-the-engine-design.md)

Three things it deliberately does **not** do. It does **not** rename the
directory or unpin the closure — `extensions/orchestration/` and the
digest-pinned `IMPLEMENTER_EXTENSION_CLOSURE` stay pinned until packaging.
It does **not** do TypeScript orchestration — the orchestrator's substrate
is the Python CLI, and TS orchestration may never happen. And it is **not**
the contract-authoring bridge — pre-chewing real handoff packets is Phase
11's job.

**Phase 11 — The handoff contract file, human-directed. Complete.** Phase
10 registered `/implement` in its ad-hoc flavor — the user's prompt mapped
onto the CLI's flags and shelled out to the existing executor — and
deliberately stopped there. This phase gives `/implement` a structured
flavor, but not the one originally shaped below: a 2026-08-15/16 spike
found machine-made **bounds** confine the implementer (proven — bare
envelope 0/24 candidate-created, `autowire`'s bounded contract 8/8) and
packet **content** moves outcomes floor-to-ceiling (proven — one contract
arm 8/8 against a 0/4 brief), but the system **authoring and gating that
content autonomously** is not established (3/8 vs. 8/8 by hand, and a
remediated authoring prompt collapsed to 0/8 all-noop). So the phase
re-scoped around what the spike actually proved instead of what it was
shaped to build: the main agent, not a machine, authors the contract
in-session, guided by the new `write-handoff-contract` skill.
`harness/contract_file.py` parses the resulting markdown-plus-YAML file
into the existing `HandoffContract` wire format; `harness/contract_lint.py`
ports the one criterion that survived a five-criterion gate's own
deletion — a path the packet names that can be neither read nor created;
and `tools/deliver_candidate.py --contract` (`--prompt-file` removed
outright) refuses a bad packet before spending a single model call.
`/implement <contract-file>` drives it end to end.
[rescope spec](docs/superpowers/specs/2026-08-16-phase11-rescope-design.md),
[plan](docs/superpowers/plans/2026-08-16-phase11-contract-file.md),
[smoke test](docs/superpowers/research/2026-08-16-phase11-contract-file-smoke.md)
(n=1, a wiring check, not a rate — not a substitute for the spike's own
evidence above). The original shape is superseded in place, not deleted:
[shape](docs/superpowers/specs/2026-08-14-phase11-contract-authoring-bridge-shape.md).

Autonomous authoring and gating — the piece this phase explicitly does
not establish — moves to Phase 14, along with `--contract-task`'s removal
(the harness-only four-task bridge this phase left untouched, marked for
removal) and a runtime-signal meter the spike's evidence pointed at but
nobody built.

**Phase 12 — The engine, packaged. Complete.** The engine installs by
copying two files into user scope; the npm package was deferred to "the
packaging effort" in Phase 9 and again in Phase 10. This phase makes the
engine a real pi package: a `pi` manifest in the root `package.json`
pointing at exactly the two installable files (which disables Pi's
convention-directory auto-discovery, so the research `extensions/` tree
never loads into a user session), a pinned ref for stable installs, and
`pi install git:github.com/pauleveritt/local-ai-pi@<ref>` as the one-line
story. The deferred re-org lands here too: the directory rename
(`extensions/orchestration/` → `extensions/implementer/`), orchestration
consolidation into the package (the digest-pinned closure unfreezes), and
the `author_contract.py` vocabulary sweep. It also documents the fact
that the engine already works inside this repository (project-local
`.pi/extensions/` loads it with zero install) and decides whether that
directory keeps its double duty.
[shape](docs/superpowers/specs/2026-08-14-phase12-engine-packaged-shape.md)

### Phase 6 feature cycles

| Cycle | Summary | State |
|-------|---------|-------|
| 1 | The guard harness — `extensions/guards/`, one entry point (`index.ts`, never the directory — cycle 1's spike found a directory argument fails *silently* and the run still grades accepted) plus one file per guard, with the loop breaker moved in **unchanged** as guard #1. Collapses the current `.pi/extensions/` + `pi-agent-dir/extensions/` copy-paste pair into one installed location, in the agent dir, since cycle 9 proved `PI_CODING_AGENT_DIR` is the only seam that reaches a delegated child. Builds the replay runner the rest of the phase is judged by: it exercises the **shipped TypeScript** against recorded tool-call sequences, closing the gap cycle 6's replay script names in its own docstring ("this is an analysis of the rule, not a test of the shipped code… they can diverge, and no test here would notice"). Two replay fixtures for guard #1 from batches already banked — cycle 4's 261-turn run, on which it must fire, and a clean accepted run, on which it must stay silent. **Claims no number and runs no batch.** The same move as phase 4 cycle 1: prove the machinery on a guard whose value is already established, so the first *new* guard is not also the first test of the harness judging it. [spec](docs/superpowers/specs/2026-08-05-phase6-guards-design.md) | Done — `extensions/guards/{types,loop-breaker,preserve-symbols}.ts` and `guards.test.ts` shipped. Two deviations from the plan above, both recorded rather than quietly absorbed: there is no `index.ts` (each guard is imported by path, and `tools/deliver_candidate.py`'s `IMPLEMENTER_EXTENSION_CLOSURE` pins the whole import closure by digest instead), and `.pi/extensions/` still holds a loop-breaker copy for the standalone install the README documents, so the copy-paste pair was not collapsed. |

**The candidate well, not a commitment.** Later cycles draw from
`LESSONS.md` and Tainie, one at a time, roughly in this order of how much
recorded evidence sits behind each: a **graceful turn budget** (§11/§16;
Pi has no turn cap at any level and `ctx.abort()` is confirmed to yield
`stopReason: "aborted"`, which the shipped subagent classifies as a *failed*
delegation — so blocking dominates aborting); **tool-output limits and
recursive-listing refusal** (§8 — the initial choice is stochastic, the
context explosion after it is deterministic); a **path-keyed churn breaker**
(27× one template, 19× and 10× `app.py`; the current key includes arguments,
which is why 26 of 27 byte-identical writes tripped it and the rest did not);
**stale-anchor edit → demand a whole-file write** (§12, 27 `oldString`
mismatches in one session record); **resolved-model verification** (§10);
and a **default-deny tool policy** (§8 — a child hit its denied `ls`, then
routed the same intent through an editor-injected shell tool).

Structural/LSP navigation and deterministic write-path transforms are
**deliberately excluded** as too large for a guard — they are Tainie's whole
architecture, not a file under 150 lines. If they are wanted here, they are a
phase. The enforcement spec's **done-detector** stays unscheduled on its own
evidence: it would never have fired in its own flagship run, and both churning
runs were accepted anyway, so it would have changed zero grades.

**A constraint that must survive the phase.** A guard must never touch the
harness's acceptance file; its signal is the model's own validation command.
Running the contract mid-run would hand an arm a perfect done-signal no earlier
arm had — a *capability*, not an information leak, which is why redacting
failure text would not fix it. `grade()` already backs this structurally by
copying allowlisted paths out to a fresh directory, so the acceptance file is
never in the workspace during a run.

### Phase 8 feature cycles

| Cycle | Summary | State |
|-------|---------|-------|
| 1 | **Name registries** — `SUITES` and `IMPROVEMENTS` dicts in `harness/runner.py` keyed by short name (`agentclinic-phase-1`, `user-story`, `duration`, `tech-stack-only`, …), so a name rather than a symbol addresses a suite or improvement. The mild step short of a manifest, which the `Improvement` docstring already parks ("that is the cycle that adds the manifest"). Tests: every registry entry resolves; names are unique and stable. | Done — `SUITES` (agentclinic-phase-1, user-story, duration) and `IMPROVEMENTS` (four factories keyed by exact `Improvement.name`) shipped. Values are the *factories*, never their results, so `import harness.runner` still succeeds without Pi; the laziness test reloads in a subprocess (an in-process reload re-defines the module's dataclasses under other test modules — see the plan's execution notes). |
| 2 | **The CLI** — `harness/cli.py`, run as `uv run python -m harness.cli`, stdlib `argparse`. Subcommands `one`, `batch`, `preflight`, plus `suites` and `improvements` for discovery; flags `--suite`, `--target`, `--improvement`, `--checkpoint` (default `~/evidence/<suite>-<date>.jsonl`). `--help` is the documentation. Serves the exact contract the README documents; comparison stays manual. | Done — `harness/cli.py` ships with the six subcommands; `--suite`/`--improvement` take `choices=` from the registries so `--help` lists everything; `--checkpoint` defaults to `~/evidence/<suite>-<date>.jsonl`; `one` writes no checkpoint (checkpointing is `batch`'s job). |
| 3 | **Friendly preflight** — `one` and `batch` run `check_model_server_alive()` and the Pi-version check up front, printing a human sentence with the fix (`omlx start`; `docs/setup.md`) instead of a raw traceback. The harness already refuses; the CLI translates. | Done — `one` and `batch` check liveness up front and render `ModelServerDown` with the `omlx start` fix sentence; `batch` translates the version `RuntimeError` and the checkpoint `ValueError` as messages, exit 2. `one` deliberately does not pin the Pi version (spec D2 — `run_suite` never has); `preflight` reports both checks and makes no model call. |
| 4 | **`summarize`** — `harness.cli summarize <checkpoint.jsonl>` prints accepted/total and the grade breakdown via `load_checkpoint`. A summary is not a comparison; only read. | Done — `summarize <checkpoint.jsonl>` prints the conditions header (model, improvement, Pi version from the first record), run count, acceptance count, and one line per rejected run naming its signal; a missing path is a friendly refusal, an empty checkpoint reads as zero runs. |
| 5 | **Documentation** — give the harness a documented entry point in the README (one-liners for `one` and `batch`), and start `docs/evals.md` as the longer treatment: why measure, what a run/batch/improvement/checkpoint is, how to run each, and the three things that will bite you, moved out of the README and given room. | Done — README "Run an eval" one-liners for `one` and `batch`; `docs/evals.md` (why measure, the four concepts, how to run each, the three things that will bite you); `evals` added to the docs-site toctree; sphinx `-W` build clean. |

### Phase 9 feature cycles

| Cycle | Summary | State |
|-------|---------|-------|
| 1 | **The bundle** — one self-contained `.pi/extensions/engine.ts`: the two guards' policy plus a thin adapter registering both on `tool_call`, one-file user-scope install (`cp .pi/extensions/engine.ts ~/.pi/agent/extensions/`), guard sources untouched. Pinned against the sources by test (constants and refusal text agree; the file stays free of local imports) and driven against the recorded loop and destructive-edit fixtures; a drift test pins the install instructions; `deliver_candidate`'s closure and tests stay green. | Done — the bundle shipped and is pinned. |
| 2 | **README restructure** — four parts: why; the engine (minimal install, everyday steering, executor one-liner); the shared setup section (uv, ruff/pyrefly/pytest, local model/server, pointing at `docs/setup.md`); the evals (what exists today, not pre-empting Phase 8). `docs/index.md` gains the matching engine link and toctree. | Done — the README rebuilt. |
| 3 | **`docs/engine/`** — `index.md` (why/how/what, the two faces, where to go next) and `architecture.md` (problems being solved, guards as pure decisions, the bounded implementer underneath); cross-links to `loop-breaker.md`, `setup.md`, `evidence-index.md`. Quoted constants get the `test_loop_breaker_doc.py` drift treatment. | Done — the docs/engine pages added. |
| 4 | **The shootout pilot** — a small hermetic harness seam loads `engine.ts` into `run_suite` (extension-only `Improvement` or `extensions=`), one suite chosen with the owner, 4–6 attempts per arm, with-engine versus without. Write-up in `docs/engine/shootout.md`, labeled pilot, indexed in `evidence-index.md`; no pooling; a defect is fixed and rerun, a disappointing number recorded honestly. | Done — the seam + pilot ran (6/6 both arms, ceiling). |

### Phase 10 feature cycles

| Cycle | Summary | State |
|-------|---------|-------|
| 1 | **The evidence run** — bare control versus `ENGINE_IMPROVEMENT` (guards-only) on `agentclinic-phase-1-user-story`, pilot n=6 per arm, n=16 if the direction holds; updates `docs/engine/shootout.md` with the discriminating comparison and closes the Deferred-candidates entry. | Done — bare 0/6, guards-only 0/6 on user-story; guards inert, recorded in the shootout. |
| 2 | **The rename/re-org** — the vocabulary lands across README, `docs/engine/*`, `docs/glossary.md`, the evidence-index scope note, and the ROADMAP; "bounded executor" retires from user-facing text; user-facing strings in `tools/deliver_candidate.py` and `.pi/extensions/engine.ts` move to the vocabulary. No directory rename, no closure changes. | Done — the vocabulary landed. |
| 3 | **The `/implement` command** — a Pi command registered by the engine package via `pi.registerCommand()`; maps the user's prompt and repo onto the CLI's flags and shells out to `uv run python -m tools.deliver_candidate`; returns the candidate ref or the refusal. The vocabulary anchor, not new orchestration. | Done — `/implement` registered. |
| 4 | **Phase 11 shape** — a ROADMAP entry for the contract-authoring bridge: the orchestrator pre-chews a real `HandoffContract` from a roadmap/manifest (`author_contract.py` → `HandoffContract`, `inspectContract` as the admission gate), driving `/implement`'s structured flavor. Spec-level shape only. | Done — Phase 11 shaped. |

### Deferred candidates

*Things a cycle's brainstorming considered and passed over — usually the
"smallest choice" between two real options. Tracked here, updated at the
end of each cycle, so the next brainstorming session starts from this list
instead of re-deriving it from old specs.*

**Closed 2026-08-14 — the missing guards baseline.** The scheduled run —
bare control versus `ENGINE_IMPROVEMENT` (guards-only) on
`agentclinic-phase-1-user-story`, pilot n=6 per arm, checkpoints
`~/evidence/shootout-userstory-{control,engine}-2026-08-14.jsonl` —
floor-tied both arms at 0/6 with zero guard firings (the model asked the
human how to proceed and never wrote a file), so the guards' insurance
number is zero on this suite and the 13/16 effect lives in the
executor/stack, as recorded in `docs/engine/shootout.md`.

The 2026-07-30 re-plan absorbed this list into cycles 3–10 above (numbers
as they stood then): the hermetic grader split into cycles 3 and 5, the
typed verdict into cycle 3 (so the grader names the concept rather than
inheriting a name it never argued for), the git-diff exercise into cycle 8
(the first time a model writes changes worth diffing), checkpoint/resume
into cycle 9, and n=16 into cycle 10. That re-plan also found three things
the list had never named — a model actually being invoked, a liveness
check, and the AgentClinic spec the model builds from — which are now
cycles 8, 7, and 6. Cycle 5's own close then split its combined row and
inserted the allowlist as a new cycle 9, pushing checkpoint/resume and
n=16 to 10 and 11 — the numbers above reflect that; this paragraph is
historical record of the numbering as it stood before that split.

**Resolved by cycle 5, kept for the record.** The two notes above from
cycle 2's review (`core.hooksPath` breaking `prepare_workspace`'s commit;
`CalledProcessError` on an empty source directory) were about
`harness/workspace.py`, which cycle 5 correctly never touched — they carry
forward again below, still open. Cycle 3's git-isolation note and cycle
4's two notes (reusable attack helpers; the vacuity trap in "proven by
rejecting cycle 4's attacks") were all directly addressed by cycle 5: it
graded in the workspace with no second directory, consumed cycle 4's
helpers as planned, and its non-vacuous tests assert on `refused_config`
and `returncode is None` rather than `accepted is False` alone.

**Resolved by cycle 11.** The 2026-07-31 harvest had assigned workspace
hardening to its old cycle 13. Cycle 11 moved it before every batch
dependency: its initial commit ignores global/system Git configuration and
hooks, and `--allow-empty` permits a genuinely empty workspace with no
placeholder file.

These two notes from cycle 5 were carried to cycle 9. One is resolved,
one is still open and has nowhere else to go:

- **Still open — the `pyproject.toml` reservation.** Cycle 5 refuses a
  model-written `pyproject.toml` outright, on the grounds that AgentClinic
  Phase 1 never needs one and `[tool.pytest.ini_options]` inside it is a
  live attack path — but it's the one refused name a model might write
  for a legitimate reason (declaring dependencies). Cycle 8's real run
  didn't produce one (the model wrote `app.py`, `templates/`, and its
  own `tests/test_app.py`), so
  this note's trigger condition never fired and the question is still
  exactly where cycle 5 left it. Not cycle 9's to resolve — the allowlist
  is additive (what gets copied in), not a change to what refusal blocks.
  Carried forward with no specific owning cycle; revisit if a future run
  ever does produce one.
- **Resolved by cycle 9.** Module shadowing via `sys.path` — see the
  Backlog entry (below) for the full resolution. Cycle 9 took exactly the
  copy-only-allowlisted-files shape this note speculated about.

**Resolved by cycle 12.** Surfaced by cycle 5's brainstorming, not a
specific single cycle at the time:
`grade()` never catches `subprocess.TimeoutExpired`; it propagates
uncaught. Immaterial for a single run, but a batch needs one hung run to
record a rejection and continue, not abort the whole batch. Cycle 10's
checkpoint made resuming a batch possible; Cycle 12 makes surviving a
hang inside one possible, with group teardown and a bounded returned result.

**A collision surfaced by cycle 6's brainstorming, confirmed empirically,
and resolved by cycle 6.** `grade()` invoked `pytest -q` with
`cwd=workspace` and *no path argument*, so pytest collected every test
file in the workspace — not just the acceptance suite the harness copied
in. The AgentClinic roadmap's Phase 1 section ends by instructing the
model to "Write a smoke test in `tests/test_app.py`". So a model that
followed the spec **correctly** produced extra test files, and
`tests_executed == tests_expected` (cycle 3's condition, cycle 4's proof)
failed on a perfect solution.

Measured, not predicted: cycle 1's `reference` solution plus a two-test
`tests/test_app.py` graded as `accepted=False, executed=6, expected=4,
returncode=0`. Had it gone unresolved, cycle 8's first real run would have
rejected a correct solution and the failure would have looked like a model
problem rather than an engine problem — precisely the confusion Phase 1
was chosen to make impossible.

**Resolved by cycle 6.** `grade()` now passes the acceptance suite's
filename to pytest, so only the suite is collected — restoring what the
old harness got from `tests/test_acceptance.py` in its argv, and what the
trusted number was produced under. Pinned by
`tests/test_grading.py::test_grade_ignores_model_written_tests_and_grades_the_acceptance_file_alone`
(renamed phase 4 cycle 1 fix-up; same test).

Two alternatives were considered and rejected. Editing the smoke-test
bullet out of the transplanted spec would work, and is the wrong
direction: the 16/16 runs included that bullet, so removing it moves our
conditions away from the ones being reproduced. Deriving `tests_expected`
from what pytest collected would discard the count check that catches
`--collect-only`.

**Resolved a second way by cycle 9.** Cycle 9's allowlist took the
copy-only-allowlisted-files shape this note anticipated, so model-written
tests are now never even copied into the grading directory — independent
of this fix, not superseded by it.

Carried forward as notes from cycle 6:

- **For cycle 8 (first real run).** The transplanted task spec is Phase 1
  only. If cycle 8's run shows the model needs surrounding context the
  omitted phases supplied — a sense of where Phase 1 sits in a larger
  build — that is evidence for how much of the document to transplant,
  not a reason to add commentary to it. The file is model-facing input;
  anything added is a difference from the conditions the trusted number
  was produced under.
- **The load-bearing-facts check, worth applying before any future
  cycle's first run.** From the old branch's research: grep a spec for the
  facts its acceptance suite imports. Anything the suite reaches for that
  the spec never states is a silent dependency on whatever prose happens
  to surround it. Phase 1's suite does `from app import app`; the
  transplanted spec states `app.py` and FastAPI explicitly, so this one
  checks out — but phases 2 and 3, whose suites import `models` and
  `Complaint` by name, are where it would bite.

**Resolved by cycle 8, kept for the record.** Cycle 7's two carried-forward
notes are both closed: the `127.0.0.1:8001` default was re-confirmed
against `BRIEF.md` while writing cycle 8's spec (no drift found), and
`run_agentclinic_phase1()` calls `check_model_server_alive()` first,
letting `ModelServerDown` propagate as an environment failure rather than
a graded verdict — exactly as cycle 7 required.

**Resolved by the first live run, kept for the record.** Cycle 8's review
flagged that `pi`'s stdout/stderr was discarded, and noted it as the first
place to look if a live run came back confusing. It did: the first actual
attempt hit three bugs invisible to fixture-only testing, none caught by
Fable's review because none of them exist without a real server and a
real `pi` process —

1. `check_model_server_alive()` never sent an `Authorization` header.
   `omlx` requires one present (any non-empty value; `"not-needed"`
   works) — without it, a genuinely-up server read as down. Fixed:
   `api_key` parameter (default `"not-needed"`), sent as a Bearer token,
   proven against a stub server that 401s when the header is absent.
2. The `pi` invocation used a `--` separator `pi` doesn't recognize
   (`Unknown option: --`) and never passed `--print`, so it wasn't even
   in non-interactive mode. Confirmed against `pi --help` and a trivial
   live invocation before fixing — the prompt is a plain positional
   argument, no separator needed.
3. The captured diff included `__pycache__/*.pyc` as new binary files.
   Fixed at the time with a `.gitignore` in the now-retired `empty/`
   fixture.

`pi_stdout`/`pi_stderr` were added to `RunResult` while diagnosing bug 2 —
without them, bug 2 would have produced an empty diff and a silent
`accepted=False`, indistinguishable from the model simply failing the
task. With all three fixed, `run_agentclinic_phase1()` completed
successfully: `accepted=True, tests_executed=tests_expected=4,
returncode=0`.

Fable's light review of these fixes (below the fixes themselves) caught a
fourth instance of the same leak: `.pytest_cache/` wasn't in the `empty/`
fixture's `.gitignore` either, and the task spec has the model write its
own smoke test — so `pi` running pytest inside the workspace would create
one, showing up in the diff exactly like the `.pyc` files did. Fixed the
same way, verified the same way (no full model run needed). Cycle 11 later
removed the `empty/` placeholder entirely: `prepare_workspace()` now creates
the empty initial commit directly.

**Considered and deliberately not promoted by the 2026-07-31 harvest
re-plan.** `pi_stdout`/`pi_stderr` are captured, but only on the path
where `subprocess.run` returns normally. On a timeout,
`subprocess.TimeoutExpired` propagates uncaught (as designed — cycle 8's
spec explicitly allows this) and whatever `pi` had printed up to that
point is lost, since `subprocess.run` doesn't expose partial output from
a killed process. Immaterial for a single supervised run; a batch that
needs to diagnose *why* one run out of sixteen hung will want it. Cycle
12 (hang tolerance) makes the batch survive this case, but doesn't
capture partial output when it happens — still not fixed, still no
evidence it's needed, and `subprocess.run`'s timeout handling doesn't
offer partial capture without switching to `Popen` directly, which
remains more machinery than a single unconfirmed need justifies. Revisit
if Cycle 14's actual batch run ever produces a hang worth diagnosing.

**Resolved by cycle 11.** `prepare_workspace` no longer needs the old
`empty/` fixture's `.gitkeep` placeholder: `git commit --allow-empty`
creates a real initial commit from an empty source, while Git hooks and
ambient configuration remain isolated.

**A quiet coverage shift, surfaced by the 2026-08-01 deep review.** Cycle
5's refusal now intercepts the `--collect-only` attack before pytest ever
runs, so `test_collect_only_attack_is_refused_before_any_exit_code_exists`
(cycle 4) and `test_grade_refuses_a_workspace_carrying_config_without_running_pytest`
(cycle 5) assert the same thing by different routes. Both are kept — they
would fail differently if refusal regressed — but the consequence is worth
naming: there is no longer any *end-to-end* proof that the verdict's
count-mismatch logic catches `--collect-only`. Only the unit-level
`test_verdict_rejects_a_partial_run` covers that mechanism now. Not a bug;
worth knowing before anyone assumes the integration path still exercises
it.

Nothing else is currently deferred. Add to this list as later cycles pass
things over.

## Backlog

- **Community subagent extensions exist, and one is designed for our exact
  constraint. Researched 2026-08-04 at the owner's prompt; a third option
  the fork decision never considered.** That decision framed the choice as
  *use Pi's shipped example* versus *write our own ~150 lines*. There is a
  live third-party ecosystem, reached through Pi's own first-party installer
  (`pi install npm:<pkg>` / `git:<repo>`) and gallery at `pi.dev/packages`,
  which indexes the `pi-package` npm keyword.

  Verified directly against `registry.npmjs.org` — **not** taken from the
  research agent's summary, which warned that its own web fetches returned
  inconsistently-shaped results between calls and may have been fabricated:

  | Package | Repo | Latest | Published |
  |---|---|---|---|
  | `@mjasnikovs/pi-task` | `mjasnikovs/pi-task` | 0.28.3 | 2026-08-04 |
  | `@tintinweb/pi-subagents` | `tintinweb/pi-subagents` | 0.14.3 | 2026-07-23 |
  | `pi-subagents` | `nicobailon/pi-subagents` | 0.40.0 | 2026-08-01 |
  | `@narumitw/pi-subagents` | `narumiruna/pi-extensions` | 0.47.0 | 2026-08-03 |

  **Why this matters here specifically.** The gate for writing our own tool
  is that the shipped example puts parallel children on a single-threaded
  server. Cycle 2 measured max concurrency of 1 in all 16 runs, so that gate
  did not fire — but the risk was never that it *always* happens, only that
  the schema permits it. Two of these reportedly address it directly:
  `@mjasnikovs/pi-task` is described as targeting local single-GPU backends
  with parallelism off by default, and `@tintinweb/pi-subagents` reportedly
  exposes a `maxConcurrent` setting that can be set to 1. **Both claims are
  from the research agent reading READMEs and are unverified by us.**

  **The gate, unchanged in spirit.** Adopting one is an *improvement* in
  phase 5's sense: it competes with `sdd-orchestrator` on measured results,
  not on stars or README quality. It also enlarges the substrate-drift
  problem the fork decision was about — a third-party package moves on
  someone else's schedule, and `extension_digests` would catch that only for
  files we point at directly. Take it up when a measured arm shows the
  shipped example limiting a result, and evaluate at most one alternative
  per cycle.

- **The orchestrator's levers — an inventory, not a plan. Recorded
  2026-08-04 at the owner's prompt, who notes from prior work that "this
  orchestrator work and handoff packet has plenty of levers."** Naming them
  here keeps them from being pulled opportunistically, one at a time, in
  whatever cycle happens to be open — which is how the fourth prior attempt
  reached six arms in a single day.

  Known knobs, from this project and the prior one: the packet's shape (its
  four sections, and whether verbatim acceptance strings help or invite
  copying); how much of the task spec the orchestrator forwards versus
  summarises; whether supporting documents (tech stack, mission, domain)
  reach the packet at all; the implementer's tool allowlist; whether the
  orchestrator verifies the child's report or trusts it; and how many phases
  go in one packet.

  **The binding constraint is where they get pulled, not whether.** Cycle 2
  measured the orchestrated arm on a workload where bare Pi scores 16/16, so
  any tuning there optimises toward parity with doing nothing at eight times
  the cost. Levers belong on an arm where the bare model fails and an
  improvement has something to buy — phase 5 cycle 5+, on the user-story
  suite. One lever per cycle, each pre-registering its prediction, per the
  phase's binding one-improvement-at-a-time rule.

- **The recursive-listing spiral — a named, recurring failure, now measured.
  Owner, 2026-08-04: "recursive has been near the top of the list of my
  problems for a month."** Phase 5 cycle 4 caught it with a number. One
  orchestrated run spent **261 turns, 245 of them the identical command
  `ls -R`**, across only 7 distinct invocations in the whole run, and wrote
  nothing. Fifteen of that arm's sixteen runs repeated some identical tool
  call; six timed out.

  This is the concrete shape of the phase's long-term goal. "Keeping a small
  model on track" is abstract; *"stop it running `ls -R` 245 times"* is
  testable, and the evidence is already banked in
  `~/local-ai-pi-evidence/satyrn-phase5-cycle4-user-story-sdd-n16.jsonl`.

  **Candidate levers, none built, listed so the choice is deliberate:** deny
  or cap recursive listing in the implementer's tool allowlist (it currently
  gets `read,write,bash`, and `bash` is the hole); supply a file inventory in
  the packet so exploration is unnecessary; a turn cap; or a repeat-breaker
  that refuses an identical tool call after N repetitions. The last is
  mechanism rather than prompt, which the prior project's Part IV boundary
  treated as a different class of fix — worth honouring, because a prompt
  that asks nicely and a guard that refuses are different claims.

  **The order that matters:** measure first. The thrash metric below is what
  makes any of these provable, and it recomputes over batches already
  recorded, so a lever can be scored against this batch without rerunning it.

- **`run_batch` cannot express a reduced timeout — done 2026-08-04.**
  `run_batch` now takes `timeout`, passes it to both `_conditions` and
  `run_suite`, and a test asserts both halves — either alone leaves exactly
  the mismatch that caused the abort. Two mutation checks, each reverting one
  half, each killed by that test. `run_timeout` remains part of
  `RunConditions`, so batches at different caps stay non-comparable by
  construction; this makes the cheap one *possible*, not equivalent. The
  original entry follows.

  **Found 2026-08-04 by cycle 5's pilot.** It computes the conditions it
  enforces with a hardcoded 600 s and takes no `timeout` parameter, while
  `run_suite` records whatever it was given, so a pilot at a shorter cap
  aborts with `"run conditions changed during batch"`. The refusal is
  correct; the gap is that the phase's committed testing-economics plan names
  "pilots at n=6, `run_timeout=300`" as its main cost control and the harness
  cannot do it. Cycle 5's pilot ran as six direct `run_suite` calls appended
  to one checkpoint, which works and gives up resume-on-interrupt. Two lines
  plus a test asserting the conditions record the timeout actually used. Owed
  before the plan leans on pilots again.

- **Thrash metrics: hang rate, repeated tool calls, turn-count tail.
  Recorded 2026-08-04, gated, and deliberately not built.** The phase's
  long-term goal is keeping a small model on track rather than making it
  cheaper, and nothing in `harness/telemetry.py` measures *off* track
  directly. `tool_errors` and `complete` are the two nearest things.

  **What a measurement would add:** an incomplete/hung rate, and a count of
  repeated *identical* tool calls — same `toolName` and same arguments,
  which is what a loop looks like from outside. Prototyped ad hoc while
  cycle 2 ran: roughly ten lines over the retained `pi_stdout`, so it
  recomputes over every batch this project has ever recorded, cycle 2's
  included, without rerunning anything. That property is why there is no
  hurry — the data is already banked.

  **Why not now.** AgentClinic Phase 1 with the detailed roadmap shows
  essentially no thrash to measure: cycle 2's bare arm was 16/16 accepted,
  0 tool errors across all sixteen runs, 2 runs with a single repeated call
  each, no incomplete runs, turns 7–10. A metric introduced here would be
  reporting a floor. That is a third ceiling on this workload, alongside the
  saturated success rate and the saturated turn count.

  **Gate satisfied 2026-08-04, with one qualification.** Phase 5 cycle 4
  produced a batch in which loops occur — 15 of 16 runs with a repeated
  identical tool call, six timeouts, one run at 261 turns. The
  qualification: it is the *orchestrated* arm that thrashes, not the bare
  one, because the bare arm takes a single turn and cannot repeat itself.
  The entry's intent — do not build a metric where there is nothing to
  measure — is met. Promote it to a cycle when a lever needs scoring.

  **The original gate, for the record:** build it when a batch runs on a
  workload where the bare arm actually thrashes. The prior project's evidence says where to look — turn
  counts of 12.6 and 14.8 on AgentClinic phases 2 and 3 against 7.8 on phase
  1, and `docs/section-3-sdd/research/2026-07-28-phase3-run4-repeat-spiral-incident.md`
  on the `user-story-batch` branch, which traces **4 of 16 hangs in a single
  batch to one root cause**: the delegated implementer verifying its work
  with a self-invented `TestClient` probe instead of the packet's stated
  validation command.

  **Carry this into any such cycle:** that spiral happened *under*
  delegation. Orchestration is not automatically protective, and there the
  implementer's freelancing is what caused it. Improvement #1's
  `implementer.md` already instructs running the packet's validation command
  and reporting what it printed, which is aimed at exactly this failure — but
  that is an untested guess, not a result, and must not be written up as
  though the incident had been addressed.

- **Deep dive: how Pi actually decides to load an extension. Owner, 2026-08-04:
  "this has happened before."** It has, three times, each costing a live run
  or a wrong conclusion:

  1. **`--extension <dir>` loads nothing** — it needs the entry-point *file*.
     No error, no stderr, exit 0, other extensions still loading; the only
     symptom was `"Tool subagent not found"` much later, and the run still
     graded *accepted* (phase 5 cycle 1).
  2. **An entry appended during `session_start` is dropped** — print mode
     attaches its json subscriber only after `bindExtensions` returns, so 80
     recorded runs emitted nothing observable (phase 3 cycle 1).
  3. **Project-local `.pi/extensions/` is not loaded by a child-style
     invocation**, verified 2026-08-04 with a probe extension appending an
     entry on `agent_start`: `pi --mode json -p --no-session` with the
     extension in `cwd/.pi/extensions/` produced no entry, **and adding
     `--approve` changed nothing**. Note the asymmetry with agents:
     `.pi/agents/` *is* discovered from cwd when `agentScope: "both"` is
     passed, which is how this project's implementer specialist reaches the
     child at all.

  **Why it matters now, concretely.** Phase 5 cycle 8 needs a guard inside the
  delegated child, which is a separate `pi` process the shipped subagent
  extension spawns with args we do not control. Seeding our loop-breaker into
  the workspace was the obvious cheap fix and finding (3) closes it. Every
  remaining option is more expensive, so the loading rules are now
  load-bearing for a design decision rather than merely annoying.

  **What a deep dive should answer**, from the installed source rather than
  by experiment where possible: the full precedence order (`--extension`,
  `~/.pi/agent/extensions`, project-local, `pi install`); exactly what
  `--no-extensions` and `--approve` each govern; whether project-local
  extensions are gated on trust, on a UI, or simply not consulted; and what,
  if anything, a spawned child inherits. Output belongs in the gotchas record
  with `file:line` citations anchored to a named revision.

- **Rewind: git-as-savepoint as a feature of the shipped extension.
  Recorded 2026-08-04 after the owner asked, and scoped to the *product*
  rather than the harness.** `BRIEF.md` says what we are building is a Pi
  extension "for keeping small local models on track during real Python
  development." A small local model going off the rails is not an edge case
  here; it is the premise. What a developer needs at that moment is to undo
  the model's last few turns cheaply, without hand-reverting files and
  without polluting their git history.

  **Pi already ships most of the mechanism.** `git-checkpoint.ts` runs
  `git stash create` on every `turn_start`, keys the ref by session entry id,
  and offers `git stash apply <ref>` on `session_before_fork` — so `/fork`
  rewinds the *conversation* and this rewinds the *code* to match. Three
  neighbours show the same `pi.exec("git", …)` pattern:
  `auto-commit-on-exit.ts`, `dirty-repo-guard.ts`, `git-merge-and-resolve.ts`.
  Read as a worked example, not adopted.

  **The primitive is `git stash create`, and it is the reason this is
  tractable.** It writes a commit object and prints its ref *without*
  touching the stash stack, HEAD, the index, or the working tree. Nothing
  appears in the user's history, `git log`, or `git stash list`. For an
  end-user feature operating on somebody's real repository, that
  write-nothing property is the whole ballgame — a savepoint the user never
  has to know about until they want it. It is also why this project's
  never-`git stash` rule does not apply: that rule exists because the stash
  *stack* is shared across worktrees, and `stash create` pushes nothing.

  **Where our version would differ from the shipped example, which is the
  part worth building.** The example ties restoration to `/fork`, so the user
  must already know which turn to go back to. We have something Pi does not:
  the concept of an acceptance suite and a verdict. A savepoint labelled with
  whether the tests passed at that turn makes the useful command *"rewind to
  the last turn where the suite was green"* — the user does not have to
  remember, and the model's thrashing becomes recoverable rather than
  expensive. That is a feature the two halves of this product enable jointly
  and neither could offer alone.

  **It is also measurable, which closes the loop.** "Does rewind actually help
  a 12B model finish?" is exactly a phase 5 improvement: name it, run it
  against the unchanged baseline, keep or drop it. So the product feature and
  the evidence for it come from the same machinery.

  **Hazards, all of them real and none blocking.** `stash apply` *does* modify
  the working tree, and end-user repositories contain work we did not create;
  conflicts and uncommitted user edits need an answer before anything is
  offered automatically. One stash object per turn costs disk in a long
  session. And a note on inversion: `git-checkpoint.ts` returns early when
  `!ctx.hasUI`, so its restore half is inert in *our* headless harness while
  being fully functional for the end users this entry is about. The same
  extension is dead in one context and load-bearing in the other, which is a
  useful reminder that gotcha 9's `hasUI` finding cuts both ways.

  **Not a harness feature, and worth saying why.** For the eval harness this
  buys much less: a run is already atomic, since the workspace is freshly
  `git init`-ed and removed in a `finally`. It would add turn-indexed
  telemetry of the *artifact* rather than the stream — today a run's middle is
  invisible, so we cannot say when a solution became correct or whether the
  model thrashed — but the project's two open atomicity gaps are batch-level
  (a dead run leaves no trace; a commit in the batch's working directory
  strands the checkpoint) and in-workspace git touches neither. It must also
  never ride along in a measured arm: another extension changes
  `extension_digests`, and one shelling git every turn adds work to precisely
  what a cost comparison measures.

- **`RunConditions` does not record the acceptance contract or the
  allowlist — a real gap, deliberately left open.** Phase 4 cycle 1 made
  `task_spec_sha256` the field that distinguishes two suites, and tests
  now lock that. Discrimination *within* a suite is a different matter:
  nothing records the acceptance file's *contents* or the
  `source_allowlist`, and `harness_revision` is `git rev-parse HEAD`
  (`harness/runner.py:206-207`), so an **uncommitted** edit to an
  acceptance file, or a changed allowlist, leaves conditions
  byte-identical and a batch resumes a checkpoint graded under a different
  contract. This is exactly the bug class `extension_digests` was added to
  close in phase 3 cycle 1 — the same mistake, one layer over. Between-suite
  discrimination is itself conditional on distinct suites having distinct
  task-spec files — a property of the current suites' data, not of the
  mechanism — which is now enforced by
  `tests/test_runner.py::test_every_suites_task_spec_digest_is_pairwise_distinct`.

  **Why it was not fixed there.** Every field added to `RunConditions`
  makes existing checkpoints non-matching, and the recorded evidence lives
  outside version control in `~/local-ai-pi-evidence/`. Cycle 1's claim
  did not need it, and paying for it would have cost the existing
  checkpoints' resumability.

  **The gate:** fix it when a second contributor's evidence has to be
  compared against ours, or the first time such an edit is *discovered* to
  have happened. Nothing detects the edit itself as it occurs — the gap is
  found only after the fact, by some other means. The `("<pre-cycle1>",)`
  sentinel pattern (`runner.py:65-68`) is the precedent — old checkpoints
  become unresumable-but-readable, not lost.

  **Pulled forward to phase 5 cycle 1, 2026-08-04 — before either gate
  condition fired.** The gate above asks for a triggering event; none has
  occurred. What changed is the price. Cycle 1 adds an improvement digest to
  `RunConditions` for its own reasons, which breaks every existing
  checkpoint's resumability whether or not these two digests come with it.
  Paying a recorded debt at the moment its marginal cost is zero is a better
  trade than holding it until the gate fires and paying a *second* break for
  the same evidence. The rule this bends — no machinery ahead of its
  contract — is about building mechanisms nobody needs yet; here the
  mechanism is being built regardless and the question is only what rides
  along. Recorded as a deliberate early payment rather than a satisfied gate,
  so nobody later reads it as evidence the gate worked.

- **A run that dies leaves no trace in the harness's own records.**
  Found 2026-08-04 during phase 4 cycle 1, when a live single run was
  hard-killed mid-flight. Nothing was written anywhere: no checkpoint
  line, no log, no partial record. The only evidence the run had ever
  happened was an orphaned temp directory under `/var/folders/...`, and
  diagnosing it depended on knowing that `prepare_workspace` removes the
  workspace in a `finally` block (`harness/workspace.py:76-77`) — so a
  *surviving* workspace means the process was hard-killed rather than
  that a test failed or an exception was raised. That inference is
  reliable but it is folklore, not instrumentation.

  **Why it was not fixed here.** At n=1 it cost one diagnosis and no
  data. The cycle claimed no number, so nothing was lost.

  **The gate:** fix it when a batch first dies partway. `run_batch`
  appends per completed run, so a death between appends is invisible —
  the checkpoint simply has fewer lines than the operator remembers
  requesting, with nothing distinguishing "the batch was stopped" from
  "a run died and was skipped". That ambiguity is the actual cost, and
  it only bites at batch scale.

  **Not to be confused with a project defect in that incident.** The
  kill had an external cause outside the engine — a controlling process
  tearing down a long-running command it had backgrounded. No OOM or
  jetsam kill was logged and memory was 77% free, so resource
  contention was ruled out rather than assumed. The engine did nothing
  wrong; it simply recorded nothing.

- **Pin the Pi version the harness runs against — gate satisfied; done.**
  Discovered the hard way on 2026-08-03: Pi went from 0.82.0 to 0.83.0
  *during a working session*. Every mechanism this project depends on
  survived, but eight `file:line` citations in a published chapter went
  stale in one upgrade, and nothing in the suite could catch it — no test
  can check a citation into `dist/`. `harness/runner.py` now names
  `EXPECTED_PI_VERSION`, and `run_batch` raises `RuntimeError` when the
  installed Pi differs, naming both versions and both remedies. A single
  run is unaffected, so exploring the harness on a different Pi is never
  blocked — only batch evidence is. The suite is a different case: one test
  asserts the constant matches the installed `pi --version`, skipping when
  Pi is not on PATH and *failing* when it is a different version, which is
  deliberately the drift alarm. Another proves a matching version still
  proceeds; a third proves the refusal fires before the checkpoint
  conditions comparison, so a contributor who upgraded mid-batch is told
  why. This cycle is recorded as a row in the Phase 3 table.

  **What this does not solve.** Documentation drift is still uncaught — no
  version check can find a stale `file:line`, and the pin does not add one.
  What it buys is that an upgrade becomes a *decision* someone makes, and
  re-checking the docs that cite Pi by file and line is part of making it.
  It also does not touch the model server: `BRIEF.md` names oMLX as part of
  the recorded environment, and `RunConditions` records nothing about its
  version or build, so two contributors on identically pinned Pi can still
  differ. The pin removes one variable, not the set.

  This also answers the question the entry originally raised: whether
  pinning would change the deliberate choice in cycle 2's quote-checking
  test to leave installed-Pi quotations ungated. It does not. The suite must
  still pass for a contributor without Pi installed, which is exactly why
  the new installed-version test skips rather than fails in that case.

- **Per-delegation extensions, without a tool or a dependency — one probe,
  then decide.** Today `PI_CODING_AGENT_DIR` gives the child *one* extension
  set: every child gets whatever is in `<agent dir>/extensions/`, or nothing.
  Pi's agent frontmatter reads only `name`, `description`, `tools` and
  `model` (verified in `examples/extensions/subagent/agents.ts`), so there is
  no `extensions:` key to select per agent.

  **The hypothesis.** A parent-side extension of ours handles `tool_call`
  for `subagent`, reads `event.input.agent`, and rewrites
  `process.env.PI_CODING_AGENT_DIR` to a per-agent directory *before* the
  shipped extension spawns. `spawn` inherits `process.env` at spawn time
  (`index.ts:335-339` passes no `env:`) and `tool_call` fires before
  execution, so the child should receive whatever we set. The parent has
  already loaded its own resources, and it resolves the agent and passes its
  body via `--append-system-prompt`, so the child never re-discovers agents
  and the switched `agents/` directory should not matter.

  **Two assumptions, both unverified, and both cheap to settle:** that our
  `tool_call` handler runs before the shipped extension's execution when
  both are loaded, and that the env mutation lands before the snapshot. A
  ~20-line probe answers it — two agent dirs whose `extensions/` differ by a
  sentinel extension that writes a file, one delegation to each agent, then
  check which sentinel files exist. Same shape as the threshold-0 check that
  settled whether the guard reaches the child at all, which cost minutes and
  replaced a wrong conclusion.

  **Why it is worth trying before the alternatives.** If it works, we get
  per-agent extension sets with no dependency and no fork, and the
  `pi-subagents` package and our own tool both stay unbuilt. If it does not,
  the probe has priced the question and the two entries below are the honest
  next options — `pi-subagents` already ships per-agent `extensions:` and
  `subagentOnlyExtensions`, at the cost of a result payload that will not
  match what `harness/telemetry.py` parses.

  **Not needed by anything today.** One global set is correct for the loop
  breaker, which every child should have. This is for the first improvement
  that wants a guard for *one* specialist and not the others, and it should
  wait for that improvement rather than anticipate it.

- **Our own minimal subagent tool — gated on evidence, not on preference.**
  Roughly 150 lines: register one tool, read one frontmattered agent file,
  spawn `pi --mode json -p --no-session` with flags *we* choose, parse the
  child's stream, return its final text. It would buy exactly one thing the
  shipped example cannot: a model-facing schema with no `parallel` or `chain`
  mode, so the model cannot put several children on the single-threaded local
  server at once. **The gate:** adopt it when a measured run shows the shipped
  extension contaminating or losing a measurement — the model reaching for
  parallel despite the prompt and the refusal check, child contamination
  surviving `PI_CODING_AGENT_DIR`, or the deferred parent/child attribution
  work needing the child's raw byte
  stream rather than what the parent's `tool_execution_end` already carries.
  Until one of those fires it is machinery ahead of its contract, and the
  shipped example is maintained by the people who move the APIs it depends
  on. See the fork decision recorded under Phase 3.

  **Resolved 2026-08-04: the original gate fired, and then closed again.**
  Phase 5 cycle 8 met it exactly as written — two runs of six lost their
  result to a child the shipped extension spawned with arguments we cannot
  influence, and the guard we had built could not reach it. Cycle 9 then
  removed the motivation rather than the evidence: `PI_CODING_AGENT_DIR`
  delivers the guard to the child through user scope, so the one thing the
  tool was going to buy is already bought. The gate above is therefore
  **still shut**, on the narrower triggers it now names, and this entry stays
  a candidate rather than a plan.

  **The uncomfortable part.** Both the failure and the fix were already in
  this repository. The gotchas record's #4 and #5 state the child's argv and
  name `PI_CODING_AGENT_DIR` as "the one lever that isolates a child whose
  spawn you do not control," and the withdrawn phase 3 cycle 2 spec said the
  same. Cycle 8 was spent concluding the opposite. Nothing was wrong with the
  research; it was never retrieved.
- **Pi's extension-loading rules — closed 2026-08-04, answered rather than
  investigated.** Opened after three surprises in one project (an
  `--extension` pointed at a directory failing silently, `session_start`
  entries dropped in print mode, and a project-local `.pi/extensions/` not
  reaching a child). A source-level pass answered all of it, and most of the
  answer turned out to be **already recorded**: precedence, what
  `--no-extensions` governs versus `--approve`, and what a child inherits are
  gotchas 2–5 of the
  [Pi gotchas record](docs/superpowers/research/2026-08-03-phase3-cycle2-pi-gotchas.md),
  which now also carries the three findings that were genuinely new (11–13).
  The one open question is narrow and recorded there: source and shipped docs
  both say `--approve` should make a workspace-local `.pi/extensions/` load in
  a headless child, and our probe said it did not. Not worth a cycle — the
  user-scope route works and is the one we use.

- **When a written record does not reach the cycle that needs it.** The
  companion to *"why seven reviews missed a stale figure"*, and the same
  shape one layer out: that entry is about a stale fact surviving review;
  this is about a *correct* fact never being consulted. Phase 5 cycle 8 spent
  a full cycle — a spec, a build, a pilot, a research record — on the premise
  that a guard could not be delivered to a delegated child, while two
  committed documents said how to deliver it. The cost was one cycle and a
  research record that had to be re-framed from discovery to re-discovery.

  What is **not** proposed is a rule to "read the docs first"; that is
  unfalsifiable and everyone believes they already do it. Two candidates
  worth testing instead: making the gotchas record's numbered findings
  greppable by symptom rather than by mechanism (cycle 8 was searching for
  *how to reach a child*, and the record files that under *what a child
  inherits*), and requiring a cycle spec whose premise is an impossibility
  claim to cite the check that establishes it. Revisit as a discipline cycle
  alongside the entry below, since the two may share a cause.

- **Why seven reviews missed a stale figure.** Phase 3 cycle 1 shipped "48
  inert runs" in five documents; the true census was 80, and a light
  independent review found it after six task-scoped reviews and one
  whole-branch review had not. It was the third claim that cycle got wrong
  in the same way — all three were *correction-adjacent*, written while
  fixing something else. Two candidate responses, neither adopted:
  a one-line process rule (*when a correction retires a fact, grep for every
  other statement of that fact before committing*), and a reviewer role whose
  explicit job is checking derived figures against their sources. What is
  **not** proposed is extending cycle 4's table gate — all three misses were
  prose claims about things outside the repo, a shape no plausible extension
  of that gate reaches, and building one would be machinery ahead of its
  contract. Revisit as an isolated discipline cycle, after checking the
  hypothesis against the actual review transcripts rather than accepting the
  diagnosis of the process that produced the misses. Not urgent: the misses
  were all caught, and all by review.
- Formatting cleanup: `uv run ruff format --check .` currently reports 21
  unformatted files across historical source, specs, and plans. This is
  mechanical, non-behavioral debt, so it stays deferred rather than widening a
  corrective cycle into a noisy rewrite. Revisit as one isolated mechanical
  cycle when a clean repository-wide formatter check is worth the review cost.
- Sphinx glossary for the concept budget. Cycle 1's spec listed its terms as
  "candidates for a Sphinx glossary once docs exist." Docs now exist and are
  published, and the glossary was never built — there is no `glossary::`
  directive or `:term:` role anywhere in the repo. This is recorded so the
  aspiration stops being an invisible loose end, **not** because it should be
  built now: the `ROADMAP.md` table is doing the job at zero cost, and a
  directive with cross-references is machinery ahead of its contract. Revisit
  if contributors start needing to link a term from several documents at once.
- Volunteer-reader / section-structure design (superseded Phase 1 framing;
  revisit once an engine and real suites exist to write about)
- Telemetry — **gate satisfied; promoted to Phase 2 cycle 1.** The gate was
  "only after a suite author has named a claim they need those measurements
  to support," and the handoff-packet cost claim named one. What remains
  deferred is everything past the reader itself: wall time, cost,
  parent/child attribution, and any aggregation or report format. Each is
  listed with its reason and a path back in the cycle 1 spec's "Deliberate
  exclusions" table — that table is a record of decisions, not a backlog to
  work through.

  **Honesty note, 2026-08-02.** The claim that satisfied this gate is no
  longer scheduled: the orchestrator experiment was withdrawn from Phase 2.
  The instrument still earns its place — it serves the reaffirmed direction
  (trustworthy, repeatable measurement) on general grounds — but no future
  reader should infer from "gate satisfied" that the handoff-packet
  experiment is imminent, nor treat that one claim as a standing
  justification for further telemetry features. Each new field needs its own
  named consumer; the gate was paid once, for the instrument, not for
  everything downstream of it.

- **Wall-clock timing — deferred, and a schema correction to carry into any
  future spec.** Cycle 1's "Deliberate exclusions" table defers wall time on
  the grounds that "epoch-ms timestamps are already in the stream
  (`message_start`/`message_end`), so deferring the *field* loses no *data*."
  The deferral holds — raw stdout is retained, so the data is recoverable
  forever. But the parenthetical's implied schema is wrong, and this was
  verified against the committed fixture rather than reasoned about:
  `message_end.message.timestamp` is **identical** to its matching
  `message_start.message.timestamp` for all 12 message pairs. It is a
  message-*creation* time, not an end time. Consequences for whoever specs
  this: per-message durations do not exist as start/end pairs; any wall-clock
  figure must be reconstructed from deltas between successive message
  creations (which bundle generation *and* tool execution together); and a
  run's total span computed this way is a lower bound, because nothing after
  the final `message_start` carries a timestamp. Recorded now because it is
  exactly the author's-belief-versus-captured-stream failure the fixture
  discipline exists to catch — the pre-restructure reader made the same class
  of mistake about pi 0.81.1.

  **How much of a lower bound, measured 2026-08-02:** the gap between
  in-stream span and true end-to-end wall clock is a median of **7.6
  seconds per run, ~17% of total** (5 timed runs, `omlx`
  gemma-4-12B-it-MLX-8bit, owner's machine). The gap covers Pi startup,
  workspace provisioning and `git init`, the grading subprocess, and the
  final generation tail. It is essentially task-independent, so it adds a
  roughly constant amount per run rather than scaling with task size — the
  per-run floor for a trivial single-turn invocation, workspace included,
  is **1.6 seconds**. This matters for anyone converting run counts into a
  time budget; see
  `docs/superpowers/research/2026-08-02-phase2-remaining-plan.md` for the
  full measurement and
  `docs/superpowers/research/2026-08-02-phase2-cycle2-precision-baseline.md`
  for the correction it forced there.
- **The orchestration-cost experiment itself — deferred out of Phase 2,
  2026-08-02.** The claim, unchanged and still worth testing: *getting an
  orchestrator to write handoff packets for an implementer may consume more
  tokens than the orchestrator simply doing the work itself.* It was cited in
  cycle 1's spec as motivation for **which metrics to collect** — why
  `context_processed` is the headline and why `is_error` earns its place —
  and that motivation did its job. What does not follow is building the
  orchestrator soon: doing so would be the exact trap `BRIEF.md` names, where
  three prior attempts "turned into engineering efforts about orchestration."
  When it is scheduled, it revives the `orchestrator` and `handoff packet`
  terms, and per the owner it should be proved against **synthetic, fake,
  disposable examples** rather than a real orchestrator or a real
  multi-agent batch.

  **Phase 3's cycles 3 and 4 folded into this entry, 2026-08-03.** They were
  *parent/child telemetry* — attributing a delegated run's cost — and *the
  handoff-packet cost claim* itself. Both were scheduled inside Phase 3 on
  the same day this entry said not to build the orchestrator soon, and the
  contradiction stood until the owner challenged a cycle 2 design built on
  them. They are not separate work from the experiment above; they are its
  measurement and its conclusion, and they arrive when it does, on the
  synthetic-examples footing recorded here. **The debt this leaves, stated
  plainly:** the handoff-packet claim is what satisfied the gate to build
  `harness/telemetry.py` at all. Deferring it again means the instrument
  still has not been used for the question that justified it. That is an
  argument for scheduling the experiment deliberately some day, not for
  smuggling it into a phase about something else.

  **Scheduled as Phase 5, 2026-08-04.** "Some day" is now, and deliberately
  rather than smuggled: the phase is *named* for it, the two withdrawals are
  cited in "Now," and both terms are revived in the concept budget on the
  retirement note's own terms. Two conditions this entry set are honoured
  literally — the arms stay small and disposable, and comparison stays
  manual. One is honoured in substance but not in letter: the arm runs
  against AgentClinic Phase 1, a real workload, not a synthetic example. The
  reason to prefer synthetic examples was to avoid an engineering effort
  about orchestration, and that risk is addressed more directly here — the
  cost arm builds no orchestration machinery at all, since it runs Pi's
  *shipped* subagent extension with two authored markdown files on a suite
  whose grader floor already exists. A synthetic example would cost more to
  build than the real workload already sitting in the repository, and would
  produce a number about nothing. Recorded as a departure so it is visible.

- **Investigate Recursive Language Models (RLM) and DSPy for constructing the
  handoff packet.** The deferred orchestration-cost experiment (above)
  assumes the orchestrator *writes* a packet: it reads the spec, decides what
  the implementer needs, and hands over prose. That framing is worth
  challenging before a long sequence of incremental fixes is spent improving
  it, because two nearby techniques attack the same problem from opposite
  ends.

  *Recursive Language Models* treat a large context as a queryable variable
  the model interacts with programmatically — recursing on sub-parts —
  instead of reading everything into one context window. Applied here, the
  implementer would *pull* what it needs rather than receive a pre-digested
  packet, which would dissolve the packet-sizing tradeoff rather than
  optimize it.

  *DSPy* is a declarative framework for modular AI programs: you define
  modules by signature and an optimizer compiles them into effective prompts
  (and optionally weights). Applied here, packet construction stops being
  prompt engineering and becomes a compiled artifact.

  These are related but distinct levers — RLM is an inference strategy, DSPy
  a program-optimization framework — and they can be evaluated separately.

  **The non-obvious reason this is worth recording now:** a DSPy optimizer
  takes `metric: Callable` and compiles a program against a trainset
  (verified against current DSPy docs, 2026-08-02). This project is already
  building exactly that metric from both directions — Phase 1 produces
  accept/reject, and Phase 2 cycle 1 produces `context_processed`. "Did the
  packet work, and what did it cost" is precisely the signal a
  packet-construction optimizer would need, and we will have it before
  anything here is attempted.

  **Skepticism to carry in, all of it load-bearing:**
  - *Order matters.* The orchestration-cost experiment exists to measure
    whether handoff packets pay for themselves **at all**. If they don't,
    optimizing them optimizes the wrong thing. This comes after that
    baseline, never before it — and that baseline is itself now deferred out
    of Phase 2, so this sits two decisions away, not one.
  - *A trainset of one is overfitting, not optimization.* There is currently
    one task (AgentClinic Phase 1). DSPy optimizers need examples to compile
    against; a second real workload is a prerequisite, not a nicety.
  - *RLM adds a REPL/tool loop* — orchestration machinery, the exact class
    `BRIEF.md` says "every hang and timeout lived here." Cycle 12's hang
    tolerance would need to cover it.
  - *Both add a dependency and vocabulary.* Neither `RLM` nor `DSPy` enters
    the concept budget unless promoted to a cycle.
- Authoring scaffold for future acceptance suites (phase 2+): stub test
  functions named for the fact they prove, `raise NotImplementedError`
  bodies, a model fills in from owner-dictated bullets, owner reviews by
  tracing each assertion back to its bullet. Not needed for phase 1 (its
  suite already exists, human-authored).
- Which AgentClinic roadmap variant (implementation-detail vs. user-story)
  a model should build from — i.e. *does a spec's abstraction level change
  what a small model can build?* **Promoted to cycle 6 by the 2026-07-30
  re-plan; that promotion is withdrawn.** It is a discovery question, and
  Phase 1 is explicitly a reproduction milestone — `BRIEF.md`: "reproduce a
  number we already trust, not to discover one." With that framing there is
  no choice to make: reproduction uses the document the trusted number was
  produced against, which is the detailed variant. Cycle 6 transplants;
  it does not choose.

  Evidence gathered while the question was (wrongly) live, worth keeping so
  the experiment starts from it rather than re-deriving it — all from
  `user-story-batch`'s
  `docs/section-3-sdd/research/2026-07-29-user-story-workload-is-not-substitutable.md`,
  which carries a PENDING RULE 8 REVIEW banner and is not citable prose:
  - Phase 1, n=16, same model and Pi version this reboot uses: detailed
    spec 16/16 (reproducing the published 15/16); user-story spec 1/16
    bare.
  - The cause is narrow, not a general property of user-story framing. The
    Phase 1 suite's only structural coupling is `from app import app`; the
    detailed spec states it ("Create `app.py` with the FastAPI application
    instance"), the user-story variant never names `app.py`, FastAPI, or
    even that this is Python. Supplying that one fact separately recovered
    the arm to 15/16 — but that recovery is flagged post-hoc in the source,
    "a lead for a pre-registered replication, not a confirmed result," and
    the replication was never run.
  - The generalizable hazard, worth applying to any future suite: **grep a
    spec for the facts its acceptance suite imports.** Anything the suite
    reaches for that the spec never states is a silent dependency.

  Revisit as a deliberate experiment once a trusted number is in hand —
  not during Phase 1.

  **Pulled forward to phase 5 cycle 2, 2026-08-04, with its condition met.**
  The trusted number is in hand: Phase 1 closed at 16/16 and Phase 2 made the
  environment honest. The question also changes shape here, and the change
  matters. This entry framed it as *which* variant a model should build from —
  a choice between two task specs. Phase 5 keeps both, because they measure
  different things: the detailed variant is saturated and can only answer what
  an improvement **costs**, and the user-story variant has the headroom to
  answer what it **buys**. The evidence recorded above stays exactly as
  useful, and its generalizable hazard — *grep a spec for the facts its
  acceptance suite imports* — becomes a build step in cycle 2 rather than a
  note, since the user-story suite needs its own acceptance file and the
  1/16-vs-15/16 gap in the prior series was caused by one such silent
  dependency.
- Acceptance-suite rules beyond human-authorship (cumulative,
  contract-vs-implementation, non-vacuous, naming convention) — untouched,
  each needs its own argument when it becomes relevant.
- **Out-of-process suite execution. Still Backlog — promoted to a Phase 1
  cycle on 2026-07-31 and withdrawn on 2026-08-01.** Acceptance grading
  trusts a same-process signal a model can forge. A model-authored
  `app.py` can read the results-file path from the environment it shares
  with `harness/grading_plugin.py` and write forged `nodeid<TAB>outcome`
  lines and a completion marker straight into the results file. No
  in-process secret closes it — anything the plugin can read, model code
  sharing its process can read too. Scoped out of cycle 4 by explicit
  decision, not oversight (see that cycle's design doc, "Out of scope for
  this cycle").

  **Research done during the brief promotion, worth keeping — it is
  expensive to re-derive and one half of it is counter-intuitive.**

  *The obvious fix does not work.* Running the app in a separate process
  with `SATYRN_GRADE_RESULTS_PATH` scrubbed does **not** close this. The
  app subprocess globs `$TMPDIR/satyrn-grade-results-*.txt` — the prefix
  is a literal in `grading.py` — and forges a pass, because it runs as
  the same UID that owns the `0600` file. Demonstrated directly, not
  argued: a broken solution graded as `accepted`.

  *What does work, also demonstrated.* Hold the results file's fd, unlink
  its path immediately so nothing is on disk to find, and pass the fd
  only to the trusted pytest process via `pass_fds`. The hostile
  subprocess then found zero glob candidates, no `SATYRN_*` variables,
  and no writable inherited fd, while the real outcome came through
  intact.

  *It is all-or-nothing.* The fd fix only works **after** out-of-process
  execution — in-process, model code reads the fd from its own process
  table or introspects `sys.modules` for the plugin. There is no cheap
  partial version.

  *Two further design findings.* Once the suite talks HTTP, the pytest
  process needs nothing model-written, so the grading directory can split
  into an `app_dir` (allowlisted files) and a `suite_dir` (suite only),
  making the pytest process model-free by construction — and closing an
  unnamed vector where `app.py` could read `test_acceptance.py` at import
  time and craft responses against its literals. Feasibility confirmed
  against real uvicorn subprocesses: `reference` serves 200 with the
  tagline, `broken` serves 404 despite having no `templates/`, both from
  a directory containing no acceptance suite.

  **Why it was withdrawn.** Ranked by severity-if-exploited rather than
  expected value. Forging requires a 12B model to know a grader exists,
  its filename prefix, and its file format — none of which is in the task
  spec it receives. The fidelity case was overstated for *this* suite,
  which asserts a 200, a substring, two links, and a doctype, and touches
  none of where `TestClient` actually diverges from a live server. And
  the acceptance suite is the measuring instrument that produced the
  trusted number: rewriting it during a reproduction phase, at the cost
  of a sixteen-run re-baseline, is the move cycle 6 refused for a single
  bullet of the task spec.

  **What would make it worth building.** Contributors writing suites for
  arbitrary workflows, where the grader's trustworthiness becomes
  load-bearing for a claim someone acts on; a suite that genuinely needs
  real-server semantics (lifespan, streaming, websockets, middleware
  ordering); or models strong enough to reason about their own evaluation
  environment. A natural Phase 2 candidate alongside telemetry. The
  withdrawn cycle-14 design doc
  (`docs/superpowers/specs/2026-08-01-phase1-cycle14-live-server-execution-design.md`)
  is kept as the starting point.
- **Move environment setup out of the model entirely — a venv agent, and
  taking the ability away from everyone else.** Raised by the owner
  2026-08-05, after cycle 11 measured **28 child `pip install` invocations
  against the undelegated arm's 2**, for the same output-token total and
  1,416 more seconds of wall clock. Cycle 13 answers that with a sentence in
  the stack prompts ("already installed and importable, do not install
  anything"), which is the cheap version and may be enough.

  The idea beyond it is structural: one specialist owns 100% of the
  environment, and `pip`/`uv`/`venv` are **denied to every other agent** —
  enforcement rather than instruction, which is the pivot's premise and the
  thing a `tool_call` hook can actually do. It is attractive because the
  failure it removes is one no prompt can reliably prevent: a model that
  believes its environment is broken will keep trying to fix it.

  **Deliberately not scheduled, and the owner's own framing was "maybe,
  maybe not."** Three things must land first. (1) See whether cycle 13's
  sentence already removes the cost — if `pip` calls go to ~zero, a
  mechanism buys nothing on this workload. (2) A denial has a failure mode
  the instruction does not: when a package genuinely *is* missing, an agent
  forbidden to install it cannot recover, so the guard needs a real escape
  hatch before it guards anything. (3) It only pays where environment setup
  is a real part of the task, and this suite's is pre-built — so it belongs
  with a harder workload, not this one.

- **Interleave runs across arms within a batch — every wall-clock number
  this project has published is biased, not merely noisy.** Found 2026-08-05
  when the owner noted unrelated load on the machine mid-batch. The harness
  runs each arm as one contiguous block, so any drift in machine conditions
  falls entirely on whichever arm was running and presents as an arm effect.
  It is not hypothetical: **cycle 10's own batch swings 3× internally**
  (runs 7–9 at 3.7–4.6 tok/s, runs 10–16 at ~13.5), and cycle 13's rerun
  drifted monotonically from 27.3 to ~15 tok/s. Cycle 11's "1,416 more
  seconds" finding was withdrawn on this basis.

  The fix is to interleave: run arm A run 1, arm B run 1, arm A run 2, and
  so on, so drift becomes noise on both sides instead of bias on one. The
  model server is single-threaded, so this costs nothing in throughput — it
  is purely a change to run order.

  **What makes it non-trivial**: `run_batch` resumes by counting valid lines
  in one checkpoint per arm, so interleaving means either one checkpoint
  carrying an arm label per record, or coordinated resume across several
  files. The resume semantics are load-bearing and were hardened in phase 1
  cycle 11, so this is a real change rather than a loop reordering.

  **A precondition for any future timing claim.** Counts — turns, context,
  executed tool calls — are unaffected and remain citable. Timeouts sit in
  between: a timeout is a count, but the cap it counts against is wall
  clock, so a contended machine manufactures them.

## Prior work

The pre-restructure project lives on the `user-story-batch` branch, untouched.
Nothing there is imported here except by an explicit phase decision.

## Workflow

`restructure` is this reboot's trunk — `main` stays untouched until the whole
reboot is ready to replace the old project. Starting with cycle 2, each
feature cycle branches from `restructure` and merges back to it, never to
`main`.
