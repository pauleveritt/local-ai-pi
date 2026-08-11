# Cycle 7 — pre-registration for the held-out comparison

**Phase:** 7 — workload first, envelope to candidate commit
**Status:** frozen at commit time; see "Freeze discipline" below
**Roadmap basis:** [`2026-08-09-phase7-workload-first-roadmap.md`](../plans/2026-08-09-phase7-workload-first-roadmap.md), Cycle 7 and the 2026-08-11 re-plan
**Supporting record:** [`2026-08-11-morning-summary.md`](../research/2026-08-11-morning-summary.md), and this session's own pilot runs (n up to 10 per task, `harness/typed_contract.py`, `tools/deliver_candidate.py --contract-task`)

## What this is and is not

This fixes every dimension governing rule 8 and the roadmap's Cycle 7 require
before a confirmatory batch may run. It is **not** the batch itself — no
confirmatory model call has been made under this pre-registration as of the
commit that adds it. Once committed, contracts, gates, and cohort membership
for the arms named below may not be tuned; a defect found after that point is
handled as an *invalidator* (see "Abort conditions"), not a quiet edit.

Everything cited as "today's pilot data" below is exactly that — pilot. Rule
8: it selected this cohort and these margins. It is not offered as evidence
of the confirmatory result, and none of it will be re-cited as such once the
batch runs.

## Frozen task manifest and contract versions

Four tasks, not the full svcs cohort. The other qualified tasks
(`async-cm-enter`, `fastapi-get-registry`, `magicmock-factory`,
`registry-iter`, `register-value-enter`, `suppress-context-exit`, and the
harder/larger candidates further down the ladder) have no typed contract
built against the real engine and no pilot evidence from this branch. Adding
them requires extending `harness/typed_contract.py` beyond the narrow bridge
it declares itself to be, which is separate work this pre-registration does
not fold in. Scoping to four is a deliberate narrowing, not an oversight.

| Task | `manifest.toml` | Locating contract | Brief |
|---|---|---|---|
| `flask-extensions` | `workloads/svcs/tasks/flask-extensions/manifest.toml` | `workloads/svcs/contracts/locating/flask-extensions.md` | `workloads/svcs/tasks/flask-extensions/brief.md` |
| `stringified-annotations` | `workloads/svcs/tasks/stringified-annotations/manifest.toml` | `workloads/svcs/contracts/locating/stringified-annotations.md` | `workloads/svcs/tasks/stringified-annotations/brief.md` |
| `local-pings` | `workloads/svcs/tasks/local-pings/manifest.toml` | `workloads/svcs/contracts/locating/local-pings.md` | `workloads/svcs/tasks/local-pings/brief.md` |
| `autowire` | `workloads/svcs/tasks/autowire/manifest.toml` | `workloads/svcs/contracts/locating/autowire.md` | `workloads/svcs/tasks/autowire/brief.md` |

Contract version: the exact committed bytes of each file above, at the commit
that adds this document. `harness/typed_contract.py`'s
`strip_authoring_narration()` is applied to the locating contract, unchanged
from today's pilot; the brief is used verbatim, stripped only of surrounding
whitespace. `autowire`'s writable scope is `{src/svcs/_autowire.py,
src/svcs/__init__.py}` (`AUTOWIRE_TARGET`, `AUTOWIRE_INIT` in
`harness/typed_contract.py`) for both arms — an executor-bounds decision, not
part of either arm's task text, so it does not confound the comparison.

## Arms and information boundaries

Two arms, both against the exact bounded executor (`gemma12b-implementer-v1`
cell: `read`/`write`/`edit` mediated by the mutation engine, 16-turn/30-tool
caps, `maxTokens` 32768). The executor, model, tool policy, writable scope,
baselines, and validation command are **identical** between arms for a given
task — `harness/typed_contract.py`'s `task_source` parameter changes only
`contract["task"]`, confirmed by
`test_task_source_only_changes_contract_task_not_the_executor_bounds`.

- **Arm A — brief.** `contract["task"]` is the manifest's own concise,
  behavior-only brief: what must change and why, no file names, no line
  numbers, no mechanism. `tools/deliver_candidate.py --contract-task <task>
  --task-source brief`.
- **Arm B — locating contract.** `contract["task"]` is the complete
  human-authored locating contract: exact files, exact locations, a
  verification checklist. `--task-source locating-contract` (the default;
  everything measured in this session's pilot was this arm).

**Deferred, explicitly, not silently:** a planner-authored-contract arm
(roadmap Cycle 6's third arm) is not included. Cycle 6 is piloted on one task
only; the full four-task cohort's contracts have not been re-authored under
the settled planner-output decision. Adding this arm is future work, tracked
in the roadmap, not folded in here.

**Information boundary, both arms:** the model never sees the target commit,
the target diff, or the hidden oracle test content — `readableFiles` is
empty in both arms' contracts (matching today's pilot; the model has not
needed additional reads to succeed on the three tasks it can solve). The
oracle overlay (`harness.workload.overlay_oracle`) touches only a disposable
grading copy created *after* the child process exits, never the worktree the
model can read or write.

## Repetitions per task

**n = 8 per arm per task** (2 arms × 4 tasks × 8 = 64 attempts). Matches this
session's already-run pilot depth for the two tasks it mattered most for
(`flask-extensions`, `autowire`), chosen because the Wilson-interval
narrowing from n=4 to n=8 was concretely worth it there and diminishing
past n=8 for a same-day batch (see the analysis in-session: n=8 to n=18 on
`local-pings` narrows width by ~0.10, at more than double the cost). Not
claimed to be enough for a tight interval on every task — `local-pings`'
~30% rate will still carry a wide interval at n=8. It is enough to tell
`flask-extensions` and `stringified-annotations`'s near-ceiling results
apart from `autowire`'s near-floor one, which is what a first held-out
comparison needs to do.

## Acceptance definition

Two-tier, and the confirmatory batch's primary metric is the *second* tier,
not the first — this is load-bearing, not a formality. Today's pilot found
that `candidate-created` (the product's own gate: the preservation suite
passes) is necessary but not sufficient; `local-pings` and `autowire` both
show high `candidate-created` rates alongside low correctness.

1. **`candidate-created`**: `tools/deliver_candidate.py`'s own outcome —
   preservation suite passes (with `_effective_preservation_command`'s
   deselects applied), candidate committed to a `refs/satyrn/candidates/`
   ref. Recorded for every attempt, reported as a secondary metric (does the
   arm produce *safe* output).
2. **`oracle-passed`** (primary): of the `candidate-created` attempts, the
   candidate commit's tree, overlaid with the real target oracle test file
   (`harness.workload.overlay_oracle`, hash-verified against the manifest),
   passes `manifest.oracle_command`. This is the confirmatory metric. An
   attempt that is not `candidate-created` is `oracle-passed = false` by
   construction — it never reaches the check.

An attempt is **accepted** for the primary comparison iff `oracle-passed`.

## Accepted-by-deadline endpoint and deadline

The cell's own frozen budget, unchanged from today's pilot and not
loosened for this batch: **16 turns** (`MAX_IMPLEMENTER_TURNS`,
`extensions/orchestration/implementer.ts`), **30 tool calls**
(`ImplementerPolicy`'s default `maxTools`), **900 seconds** wall clock per
attempt (`wall_clock_seconds` in `gemma12b-implementer-v1.toml`). An attempt
that exhausts any of these without producing a change is `candidate-created
= false` (`deliver()`'s "candidate changed nothing" path) and therefore not
accepted. No retry, no extension, no repair call — governing rule 5 and the
roadmap's explicit Cycle 4 exclusions apply unchanged.

## Task weighting and aggregate rule

**Per-task reporting is primary.** A pooled 64-attempt rate is reported as a
secondary summary only, computed by simple unweighted pooling (each attempt
counts once) — not weighted by task difficulty, since this cohort's four
tasks were not selected to be equally difficult and a difficulty weighting
would itself need pre-registering. The pooled number exists to answer "did
this comparison find anything at all," not to stand in for the per-task
picture; a write-up that reports only the pooled rate is out of compliance
with this document.

## Non-inferiority or superiority margins

The directional hypothesis, stated before any confirmatory data: **Arm B
(locating contract) has a higher oracle-passed rate than Arm A (brief) on at
least the tasks where Arm B has already shown near-ceiling pilot performance
(`flask-extensions`, `stringified-annotations`).** This is a superiority
question, not non-inferiority — the roadmap's whole premise for building the
typed-contract path is that a bare envelope (no locating information, which
Arm A is not quite — it retains the executor's exact-path scoping — but
approximates) measured 0/24 in the 2026-08-10 mechanism screen.

**Superiority is called per task** when the Newcombe/Wilson-based confidence
interval for (Arm B rate − Arm A rate) excludes 0 in the positive direction.
No fixed minimum-difference threshold beyond "excludes 0" — at n=8 per arm,
a threshold tighter than that would not be resolvable, and a looser,
p-value-style claim is exactly the kind of hand-computed statistic the
2026-08-10 external review already found wrong once in this project
(defect 6, the roadmap's status appendix). The interval must be computed by
tested code (see "Confidence interval and estimator procedures"), not by
hand.

## Treatment of infrastructure failures

An attempt is **void**, excluded from both numerator and denominator of
every rate above (not counted as a failure), when:

- the model server is unreachable (`ModelServerDown`, or Pi exits having
  never reached a tool call);
- the cell fails `verify()` against live configuration (arm mismatch — the
  attempt is not measuring the arm it claims to);
- the candidate worktree or the disposable materialization fails to create
  for a reason unrelated to the model (disk, git, permissions).

Void attempts are logged with their reason and reported alongside the
accepted-rate table, per the roadmap's defect 2 (void attempts must not
inflate the denominator the way `cycle1/summary.json` once did). A void
attempt is **replaced** — the batch runs a fresh attempt in its place to
reach the pre-registered n, logged as a replacement, not silently dropped.

## Workload floor/ceiling stop rule

If, after the full batch, **both arms** land at a universal floor (0/8) or
ceiling (8/8) on the same task with no separation between arms, that task
contributed no comparative information and is flagged as such in the
write-up rather than silently pooled as if it discriminated. This is not
expected given today's pilot shape (`autowire` floors under Arm B already;
if it also floors under Arm A, that is itself informative — it would mean
the locating contract's detail is not what autowire's ceiling is about) but
must be checked, not assumed away.

## Confidence interval and estimator procedures

Wilson score interval (95%, z = 1.96) for each arm's single-task rate.
Newcombe's method (two independent Wilson intervals combined) for the
per-task arm-difference interval. Both computed by a small, tested Python
helper added alongside the batch runner — not by hand, not inline in a
report. The helper is a straightforward, well-known closed-form
computation (the same formula already used ad hoc in this session's
analysis, now made reusable and tested) — this is bookkeeping, not new
statistical machinery, and does not require its own design review.

## Inconclusive region

A task's comparison is **inconclusive** when the Newcombe interval for
(Arm B − Arm A) includes 0. Inconclusive is reported as its own outcome
category, not folded into "no difference found" or rounded toward either
arm.

## Directness metrics

Not applicable to this comparison. Directness metrics (per the roadmap's
Cycle 6 autowiring-decomposition section) apply to comparing a direct
executor attempt against a planner-decomposed one; this batch has no
decomposition arm.

## Planner authoring-cost accounting

Not applicable — no planner arm in this batch (see "Arms" above).

## Exclusions and abort conditions

**Excluded from the batch entirely:** any task outside the four named above;
any arm beyond the two named above; any attempt using a cell other than
`gemma12b-implementer-v1` (in particular, `gemma12b-envelope.toml` and
`qwen27b-envelope.toml` remain untouched, per the roadmap's standing
instruction, and are not part of this comparison).

**Abort the remaining batch** (stop, do not complete the pre-registered n,
report what ran and why it stopped) on any of:

- a `CellMismatch` that is not resolved by discovering the *harness* (not
  the cell file) drifted — e.g., `pi-agent-dir/models.json` left bumped by
  a prior run's failed restore. If the mismatch is a harness-side leftover,
  fix the harness state and resume; if it is because the cell's own pinned
  values no longer match the code (e.g., an in-flight, uncommitted edit to
  `extensions/orchestration/implementer.ts`), abort and re-freeze this
  pre-registration first — governing rule 8's tuning ban is precisely about
  not letting that happen silently mid-batch.
- an internal `policy_error` (the `try`/`catch` in `implementer.ts`'s
  `tool_call` handler firing) more than once in the batch — that is an
  unexpected implementation fault, not a normal refusal, and needs
  diagnosis before more model time is spent.
- discovery, mid-batch, of a validation-gate defect of the same shape as
  the `flask-extensions` deselect bug found earlier this session (a task's
  gate provably rejects or accepts independent of candidate correctness).
  Stop, fix, re-freeze a new pre-registration version, do not patch and
  continue under the old one.

**Not an abort condition:** a disappointing rate, a single task flooring,
non-determinism producing "changed nothing" on some attempts. Governing
rule 8's run discipline is explicit: stop on hard invalidators, not
disappointing outcomes.

## Run discipline

- **Interleave arms within task and within blocks.** For each task, run in
  the order A, B, A, B, … (not all of A then all of B), so time-of-day model
  server drift or thermal/load effects on this shared machine (observed
  repeatedly this session — see the timing discussion in-session) affect
  both arms comparably rather than confounding with arm.
- **Cell verify() at preflight and at every block boundary** (per task),
  matching Cycle 1's integrity-check discipline.
- **`models.json` bump/restore via `harness.model_config.bumped_max_tokens`**
  for the whole batch's duration, not per attempt — one bump, one restore,
  reducing the restore-forgetting risk that motivated building that helper.
- **No contract, gate, or cohort edits once this document is committed.**
  A defect found mid-batch is an abort condition (above), not a quiet fix.

## Freeze discipline

This document is frozen at the git commit that adds it to the repository.
"Frozen" means: the task manifest table, the arms, n=8, the acceptance
definition, the margin, and the abort conditions above do not change without
a new dated pre-registration document superseding this one and an explicit
note of what changed and why. The batch itself — the actual 64 model
attempts — is separate, later work; this document's existence is not a
claim that it has run.
