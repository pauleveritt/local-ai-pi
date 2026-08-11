# Brief: Phase 7 cleanup and small-group distribution

**Repository:** `local-ai-pi`, branch `phase7-workload`  
**Audit point:** `0373ed9`, while the pre-registered Cycle 7 batch is running  
**Audience:** the owner and the first one or two collaborators  
**Purpose:** preserve the research record, remove avoidable complexity, and make one product path understandable and runnable without pretending the repository is already a polished public project

## Verdict

This is feasible. The repository is not yet reasonable to hand to a new
collaborator, but it no longer needs an architectural reset before that can
happen. The recent commits changed the answer: the candidate-delivery path and
the bounded implementer now live together on this branch, use the same typed
handoff, and have tests around the important failure boundaries. The earlier
problem -- a research repository describing an engine that existed somewhere
else -- is gone.

The remaining problem is mostly one of **separation and presentation**:

- the current product path is buried under several generations of experiments;
- roughly 106 MiB of tracked `workloads/svcs/screen/` evidence, including 142
  JSONL transcripts, sits beside the code a contributor is meant to understand;
- the top-level `README.md`, `BRIEF.md`, and 1,888-line `ROADMAP.md` describe
  different moments in the project rather than one current entry point; and
- one newly introduced guard integration appears to contradict a capability of
  the mutation engine and should be resolved before distribution.

The right target is a **curated collaborator repository backed by an immutable
research archive**, not a destructive rewrite of this repository's history.
The current repository should remain the provenance record. A fresh or
history-light shareable repository can then contain the product path, compact
evidence, current documentation, and only the tests and workload fixtures that
still explain or protect shipped behavior.

Do not begin artifact removal or history-changing cleanup while Cycle 7 is
running. Documentation and a cleanup inventory are safe; deletion, movement,
cell changes, and commits should wait.

## What the recent commits earned

The changes from `220c319` through `38298d8` are not merely more spike
machinery. They close the largest gap identified in the previous cleanup
review: there is now one end-to-end candidate path worth curating.

### Product path now present on this branch

- The Phase 6 mutation and implementer stack is ported under
  `extensions/orchestration/` and `extensions/guards/`.
- The model can propose small, diff-shaped edits instead of reproducing a
  complete 30 KiB file. The mutation engine applies those edits against a
  revision-checked file and evaluates the resulting whole file before an
  atomic write.
- Whole-file and diff-shaped mutations share path, baseline, stale-revision,
  proposal-size, newline, mode, and public-symbol checks.
- Candidate delivery now invokes the bounded implementer and terminates in a
  reviewable Git ref rather than promotion into the user's branch.
- The implementer cell records and verifies the complete same-repository
  extension import closure, closing the earlier digest blind spot where a
  dependency could change without changing the cell identity.
- Typed handoff construction now supports the four-task smoke/comparison
  cohort, carries the effective preservation command, and keeps the brief and
  locating-contract arms identical except for `contract.task`.
- The temporary `maxTokens` increase is managed by a restoring context rather
  than a manual edit that can silently mutate an experimental cell.
- The statistical procedures used by the Cycle 7 comparison are implemented
  and tested rather than recomputed by hand.

### Correctness work worth keeping

The review/fix sequence also caught defects at the right layer: literal
replacement corruption from JavaScript replacement syntax, incorrect gained-
symbol bookkeeping, missing import-closure hashing, a validation gate that
rejected correct `flask-extensions` candidates, and misleading defaults in
the delivery CLI. These fixes belong in the shareable product. They are not
research residue.

The cleanup commits removed dead ledgers, exports, helpers, and style noise.
That is useful, but it has not materially reduced the repository's onboarding
surface: tracked experiment artifacts and stale narrative documents remain the
dominant cost.

## One correctness gate before distribution

### The pre-edit guard and `removableSymbols` disagree

`extensions/orchestration/implementer.ts` now calls the contract-blind
`createPreserveSymbols()` guard before the authoritative mutation engine. The
guard refuses an `edit` whenever a function, class, or route appears in an
`oldText` but not in the union of that call's `newText` values.

The mutation engine deliberately supports two cases the pre-guard cannot see:

1. a rename or removal explicitly authorized by
   `HandoffContract.removableSymbols`; and
2. a cross-file move whose destination was written earlier in the invocation
   and recorded in the engine's gained-symbol ledger.

The pre-guard receives neither the contract nor that ledger. It therefore
blocks both cases before `MutationEngine.proposeEdits()` can admit them. The
existing rename and move tests exercise the mutation engine in isolation;
the new wiring tests only inspect source text to prove that the guard is
called. They do not test the integrated behavior. The guard's suggestion to
perform an intended deletion in a separate edit does not help: that separate
edit is rejected for the same reason.

Before distribution:

1. Add an integrated test that sends a contract-authorized rename through the
   implementer's actual `tool_call` and registered `edit` path.
2. Add the corresponding destination-first cross-file move test.
3. Choose one source of authority. The simpler resolution is to remove this
   redundant pre-guard from the implementer and let the revision-aware,
   contract-aware mutation engine decide. If early refusal is retained, make
   it consume the same contract and invocation ledger rather than implementing
   a second, contradictory policy.
4. Preserve the standalone guard only if it still has a separately supported
   Pi-extension use case. Do not cite it as defense in depth when it narrows
   valid behavior differently from the engine.

This does not invalidate the running Cycle 7 comparison: the four generated
typed handoffs do not declare `removableSymbols`, and the comparison was
frozen with this integration already present. It is nevertheless a product
correctness defect for general work and a blocker to telling collaborators
that declared renames and moves are supported.

## What the running Cycle 7 batch changes

Cycle 7 is the last confirmatory evidence batch before cleanup. It compares
brief-only and locating-contract task text through the same bounded
implementer on four tasks, with eight attempts per arm and task. Its result
can change the project's evidence-backed product claim -- especially whether
locating information improves oracle-passed rates -- but it does not change
the repository cleanup plan in this brief.

Treat completion as a hard cleanup gate. Before moving or deleting evidence,
confirm all of the following:

1. The batch finished, or was formally aborted under its pre-registered abort
   rules.
2. `pi-agent-dir/models.json` returned from the intentional 32768-token bump
   to its committed 8192-token value.
3. All intended attempts, voids, and replacements are accounted for; no
   denominator silently includes a void.
4. Per-task candidate-created and oracle-passed results, Wilson intervals,
   Newcombe differences, floor/ceiling flags, and abort-condition checks were
   computed by the tested helpers.
5. A committed research record states both the result and what it does not
   establish. Pilot results must not be pooled into the confirmatory result.
6. Raw transcripts, receipts, patches, cell identity, contract bytes, and
   task-manifest hashes have been copied into the external evidence archive
   and the archive has a generated checksum manifest.
7. Any candidate refs created by the run have been inventoried before cleanup,
   even if the runner normally removes or consumes them after grading.

If Cycle 7 finds a new harness or validation defect, fix and re-freeze before
distribution. If it merely finds disappointing or inconclusive model results,
record them and continue with cleanup. A negative product result is not a
reason to keep 100 MiB of raw telemetry in the collaborator repository.

## Cleanup and distribution sequence

### 1. Freeze and archive the evidence

Keep the full current repository and its Git history as the primary research
provenance. In addition, create an external, immutable evidence bundle for
the large runtime artifacts. The bundle should contain raw JSONL transcripts,
receipts, patches, summaries, cell manifests, task/contract versions, and a
machine-generated SHA-256 manifest. Record the bundle's location and checksum
in the repository, but do not require a collaborator to download it to run
tests or use the executor.

The archive is not a dumping ground with no index. Give every retained batch a
small manifest naming:

- its pre-registration or prediction document;
- Git revision and resolved cell;
- tasks, arms, and repetition count;
- result summary and research write-up;
- raw-artifact paths and hashes; and
- whether the batch is valid, superseded, pilot-only, or withdrawn.

This preserves auditability more reliably than leaving hundreds of files in a
tree whose status is known only from surrounding prose.

### 2. Create the curated repository boundary

Prefer a fresh shareable repository, or a clean export branch with intentionally
short history, over filtering the current repository in place. Keep:

- `extensions/orchestration/` and the guards actually used by the product;
- candidate delivery, Git/worktree safety, process handling, liveness, typed
  handoff, cell verification, and the small Pi invocation seam;
- the four qualified task definitions needed for a collaborator smoke test;
- compact summaries, candidate patches, predictions/pre-registrations, and
  research conclusions that substantiate current claims;
- minimized transcript fixtures that reproduce specific telemetry and guard
  behavior; and
- tests that protect a live product boundary or a still-published evidence
  claim.

Externalize from the shareable repository:

- raw screen and overnight JSONL transcripts;
- superseded and buggy-grading result directories;
- rejected/void contract-authoring drafts once tests no longer read their
  repository paths;
- repeated per-run files whose compact summary, patch, and checksum are enough
  for ordinary review; and
- derived environments and caches.

Do not delete `harness/liveness.py`, `harness/similarity.py`,
`tools/replicate.py`, or `tools/stage_author_packets.py` merely because they
are small or specialized. They have current, distinct jobs and are not the
source of the complexity. Judge them after the artifact boundary is clean.

### 3. Decouple tests from historical artifacts

`tests/test_screen.py` currently reads committed void drafts under
`workloads/svcs/overnight/drafts/` and a rejected `draft-qwen` contract to
prove the authoring gate rejects those exact bytes. That makes obsolete
research artifacts runtime dependencies of the test suite.

Replace those dependencies with small named fixtures that preserve the
failure shapes: one solution-bearing draft, one empty/preamble-only draft,
one wrapped contract, and one plainly written contract containing fences.
If exact historical bytes matter for a published claim, keep their hashes and
archive locations in the research record; the default unit suite does not
need multi-megabyte authoring transcripts or an eight-file rejected draft
bank.

Then add repository policy checks that fail when raw transcripts or oversized
runtime artifacts are newly tracked. A narrow allowlist for intentionally
minimized JSONL fixtures is preferable to a blanket exception.

### 4. Simplify the active code path

Do this after artifact removal, because otherwise line-level refactoring will
look more valuable than it is.

- Extract `_pi_command`, `pi_env`, and the default model definition from the
  legacy 32 KiB `harness/runner.py` into a small Pi invocation/configuration
  module. `screen.py`, `author_contract.py`, `leak_probe.py`, and
  `deliver_candidate.py` all currently reach into `runner.py` for these
  primitives.
- Keep `harness/typed_contract.py` explicitly narrow for the Cycle 7 result,
  but do not present it as general product contract authoring. Before a
  collaborator adds a fifth task, either design the manifest-to-handoff
  boundary or make the four-task restriction fail clearly at the CLI.
- Give the running comparison a discoverable checked-in driver or command.
  The pre-registration is detailed, but a collaborator should not need session
  history to learn what produced its results.
- Trace the one supported route from CLI to candidate ref and remove only dead
  alternatives proven unreachable from that route. Avoid folding
  `liveness.py` or `similarity.py` into larger modules just to reduce the file
  count.

### 5. Rewrite the contributor front door

The current top-level documents are historical artifacts:

- `README.md` says Phases 1--5 are complete and primarily advertises the old
  standalone loop breaker and AgentClinic harness.
- `BRIEF.md` still describes a clean-slate bootstrap and says nothing has been
  transplanted, which is now false.
- `ROADMAP.md` is 1,888 lines and cannot serve as a first-day task map.

Replace their front-door role, not their historical value:

1. A short README should state what is usable now, what evidence supports it,
   what remains experimental, prerequisites, and one verified command that
   produces or refuses a candidate ref.
2. A current architecture page should show the single path: task input ->
   typed handoff -> bounded implementer -> mutation engine -> preservation
   validation -> candidate ref -> optional hidden-oracle grading.
3. A contributor page should describe the test commands, local-model optional
   path, repository conventions, and three starter tasks small enough to
   finish without reading the research history.
4. Move the long roadmap and old brief under a clearly labeled history or
   research section. Do not silently rewrite the old decisions into a cleaner
   story.
5. Add an evidence index that distinguishes pre-registration, pilot,
   confirmatory result, correction, superseded result, and raw archive.

### 6. Perform a clean-machine collaborator rehearsal

Before inviting people, test the repository as they will encounter it, not
from the owner's configured checkout:

- clone the curated repository into a new directory;
- follow only the README;
- run the Python and Bun suites without a model server;
- verify model-dependent tests are explicitly opt-in;
- configure a model through documented values rather than owner-specific
  paths;
- run one small candidate-delivery smoke task;
- inspect and discard the resulting candidate ref; and
- confirm no credentials, absolute owner paths, untracked generated files, or
  multi-megabyte telemetry appear.

Have the first collaborator record every undocumented assumption. Fix the
front door before explaining those assumptions privately; otherwise the owner
becomes an undocumented runtime dependency.

## Distribution acceptance checklist

The repository is ready for one or two collaborators when:

- Cycle 7 has a committed disposition and its raw evidence is archived.
- The temporary model configuration is restored and the worktree is clean.
- The preserve-symbol/removable-symbol contradiction is resolved and covered
  through the integrated implementer path.
- Default Python and Bun tests pass from a fresh clone without a live model.
- The ordinary clone does not contain the 100+ MiB raw transcript corpus.
- No unit test depends on rejected overnight drafts at their historical paths.
- One README command reaches a candidate ref or an actionable refusal.
- The README and architecture page agree on which executor is the product.
- The four-task typed bridge is labeled as a limited evaluation bridge, not a
  general planner implementation.
- Every retained evidence claim points to a compact result and an externally
  hashed raw archive.
- CI rejects newly tracked raw transcripts, oversized artifacts, and secrets.
- A collaborator can complete one starter change without reading the old
  roadmap or asking the owner how the repository is meant to run.

## What not to do

- Do not clean the live research branch destructively or rewrite its history
  before the evidence archive is verified.
- Do not use Cycle 7's result as permission to add another arm, workload, or
  repair mechanism before the repository is shareable.
- Do not spend the cleanup budget merging every small module. Artifact volume,
  stale narrative, and multiple implied entry points are the real problems.
- Do not promise a general planner or general coding executor. The shipped
  typed bridge is four-task-specific and the current evidence is an svcs
  commit-replay cohort.
- Do not postpone distribution until the research program is complete. The
  small group needs an honest, bounded product path and a legible research
  record, not a final scientific verdict.

## Recommended immediate order

1. Let Cycle 7 finish without commits or configuration changes.
2. Verify restoration, completeness, abort rules, candidate refs, and raw
   evidence; write and commit the result.
3. Fix and integrally test the preserve-symbol policy contradiction.
4. Produce and verify the external evidence archive plus index.
5. Create the curated repository/export and remove historical artifact
   dependencies from tests.
6. Extract the Pi invocation seam and document the four-task bridge boundary.
7. Rewrite the README/architecture/contributor front door.
8. Run a clean-clone rehearsal, then invite the first collaborator.

That is enough. Further engine improvement should happen with collaborators
inside the smaller repository, one measured capability at a time.
