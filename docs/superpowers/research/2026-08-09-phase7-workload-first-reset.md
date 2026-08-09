# Phase 7 reset — choose a workload before rebuilding the engine

**Date:** 2026-08-09  
**Status:** research decision and basis for the Phase 7 roadmap  
**Roadmap:**
[`../plans/2026-08-09-phase7-workload-first-roadmap.md`](../plans/2026-08-09-phase7-workload-first-roadmap.md)  
**Precedent:**
[`2026-08-09-phase7-cycle2-overnight-spike.md`](2026-08-09-phase7-cycle2-overnight-spike.md),
[`../reviews/2026-08-09-phase7-cycle2-review-brief.md`](../reviews/2026-08-09-phase7-cycle2-review-brief.md),
[`2026-08-08-phase6-bounded-executor-pivot.md`](2026-08-08-phase6-bounded-executor-pivot.md)

---

## Decision

Phase 7 becomes **workload-first**.

Keep Cycle 1's batch-integrity instruments. Preserve the coherent envelope as
the behavioral baseline. Do not merge the whole Cycle 2 bounded-executor bundle
as the new product merely because its deterministic path was fast. First build
a workload capable of distinguishing approaches; then productize the envelope
with only the minimum repository-safety boundary; then admit additional pieces
one at a time when replay or a focused probe shows that they catch a real
failure without rejecting valid work.

The first workload cohort will come from the `svcs` project. An application
cohort is explicitly postponed. `svcs` is sufficient to begin because it has a
dense core, several framework integrations, real sync/async and typing
semantics, a rich commit history, and a test suite fast enough that model
inference—not validation—remains the long pole.

This is not a decision to optimize the product for library maintenance forever.
It is a decision to use the best immediately available discriminator rather
than delay for an application repository or continue measuring on AgentClinic
Phase 2, which has reached ceiling.

## What changed the plan

The four-arm experiment established a narrow but important result:
`envelope-coherent` matched the engine's acceptance on AgentClinic Phase 2 and
delivered accepted work much earlier. The engine's normal latency premium was
one sequential controller-model call. Cycle 2 then tried to retain the winning
one-call topology while adding a candidate worktree, five deterministic gates,
containment, receipts, and promote/discard.

The overnight probe showed that the topology survived: over the two probe
files, bounded executor and coherent envelope both accepted 14/14, and their
model-call times overlapped. The candidate boundary, gates, and promote path
cost 376–624 ms, with a pooled median of 386.5 ms. That supports the claim that
the deterministic path is inexpensive on this small repository.

It did **not** establish the value of the safety bundle:

- every bounded candidate promoted;
- all five gates passed every time;
- containment blocked nothing;
- the discard path was not reached by ordinary model output;
- AgentClinic Phase 2 could not expose false rejections from legitimate
  cross-file moves, broad preservation requirements, or incomplete discovery.

The bundle was carried, not exercised. More runs on the same task cannot repair
that evidentiary problem. A discriminating workload has to come before further
architectural selection.

## Product assumptions for this phase

### Local execution, not hostile-code isolation

The product will not require users to run the engine in a container. Like other
local coding agents, it executes model-authored code and validation commands
with the user's privileges. The Phase 7 threat model is therefore accidental
damage, incoherent partial edits, stale repository state, and uncontrolled
scope—not a malicious candidate deliberately escaping a security sandbox.

The path-containment hook can still be useful defense in depth against an
accidental absolute-path read or write. It must not be described as a security
boundary: validation may import or execute candidate code, and no path hook can
confine arbitrary code executing as the user.

### Pre-chewed routine work remains the pitch

The intended topology remains:

```text
one-time planning and contract authoring
→ complete behavioral contract
→ one bounded small-model executor
→ deterministic observation and validation
→ candidate artifact
```

The planner may eventually be a large model, a local planning/scouting model,
or a human. Planning is an upstream stage and must be priced and evaluated
separately. Reintroducing a planner inside every executor run would recreate the
two-sequential-model topology that the four-arm result rejected.

### No custom automatic promotion in the first product version

Cycle 2's custom copier validates all paths before applying them, but the apply
phase remains multi-file and non-transactional. An I/O error can still leave a
`promoted-partial` result. Its predictable temporary path also creates avoidable
symlink and concurrency concerns. Implementing a reliable multi-file
transaction, rollback journal, concurrency lock, and filesystem fault model is
not the fastest route to product value.

The first product version will instead produce a durable candidate Git commit
and receipt. It will not copy candidate files into the live tree. A later,
explicit apply operation may use Git under strict preconditions: the live tree
is clean, `HEAD` still equals the candidate's parent, the candidate contains
only admitted paths, and a fast-forward is possible. If any precondition fails,
the candidate remains available and the live tree is untouched.

This is intentionally called **candidate delivery**, not atomic promotion.

## Why `svcs` is the first cohort

Repository inspected:
`/Users/pauleveritt/PycharmProjects/svcs`.

Upstream `main` was pulled on 2026-08-09 and now points to:

```text
7d56b11 FastAPI/Starlette: add get_registry(app|testclient) (#186)
```

The existing checkout remains on `feature/autowiring`; the update was performed
through a temporary `main` worktree so that branch and its untracked
`.python-version` and `uv.lock` were not modified.

`svcs` is a compact but semantically dense production library:

- roughly 5,700 implementation and test lines in the inspected checkout;
- a service registry and container with caching and lifecycle semantics;
- synchronous and asynchronous factories and context managers;
- Flask, FastAPI, Starlette, aiohttp, and historical Pyramid integration work;
- strict typing and public API compatibility requirements;
- 669 commits at the time of inspection, including substantive bug fixes and
  features with tests in the same commit;
- no database server, browser, Docker daemon, or network service required for
  ordinary core tests.

The updated `main` suite ran 206 tests in 0.24 s of pytest time in a detached
worktree. The surrounding process took under one second. This is ideal for fast
research iteration: a failed validation does not turn each architectural step
into an hour-long experiment.

### What `svcs` can discriminate

`svcs` can test whether a bounded executor can:

- locate the correct abstraction in an unfamiliar but bounded repository;
- preserve sync/async lifecycle semantics;
- propagate a public API change across framework adapters;
- reason about reflection, annotations, defaults, overloads, and context
  managers;
- coordinate changes across implementation, exports, integrations, and types;
- distinguish a local override from a global registration;
- implement a behavioral contract without being handed the historical patch.

These are materially more demanding than adding one known route, data class,
and template to AgentClinic.

### What `svcs` cannot establish

It is a library, not an application. It does not cover migrations, database
state, route/schema/service layering, templates, frontend behavior, or an
end-to-end user workflow. It may also favor compact static contracts because
its APIs and invariants are unusually explicit.

An application cohort remains necessary before making a claim about general
coding. It is postponed so that it does not block Phase 7. No Phase 7 write-up
may silently generalize `svcs` results to application development.

The history is public, so commit replay is held out from the agent's provided
context, not guaranteed absent from model training. Recent 2026 commits reduce
but do not eliminate that concern. The limitation must be recorded alongside
the results.

## Initial `svcs` task ladder

The following commits are candidates, not yet an evidence cohort. Each must
pass the qualification procedure below.

| Target | Work shape | Proposed role |
|---|---|---|
| `c016b37` | Add `Registry.__iter__` | Easy floor/calibration; likely too simple for evidence |
| `c91f1f1` | Do not crash when a factory returns `MagicMock` | Narrow bug and preservation check |
| `32ddce2` | Enter context managers returned by async factories | Semantic async/lifecycle bug |
| `52c6689` | Include locally defined services in `get_pings()` | Nonlocal behavior and override semantics |
| `012b6a9` | Store Flask registry in `app.extensions` | Framework integration and preservation |
| `c5c5f48` | Change `register_value(..., enter=...)` defaults consistently | Cross-file public API propagation |
| `f81e493` | Handle stringified annotations in signature inspection | Reflection, typing, and discovery |
| `7d56b11` | Add `get_registry(app | test client)` to FastAPI and Starlette | Recent upper-middle cross-integration feature |
| `c0bd379` | Add `suppress_context_exit` | Large cross-cutting stretch task |
| `6bb3f28` | Add synchronous and asynchronous autowiring helpers | Deliberately heavy ceiling task |

The cohort should not contain only medium tasks. It needs an easy anchor that
detects a broken harness and a ceiling anchor that reveals how failure changes
when the requested feature exceeds routine bounded execution. Neither anchor
should dominate the aggregate verdict.

## The high-end ceiling: autowiring

The ceiling candidate is target commit:

```text
6bb3f28 feat: add autowire helpers (#167)
parent: 816403b
```

The historical change adds 1,486 lines across 11 files, but that count is
mostly oracle and documentation: the production implementation is a new
251-line `_autowire.py` module plus public exports. The hidden pytest oracle is
838 lines and contains 67 tests.

It is a useful ceiling because it combines several failure surfaces in one
coherent feature:

- synchronous `autowire` and asynchronous `aautowire` public APIs;
- signature inspection and lazy forward-reference resolution;
- positional-only, keyword, defaulted, variadic, and unannotated parameters;
- `dataclasses.InitVar` unwrapping;
- injecting the current `Container` specially;
- falling back to a default only when the missing service is the parameter's
  own annotation, not when a nested dependency is missing;
- sync and async service lookup;
- awaitable results and context-manager precedence;
- rejection of bare generator and async-generator factories whose cleanup
  would otherwise be lost;
- overloads and public typing behavior;
- public exports and documentation expectations.

This is intentionally above the expected comfort zone of the initial small
model. The useful questions are not only “did it pass?” but also:

- Did it find the right extension point?
- How much coherent functionality did it complete before failing?
- Was the failure localized or repository-damaging?
- Did a complete human-authored contract make the work tractable?
- Could a planner decompose it into routine subcontracts that the executor can
  complete separately without losing global coherence?

The ceiling must not be decomposed for the first direct run. That would change
the question from “where is the executor's ceiling?” to “can the planner hide
the ceiling?” Decomposition is a later planner experiment.

### Qualification already performed

Using detached temporary worktrees and the current local test environment:

- target `6bb3f28`: the 67 autowiring tests pass in 0.06 s;
- parent `816403b` plus the hidden autowiring tests: collection fails because
  `svcs.autowire` and `svcs.aautowire` do not exist;
- parent preservation suite excluding the historical Pyramid integration: 124
  tests pass in 0.19 s.

One environment issue was exposed rather than hidden: the parent's full suite
imports `httpx2` for the old Pyramid integration, while the current environment
does not contain that dependency. Before the task enters a cohort, the
qualification step must either reconstruct and freeze the historical test
environment or explicitly pre-register a preservation suite that excludes
Pyramid. The choice must be made before any model output is seen. Quietly using
today's environment and calling the full parent “green” is not allowed.

## Commit-replay construction

Each task is defined by a base commit and a target commit, but the model sees
neither the target diff nor target tests.

```text
clean worktree at target^ (base)
→ frozen task brief or contract
→ bounded executor writes candidate
→ candidate is preserved as a commit
→ grader overlays hidden tests from target
→ preservation tests + hidden oracle run
```

The task manifest records:

- repository and immutable base/target SHAs;
- task title and behavioral brief;
- contract text and hash;
- readable and writable policy;
- hidden oracle paths and targeted command;
- preservation command;
- frozen interpreter and dependency environment identity;
- base-preservation result;
- base-plus-oracle expected failure and failure class;
- target-plus-oracle expected pass;
- validation runtime;
- contract-authoring source and elapsed time;
- any exclusion, with its justification.

### Admission rubric

A task enters the pilot only when:

1. The base passes the pre-registered preservation suite.
2. The hidden oracle rejects the base for the intended missing behavior.
3. The target passes preservation and hidden acceptance.
4. The oracle tests behavior rather than the historical implementation's exact
   private structure.
5. The task can be stated behaviorally without revealing the patch.
6. It requires no network service or external mutable state.
7. Its validation is fast and deterministic enough for repeated local runs.
8. Its change is substantive: not formatting, dependency churn, mechanical
   typing cleanup, or a rename whose answer is already in the brief.
9. Its expected writable surface is bounded but not chosen after seeing model
   output.
10. Curators record any judgment used to adapt historical tests.

### Difficulty axes

The final cohort should cover several independent axes rather than a single
line from “small diff” to “large diff”:

- amount of repository discovery;
- number of coordinated files and adapters;
- semantic depth of sync/async or lifecycle behavior;
- preservation surface;
- public API and typing obligations;
- completeness of the contract;
- amount of implementation freedom left by the behavior specification.

Diff size is descriptive, not the selection criterion. A six-line lifecycle
fix can require more reasoning than a hundred-line mechanical propagation.

## Fast calibration instead of a batch after every change

Phase 7 uses a funnel:

1. **Offline qualification:** no model calls. Verify manifests, environments,
   base failures, target passes, and test timing.
2. **Single-pass screen:** one coherent-envelope attempt per candidate. Its job
   is to find broken tasks, obvious floors, and impossible ceilings—not to
   support a claim.
3. **Short pilot:** two additional attempts only on the most informative
   candidates. Classify failure modes and choose the cohort.
4. **Replay bench:** run proposed deterministic components against the saved
   candidates. No new model call is needed to learn whether a gate would have
   caught or falsely rejected each result.
5. **Focused negative probes:** use synthetic or instructed candidates to force
   scope violations, stale-tree conflicts, process timeout, cross-file moves,
   and candidate-delivery failure paths.
6. **One pre-registered evidence batch:** only after the workload and product
   path are frozen.

At the observed 40–80 seconds per local model call, screening ten tasks costs
minutes. The expensive batch is paid once, after the instrument has shown that
it can distinguish outcomes.

Pilot results are explicitly not evidence. They select tasks and thresholds;
they cannot later be pooled into the confirmatory result.

## Architecture rebuilt from the envelope

The current Cycle 2 branch remains a research inventory. It contains useful
code and lessons, but the product should not be defined by subtracting bugs from
a 3,200-line bundle until it looks small enough.

### Keep now

- Cycle 1 prompt ledger, prompt/tool coherence, analysis tests, process
  sentinel, and block-boundary integrity checks;
- the extension-lifecycle fix discovered when real Pi loading broke;
- the typed source contract and byte-stable coherent renderer;
- the exact one-call envelope invocation and budget;
- prompt hashes, receipts, and timing fields;
- the concept of running in a separate candidate Git worktree;
- process-group termination and escalation from the validation runner.

### Build as the minimum executor

```text
require repository root and clean live tree
→ create candidate worktree at exact HEAD
→ run exact coherent envelope once
→ observe changed paths and enforce scope
→ run the contract's declared validation locally
→ create durable candidate commit/ref
→ return receipt, diff summary, and candidate ref
```

There is no controller call, repair call, five-gate bundle, or automatic live
tree mutation in this minimum.

Requiring a completely clean live tree is restrictive but honest. Cycle 2
refused dirt only on writable files while the candidate read all other files
from `HEAD`; that can make it reason against stale dependencies and then deliver
code into a different live state. Dirty-workspace support is a later capability
that must snapshot the complete working state, including relevant untracked
files.

### Components that must re-earn admission

| Component | Current disposition | Admission evidence |
|---|---|---|
| Scope allowlist | Keep in the minimum | It is an explicit contract invariant |
| Candidate worktree | Keep, simplified | Negative tests show no live mutation before apply |
| Path containment hook | Research/defense in depth | Forced escape probe; no security claim |
| Smoke validation | Keep | Fast deterministic command; process cleanup verified |
| Required-literal gate | Do not include initially | Must catch failures beyond validation without false confidence |
| Source-specific AST probes | Keep with task/oracle, not generic engine | Each probe tied to a demonstrated failure class |
| Per-file symbol-loss gate | Exclude | Cross-file move false rejection must be solved first |
| Repair | Exclude | Three historical firings are not a sufficient product basis |
| Custom file promotion | Remove | Candidate commit replaces it |
| Pi tool entry point | Defer | Product path follows after candidate delivery is stable |

For a future “directness” or safety metric to enter the write-up, its definition
and admission rule must be frozen before it is computed over new results. A
component does not earn a place because its runtime is small; it earns a place
because it prevents an identified bad outcome at an acceptable false-rejection
and maintenance cost.

## Planner experiment, after the executor baseline

The cohort is first curated with complete human-authored contracts so that
executor capability is measurable. Once the candidate executor is stable, the
same bases support a planner experiment:

1. A planner sees only the base repository and behavioral task brief.
2. It emits the typed contract; it never sees the target diff or hidden tests.
3. Contract generation time, tokens, model, and human correction are recorded.
4. The unchanged bounded executor runs the resulting contract.
5. Downstream acceptance, accepted-by-deadline, and contract defects are
   attributed to the combined planner→executor system, while executor-only
   results remain separately visible.

The first planner candidate can be a larger model used once up front, matching
the product pitch. A local planner/scout is a later comparison, not an assumed
replacement. The autowiring ceiling is especially useful here: direct failure
followed by successful planner decomposition would be evidence for planning;
direct success would show that decomposition was unnecessary.

## Success and failure conditions

Phase 7 succeeds if it produces:

- a qualified multi-task `svcs` cohort that is not at universal floor or
  ceiling;
- a minimum candidate-commit executor behaviorally equivalent to the coherent
  envelope on the same contracts;
- fast replay and negative-path tests for component selection;
- one pre-registered held-out comparison whose thresholds are chosen after the
  pilot and before confirmatory runs;
- an honest separation of contract-authoring value, executor value, and
  repository-safety value.

The reset should be reconsidered if:

- no `svcs` task produces a useful middle region after qualification and pilot;
- candidate isolation materially changes model behavior or directness relative
  to the exact envelope;
- a human-authored complete contract does no better than a concise facts-bearing
  brief on the qualified cohort;
- the minimum executor cannot preserve the envelope's latency and acceptance;
- the ceiling and medium tasks fail for the same trivial harness or environment
  reason rather than revealing capability limits.

No result from `svcs` alone licenses a claim about general application coding.
That claim waits for the postponed application cohort.

