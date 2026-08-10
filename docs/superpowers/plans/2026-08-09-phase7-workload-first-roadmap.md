# Phase 7 roadmap — workload first, envelope to candidate commit

**Date:** 2026-08-09  
**Status:** proposed execution plan  
**Research basis:**
[`../research/2026-08-09-phase7-workload-first-reset.md`](../research/2026-08-09-phase7-workload-first-reset.md)  
**Supersedes for forward work:** the assumption that the complete Cycle 2
bounded-executor bundle should become the Phase 7 starting point  
**Preserves:**
`specs/2026-08-08-phase7-pre-batch-integrity-design.md` on the `phase6-orchestrator-spike` branch

---

## Goal

Produce credible evidence for a small local model performing routine,
pre-chewed coding work, while turning the coherent envelope into the smallest
useful repository-safe executor.

The phase proceeds in this order:

```text
preserve batch integrity
→ qualify a discriminating svcs workload
→ screen and freeze the cohort
→ package the exact envelope as candidate delivery
→ admit protections by replay and forced negative paths
→ evaluate planner-authored contracts
→ run one pre-registered evidence batch
```

The workload and product tracks may overlap in calendar time, but evidence work
does not proceed until both are frozen.

## Governing rules

1. **AgentClinic Phase 2 is retired as a discriminator.** It may remain a smoke
   fixture, never the basis of another capability claim.
2. **Cycle 1 stays.** Repair any integration defect it introduced; do not remove
   its instruments because Cycle 2 is being simplified.
3. **The exact coherent envelope is the behavioral control.** Prompt bytes,
   model, tools, budgets, environment, and Pi flags are condition-recorded.
4. **No container requirement.** The engine is a local coding agent, not a
   hostile-code sandbox. Documentation states that validation executes with the
   user's privileges.
5. **No custom automatic promotion in the first product version.** Successful
   work becomes a durable candidate commit/ref.
6. **No dirty live repository in the first version.** Complete dirty-state
   snapshotting is deferred; partial snapshots are forbidden.
7. **No component earns admission from low runtime alone.** It must catch a
   named failure and survive false-rejection tests.
8. **Pilot data selects the cohort and margins; it is not confirmatory
   evidence.**
9. **The application workload is postponed.** Phase 7 claims remain scoped to
   the `svcs` cohort.

## Cycle 1 — retain and close the batch-integrity baseline

### Work

- Keep the prompt ledger and its constant/varying declarations.
- Keep prompt/tool coherence checks.
- Keep estimator tests and `insufficient-n` behavior.
- Keep process-baseline capture, contention sentinel, and hard/diagnostic
  block-boundary split.
- Keep replay over banked evidence.
- Backport/retain the fix that emits prompt telemetry only after extension
  initialization; Cycle 2's first live run showed that Cycle 1 had broken the
  engine comparator during extension load.
- Add one real Pi extension-lifecycle smoke test or probe. A direct unit call
  with a stub is insufficient for an API whose load phase rejects action
  methods.
- Correct the Cycle 2 review brief's Python verification command to include the
  venv on `PATH` for subprocesses.

### Acceptance

- Existing Cycle 1 replay bench passes.
- Real extension loading completes without “runtime not initialized.”
- Telemetry on/off leaves the child transport hash unchanged.
- The documented TypeScript and Python verification commands pass from a clean
  worktree.

### Model cost

At most one short live lifecycle probe. Everything else is deterministic.

## Cycle 2 — build the `svcs` replay manifest

### Repository pin

- Repository: `/Users/pauleveritt/PycharmProjects/svcs`
- Upstream `main` inspected at `7d56b11` after a pull on 2026-08-09.
- Never run experiments in the existing `feature/autowiring` checkout.
- Create a fresh detached worktree from each task's immutable base SHA.
- Record upstream URL and target SHA in every manifest entry.

### Candidate ladder

Qualify these in order, stopping only when there are at least six useful tasks
covering the required axes:

| Target | Role |
|---|---|
| `c016b37` | Easy harness/floor anchor |
| `c91f1f1` | Narrow bug |
| `32ddce2` | Async/lifecycle semantic task |
| `52c6689` | Local/global override feature |
| `012b6a9` | Framework integration migration |
| `c5c5f48` | Cross-adapter API propagation |
| `f81e493` | Reflection and typing bug |
| `7d56b11` | Recent FastAPI/Starlette upper-middle task |
| `c0bd379` | Large cross-cutting stretch task |
| `6bb3f28` | Autowiring ceiling |

### Manifest schema

For every candidate, record:

- `task_id`, repository URL, base SHA, and target SHA;
- behavior-only task brief;
- complete human-authored source contract;
- task and contract hashes;
- contract-authoring elapsed time;
- readable/writable policy;
- candidate-output paths;
- hidden oracle files and command;
- preservation command;
- Python and dependency-environment identity;
- base preservation result;
- base plus hidden-oracle expected rejection;
- target plus hidden-oracle pass result;
- test runtime and nondeterminism notes;
- exclusions or test adaptations and the reason for each.

Keep raw target tests outside the candidate worktree. The model and any planner
must not be able to read the target diff, target tree, or hidden oracle through
normal task tools.

### Qualification script

Build one deterministic script that, for each manifest entry:

1. creates a detached base worktree;
2. verifies the preservation suite;
3. overlays the hidden oracle into a separate grading copy;
4. verifies that the base is rejected for the expected reason;
5. creates a target worktree and verifies preservation plus acceptance;
6. records timing and exact commands;
7. removes both worktrees even after failure.

Do not duplicate environment setup ad hoc per task. Freeze one cohort
environment or explicitly record task-specific exclusions before the pilot.

### Autowiring ceiling qualification

The manifest entry for `6bb3f28` must preserve these already-verified facts:

- parent `816403b`;
- 67 hidden autowiring tests reject the parent during collection because the
  APIs are absent;
- those tests pass on the target in 0.06 s;
- 124 parent preservation tests pass in 0.19 s when the historical Pyramid
  integration is excluded;
- the full historical parent suite is not yet qualified in the current
  environment because `httpx2` is absent.

Before admission, choose and freeze one of:

- reconstruct the historical dependency environment and run the full parent
  suite; or
- exclude Pyramid with a written argument that autowiring cannot affect it,
  and use the same exclusion for every arm.

### Acceptance

- At least six qualified tasks.
- At least one easy anchor, three medium tasks on different difficulty axes,
  one upper-middle/stretch task, and the autowiring ceiling.
- Every accepted task has a base rejection, target pass, preservation pass, and
  sub-minute deterministic validation.
- No task was selected using results from an arm that will later be presented
  as confirmatory evidence.

### Model cost

None.

## Cycle 3 — screen the workload with the exact envelope

### Arm

Use the byte-stable coherent renderer and the exact one-call envelope:

- same local model as the existing coherent-envelope condition;
- `read,write` only;
- same turn and tool budgets;
- no controller, planner, repair, candidate gates, or automatic promotion;
- hermetic agent directory and condition record;
- one fresh base worktree per attempt.

For screening, the worktree itself is disposable output. Product candidate
delivery is not yet under test.

### Funnel

1. Run one attempt on every qualified candidate.
2. Inspect failures by a predeclared taxonomy: contract defect, discovery
   failure, incomplete implementation, semantic error, scope error, timeout,
   harness/environment failure.
3. Exclude only broken workload entries or tasks that plainly do not measure
   the intended behavior. Record every exclusion.
4. Run two more attempts on six to eight finalists.
5. Freeze a cohort that includes useful middle outcomes plus the easy and
   ceiling anchors.

The screen is allowed to discover that a contract is defective. Correct the
contract, increment its version/hash, and restart that task's screen. Never
silently edit a contract between attempts.

### Desired—not mandatory—pilot shape

- Easy anchor usually succeeds.
- Several medium tasks produce mixed outcomes across three attempts.
- At least one stretch task is difficult without being a pure infrastructure
  failure.
- Autowiring reveals a capability ceiling or a coherent near-ceiling attempt.
- The whole cohort is neither 0% nor 100% accepted.

These are workload-selection properties, not evidentiary thresholds.

### Acceptance

- Frozen task set, contracts, hashes, environment, grader commands, and failure
  taxonomy.
- A written explanation for each included and excluded task.
- No universal floor or ceiling unless the phase is stopped and reconsidered.

### Model cost

Approximately 10 single-pass calls plus 12–16 finalist calls. At observed local
latency this should be tens of minutes, not a sequence of hour-long batches.

## Cycle 4 — productize the envelope as candidate delivery

### Minimum flow

```text
preflight clean repository at root
→ capture exact HEAD
→ create candidate worktree and branch at HEAD
→ run exact coherent envelope once
→ observe final changed paths
→ reject out-of-scope candidate
→ run declared validation with process-group timeout handling
→ commit candidate on success
→ create durable candidate ref
→ return receipt and diff summary
```

On failure, discard the worktree and temporary branch. On success, remove the
worktree but retain the durable candidate ref until the caller explicitly
accepts or discards it.

### Explicit exclusions

- no controller model call;
- no repair call;
- no required-literal gate;
- no generic source-AST gate bundle;
- no symbol-loss gate;
- no custom copy into the live tree;
- no implicit fast-forward;
- no dirty-repository snapshotting;
- no live Pi tool entry point until the CLI path is stable.

### Receipt

Record:

- repository identity, base SHA, candidate commit/ref;
- task, rendered, transport, and system prompt hashes as applicable;
- model, Pi version, budgets, tools, and environment condition;
- changed paths and scope result;
- validation command, exit, timeout, and output digest/tail;
- child, validation, commit, and total timing;
- outcome: `candidate-created`, `discarded`, or `infrastructure-failure`;
- cleanup result.

No outcome is named `promoted` in this cycle.

### Process lifecycle

Port the validation runner's process-group behavior to the model child:

- handle an already-aborted signal;
- send `SIGTERM` to the process group;
- wait for exit;
- escalate to `SIGKILL` after the grace period;
- do not remove the candidate worktree while the child or descendants remain
  alive.

### Acceptance

- On the frozen workload, prompt and invocation conditions match the coherent
  envelope exactly except for the candidate lifecycle.
- Candidate delivery does not mutate the live repository.
- Success leaves a readable durable commit/ref with the expected diff.
- Failure leaves no live changes, temporary worktree, or temporary branch.
- Concurrent or stale live state causes refusal, never copying.
- Model-call acceptance and latency remain compatible with the envelope pilot;
  exact confirmatory margins wait for pre-registration.

### Verification cost

- Deterministic lifecycle and Git tests on every change.
- Two to four live-model equivalence probes only after the flow is integrated.
- Replay previously saved Cycle 3 candidates where possible.

## Cycle 5 — component admission by replay and forced failure

Do not run a fresh model batch for each component. Save Cycle 3 and Cycle 4
candidate diffs, receipts, and grading outcomes, then replay proposed observers
over them.

### Required negative paths

Create deterministic fixtures or focused instructed probes for:

- out-of-scope modification;
- absolute-path tool attempt;
- stale live `HEAD`;
- dirty live tree;
- timeout with a child process that ignores `SIGTERM`;
- descendant process surviving the direct child;
- valid symbol move between files;
- missing required behavior that still contains all requested literals;
- validation failure;
- candidate commit/ref creation failure;
- two concurrent delivery/apply attempts.

### Admission table

| Candidate component | Test before admission |
|---|---|
| Scope allowlist | Deterministic final-diff rejection; zero effect on in-scope replay |
| Containment hook | Forced absolute-path attempt blocked and recorded; described only as defense in depth |
| Required literals | Must catch a real replay miss not already caught by validation and avoid comment/dead-code false confidence |
| Source AST probes | One named probe per demonstrated failure; stays in task/oracle layer |
| Cross-file symbol preservation | Must accept moves/renames and detect genuine disappearance before replacing current gate |
| Candidate apply | Separate design/review; not required for Phase 7 evidence |
| Repair | Remains excluded until more than one failure class and a safe losing path exist |

### Acceptance

- Every admitted component has a named failure it prevents.
- Replay reports marginal catches, overlap with validation, and false
  rejections.
- Naturally inactive components are not marketed as validated.
- No component changes model-visible input unless that change becomes its own
  pre-registered arm.

### Model cost

Normally zero. Use a live model only when the property depends on model/tool
interaction and cannot be represented by an injected child.

## Cycle 6 — planner contracts

### Baselines

Preserve the complete human-authored contracts from Cycle 2 as executor
baselines. They answer whether the bounded executor can do pre-chewed work.

### Planner study

For each frozen base:

1. Give a planner the behavioral task brief and base repository only.
2. Ask it to emit the same typed contract schema.
3. Record planning model, tokens, latency, and any human edits.
4. Run the unchanged candidate executor.
5. Grade with the same hidden oracle.

Start with the large-model, one-time planner that matches the product pitch.
Treat a local planner/scout as a later exploratory arm if time permits.

### Autowiring decomposition probe

After the direct ceiling attempt is frozen, allow the planner to decompose
autowiring into bounded subcontracts. Preserve the following distinctions:

- direct executor outcome;
- planner decomposition quality;
- per-subcontract executor outcomes;
- integration outcome over the combined candidate;
- total planning and execution time.

Do not count a decomposed success as a direct executor success.

### Acceptance

- Planner never sees target commits or hidden tests.
- Contract defects are classified separately from executor defects.
- Authoring cost is included in end-to-end results.
- Planner study does not alter the already-frozen executor baseline.

## Cycle 7 — pre-register and run one held-out comparison

The exact arms and margins are fixed after the pilot. The default comparison is:

1. concise facts-bearing task brief → exact bounded executor;
2. complete human-authored contract → exact bounded executor;
3. planner-authored contract → exact bounded executor, if Cycle 6 is ready.

The legacy controller engine may appear as a calibration comparator on a small
subset, but it is not required to decide whether the new product path works.

### Pre-registration must fix

- frozen task manifest and contract versions;
- arms and information boundaries;
- repetitions per task;
- acceptance definition;
- accepted-by-deadline endpoint and deadline;
- task weighting and aggregate rule;
- non-inferiority or superiority margins;
- treatment of infrastructure failures;
- workload floor/ceiling stop rule;
- confidence interval and estimator procedures;
- inconclusive region;
- directness metrics, if any;
- planner authoring-cost accounting;
- exclusions and abort conditions.

### Run discipline

- Interleave arms within task and blocks.
- Use Cycle 1 integrity checks at preflight and block boundaries.
- Stop on hard invalidators, not disappointing outcomes.
- Do not tune contracts, gates, or cohort after confirmatory results begin.

## Later explicit apply — separate from Phase 7 minimum

If candidate delivery proves useful, design an explicit Git-mediated apply:

1. acquire a repository-level apply lock;
2. require a clean index and worktree;
3. require current `HEAD` to equal the candidate parent;
4. re-check candidate scope and object existence;
5. use Git fast-forward/merge machinery rather than a custom per-file copier;
6. retain the candidate ref until success is verified;
7. on refusal, make no attempt to merge or repair automatically.

Describe this as strict-precondition Git apply, not filesystem-atomic promotion.
Fault injection, concurrent apply, symlink, interrupted process, and disk-error
behavior require their own review before a live-session tool uses it.

## Deferred beyond Phase 7

- Django/FastAPI application cohort;
- claims about general application coding;
- dirty-workspace snapshotting;
- hostile-code sandboxing or containerization;
- automatic repair;
- generic semantic-preservation engine;
- automatic live-tree promotion;
- filesystem-churn observer;
- planner inside every executor run.

## Deliverables checklist

- [ ] Cycle 1 lifecycle defect closed and replay green.
- [ ] `svcs` task manifest and qualification script.
- [ ] Six or more qualified tasks including autowiring ceiling.
- [ ] Frozen envelope pilot cohort and failure taxonomy.
- [ ] Minimum candidate-commit executor and receipt.
- [ ] Replay corpus and forced-negative-path suite.
- [ ] Component admission report.
- [ ] Planner contract study or explicit deferral.
- [ ] Pre-registration with margins and inconclusive region.
- [ ] One confirmatory held-out batch.
- [ ] Research write-up scoped explicitly to `svcs`.

---

## Status appendix — 2026-08-10

Where the sequence actually stands after the frontier/variance/contract
work, corrected after external review. Numbers live in
[`../research/2026-08-10-phase7-frontier-contracts-variance.md`](../research/2026-08-10-phase7-frontier-contracts-variance.md);
this appendix records cycle status and the re-plan.

An earlier version of this appendix said "Qualify (Cycle 2): closed."
That was wrong in the way this project keeps being wrong: it graded a
cycle against the work actually done rather than against what the cycle
specifies. Cycle 2 requires complete contracts with recorded hashes in
the manifests. No manifest carries a contract. Corrected below.

### Cycle status

- **Qualification:** closed. Eight qualified tasks, manifests, reference
  patches, and a ceiling replay that all eight target diffs clear.
- **Contract baseline (Cycle 2's remaining half):** open, not started.
  No manifest has a `contract` or `contract_sha256`. The eight files
  under `workloads/svcs/overnight/drafts/` are uncorrected drafts, three
  of them empty stubs, composed into prompts at runtime and deliberately
  never written into manifests.
- **Screen and freeze (Cycle 3):** open, and the measured pilot **is not
  the arm this cycle specifies**. Cycle 3 names the exact `read,write`
  coherent envelope; every cell measured so far used
  `read,bash,edit,write`, probe budgets of 60 turns / 150 tool calls, a
  provisioned dev environment, and an 1800s wall clock. Those are a
  different executor. The pilot is informative about models; it is not
  the envelope control this cycle exists to produce.
- **Package envelope to candidate commit (Cycle 4):** **closed.**
  `harness/candidate.py` plus `tools/deliver_candidate.py`. Every
  acceptance criterion demonstrated: the live repository is not mutated,
  failure leaves no worktree or branch, success leaves a readable ref
  under `refs/satyrn/candidates/`, and a dirty or non-repository state
  refuses rather than copies. Nine lifecycle branches are covered by
  deterministic tests with the model call injected; three live probes
  confirmed the integrated flow (3/3 candidates, validation exit 0). The
  transactional boundary costs about 0.1s against a 33-75s model call,
  under 0.3% -- independently consistent with the Cycle 2 spike's 385ms
  from a separate implementation. Receipts in `workloads/svcs/probes/`.
- **Admit protections by replay (Cycle 5):** two investigations, two
  findings, **nothing admitted.** Rule 7's bar held.
  - Replay fixtures are now committed and reproducible (main repo,
    `7ca49cb`), but the first set was wrong: it was extracted from
    `tool_execution_start`, which records attempts that never reach the
    hook. Pi validates arguments at `agent-loop.js:404` and calls
    `beforeToolCall` on the next line, so a malformed call throws above
    every `tool_call` guard. 52 of one fixture's 57 calls were
    unreachable, and replay reported 44 blocks for a loop the guard
    cannot see.
  - Live test, prespecified: `registry-iter` guarded 4/6 accepted but
    2/6 loop deaths, and the guard never fired -- that half of the plan
    was aimed at the unguardable failure class. The `magicmock` half
    fired once in four runs, and that run was the worst outcome in the
    set (101 preservation nodes lost). The guard demonstrably fires and
    does not false-reject; there is no evidence it improves an outcome.
  - Consequence for the next attempt: malformed-call loops are not
    reachable from `tool_call` **or** `tool_result` -- a validation
    failure returns `kind: "immediate"`, skipping
    `finalizeExecutedToolCall` where `afterToolCall` lives. Only
    `tool_execution_start`/`end` and the synthesized result message see
    them. A pre-validation block needs a change to Pi core.
- **Planner contracts (Cycle 6):** piloted on one task, with the
  transcription caveat recorded. The unresolved question is which
  product Cycle 6 is buying — see the decision below.
- **Pre-registered evidence batch (Cycle 7):** blocked on all of the
  above. Under rule 8 everything to date is pilot.

### Instrument defects found by external review, 2026-08-10

Ordered by consequence. None invalidate a banked result; all block the
confirmatory batch.

1. **The grader can accept skipped oracle tests.** `accepted` requires
   `oracle.reason_class == "pass"` and never `oracle.tests_passed ==
   target_total`, and `missing_nodes` is computed from the preservation
   run only — so the oracle run carries no node-inventory check. A
   candidate that makes the hidden assertions *skip* would be accepted.
   Verified latent, not live: all 43 banked accepts have
   `tests_passed == target_total`.
2. **Void attempts inflate the denominator.** Both `screen_workload` and
   `regrade_workload` write `attempted = len(rows)` including void
   attempts. `cycle1/summary.json` reads `attempted: 8, accepted: 2`
   where the honest cell is 2/7. The reporting CLI excludes void
   correctly; the stored summary does not.
3. **The experimental cell is not fully recorded.** Attempt records omit
   resolved `maxTokens`, context window, extension digest, Pi version,
   and server configuration. Experiment B's 32768 exists only in its
   driver and directory name. This violates governing rule 3, which
   already requires condition recording.
4. **Contract authoring treats any nonempty text as success.** That is
   how three 29–80 byte stubs were recorded as authored drafts. Stop
   reason is neither recorded nor gated.
5. **Validity checking is narrower than its prose.** The audit matches
   literal workspace-shaped names and four substrings in tool arguments.
   Relative traversal, globs, generic `find`, and network access are not
   detected, and the manifest's `readable` policy is never enforced.
   "0 tainted" means "no detected escape of these shapes," and no
   document may say "hermetic executor."
6. **A prespecified margin was justified with a wrong statistic.**
   Experiment B's driver cites Fisher one-sided ≈ 0.01 for 1/6 versus
   6/8; the correct value is 0.0513. The observed 3/8 conclusion is
   unaffected, but margins must be computed by tested code, not by hand.
7. **The guard replay is not reproducible here.** The research record
   cites `extensions/guards/loop-breaker.ts`, which does not exist on
   this branch; the tracked artifact is `.pi/extensions/loop-breaker.ts`.
   The two transcript-derived fixtures are uncommitted.

### Re-planned sequence

The correction that matters is direction, not ordering. Phase 7 has
added roughly six thousand lines of engine, tool and test code, ninety-
seven mebibytes of tracked workload artifacts, and fifty-six commits,
and has produced no packaged candidate-delivery path. That is the
machinery trap the brief names. **The next milestone is fewer moving
parts and one trustworthy delivery path, not another measured cell.**

**No new model runs until step 3 completes.**

1. **Repair the instrument.** Close defects 1–6 above. Acceptance
   requires full oracle passage and an oracle node inventory; void
   attempts leave the denominator; every attempt records its resolved
   cell (`maxTokens`, context window, extension digest, Pi version,
   server); authoring gates on stop reason and a minimum viable draft;
   validity language is narrowed everywhere it appears. Offline, tested,
   no model calls.
2. **Make the guard replay reproducible.** Commit the two
   transcript-derived fixtures against the tracked
   `.pi/extensions/loop-breaker.ts`, asserting first-block index and
   blocked count. Correct the research record's path.
3. **Freeze one executor arm as a cell manifest.** One file naming
   tools, budgets, caps, environment, model, and extension digest — the
   thing every later run cites instead of re-deriving. This is the
   artifact whose absence made defect 3 possible.
4. **Run the narrow prespecified guard test.** Measured: block observed,
   no further identical loop, an alternative action taken, accepted by
   deadline. Small, live, thresholds committed before results.
5. **Cycle 4 — package the candidate-commit executor.** The missing
   product milestone. Nothing further is measured until a contributor
   can install something and get a candidate commit.
6. **Decide what planner output is.** A solution-bearing implementation
   plan for safe transcription, or a requirements-only contract intended
   to improve reasoning. These are different products with different
   comparisons, and the current authoring prompt silently chose the
   first. Re-author all eight contracts under whichever is chosen.
7. **Then** freeze the cohort and pre-register the held-out batch.

### What changed since this appendix was written

Steps 1 through 5 of the re-planned sequence below are done: the
instrument was repaired (rule 8 closes the skipped-oracle hole; void
attempts leave denominators; the resolved cell is recorded per attempt;
authoring gates on length and stop reason; validity language narrowed),
the guard replay is reproducible, `workloads/svcs/cells/` freezes four
arms and verifies them against live configuration before any call, the
narrow live guard test ran and admitted nothing, and Cycle 4 shipped.

Step 6 -- deciding what planner output *is* -- is **settled**: a contract
locates and bounds the work and does not contain the implementation. See
[`../research/2026-08-10-phase7-what-planner-output-is.md`](../research/2026-08-10-phase7-what-planner-output-is.md).
All eight current drafts are void, three as empty stubs and five as
solution-bearing, and re-authoring is the next authoring action.

A review of that work then found the gate it rests on was unsound in
both directions: `extract_contract` could not tell a document *wrapped
in* a fence from one *containing* fences, and on a plainly written
contract with two or more examples it deleted the title, the locating
prose and the Bounds section, leaving inverted fence parity that made
the gate read code as prose. Fixed before any re-authoring, and the gate
now reads the raw text as well as the extracted body. Step 7 is
unchanged and still last.

**The simplicity budget is the standing risk.** Cycle 4 added roughly 400
lines and closed a milestone; the guard work added fixtures, cells and a
diagnostic path and admitted nothing. The next change that earns its
place is more likely to be a removal than an addition.

### Standing correction to the governing rules

Rule 3 already requires condition recording; defect 3 shows it was
honoured in prose and not in code. Rule 7 says no component earns
admission from low runtime alone — the loop-breaker's admission must
therefore clear step 4's live test, not the replay alone.

