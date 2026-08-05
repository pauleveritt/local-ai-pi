# Roadmap

*Phases group feature cycles. One direction at a time. Tangents go to the
Backlog, not into the current phase.*

## Now

**Phase 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine.
Complete.** One run, hermetically graded, recorded to a checkpoint; then
n=16 reproducing ~15/16 — the supervised batch accepted 16/16. The engine's
first job was to reproduce a number we already trust, not to discover one —
see `BRIEF.md` for why.

**Phase 2 — Measurement we can trust, cheaply enough to repeat.
Complete.** Phase 1 measured whether generated code can be *trusted*; it
says nothing about speed, cost, or effort. Four cycles: the instrument
(`harness/telemetry.py`), its precision characterized against a real
baseline, an honest environment and a clean re-measurement, and the
discipline that keeps the numbers trustworthy.

*(The affordability target was retired by the phase's own findings,
2026-08-02, and this paragraph is corrected accordingly rather than
rewritten. It previously read: "What Phase 2 pursues from here is making
measurement trustworthy and affordable: a slice small enough that n=100 is
practical." Two cycles' evidence dissolved that. Cycle 3 found the friction
that dominated turn-count variance was environmental, and that fixing it
attacks the required **n**, not the per-run cost — a defensible clean claim
needs roughly 30–48 runs, not 100+. The cheaper task slice that the n=100
framing existed to motivate was withdrawn twice, most recently by cycle 3's
spec. What the phase actually delivered is the first half of that sentence:
measurement you can trust. The second half turned out to be answering a
question nobody had asked yet.)*

**Phase 3 — Build the extension half. Complete.**
Cycle 1 made the project's Pi extension observable — an entry it appends now
reaches captured stdout and the telemetry reader. Cycle 2 teaches the
mechanics and records the gotchas.

*(Corrected 2026-08-03. This paragraph previously said Phase 2 "closes having
paid its debts" to Phase 3 because `read_telemetry` counts delegations and
cycle 3's honest environment supplies "the clean baseline an orchestrated arm
gets compared against." That described a phase that was going to run an
orchestrated arm. Phase 3 is not: its orchestration cycles were withdrawn to
the Backlog. Those Phase 2 assets are real and still useful — they are simply
owed to the deferred orchestration-cost experiment, not to this phase.)*

*(Withdrawn framing, kept for the record — corrected 2026-08-02. An earlier
pass, written at cycle 1's close, gave Phase 2 three steps: "step 1 builds
the instrument; step 2 brings back a hello-world Pi extension teaching
lifecycle events and `appendEntry`; step 3 begins incremental orchestrator
work." Two things were wrong. Step 2 described as future work something
that already exists and is load-bearing: `.pi/extensions/hello-world.ts`
was transplanted in cycle 8 and is wired into every Pi invocation as
isolation plumbing (`harness/runner.py`, `docs/setup.md`) — it never left,
and teaching the extension API is a separate concern that need not precede
anything here. Step 3 is withdrawn from Phase 2 by owner decision: **the
orchestrator is not being built in this phase.** The handoff-packet cost
claim that satisfied the telemetry gate remains real and worth testing, but
its experiment is deferred — see the Backlog. The prose was also written
without checking the repository, the same drift the concept-budget note
below diagnoses in itself.)*

*(Superseded framing, kept for the record: an earlier pass named Phase 1 "the
restructure spec" — define the volunteer reader, then derive a section
structure for them. That's a real question, but it's downstream of having a
working engine and real suites to write about; it isn't Phase 1's job. See
`BRIEF.md`, "First decision for the new session.")*

**Phase 4 — Prove the engine generalizes beyond one workload.
Complete.** Three phases built the engine against a single workload, so the
parameters standing where hardcodes used to be had exactly one caller
apiece — which `BRIEF.md` names as the one thing that actually cost the
previous project. Cycle 1 added a second suite and demonstrated the spec
and grading seams with a real second caller.

*(Closed 2026-08-04 at one cycle. The phase's claim — two suites through one
code path, each grader floor-proven — was delivered whole by cycle 1, and
stretching it across a third and fourth suite was judged thin: the seam is
either proved by a second caller or it isn't, and further callers buy
repetition rather than evidence.)*

**Phase 5 — The improvement loop.** Next. Four phases produced an engine
that measures one unmodified model against a fixed workload. Nothing in it
can yet express *"this run had something applied to it"* — so an idea about
how to steer a small model can be argued but not weighed. Phase 5 makes an
improvement a named, digested artifact the harness records, and runs the
loop once end to end: propose, measure against the unchanged baseline, keep
or drop. The orchestrator/implementer pair is improvement #1 and stays
optional; a contributor who finds SDD too formal is never obliged to adopt
it. The phase ends pointed at something installable — `BRIEF.md` promises "a
Pi extension (not a fork of Pi) plus an eval harness," and four phases have
built harness.

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
| 5 | The improvement loop | Make an improvement a named artifact the harness digests, then run the loop once end to end — what orchestration costs on a saturated workload, what it buys on one with headroom — and finish pointed at something installable | next |

### Phase 1 feature cycles

| Cycle | Summary | Spec | Plan | State |
|-------|---------|------|------|-------|
| 1 | Accept/reject fixture pair — known-good and known-broken AgentClinic Phase 1 solutions, proven by plain pytest | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle1-fixture-pair-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle1-fixture-pair.md) | Done |
| 2 | Workspace provisioning — `prepare_workspace` context manager copies a fixture into a fresh, git-initialized, disposable workspace; proven by an automated pytest test re-running cycle 1's accept/reject procedure through it | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle2-workspace-provisioning-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle2-workspace-provisioning.md) | Done |
| 3 | Verdict from a hook-written results file — grade by reading a file a pytest hook wrote, not pytest's exit code. Names the verdict type. | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle3-verdict-file-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle3-verdict-file.md) | Done |
| 4 | Subversion fixtures — fixtures that attack grading (`addopts = --collect-only`; import-time `os._exit(0)`), confirmed to defeat a naive exit-code grader | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle4-subversion-fixtures-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle4-subversion-fixtures.md) | Done |
| 5 | Refusal of model-written config — the grader refuses to certify a run whose workspace carries model-written `pytest.ini`/`.pytest.ini`/`pyproject.toml`/`tox.ini`/`setup.cfg`/`conftest.py`/`sitecustomize.py`, before pytest ever runs. Split from the original combined row (below) — the allowlist half needed evidence this half didn't. | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle5-config-refusal-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle5-config-refusal.md) | Done |
| 6 | AgentClinic task spec — transplanted **Phase 1's section only** of the detailed roadmap to `examples/agentclinic/specs/roadmap.md`, the document the trusted number was produced against, resolving a citation cycle 1's suite had carried since. Deliberately *not* a variant choice: see the Backlog note. Also fixed the grading regression the transplant made reachable. | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle6-task-spec-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle6-task-spec.md) | Done |
| 7 | Model-server liveness check — `check_model_server_alive` GETs `/v1/models` on the `omlx` server (`127.0.0.1:8001` default, a seam) and raises `ModelServerDown` on anything but a 200; proven against a stub HTTP server, not a real model, with two distinct down-modes (nothing listening; a completed exchange with a bad status) so the raise isn't just "catch anything." | [spec](docs/superpowers/specs/2026-07-31-phase1-cycle7-liveness-check-design.md) | [plan](docs/superpowers/plans/2026-07-31-phase1-cycle7-liveness-check.md) | Done |
| 8 | First real run — `run_agentclinic_phase1()` invokes `pi` against a fresh, literally-empty workspace, captures a diff against the workspace's initial commit, and grades hermetically via cycles 3–6's grader. The task spec is passed as `pi`'s prompt text, never placed in the workspace. **Actually run, live, against the real `omlx` server, once the harness code and three bugs invisible to fixture-only testing were fixed** (see below): the model built a working AgentClinic Phase 1 app and it graded `accepted=True, tests_executed=tests_expected=4, returncode=0`. | [spec](docs/superpowers/specs/2026-07-31-phase1-cycle8-first-real-run-design.md) | [plan](docs/superpowers/plans/2026-07-31-phase1-cycle8-first-real-run.md) | Done |
| 9 | Source allowlist — `grade()` now copies only allowlisted paths plus the acceptance file into a fresh grading directory and runs pytest there, instead of `cwd=workspace`. Closes the sys.path-shadowing threat by construction: a model-written `harness/` package or `pytest.py` is never copied in, so it can never be imported in place of the real thing. Proven with a verified-first exploit — a rogue `harness/grading_plugin.py` that crashed collection and leaked into `stderr` under the old code, confirmed inert after the fix. *(Corrected phase 4 cycle 1: this cell named the allowlist's contents as `app.py`, `templates` and called them a "default", and said "plus the suite". There is no default any more — `source_allowlist` is required, and each suite carries its own — and "suite" here meant the acceptance file, which is now what it is called.)* | [spec](docs/superpowers/specs/2026-07-31-phase1-cycle9-source-allowlist-design.md) | [plan](docs/superpowers/plans/2026-07-31-phase1-cycle9-source-allowlist.md) | Done |
| 10 | Checkpoint recording — `harness/checkpoint.py`'s `append_checkpoint`/`load_checkpoint` persist a `RunResult` per completed run as JSONL, resuming by position (the Nth valid line is run N). `load_checkpoint` tolerates a truncated final line (a process that died mid-write); `append_checkpoint` cleans up that same dangling fragment before writing its own record, so resuming more than once stays safe — a real corruption bug Fable's review caught before implementation, where the naive version would have concatenated onto the fragment instead. | [spec](docs/superpowers/specs/2026-07-31-phase1-cycle10-checkpoint-recording-design.md) | [plan](docs/superpowers/plans/2026-07-31-phase1-cycle10-checkpoint-recording.md) | Done |
| 11 | Corrective hardening — checkpoint append preserves complete final records and never rewrites valid prefixes; grading uses a controlled child environment; workspace setup is independent of hooks/global Git config and supports a literally empty workspace; missing proof regressions are added. | [spec](docs/superpowers/specs/2026-08-01-phase1-cycle11-corrective-hardening-design.md) | [plan](docs/superpowers/plans/2026-08-01-phase1-cycle11-corrective-hardening.md) | Done |
| 12 | Hang tolerance — Pi and pytest timeouts terminate their entire process groups, yield bounded rejected results with partial output, and let a later batch attempt continue. | [spec](docs/superpowers/specs/2026-08-01-phase1-cycle12-hang-tolerance-design.md) | [plan](docs/superpowers/plans/2026-08-01-phase1-cycle12-hang-tolerance.md) | Done |
| 13 | Batch contract — restore the trusted Pi invocation shape, prove real model output before a batch, and record the conditions that make completed runs comparable. | [spec](docs/superpowers/specs/2026-08-01-phase1-cycle13-batch-contract-design.md) | [plan](docs/superpowers/plans/2026-08-01-phase1-cycle13-batch-contract.md) | Done |
| 14 | n=16 batch, sequential and resumable — target ~15/16; the supervised run completed 16/16 accepted with no rejected attempts. | [spec](docs/superpowers/specs/2026-08-01-phase1-cycle14-n16-batch-design.md) | [plan](docs/superpowers/plans/2026-08-01-phase1-cycle14-n16-batch.md) | Done |

### Post-Phase 1 corrective cycles

| Cycle | Summary | Spec | Plan | State |
|-------|---------|------|------|-------|
| 15 | Pi exit veto — a run remains diagnostically graded after Pi returns, but it is accepted only when Pi did not time out, Pi exited zero, and the grade is accepted. The recorded Phase 1 batch is unaffected: all sixteen Pi return codes were zero. | [spec](docs/superpowers/specs/2026-08-01-post-phase1-pi-exit-veto-design.md) | [plan](docs/superpowers/plans/2026-08-01-post-phase1-pi-exit-veto.md) | Done |
| 16 | n=16 batch evidence — a compact, committed [record](docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md) identifies the raw checkpoint and its measured conditions/results without committing 4.5 MB of model output. | [spec](docs/superpowers/specs/2026-08-01-post-phase1-batch-evidence-record-design.md) | [plan](docs/superpowers/plans/2026-08-01-post-phase1-batch-evidence-record.md) | Done |
| 17 | Local workspace hygiene — active linked worktrees and local agent state are ignored; nine old generated session files moved unchanged into the preserved old-project worktree after SHA-256 verification; the stale Sphinx static-path setting is removed so strict docs builds pass. | [spec](docs/superpowers/specs/2026-08-01-post-phase1-local-workspace-hygiene-design.md) | [plan](docs/superpowers/plans/2026-08-01-post-phase1-local-workspace-hygiene.md) | Done |
| 18 | Pages publication — restore the `main`-push Pages workflow with strict Sphinx, update the landing status, and leave a migration page at the old Section III URL. | [spec](docs/superpowers/specs/2026-08-01-post-phase1-pages-publication-design.md) | [plan](docs/superpowers/plans/2026-08-01-post-phase1-pages-publication.md) | Done |

### Phase 2 feature cycles

| Cycle | Summary | Spec | Plan | State |
|-------|---------|------|------|-------|
| 1 | Telemetry reader — `harness/telemetry.py`'s `read_telemetry()` derives turns, tool calls, and token counts from the JSONL `RunResult.pi_stdout` already captures. A pure function over a string: `runner.py`, `checkpoint.py`, and the batch are untouched, and nothing consumes the result yet. Proven against a real captured pi 0.82.0 stream, because the schema drifts across pi versions — the pre-restructure reader's 0.81.1 beliefs (no usage in `--mode json`; `isError` a string) are both false in 0.82.0. Three cases real data cannot reach are proven with inline synthetic streams. | [spec](docs/superpowers/specs/2026-08-02-phase2-cycle1-telemetry-reader-design.md) | [plan](docs/superpowers/plans/2026-08-02-phase2-cycle1-telemetry-reader.md) | Done |
| 2 | Precision baseline — `harness/precision.py` answers how many runs a claim needs before it's evidence: `bootstrap_ci_halfwidth`, `minimum_n_for_precision`, and a `leave_one_out_spread` stability diagnostic, proven against synthetic samples with known ground truth. Applied to a real n=48 sample (the preserved n=16 checkpoint plus 32 more runs executed specifically to extend it, after a jackknife check demonstrated n=16 wasn't yet trustworthy) — new turn-count values (10, 12) appeared that n=16 never showed, confirming the extension was necessary. Recommendation expressed in runs, not minutes, so it holds on any hardware. | [spec](docs/superpowers/specs/2026-08-02-phase2-cycle2-precision-baseline-design.md) | [plan](docs/superpowers/plans/2026-08-02-phase2-cycle2-precision-baseline.md) | Done |
| 3 | Honest environment, clean baseline — the 48-run baseline's turn variance was ~95% tool errors, all of it environment friction, and all 20 of its zero-error runs reached zero by never running a test. Two lines appended verbatim to the task spec state that dependencies are installed and that tests run with `python -m pytest`; `RunTelemetry.tool_errors` counts the friction. A fresh n=32 batch came back **0 errors across 203 tool calls, 32/32 accepted, and 32/32 actually running a test** — the fix works, and works without buying the old zero-error number by skipping verification. Cycle 2's record and Phase 1's teaching record are corrected: what Phase 1 provisioned was a git repository, not a working environment. | [spec](docs/superpowers/specs/2026-08-02-phase2-cycle3-honest-environment-design.md) | [plan](docs/superpowers/plans/2026-08-02-phase2-cycle3-honest-environment.md) | Done |
| 4 | Claim discipline — six derived-prose errors in a single day, none reachable by any existing test. `tests/test_research_records.py` diffs each research record's per-run table against its recompute script's committed output, so a published table cannot silently diverge from the committed output it claims to come from; `docs/sdd.md` gains "Checking a quantitative claim", four questions carrying the casualty list that motivates each. Cycles 2 and 3 backfilled: both published tables matched their scripts exactly, 48 rows and 32, and the audit found nothing — one clean audit is one data point, not evidence the gate has earned its keep. | [spec](docs/superpowers/specs/2026-08-02-phase2-cycle4-claim-discipline-design.md) | [plan](docs/superpowers/plans/2026-08-02-phase2-cycle4-claim-discipline.md) | Done |

**Cycle 2 spent nothing.** "Bootstrap," "confidence interval," "half-width," and "precision" are standard statistical vocabulary, not project-specific jargon. The check was run at close against the spec's explicit "Concept budget" section.

**The cycle spent six terms, not the four its spec budgeted.** The spec
authorised `telemetry`, `turn`, `tool call`, and `context processed`, and
called four "the largest single-cycle spend so far, worth stating plainly
rather than slipping through." Writing the Phase 2 framing at cycle close
then introduced `orchestrator` and `handoff packet` in prose without
checking them against the table — neither word appears anywhere in the
project before this cycle. ("Orchestration" did, but only in `BRIEF.md` as
the name of the trap being avoided, never as an actor; "packet" only as
`packet_context.py`, a transplant candidate rejected outright.) Both were
budgeted rather than quietly retained, on the grounds that they stated
Phase 2's central claim and the direction could not be read without them.

**That justification dissolved the same day.** The orchestrator experiment
was withdrawn from Phase 2 on 2026-08-02 and the direction rewritten without
either word, so both terms were retired unspent (see "Retired, not currently
spent" above). The episode is kept in full because it demonstrates the
failure mode twice over: prose introduced jargon the code never needed, and
then the jargon's own justification was a forward-looking plan that did not
survive contact with the owner. The lesson is the budget's own, sharpened —
it catches drift only when the check runs at *close*, against prose as well
as code, and a term justified by a *plan* rather than by working software
is exactly the kind that gets retired a day later.

**Cycle 3 spent nothing, and the check was run at close against the prose.**
That is the correction cycle 2's episode above demands, so it is recorded
rather than assumed. `tool_errors` aggregates *tool call* and its `is_error`,
both already in the table. "Environment" is used in its ordinary sense and
names no mechanism. Two candidates were considered and rejected: `ran_a_test`
and *support coverage*. The first is a helper inside one research script, the
same status as cycle 2's `message_span`, which was also not budgeted; the
second is ordinary statistical usage that cycle 2's record already used in
prose. Neither is vocabulary a contributor must hold to read the design.

**Cycle 4 spent nothing.** "Claim", "check", and "gate" are used in their
ordinary senses; the two artifacts are named literally
(`tests/test_research_records.py`, `*-recompute-output.txt`). The check was
run at close against the spec, the `docs/sdd.md` section, and the roadmap row.

### Phase 3 feature cycles

*Phase 3 is the first work on the half of the product `BRIEF.md` names and
neither prior phase has touched: **"a Pi extension (not a fork of Pi) plus
an eval harness."* Phases 1 and 2 built the harness. `.pi/extensions/hello-world.ts`
had, until cycle 1 of this phase, exactly one commit in its history —
cycle 8's transplant — and was loaded
on every run only as isolation plumbing.*

**The prior project already built this, and its specs survive.** The
pre-restructure worktree carries a complete, approved spec and plan at
`.worktrees/pre-restructure/docs/section-1-hello-agent/` (spec 170 lines,
plan 486, chapter 222), where the hello-world extension was SP0 / Part I of
a course. Per `BRIEF.md`'s gardening rule these are *candidates*, read and
argued on their merits, not a manifest — and cycle 1 starts with
brainstorming, not with a copy.

**Two findings from reading that prior work, verified against the installed
package, that shrink Phase 3 considerably:**

- **Pi ships a complete subagent extension** at `examples/extensions/subagent/`
  (verified present: `index.ts` 34 KB, `agents/`, `prompts/`). It calls
  `pi.registerTool(…)` and spawns a real child with
  `["--mode","json","-p","--no-session"]`. The prior project's own dated
  review correction records the consequence: the work is **not** rebuilding
  it, it is *specialization* — an `implementer` specialist as data
  (`.pi/agents/<name>.md`) plus an orchestrator prompt.
- **A delegation is therefore a tool call, and the child is `pi --mode json`.**
  Both are shapes `harness/telemetry.py` already reads. Phase 2 cycle 1
  excluded parent/child attribution as "unmeasurable today — Pi is invoked
  once, bare, with no delegation"; this is the path that makes it
  measurable, using the instrument already built.

**A finding of our own, and the reason cycle 1 is not a file copy.** The
extension file here is **byte-identical** to the prior project's. But it is
**inert in the harness's invocation mode**: zero custom entries appear in
any recorded run. The cause is subscribe ordering. Print mode wires its
json-mode subscriber only *after* `bindExtensions()` returns
(`modes/print-mode.js:50, 80`), and `bindExtensions()` emits `session_start`
before returning (`core/agent-session.js:1761`, in installed 0.83.0) — so the
`entry_appended` our `session_start` handler produced was emitted with no
subscriber attached and dropped, irrecoverably (`core/agent-session.js:285-289`).
`--print` does leave `ctx.ui.notify` no TUI
(`core/extensions/runner.js:88-92`) — print mode passes no `uiContext` to
`bindExtensions`, so `setUIContext(undefined)` falls back to `noOpUIContext`;
the operational half of the original claim was right. Every one of the 80
recorded runs loaded seven handlers that produced nothing observable.

*This paragraph previously attributed that silence to `--no-themes`. The
conclusion held, but the cause did not: `--no-themes` governs theme discovery
only (`cli/args.js:258`), and `notify` would be silent under `--print` with
themes fully enabled. The four-hop chain is gotcha 9 of
`docs/superpowers/research/2026-08-03-phase3-cycle2-pi-gotchas.md`.*

*This paragraph previously attributed the inertness to `--no-session` leaving
`appendEntry` nowhere to write. That claim was justified by reading, not by a
run; it was wrong — `appendCustomEntry` stores into an in-memory map and disk
persistence is a separate step (`core/session-manager.js:820-831`) — and it was
retired when a run disagreed with it. Cycle 1's gating spike moved the call to
`agent_start` and the entry reached stdout, captured at
`tests/fixtures/pi-run-0.82.0-entry-appended.jsonl`. See
`docs/superpowers/research/2026-08-02-phase3-cycle1-event-vocabulary.md`.*

Cycle 1's real question is what an extension *can* emit in the mode we
actually run.

| Cycle | Summary | State |
|-------|---------|-------|
| 1 | Observable extension — establish what an extension can emit under `--print --mode json --no-session`, and get one piece of evidence to travel extension → captured stdout → `read_telemetry`. Transplant the prior chapter/spec as the teaching artifact, with a drift audit: the prior spec's `appendEntry({type, data})` is already stale against the installed `appendEntry(customType, data?)`. This row previously claimed that changing the extension changes run conditions because `RunConditions` records its path. It did not: `RunConditions` recorded only the path, never the contents, so editing `hello-world.ts` left the conditions byte-identical and `run_batch` would have resumed a checkpoint recorded under a different extension. That gap is closed by this cycle's new `RunConditions.extension_digests` — a SHA-256 per extension file — and only from that point is the claim true. | Done |
| 2 | Extension mechanics, and the gotchas we paid for — teach how a Pi extension actually works, using `hello-world.ts` and Pi's shipped subagent extension read as a worked example, plus one small teaching extension of our own that registers a tool. Record the gotchas this project has already paid to find. **No orchestrator, no delegation in the harness, no harness changes at all.** [spec](docs/superpowers/specs/2026-08-03-phase3-cycle2-extension-mechanics-design.md), [plan](docs/superpowers/plans/2026-08-03-phase3-cycle2-extension-mechanics.md) | Done |
| corrective | Pi version pin — `EXPECTED_PI_VERSION` in `harness/runner.py`, and `run_batch` raises `RuntimeError` when the installed Pi differs, so two contributors' batches cannot be silently compared across an upgrade. Prompted by Pi moving 0.82.0 → 0.83.0 *during* a working session: every mechanism survived, eight `file:line` citations in a published chapter did not, and no test can check a citation. One constant and one comparison, reading a value `_conditions()` already shells `pi --version` for — batch-scoped, with no override, so a bump is a one-line commit that leaves a record. A single run is unaffected; the suite skips when Pi is absent and fails on a *different* version, which is the drift alarm. [spec](docs/superpowers/specs/2026-08-03-pi-version-pin-design.md), [plan](docs/superpowers/plans/2026-08-03-pi-version-pin.md) | Done |

**Cycle 1 spent nothing.** No new project-specific terms were introduced. The cycle makes `extension_digests` a `RunConditions` field (a technical detail, not a design concept) and parses `entry_appended` events into a `RunTelemetry` tuple — both use existing vocabulary. The check was run at close against the spec, code, and design artifacts.

**Cycle 2 spent one term: `gotcha`.** The cycle introduces the gotchas record as a primary teaching artifact, documenting ten non-obvious Pi behaviors this project discovered at a cost. The term names a pattern worth holding: expensive-to-find, invisible-in-documentation findings that need their price recorded so they are remembered. It appears 20 times in shipped materials (chapters and research) as both a concept and a label. The research document explicitly organizes findings as gotchas. While used only in research/teaching, not in structural code, the pattern is load-bearing for explaining this project's hard-won insights about Pi — something a contributor must understand to read the chapters and design documents. Added to the table.

**The corrective cycle spent nothing.** `EXPECTED_PI_VERSION` is a constant name, not a concept a contributor must hold — the cycle names no new mechanism and reuses *batch*, *run*, and *conditions* exactly as the table already defines them. The check was run at close against the spec, the code, and this row.

**Cycles 3 and 4 were withdrawn from this phase, 2026-08-03.** They were
*parent/child telemetry* and *the handoff-packet cost claim*, and both are
orchestration experiments. They contradicted the Backlog entry that had
already deferred the orchestration-cost experiment out of Phase 2 — the one
recording that when it is scheduled it should be proved against **synthetic,
fake, disposable examples** rather than a real orchestrator or a real
multi-agent batch. The Phase 3 entry scheduled the opposite on the same day
that entry was written, and the two were never reconciled until the owner
challenged a cycle 2 design built on the Phase 3 side. Both now live in the
Backlog with the experiment they belong to. Phase 2 cycle 4's
claim-checking discipline still applies to whatever tests that claim.

**The fork was proposed and rejected, 2026-08-03.** The owner asked whether
to fork Pi's shipped subagent example and own it. The decision is no, on one
argument that would hold even if this roadmap had said the opposite: a fork
freezes our copy against a substrate that keeps moving — the example imports
from `pi-coding-agent`, `pi-tui`, `pi-ai`, and `pi-agent-core` — which is
the posture that has already bitten this project twice. Referencing the
shipped tree by path and digesting it into `RunConditions` instead means a Pi
upgrade changes the digest and `run_batch` refuses to resume, so drift
becomes loud rather than silent. The one thing a fork genuinely buys —
removing `parallel` and `chain` from the model-facing schema, which would
otherwise put several children on the single-threaded local model at once —
is bought more cheaply by a refusal check. A ~150-line own tool is in the
Backlog behind an evidence gate. Also worth recording: of the example's 1015
lines, ~410 are TUI renderers dead under `--no-themes`, so "fork the example"
and "write the small tool the example taught us to write" are different
proposals wearing one word.

**Cycles 1 and 2 are both done.** There is no cycle 3 or 4 in this
phase — they were withdrawn to the Backlog, above. This entry records the
prior art's location so a later session need not re-derive it. Any further
cycle in this phase still gets its own brainstorm → spec → plan.

**Why this order.** Cycles 3–7 build and prove the entire judging apparatus
*before* a model runs once — every one of them is provable against fixtures
with no model in the loop. That is deliberate: it means the ~15/16 at cycle
14 measures the model rather than the engine, which is the whole reason
Phase 1 was chosen for being boring (see `BRIEF.md`). Building the grader
after the first run would produce output with no trusted way to judge it.
Cycle 9 (the allowlist) is the one deliberate exception — it is judging
apparatus built *after* a model has run, because it is the one piece that
needs a model's actual output to be anything more than a guess. Cycle 10
(checkpoint recording) returns to the fixture-only pattern: its tests
construct a `RunResult` by hand and never invoke `pi` or the model
server, exactly like cycles 3–7.

Cycles 4-before-5, 6-before-8, and 8-before-9 follow cycle 1's precedent:
the artifacts that make a proof possible get their own cycle, ahead of the
machinery that consumes them.

**Current dependency order, corrected 2026-08-01.** The post-cycle-10
harvest originally placed workspace hardening after the batch. The deep
review demonstrated that a contributor's `core.hooksPath`, checkpoint repair,
and caller-controlled pytest settings can break or corrupt an otherwise valid
batch before it starts. Cycle 11 repairs those prerequisites first; cycle 12
then makes one timed-out attempt survivable; cycle 13 establishes the exact
conditions and real-output preflight for comparable runs; and cycle 14 is the
batch that consumes all three. The historical harvest notes below retain their
original cycle numbers only as a record of that superseded plan.

**The 2026-07-31 harvest re-plan.** After cycle 10 closed, a stocktake of
everything sitting in Deferred candidates and the Backlog turned three
items into cycles rather than leaving them to fall off the end of Phase 1
unaddressed: hang tolerance (new cycle 11, following the same
before-the-machinery-that-needs-it logic as cycle 1's precedent — the
n=16 batch is the machinery, hang tolerance is the artifact it depends
on), the n=16 batch itself (pushed from 11 to 12), and
`harness/workspace.py` hardening (new cycle 13, closing two bugs homeless
since cycle 2's review). Items deliberately *not* promoted: the
`pyproject.toml` reservation and `pi_stdout`/`pi_stderr`-on-timeout
capture are both evidence-gated with no evidence yet — forcing them into
a cycle now would be exactly the "machinery ahead of the contract it
serves" `BRIEF.md` warns against; the roadmap-variant experiment, the
phase-2+ authoring scaffold, and telemetry all stay in the Backlog
because they're Phase 2's business, not Phase 1's — see the Backlog
section.

**Correction, 2026-08-01: the harvest re-plan also promoted
out-of-process suite execution as cycle 14, and that promotion is
withdrawn.** It was ranked by severity-if-exploited rather than by
expected value against the actual threat, and "largest known gap" quietly
became "next thing to build." Three arguments against it, in ascending
order of weight. The threat is not live: forging a verdict requires a 12B
model to know a grader exists, know its filename prefix, and know its
`nodeid<TAB>outcome` file format, none of which appears in the task spec
it receives. The fidelity argument was overstated: `TestClient` diverges
from a real server on lifespan events, streaming, and connection
semantics, and Phase 1's suite exercises none of them — it asserts a 200,
a substring, two links, and a doctype. And decisively, the acceptance
suite *is* the measuring instrument that produced the trusted number;
rewriting it at the end of a reproduction phase, and paying a sixteen-run
re-baseline to get back to where we already are, is the same move cycle 6
refused for one bullet of the task spec. Phase 1 now ends at cycle 14.

**Post-Phase 1 correction, 2026-08-01.** Reviewing the completed batch
found one missing run-level condition: a nonzero Pi exit could coexist with
an accepted grade. Cycle 15 closes that gap without changing the grading
contract or discarding diagnostic evidence; the runner still diffs and grades
the workspace after Pi returns. It is deliberately outside Phase 1's feature
sequence because all sixteen historical records already have return code zero,
so the correction does not alter the reproduced result. The concept budget is
unchanged: it uses the existing terms *run* and *verdict* rather than naming a
new mechanism.

**Post-Phase 1 Pages publication, 2026-08-01.** Cycle 18 restores the
GitHub Pages workflow on `main`, gates deployment on a warning-free Sphinx
build, updates the landing page to Phase 1 complete, and leaves a migration
page at the old Section III URL. The concept budget is unchanged: this is
publication wiring and compatibility documentation, not an engine mechanism.

**Post-Phase 1 evidence record, 2026-08-01.** Cycle 16 records the raw
n=16 checkpoint's path at verification time, size, checksum, shared
conditions, and aggregate result in a committed
[research page](docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md).
The 4.5 MB raw JSONL remains outside Git and has not been archived externally;
the path is a reference, not durable storage. The concept budget is unchanged:
this preserves existing checkpoint evidence rather than adding a mechanism.

**Post-Phase 1 local workspace hygiene, 2026-08-01.** Publishing the orphan
history as `main` exposed active worktrees, local agent state, and generated
old-project session files in the root worktree. Cycle 17 adds only the two
general local ignore rules (`.worktrees/`, `.superpowers/`) and moves the
nine session files unchanged into the matching ignored path of the preserved
old-project worktree, verified by SHA-256 before and after. The concept budget
is unchanged: this is file placement and repository hygiene, not a new engine
mechanism. Cycle 17 also removed the unused `html_static_path` setting from
`docs/conf.py`; no custom static assets exist, and the strict Sphinx build now
passes without warnings.
The research survives in the Backlog entry — it is worth keeping and
expensive to re-derive.

### Phase 4 feature cycles

| Cycle | Summary | State |
|-------|---------|-------|
| 1 | A second eval suite — a stdlib-only duration parser under `examples/duration/`, so the spec and grading seams have a real second caller instead of a parameter with one caller and a workload-shaped default. Dissolves `PHASE_1`, `TASK_SPEC`, and `run_agentclinic_phase1` into a `Suite` descriptor; makes `grade()`'s `source_allowlist` required; makes `_conditions` hash the suite it was handed, which is load-bearing because `task_spec_sha256` is the only `RunConditions` field distinguishing two suites. Claims no number and runs no batch. [spec](docs/superpowers/specs/2026-08-04-phase4-cycle1-second-suite-design.md), [plan](docs/superpowers/plans/2026-08-04-phase4-cycle1-second-suite.md), [research](docs/superpowers/research/2026-08-04-phase4-cycle1-what-the-second-suite-cost.md) | Done |

### Phase 5 feature cycles

| Cycle | Summary | State |
|-------|---------|-------|
| 1 | The improvement mechanism — a frozen `Improvement` descriptor (seed directory, extra extensions, system prompt) and `run_batch(suite=…, improvement=…)`, with the orchestrator/implementer pair as improvement #1. Breaks `RunConditions` once rather than twice: the improvement digest plus the two digests the Backlog already owed (the acceptance file's contents, the allowlist), all sentinel-loading like `extension_digests`. Decides how a *directory* extension is digested, which `_extension_digest` explicitly deferred to "the cycle that needs it". Ends with one live delegation observed under this harness's flags. **Claims no number and runs no batch.** The spike found that `--extension` needs the entry-point *file*: pointed at the `subagent/` directory it fails silently and the run still grades accepted. [spec](docs/superpowers/specs/2026-08-04-phase5-cycle1-improvement-mechanism-design.md), [plan](docs/superpowers/plans/2026-08-04-phase5-cycle1-improvement-mechanism.md), [research](docs/superpowers/research/2026-08-04-phase5-cycle1-delegation-spike.md) | Done |
| 2 | The cost answer — two n=16 batches on AgentClinic Phase 1, bare and orchestrated, where success is expected to stay pinned and the only readable signal is turns and `context_processed`. The handoff-packet claim, tested with the instrument built for it. Every orchestrated run is checked for a *successful* delegation before its cost counts, because cycle 1 showed a silently unorchestrated run still grades accepted. Touches no suite. **Result: orchestration cost 8.24x the context, 2.57x the output and 3.29x the turns, and was less reliable — 12/16 against a bare 16/16, with three hangs where the bare arm had none, two of them after a correct solution was already written.** The handoff-packet claim is confirmed and not close. The pre-registered 16/16 for the orchestrated arm was falsified. Max concurrent children was 1 in all 16 runs, so the Backlog's own-subagent-tool gate did not fire. [spec](docs/superpowers/specs/2026-08-04-phase5-cycle2-cost-answer-design.md), [plan](docs/superpowers/plans/2026-08-04-phase5-cycle2-cost-answer.md), [research](docs/superpowers/research/2026-08-04-phase5-cycle2-cost-answer.md) | Done |
| 3 | Telemetry counts the delegated child — `read_telemetry` reads the parent's own events only, so a delegated run's turns and `context_processed` omit the arm's dominant cost. Cycle 2 published a wrong headline on exactly that, and the fix belongs in the instrument rather than in one research script. Pi's shipped subagent extension already surfaces the child's usage in the parent's `tool_execution_end` under `details.results[].usage`, so this is parsing that is already in the stream, not new measurement. Recomputes retroactively over every batch already banked, cycle 2's included. [spec](docs/superpowers/specs/2026-08-04-phase5-cycle3-child-telemetry-design.md), [plan](docs/superpowers/plans/2026-08-04-phase5-cycle3-child-telemetry.md) | Done |
| 4 | The user-story suite and its floor — the user-story roadmap variant as a third `Suite`, with its own task-spec file, its own known-good and known-broken fixtures, tests proving the grader accepts one and rejects the other, and `norecursedirs` / `extend-exclude` entries. Then the as-shipped orchestrator arm on it. Touches no mechanism. **Result: both arms 0/16 — a floor, not the headroom the phase needed.** Bare Pi read the spec, restated it accurately and stopped to ask what to do in all 16 runs, writing nothing; the orchestrator prompt restored agency (11/16 wrote files) but not correctness, and the arm thrashed — 15/16 runs repeating an identical tool call, six timeouts, one run at 261 turns. Also found and fixed a harness bug that let a model-created nested git repo abort a whole batch. [spec](docs/superpowers/specs/2026-08-04-phase5-cycle4-user-story-suite-design.md), [research](docs/superpowers/research/2026-08-04-phase5-cycle4-user-story-arms.md) | Done |
| 5 | Correct the orchestrator's instructions — prompt-only, no mechanism. `orchestrator.md` never names a `subagent` mode, so the model guesses: three cycle-2 runs and one cycle-4 run were answered `"Invalid parameters. Provide exactly one mode."` with no child running. It also never states that the workspace starts empty, which is the most economical account of both cycle-4 arms — bare Pi asked a human which file to begin with, orchestrated Pi ran `ls -R` 245 times looking for files that do not exist. A **correction to a demonstrably broken artifact, not a lever**: tuning from a broken baseline measures the wrong thing. **Result: parameter rejections 0/8 calls; the exploration spiral did not recur (runs with a repeated identical call 15/16 → 0/6, worst repetition 245 → 1, most tool calls in a run 261 → 7); acceptance still 0, as predicted.** The dominant failure moved to an unbounded child, which is cycle 6. Pilot only — n=6 at 300 s, not comparable with any published arm. [spec](docs/superpowers/specs/2026-08-04-phase5-cycle5-orchestrator-corrections-design.md), [research](docs/superpowers/research/2026-08-04-phase5-cycle5-orchestrator-corrections.md) | Done |
| 6 | The loop-breaker extension — the phase's installable artifact. Pi ships no turn cap, no loop detection and no tool-call budget, and upstream closed the requests pointing users at extensions (#1898, #5248, and #6158, which reports this exact scenario on a small quantized local model). `pi.on("tool_call")` returning `{block: true, reason}` is present in installed 0.83.0 (`docs/extensions.md:70-73`, verified). A ring buffer over `(toolName, args)` that trips on repeats **regardless of whether the call succeeded** — the property the local unmerged `pi-circuit-breaker` branch lacks, since it excludes successful repeats and so would not have caught 245 successful `ls -R` calls. **Result: built and proven live — a threshold-0 copy blocked every call and produced `loop_broken` entries in telemetry — and it never fired in the pilot, because cycle 5's prompt line had already removed the loop.** Replay over five banked batches: zero false positives in 55 healthy runs, 239 of 261 calls prevented on cycle 4's worst run. Its value is retrospective; it is insurance that has not yet been claimed on. [spec](docs/superpowers/specs/2026-08-04-phase5-cycle6-loop-breaker-design.md), [research](docs/superpowers/research/2026-08-04-phase5-cycle6-loop-breaker.md) | Done |
| 7 | The tech-stack lever, against a corrected and guarded baseline — the first lever proper. Prior evidence predicts supplying the technology stack moves the user-story arm off the floor; until something does, that suite discriminates nothing. One improvement, pre-registered. **Result: the suite stopped scoring zero — 5/6 grader-accepted and 4/6 run-accepted, after four arms at 0.** The lever was two facts: FastAPI, and `app.py` at the root. Every prior failure that reached the grader was `TypeError: Flask.__call__()` — a WSGI app driven by an ASGI test client — which corrects cycles 4 and 5, both of which had blamed file layout the acceptance file explicitly disclaims. The timeout comparison is unscored: the machine was ~40–60% faster for this pilot. [spec](docs/superpowers/specs/2026-08-04-phase5-cycle7-tech-stack-design.md), [research](docs/superpowers/research/2026-08-04-phase5-cycle7-tech-stack.md) | Done |
| 8 | The runaway child — the last known cause of a *correct* solution losing its run. Both cycle-7 timeouts were killed with the child still going at 98–103 turns, and the loop-breaker cannot reach it: a probe proved project-local `.pi/extensions/` is not loaded by a child-style invocation, with or without `--approve`. So this corrected the implementer prompt instead — stop re-running a command that fails identically twice — on the grounds that the mechanism was undeliverable and two previous prompt corrections had worked. **Result: three pre-registered predictions, three falsified.** Worst repeated command rose 93 → 178 and runs repeating a command ≥5× rose 2 → 3. The cycle aimed at the wrong loop: the repeats are *exploration* (`ls -R`, `ls -F`), not validation. The transferable lesson is that the two prompt wins supplied a **fact** and this one supplied a **rule of conduct**. Its real yield was the research it forced — see cycle 9. [spec](docs/superpowers/specs/2026-08-04-phase5-cycle8-child-runaway-design.md), [research](docs/superpowers/research/2026-08-04-phase5-cycle8-child-runaway.md) | Done |
| 9 | The hermetic child — **the delegated child has never been hermetic.** The parent runs with `--no-extensions --no-skills --no-prompt-templates --no-themes --no-context-files`; the child is spawned by Pi's shipped subagent extension carrying none of them, and user-scope resources load unconditionally, so every orchestrated arm this project has published ran its child with the operator's own `~/.pi/agent/extensions/` and packages — including `rtk.ts`, which rewrites bash commands. Confirmed in our own recorded transcripts, not inferred: the child's `ls -R` returns the output of `rtk ls -R`, reproduced byte-for-byte. `PI_CODING_AGENT_DIR` is the one seam that reaches the child, since the extension's `spawn` passes no `env` — so a harness-owned agent dir both removes the contamination and delivers the loop-breaker as a user-scope extension, which is the guard cycle 8 could not deliver. `RunConditions` gains `agent_dir_digest`. Affected records get correction banners. **Result: removing the contamination removed the runaway.** 5/6 run-accepted, 5/6 grader-accepted, **0/6 timeouts** where cycles 7 and 8 had 2 apiece, and every run terminated on its own. Worst repeated command across a pilot fell 178 -> 5; median run transcript fell 9.63 MB -> 0.49 MB and peak context 2.8M -> 91k. The loop-breaker refused zero calls -- there was nothing left to refuse -- though a threshold-0 copy proved separately that it does load in the child, which cycle 8 had concluded was impossible. [spec](docs/superpowers/specs/2026-08-04-phase5-cycle9-hermetic-child-design.md), [research](docs/superpowers/research/2026-08-04-phase5-cycle9-hermetic-child.md) | Done |
| 10 | One publishable arm — a single n=16 batch at the 600 s timeout on whatever configuration survives, comparable with cycles 2 and 4. The only number the phase publishes from here. **Runs on the hermetic configuration**: publishing an arm whose child loads the operator's toolbelt, after discovering that it does, is not defensible. **Result: 13/16 run-accepted and 13/16 grader-accepted, against cycle 4's 0/16 at the same n and the same timeout, with timeouts 6/16 -> 1/16.** Not attributable to the machine: cycle 10 ran ~16% *slower* (10.27 vs 12.24 tok/s). Median total turns 30 -> 14, median run transcript 2.65 MB -> 0.50 MB. The loop-breaker fired in the child for the first time in a live run -- 12 refusals across two runs, both of which still passed -- confirming at n=16 the prediction cycle 9 falsified at n=6. No run was killed with a child still calling tools. [research](docs/superpowers/research/2026-08-04-phase5-cycle10-publishable-arm.md) | Done |
| 11 | The control arms — cycle 10's headline was 13/16 against 0/16, but four changes separated those arms, so *orchestration works* and *we told it the framework* were not distinguishable. Two n=16 arms at 600 s on the hermetic config isolate them. **Bare: 0/16**, replicating cycle 4 — and more extreme than cycle 4 recorded: **15 of 16 runs made zero tool calls**, answering in prose, so the floor is a *stopped-to-ask* zero. **Facts-only: 15/16** — the empty-workspace fact and the `## Technology` section verbatim, nothing else, loop breaker kept so exactly one thing differs from cycle 10. **The two facts take the suite from 0/16 to 15/16 and orchestration's contribution is not distinguishable from zero** (15/16 vs 13/16 is Fisher p ≈ 0.6 — noise at this n, and not to be reported as a difference), while costing ~1.6× the turns and context and 1.9× the wall clock for the same 34k output tokens. The honest reading is that **this suite has no headroom left**, which is a statement about the workload, not a verdict on delegation. **The first attempt was withdrawn at 8 of 16 runs** because `stack.md` then carried only the Technology section and so differed from cycle 10 by *two* things; its checkpoint is kept as `...-PARTIAL8-withdrawn.jsonl`. **A retraction rides with this cycle**: its first reported cost figures were substring counts over the raw event stream, inflating each arm by a different factor (10.0× / 6.7× / 21.9×) because the subagent update protocol re-serializes the child's whole transcript per update. The real ratio is 1.33×, not 4.4×. [research](docs/superpowers/research/2026-08-05-phase5-cycle11-control-arms.md) | Done |
| 12 | The installable extension — the phase promised to end "pointed at something installable" and `BRIEF.md` promises "a Pi extension (not a fork of Pi) plus an eval harness." The loop-breaker is that extension and now has live evidence behind it: 12 refusals in the child across two cycle-10 runs, both of which still passed. But it appears in **no** user-facing document — not `README.md`, not `docs/index.md`, not `docs/setup.md` — and has no install instructions, so today it is an internal harness artifact rather than a product. Scope: what it is and the number that justifies it, how to install it into `~/.pi/agent/extensions/` or a project, what `WINDOW` and `THRESHOLD` mean and when to change them, and the one thing a user must know that we paid to learn — that a delegated child does not load your project's extensions, only your user-scope ones. No new mechanism. **Done:** [`docs/loop-breaker.md`](docs/loop-breaker.md), wired into the docs toctree, the README's "Start here" table and both landing pages, with three tests pinning the page to the extension — its constants, its verbatim refusal text, and the subagent paragraph — all mutation-checked. | Done |
| 13 | The pre-install sentence, and hardening the counting — cycle 11's largest clean signal was that the two arms emitted **the same output-token total to within 16 tokens** while the orchestrated arm spent **1,416 more seconds** producing it, with 28 child `pip install` invocations against the other arm's 2. Both stack prompts now state that FastAPI, Jinja2, pytest and httpx are installed and forbid installing anything — added to *both* so it is not a second variable, which is the mistake that withdrew cycle 11's first attempt. **The claim is true because a run inherits the harness's own environment through `pi_env()`**, and a test asserts it stays true from a directory that is not the repository, so the prompt cannot quietly become a lie. Prediction: child `pip install` calls fall to near zero and wall clock drops materially, with the accepted count unchanged at 13/16 ± noise. Also hardens the counting that cycle 11 got wrong: five tests over synthetic streams pin that a refusal echoed across five event types counts once, and that cumulative subagent updates do not multiply a child's call count. Both historical bugs — counting every event, and keeping only the final update — are mutation-checked as caught. | In progress |

**What the eight withdrawn runs bought, which was more than the arm they came
from — corrected 2026-08-05 by review.** The paragraph below first read the
three runs that had landed when it was written and concluded the model "fails
to stop". A recount of all eight gives **7/8 grader-accepted and 6/8
run-accepted**, with churn in only two runs and the single grading failure
caused by stopping *too early* — three tool calls, nothing written. Churn is
also present in the **orchestrated** arm at comparable amplitude (19x and 10x
`app.py` in cycle 10's children, both accepted), so the handoff packet's
definition of done does not prevent it either. The conclusion below is
withdrawn: at 7/8 against 13/16, orchestration's measured contribution once the
two facts are supplied is **indistinguishable from zero**, not termination.
The in-flight n=16 facts-only arm settles it. What survives is that the loop
breaker is the only intervention that has demonstrably arrested a runaway, in
all four churning runs across both arms.

**The original text, retained:** With the two technology facts and no orchestration, the model does not
fail to *build* — two of the first three runs were graded accepted. It fails to
*stop*. The dominant call in the longest run is the **same base template
written 27 times**; another repeats one `<nav>` edit 7 times. Across those runs
there is exactly one `ls -R`, so the old exploration spiral is gone and what
replaced it is **revision churn**. The orchestrated arm's handoff packet
carries Allowed Files, Acceptance Strings, Validation and "report and stop" —
a definition of done — and the control has none, because a user-story roadmap
has no terminal condition.

On this evidence orchestration's contribution is **termination, not
correctness**, which is a weaker headline than the phase assumed and the exact
claim `BRIEF.md` says the project is for. The loop breaker also earned its keep
here in a way it never had before: 22 refusals in one run, which still passed.
This is the material for the enforcement deep dive.

**Cycle 1 spent one term: `improvement`**, as budgeted above. `Improvement`,
`improvement_digest`, `pi_package_root`, and the `"<pre-phase5>"` sentinel are
type, field, and function names rather than concepts a contributor must hold.
The check was run at close against the spec, the code, and this row.

**What cycle 1 cost, and what it bought.** It bought the mechanism and one
finding that would have poisoned cycle 2 silently: pointing `--extension` at
the shipped extension's *directory* registers no tool, reports nothing on
stderr, exits 0 — and the run still grades **accepted**, because the parent
writes the solution itself once the delegation errors. Sixteen such runs would
have been labelled `improvement_name="sdd-orchestrator"` while comparing a
bare arm against a bare arm. That is the model-server hazard `docs/setup.md`
records, one layer over, and it is the argument for having split the mechanism
cycle from the batch cycle rather than bundling them.

It also cost three mutation checks that *survived* on first run — the
acceptance-digest deletion proving only that a field was required, a vacuous
ordering test, and a dropped `improvement` argument that left the suite green.
Each was answered by a new test rather than by an assumption. That is now the
third and fourth instance of one shape (test the collaborator, miss the
caller) since Phase 4 cycle 1, and it is worth a discipline cycle's attention
if it appears again.

**Cycle 2 spent nothing.** It runs batches with cycle 1's vocabulary and adds
no mechanism. The check was run at close against the spec, the recompute
script, and this row.

**What cycle 2 settled, and what it did not.** It paid the debt open since
Phase 2 cycle 1: the handoff-packet claim has now been tested with the
instrument built for it, and it is **confirmed, by roughly 8x in context and
2.5x in generation**. The orchestrator itself is frugal — fewer turns, a third
less output — but the implementer child it delegates to ran a median 16 turns
and ~113,000 extra tokens behind a single packet. Reliability points the same
way: 12/16 against 16/16, three hangs against none, two of them *after* a
correct solution was already written. It settles nothing about keeping a model
on track, since the bare arm on this workload does not thrash — that is the
Backlog's thrash-metrics entry, and it needs a workload with headroom.

**The record was corrected the same day, and the correction is the more useful
lesson.** Its first version counted only the parent's tokens and reported the
orchestrated arm as *cheaper* — 1.15x context, 0.69x output. Pi's shipped
subagent extension surfaces the child's usage in the parent's
`tool_execution_end` under `details.results[].usage`, and
`harness/telemetry.py` reads the parent's own events only, so a delegated
run's telemetry silently omits the arm's dominant cost. Cycle 2's own spec had
written "the parent's `tool_execution_end` carries what this question needs"
and then not read it. The error surfaced only because the owner asked an
unrelated question — whether machine contention explained the numbers — which
is a thin thread for catching a wrong headline claim.

**Cycle 3 spent nothing.** `Delegation`, `child_*` and `total_*` are type
and field names, not concepts a contributor must hold, and the pinned term
*turn* is unchanged — parent-only fields keep their meanings so every number
published before the cycle stays valid. Two of its four mutation checks
misbehaved and both were repaired rather than waved through: one silently
failed to apply, and one left the suite green because the guard it targeted
was untested speculation. The check was run at close against the spec, the
code, and this row.

**Re-planned 2026-08-04, after cycles 2 and 4 and an adversarial audit.**
The phase was going to spend cycles 5+ pulling levers. It now spends them
making the orchestrator *usable first*, because the audit established the
baseline is broken in three named, cheap ways rather than broadly weak: it is
never told the tool's mode, never told the workspace is empty, and has no
guard against repetition. Two are prompt lines and one is an extension. The
target the owner set for the phase is to emerge with **a useful baseline
orchestrator rather than an unusably broken one**, and levers pulled before
that would be tuning against noise.

Worth keeping in view: the orchestrator is *not* uniformly broken. On the
detailed roadmap it delegated on 15 of 16 runs and produced solutions the
grader accepted 12 times. It falls apart on a spec that names no files, which
is a narrower and more fixable problem than cycle 4's 0/16 first suggested.

**Why this order, revised 2026-08-04 after cycle 2.** Cycle 1 touches no
suite, cycle 4 touches no mechanism, and cycle 2 sits between them producing
the phase's first number, so no cycle can hide a defect in another. Cycle 3
was inserted after cycle 2 closed: the instrument cannot see a delegated run's
dominant cost, and every future orchestrated batch would carry the same trap.
It goes before the suite work because it is small, because it recomputes
retroactively over evidence already banked, and because the alternative is
discovering the same omission a second time on a workload that matters more.

**Cycle 7 spent nothing**, and produced the phase's first non-zero result on
a workload with headroom. What remains open is the hang: the unbounded child
is untouched by cycles 5–7 and is now the only known cause of a *correct*
solution failing its run.

**Cycles 5 and 6 spent nothing.** `sdd-orchestrator-guarded` is an
improvement instance, not a concept; the loop breaker's window and threshold
are constants. Cycle 6 also produced the phase's first artifact a contributor
could install on its own — `.pi/extensions/loop-breaker.ts` depends on no part
of this harness.

**Cycle 4 spent nothing**, and changed what cycle 5 is for. Two arms at zero
discriminate nothing, so the user-story suite is not yet a usable instrument:
cycle 5's first lever is what moves it off the floor, not optional polish
afterwards. The check was run at close against the spec, the code, and this
row.

**How these cycles get tested, because 88 minutes a batch is the real
constraint.** Cycle 4's orchestrated arm cost ~88 minutes, of which **60 were
the six hangs sitting out a 600 s timeout**; the runs that work are cheap,
half finishing inside 71 s (p50 70.9 s, p90 226 s, over all 55 completed runs
banked so far). Four measures, cheapest first:

- **Replay over banked streams.** Anything derivable from a recorded run
  needs no model at all. Cycle 6's detector is pure logic over
  `(toolName, args)` sequences, and four batches retaining full `pi_stdout`
  are already on disk — *would it trip, on which call, and would it have
  stopped run 1 at call 6 instead of 245?* Zero model time, real data, and
  the same replay is the regression suite.
- **Static assertions.** Cycle 5's mode fix is partly a property of a file:
  assert `orchestrator.md` names a mode the shipped schema accepts. That
  catches the "Invalid parameters" class in milliseconds, rather than in a
  batch discovered weeks later — which is how it *was* found.
- **Pilots at n=6, `run_timeout=300`.** Worst case 30 minutes, typically
  12–15, enough to see a gross effect: rejections 3→0, files written 0→n,
  loop tripped or not. Stated honestly: 4 of 55 completed runs exceeded
  300 s, so a shorter cap inflates the apparent hang rate, and `run_timeout`
  is part of `RunConditions` — **a pilot is never comparable with an n=16
  arm and never published as the number.**
- **One-run smokes.** Phase 5 cycle 1's spike caught the `--extension`
  directory bug for the price of a single run. Any prompt or extension change
  gets one before a pilot.

The 600 s timeout stays on published arms. Cycle 4's hang rate is a finding,
and shortening the cap there would quietly manufacture a better-looking one.

**The levers stay later, deliberately.** The orchestrator prompt, the packet
format, and the implementer specialist all have obvious knobs, and cycle 2
makes it tempting to start turning them. That would be tuning on a workload
where bare Pi already scores 16/16 — the best reachable outcome is parity with
doing nothing, at eight times the cost. Orchestration is not supposed to earn
its keep on a task the model already passes. The knobs get pulled in cycle 7,
against the arm where bare Pi fails, where an improvement can demonstrate
benefit rather than minimise damage. Mechanism before batch follows Phase 4 cycle
1's precedent of a cycle that claims no number: a batch costs a cross-session
commit freeze and hours of sequential wall time, and discovering a mechanism
defect after paying that is the expensive order. The cost arm precedes the
benefit arm because it needs nothing new — AgentClinic Phase 1 is already in
the repository with its grader floor proven — while a suite with headroom is
real work, and no number from it is citable until its fixture pair and their
tests exist.

**Every prior number is a prediction here.** Cycle 1's spec pre-registers, in
advance of the mechanism existing, that cycle 2 finds 16/16 on both arms with
higher `context_processed` on the orchestrated one; cycle 3 pre-registers
~1/16 with wrong-framework as the dominant failure mode. Those come from a
series carrying a `PENDING RULE 8 REVIEW` banner; replicating or falsifying
them is the point, and none may be written as a result before its batch runs.
A null result on the cost claim is as publishable as a positive one.

**One observation rides along in cycle 2.** The Backlog gates building our
own minimal subagent tool on "a measured run shows the shipped extension
contaminating or losing a measurement" — the shipped extension can put
parallel children on a single-threaded local server. Cycle 2 is the first
measured orchestrated batch this project has ever run, so it records whether
that happens. If it fires, the gate opens and the ~150-line tool is the
honest path to something installable.

### Deferred candidates

*Things a cycle's brainstorming considered and passed over — usually the
"smallest choice" between two real options. Tracked here, updated at the
end of each cycle, so the next brainstorming session starts from this list
instead of re-deriving it from old specs.*

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

## Prior work

The pre-restructure project lives on the `user-story-batch` branch, untouched.
Nothing there is imported here except by an explicit phase decision.

## Workflow

`restructure` is this reboot's trunk — `main` stays untouched until the whole
reboot is ready to replace the old project. Starting with cycle 2, each
feature cycle branches from `restructure` and merges back to it, never to
`main`.
