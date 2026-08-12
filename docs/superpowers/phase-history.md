# Phase history: Phases 1–5

**Complete phases, moved here from `ROADMAP.md` on 2026-08-12 so the roadmap
could stay a planning surface rather than an archive.** Nothing was rewritten,
summarized, or dropped in the move — including the withdrawn framings,
retracted figures, and corrections this project records with a banner rather
than an edit. Those are the most instructive part of the record and are
reproduced verbatim below.

For what the project does *now*, see [`../../README.md`](../../README.md) and
[`../architecture.md`](../architecture.md). For current planning, the concept
budget, and the backlog, see [`../../ROADMAP.md`](../../ROADMAP.md).

## Phase narratives


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

**Phase 5 — The improvement loop. Complete.** Four phases produced an engine
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

*(Closed 2026-08-05, thirteen cycles. **The phase's aim was met and its
headline is not the one it expected.** An improvement is now a named,
digested artifact the harness records, and the loop ran end to end — which
is what made the rest of this paragraph sayable at all.*

*Cycle 1 built the `Improvement` descriptor and its three seams; cycles 2–4
established the cost answer, child telemetry and the user-story suite with
its floor. Cycles 5–7 found the three prompt facts that work. Cycle 6 built
the loop breaker, the phase's installable artifact, which cycle 12
documented for someone outside the project. Cycles 8–9 chased a runaway
child and discovered **the delegated child had never been hermetic** — it
was loading the operator's own toolbelt, proven byte-for-byte from recorded
transcripts, and one environment variable took timeouts from 2/6 to 0/6.
Cycle 10 published 13/16 against a bare 0/16.*

***Then cycle 11's control arms undid the headline.* Facts-only scored
15/16.** The empty-workspace fact and the technology stack — two sentences,
cycle 5 and cycle 7 — take the suite from the floor to 15/16 on their own,
and orchestration's contribution is indistinguishable from zero (15/16
against 13/16 is Fisher p ≈ 0.6, and is recorded as noise rather than as a
win for the control). The honest reading is that **this suite has no
headroom left**, which is a fact about the workload, not a verdict on
delegation.*

*Cycle 13 then closed the phase's other question. A single unambiguous
sentence about a fact the model could verify in one command changed nothing
— pip calls held at a median of 2 and the total rose. **Five prompt
interventions now separate cleanly: the three that supplied a fact the model
lacked worked; the two that supplied a rule of conduct did not.** That is
the most transferable thing the phase produced.*

***Two published figures were retracted in one night, and both had the same
shape.*** *A "4.4× tool-call ratio" and a "1,416 seconds" wall-clock gap
were each published before being checked, and each pointed the way the
argument was already going. The first was substring counting over an event
stream that re-serializes a child's transcript, inflating the delegating arm
21.9× against the bare arm's 10.0×; the second compared arms run as
contiguous blocks on a machine whose load varied under them — cycle 10's own
batch swings 3× internally. Counts survive; seconds do not, and the phase
ends with **no trustworthy measurement of what delegation costs in time**.
Interleaving runs across arms is filed as a precondition for any future
timing claim.*

*The concept budget was let fall twelve cycles behind and is now paid, seven
terms, recorded as a lapse. `arm` was rejected at cycle 1 and spent anyway,
because an improvement is the change and an arm is a batch run under it.*

*What the phase does **not** establish: whether orchestration helps on any
workload. Nothing here speaks to that — this suite left it nowhere to show.
The enforcement-over-persuasion spec is parked unscheduled for the same
reason: its bar would be "beat 15/16 on a suite with no room above it.")*

## Feature cycles

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
| 13 | The pre-install sentence, and hardening the counting — cycle 11 counted 28 child `pip install` invocations against the undelegated arm's 2, so both stack prompts now state that FastAPI, Jinja2, pytest and httpx are installed and forbid installing anything, added to *both* so it is not a second variable. **The claim is true** — a run inherits the harness's environment through `pi_env()` — and a test asserts it from outside the repository so the prompt cannot quietly become a lie. **All three predictions falsified.** Pip calls did not fall: the median held at 2 and the total *rose*, 28 to 37, with a widened tail (5, 6 and 7 in single runs against a cycle-10 max of 3). Turns and context are flat (14.0 median both; 39,760 vs 41,010). Accepted 11/16 against 13/16 is noise. The wall-clock prediction is **void, not failed**: this cycle's first batch drifted 27.3 → ~15 tok/s under unrelated machine load and is kept as `...-CONTAMINATED-...jsonl`, the quiet rerun holds 13.3–25.6, and cycle 10's own range is 3.7–25.0 — so the baseline was contaminated too. **The finding is that a single unambiguous sentence about a checkable fact does not change behaviour**, which is cycle 8's persuasion ceiling under the easiest possible conditions and cleanly separates the phase's five prompt interventions: the three that supplied a *fact* worked, the two that supplied a *rule of conduct* did not. Also hardens the counting cycle 11 got wrong (five tests over synthetic streams, both historical bugs mutation-checked), pays the concept budget's twelve-cycle debt with seven terms, and files the interleaving defect. [research](docs/superpowers/research/2026-08-05-phase5-cycle13-preinstall-sentence.md) | Done |

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
