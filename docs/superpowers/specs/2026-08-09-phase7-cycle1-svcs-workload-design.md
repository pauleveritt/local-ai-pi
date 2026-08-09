# Phase 7 cycle 1 — the `svcs` replay workload

**Date:** 2026-08-09
**Status:** design, approved in brainstorming; not yet planned
**Phase:** 7 — workload first
**Roadmap:**
[`../plans/2026-08-09-phase7-workload-first-roadmap.md`](../plans/2026-08-09-phase7-workload-first-roadmap.md)
**Research basis:**
[`../research/2026-08-09-phase7-workload-first-reset.md`](../research/2026-08-09-phase7-workload-first-reset.md)
**Renumbering:** the roadmap's "cycle 2" is this cycle 1. See
[Phase 7-pre](#phase-7-pre-precondition) below.

---

## What cycle 1 builds, in one paragraph

Phase 7 rests on a claim it cannot yet test: that a bounded small-model
executor can do routine, pre-chewed coding work. AgentClinic Phase 2 has
reached ceiling and cannot distinguish approaches, so the overnight probe
carried a 3,200-line safety bundle without exercising any of it. This cycle
builds the discriminator: a commit-replay workload drawn from the `svcs`
library, where each task is an immutable base commit, a behavior-only brief, a
complete contract, and a hidden pytest oracle taken from the target commit that
the executor never sees. It builds one deterministic qualification pipeline
that proves each task is real — base green, oracle rejects base for the
declared reason, target green — and it freezes a cohort of at least six tasks
spanning a floor anchor to the autowiring ceiling. No model executor runs in
this cycle. Nothing is claimed. The output is an instrument.

## Phase 7-pre (precondition)

The completed batch-integrity and bounded-executor work becomes **Phase 7-pre**
and is retired as a live line of work. Its instruments survive the retirement —
the prompt ledger, prompt/tool coherence checks, estimator and `insufficient-n`
behavior, the process sentinel, the block-boundary split, and the
extension-lifecycle fix all stay in the tree. Retiring the phase label is not
retiring the code.

This matters here for one mechanical reason: `specs/2026-08-08-phase7-cycle1-batch-integrity-design.md`
and `specs/2026-08-08-phase7-cycle2-bounded-executor-design.md` already own the
names "phase 7 cycle 1" and "cycle 2". Renaming those artifacts to `phase7-pre-`
is a precondition task for this cycle, not an afterthought — until it happens,
two different documents claim the same cycle number and every forward reference
is ambiguous.

The roadmap's cycles therefore renumber down by one:

The roadmap's cycle 1 also carried three unfinished repair items: retain the fix
that emits prompt telemetry only after extension initialization, add a real Pi
extension-lifecycle smoke test or probe, and correct the review brief's Python
verification command to put the venv on `PATH` for subprocesses. Those are Phase
7-pre closeout tasks. They are tracked with the retirement, not with this cycle,
and this cycle does not wait on them.

| Roadmap name | Actual cycle |
|---|---|
| Cycle 1 — retain batch integrity | Phase 7-pre closeout (see above) |
| Cycle 2 — `svcs` replay manifest | **Cycle 1 (this document)** |
| Cycle 3 — envelope screen | Cycle 2 |
| Cycle 4 — candidate delivery | Cycle 3 |
| Cycle 5 — component admission | Cycle 4 |
| Cycle 6 — planner contracts | Cycle 5 |
| Cycle 7 — pre-registered batch | Cycle 6 |

## What already exists

Most of the mechanism is reuse, not new code:

| Piece | Where | State |
|---|---|---|
| Synthetic single-commit workspace | `harness/workspace.py` — `prepare_workspace` | Exists: copytree, `git init`, initial commit, hermetic `_GIT_ENV` with global/system config disabled. Needs a variant that materializes from a SHA rather than a source directory |
| Bounded child with process-group teardown | `harness/processes.py` — `run_process` | Exists, unchanged — `start_new_session=True`, `SIGTERM` to the group, escalation |
| pytest result capture | `harness/grading.py`, `harness/grading_plugin.py` — `GradeResult`, `DONE_MARKER` | Exists; the outcome-parsing shape is directly reusable for preservation and oracle runs |
| Suite fixtures and layout precedent | `examples/agentclinic/`, `examples/preservation/` | Exists — precedent for suite-as-data, though those hold seed trees rather than manifests |

## Repository source

The workload clones upstream `svcs` into a gitignored cache under `.workloads/`
and fetches the exact pinned SHAs. Detached materializations come off that
clone.

`/Users/pauleveritt/PycharmProjects/svcs` is never touched. The research doc
pinned that path, but it carries a `feature/autowiring` checkout with untracked
`.python-version` and `uv.lock`, and depending on a mutable path outside the
repository means one stray command perturbs the instrument. The manifest's
upstream URL plus SHA is the entire provenance; the cache is derived state that
can be deleted and refetched.

## Layout

```text
harness/workload.py           # manifest model; materialize base; overlay oracle; run suite
tools/qualify_workload.py     # CLI driver: qualify one task or the cohort; writes results
workloads/svcs/
  cohort.toml                 # upstream URL, cache path, frozen env identity,
                              #   cohort-wide deselects + written justification,
                              #   included/excluded task lists with reasons
  tasks/<task_id>/
    manifest.toml             # base/target SHAs, oracle paths, commands, hashes, attestations
    brief.md                  # behavior-only brief (curator-authored, diff-informed)
    contract.md               # complete contract (firewalled author + human corrections)
    contract-draft.md         # the firewalled author's uncorrected draft, kept for the delta
    qualification.json        # recorded qualification result — committed evidence
.workloads/                   # gitignored: clone cache, extracted oracles, scratch workspaces
tests/test_workload.py        # unit tests over a synthetic git repo; no svcs, no network
```

Four units with distinct jobs:

- **`harness/workload.py`** — primitives over a manifest. Knows nothing about
  `svcs` specifically, nothing about cohorts, nothing about the CLI. Given SHAs
  and paths, it materializes, runs, and returns results. A second workload
  (the postponed application cohort) should need no change here.
- **`tools/qualify_workload.py`** — orchestration and reporting only. Reads
  `cohort.toml`, loops tasks, writes `qualification.json`, prints a summary.
- **`workloads/svcs/`** — data, not code. The cohort is declarative text.
- **`.workloads/`** — derived, disposable, never committed.

`workloads/` is a new top level rather than `examples/svcs/` because
`examples/agentclinic` and `examples/preservation` hold seed source trees the
harness copies, while this holds manifests pointing at an external repository.
Different kind of thing, different home.

## The qualification pipeline

One deterministic function per task. No model calls anywhere in it.

```text
resolve cohort env + clone cache (fetch pinned SHAs if absent)
→ for each of four conditions:
      base + preservation        → must pass
      base + oracle              → must fail, with the declared fingerprint
      target + preservation      → must pass
      target + oracle            → must pass
→ run every condition three times, each in a FRESH materialization
→ require identical node-level outcomes across all three runs
→ record commands, exit codes, node outcomes, durations, and content hashes
→ tear down all workspaces, including on exception
```

Three points the roadmap left open, settled here:

**A reason class is necessary but not sufficient.** For autowiring the base
fails at *collection* — `svcs.autowire` and `svcs.aautowire` do not exist —
categorically different from a base that collects and fails assertions. But a
malformed oracle also produces `collection-error`, so the class alone still
admits broken tasks. Each manifest therefore pre-registers a **rejection
fingerprint**: the expected class, plus the specific failing node IDs or the
missing symbol names. Qualification fails when the observed fingerprint differs,
not merely when the class does.

The same reasoning forces the oracle to be *complete*. Naming only
`tests/test_autowire.py` when the target also changed supporting test modules
would grade against a partial oracle. The oracle file list is every target-side
test file the base→target diff adds or changes, and Task-level curation checks
that rather than assuming one file.

**Stability means identical, and it means fresh.** Three runs per condition, and
each run gets its own materialization — repeating inside one workspace measures
whether a suite is idempotent within a directory, which is not the question.
Comparison is node-level, using the existing `harness/grading_plugin.py` hooks
rather than parsing pytest's stdout: exit status, collected node IDs, per-node
outcomes, and counts must all match. Two runs that fail *different* assertions
are unstable even though both are `assertion-failure`.

**Grading always runs in a copy.** The oracle overlay happens on a fresh copy of
the base workspace, so a candidate workspace never contains an oracle file at
any point in its life — including when a later cycle inspects one after the
fact.

## The workspace history invariant

Task workspaces are synthetic single-commit git repositories: the tree is
exported from the cache at the base SHA, then `git init` plus one root commit.

**What this establishes, exactly.** The target commit and all later history are
absent from the workspace's own object store, and the workspace has no remotes
and no alternates pointing back at the cache. That is a checkable invariant with
a direct test, and it is the entire claim.

**What it does not establish** — stated plainly, because an earlier draft of
this document called it "the oracle seal" and that name promised far more:

- nothing about whether a process could read `.workloads/svcs.git` by path;
- nothing about network reachability of a public repository;
- nothing about what a model already knows from training on public history;
- it is not a confinement mechanism, and no test here makes it one.

Confining a process to its packet root is the executor's problem, not the
workload's. Phase 7-pre built a path-containment guard for exactly that, and it
must re-earn admission in the executor cycle under the roadmap's replay rules.
This cycle's narrower obligation is to produce workspaces and author packets
whose *layout* does not hand anyone the answer, and to test that layout.

Packet hygiene follows from the same logic. The author packet is staged outside
`.workloads/` — whose sibling is the clone containing every target — so that
"the author must not read the clone" is a statement about where things are, not
only about what someone was told.

The remaining cost is a tree export per attempt, negligible on a 5,700-line
repository. The loss is upstream history inside the workspace, which matters for
curation — performed outside the workspace — and not for execution.

Hidden oracle files are read from `target_sha` at grade time and never committed
to this repository.

## Manifest schema

```toml
task_id       = "svcs-autowire"
role          = "ceiling"          # floor | medium | stretch | ceiling
axes          = ["discovery", "async-lifecycle", "public-typing", "cross-file"]

[source]
upstream      = "https://github.com/hynek/svcs"
base_sha      = "816403b..."                   # full 40-character SHAs, never abbreviated:
target_sha    = "6bb3f28..."                   #   a short SHA is not immutable

[task]
brief            = "brief.md"
brief_sha256     = "..."
contract         = "contract.md"
contract_sha256  = "..."
contract_version = 1

[policy]
readable         = ["src/**", "tests/**", "docs/**", "README.md"]
writable         = ["src/svcs/**"]
candidate_output = ["src/svcs/_autowire.py", "src/svcs/__init__.py"]

[oracle]
files          = ["tests/test_autowire.py"]     # EVERY target-side test file the
                                                #   base->target diff adds or changes
files_sha256   = { "tests/test_autowire.py" = "..." }
command        = ["pytest", "-q", "-p", "no:cacheprovider", "tests/test_autowire.py"]

[oracle.rejection]                              # the fingerprint, not just the class
class           = "collection-error"
missing_symbols = ["svcs.autowire", "svcs.aautowire"]
failing_nodes   = []                            # used instead when the base collects

[preservation]
command         = ["pytest", "-q", "-p", "no:cacheprovider"]
deselects       = []                            # target state; see Environment freeze
deselect_reason = ""

[environment]
id          = "svcs-cohort-2026-08-09"
python      = "3.14.2"                          # exact; verified at run time
platform    = "macosx-15-arm64"
lock_sha256 = "<from the committed uv.lock>"    # nonempty and exact, never blank

[authoring]
brief_author          = "curator"
contract_author       = "firewalled-model"
authoring_seconds     = 0
correction_seconds    = 0
correction_diff_lines = 0

[qualification]                                 # written by the tool, never by hand
# status, base_preservation, base_rejection_observed, target_preservation,
# target_oracle, runtimes, repeat_stability, recorded_at
```

## Gates versus attestations

The admission rubric has ten items; only some are machine-decidable. The design
splits them rather than pretending the script covers all ten.

| Rubric item | Enforced by |
|---|---|
| 1 Base passes preservation | **Gate** — script runs it |
| 2 Oracle rejects base for the intended reason | **Gate** — exit code *and* declared reason class must match |
| 3 Target passes preservation and oracle | **Gate** — script runs it |
| 6 No network or external mutable state | **Gate (weak) plus attestation** — suites run with a scrubbed environment and no proxy variables; a network-dependent test that still passes is caught by the curator, not the tool |
| 7 Fast and deterministic | **Gate** — each suite runs three times, outcomes must be identical, wall time recorded and thresholded |
| 4 Oracle tests behavior, not private structure | **Attestation** |
| 5 Statable behaviorally without revealing the patch | **Attestation** |
| 8 Change is substantive | **Attestation** |
| 9 Writable surface bounded, chosen before model output | **Attestation plus ordering** — `policy.writable` is hashed into the frozen manifest before any attempt |
| 10 Test adaptations recorded | **Attestation** |

Attestations are prose fields, not booleans. A checkbox is worth nothing; a
sentence explaining why a deselect is safe is reviewable, and can be shown to be
wrong.

**Required, not optional.** `load_manifest` demands all five keys, each with
nonempty prose, and refuses the manifest otherwise. An attestation that silently
defaults to absent is the same as no attestation while looking like one. The
same rule covers every deselect reason and every cohort exclusion reason: the
cohort file must account for every candidate as either included or excluded with
a stated reason, and a candidate that appears in neither list is an error.

One item deserves its honest label. **"No network" is an attestation plus
environment hygiene, not a gate.** Scrubbing proxy variables and passing a
minimal environment removes the common accidental paths; it does not stop a test
from opening a socket. Calling it enforcement would be false.

## What freezes, and when

Curation corrects predictions. That is what qualification is *for*: a
`[oracle.rejection]` fingerprint is a guess until the pipeline checks it, and
three of the ten candidates had theirs corrected before the cohort froze. Doing
that is not tuning, because nothing being corrected against is a graded outcome
— base behaviour is a deterministic fact.

**That latitude ends at the first model attempt.** From the moment any executor
runs against this cohort:

- `oracle.files` and `oracle.command` are frozen. A task whose oracle scope
  turns out to be wrong is **excluded**, not renarrowed.
- `[oracle.rejection]`, `base_sha`, `target_sha`, and the environment fields are
  frozen.
- Only `contract.md` may change, under the existing rule: any edit bumps
  `contract_version`, and that task's prior attempts are invalidated rather than
  pooled with later ones.

The mechanism is already in place: every `qualification.json` records
`manifest_sha256`, and every attempt record must carry the same hash. An attempt
whose manifest hash differs from the frozen one is a different task wearing the
same name.

One edit in this cohort used that latitude and is called out rather than buried.
`suppress-context-exit` had its oracle command narrowed to `tests/test_container.py`
after the first run showed two undeclared failures in `tests/test_registry.py`,
caused by the same commit's change to a shared fixture's arity rather than by
the feature. The reasoning is in that manifest's `adaptations`, the failed
prediction is preserved in the evidence commit, and it is legitimate *only*
because no model had run. Under the rule above the same situation would now
require exclusion.

## Contract authoring firewall

Three roles. The point is that the middle one is information-starved by
construction.

**Curator** sees everything, including the target diff. Produces `brief.md`
(behavior only), selects oracle files, sets `policy.writable`, writes
attestations. Diff-informed by necessity, which is why the brief stays short and
behavioral and why rubric item 5 is a signed judgment rather than a check.

**Contract author** runs in a fresh context with exactly two inputs: a
materialized base workspace at `base_sha`, and `brief.md`. No path to the clone
cache, the oracle store, the target tree, or the curator's reasoning. Produces
`contract-draft.md`.

**Human corrector** edits the draft into `contract.md`. `correction_seconds` and
`correction_diff_lines` are recorded; the draft is kept so the delta is
inspectable.

### The corrector is not blind, and the estimand says so

The corrector and the curator are the same person. That person has read every
target diff, so `contract.md` is **diff-informed** — privileged information
reaches the baseline contract through the correction pass, and no amount of
procedure inside this cycle changes that.

Two consequences, both stated rather than papered over:

1. `contract.md` is not a "blind human-authored contract." It is a firewalled
   draft corrected by someone who has seen the answer. That likely makes it a
   *better* contract; it also makes it a contaminated one for any comparison
   that assumes blindness.
2. The comparison this cycle enables is therefore **corrected versus
   uncorrected output of one authoring process** — an ablation measuring what
   diff-informed human correction adds to a firewalled draft. It is *not* the
   roadmap's human-contract-versus-planner comparison, and no write-up may
   present it as one.

The roadmap's original estimand remains available later, at a price: a second
party who has never seen a target diff or an oracle does the correction. That
is a deliberate deferral, not an oversight.

### Provenance the authoring run must record

"Start a fresh session" is a procedure, not a reproducible firewall. Every
authoring run records, in the manifest:

- authoring model and version;
- the exact prompt, by hash, with the prompt text committed;
- tool grants and budget;
- the filesystem roots the author could reach;
- packet contents by hash (base tree hash, brief hash);
- draft output hash, and `contract.md` hash;
- elapsed authoring and correction time, and correction diff size.

Without those fields an authoring run cannot be repeated or audited, and the
recorded `correction_diff_lines` measures nothing in particular.

Two ordering rules make the freeze real: the brief is written before the
contract, and both are hashed into the manifest before any model attempt. Any
change to either bumps `contract_version` and invalidates that task's screening
results. The roadmap's "never silently edit a contract between attempts" becomes
a hash check rather than a discipline.

## Environment freeze

One cohort environment, resolved once: a single Python and a single lockfile,
identified in every manifest by `environment.id` and `lock_sha256`.

The environment is a hand-authored *union* of what the cohort's bases need,
not a sync of any one base's own lockfile. It installs dependencies only — the
project itself is never installed, so `svcs` can be imported from exactly one
place: the materialized workspace, via `PYTHONPATH=<workspace>/src`. That
removes any question of which copy a test imported.

```toml
[project]
name = "svcs-cohort-env"
version = "0"
requires-python = ">=3.14,<3.15"
dependencies = [
  "attrs>=21.3.0", "typing_extensions>=4.13.0",
  "pytest", "pytest-asyncio", "sybil>=6",
  "aiohttp", "fastapi", "flask",
  "httpx<0.28", "httpx2",
  "pyramid", "setuptools<82",
  "starlette", "sqlalchemy",
]
```

Three of those pins were derived empirically while designing this cycle, and
each is load-bearing:

- **`httpx` and `httpx2` both.** Bases before the 2026 migration `import httpx`;
  later ones `import httpx2`. A union spanning the ladder needs both.
- **`httpx<0.28`.** The historical Pyramid tests construct
  `httpx.Client(app=...)`, which 0.28 removed. Without the ceiling, four bases
  fail collection or error.
- **`pyramid` and `setuptools<82`.** Present in the older bases' `optional`
  group, dropped from the newest. The union keeps them so historical
  integration tests run rather than being excused.

`pyramid` deserves one further note: **upstream `svcs` plans to drop Pyramid
support.** That does not affect this cohort — the historical bases still ship
Pyramid tests, and those tests are part of their preservation surface. It does
mean the pin is historical-bases-only and will age out as newer targets enter,
and that the frozen lock is what keeps an eventually-unmaintained `pyramid`
installable for this cohort.

**This supersedes the research doc's Pyramid exclusion.** That constraint was an
artifact of the inspecting venv lacking `httpx2`, not a property of the
workload.

**The counts below are measured against the committed lock**
(`workloads/svcs/env/uv.lock`, sha256 `6d0058e1…`, 57 packages) on a verified
CPython **3.14.2**, via the same `materialize` used by qualification.

That verification mattered. An earlier draft of this table came from an
*unlocked* resolution, and an independent reviewer resolving the same dependency
list got different collections — 203 rather than 191 for `98198df`, 142 rather
than 130 for `816403b`. Re-running under the committed lock reproduces the
figures below exactly. Neither reading was wrong; two unlocked resolutions of one
dependency list are simply two different environments, which is precisely why the
lock is part of the evidence rather than an implementation detail.

| Base | Target it precedes | Full-suite result | pytest |
|---|---|---|---|
| `32ddce2` | `c016b37` | 131 passed | 0.29 s |
| `f8585ce` | `c91f1f1` | 140 passed | 0.26 s |
| `25d8a0b` | `32ddce2` | 129 passed | 0.25 s |
| `31bc6df` | `52c6689` | 137 passed | 0.26 s |
| `85827a1` | `012b6a9` | 128 passed | 0.26 s |
| `e9d9cc1` | `c5c5f48` | 119 passed | 0.25 s |
| `4b05ab8` | `f81e493` | 121 passed | 0.25 s |
| `98198df` | `7d56b11` | 191 passed | 0.28 s |
| `1676980` | `c0bd379` | 132 passed | 0.26 s |
| `816403b` | `6bb3f28` | 130 passed | 0.24 s |

Every base runs its full suite green, Pyramid included, so the exclusion is
unnecessary. Pytest time is 0.24–0.29 s; end-to-end per condition, including
tree export and `git init`, is 1.1–2.5 s. Twelve conditions per task therefore
cost well under a minute, which is what makes the three-runs-per-condition
stability gate affordable rather than aspirational.

Short SHAs appear above for readability. Manifests carry the full
40-character forms, which `load_manifest` requires.

One property of a union environment must be recorded rather than glossed:
historical bases run against dependency versions **newer** than they were
written for. This preserves fairness across arms — every arm sees the same
environment — but it slightly weakens historical fidelity, since a base is not
being validated in the world it shipped in. The alternative, per-base
reconstruction, was rejected in this design for cost and cross-task variance.

The deselect mechanism stays in the schema as a fallback, under the same rule:
any deselect must carry a written argument that the task's behavior cannot
affect the deselected tests, and must be frozen before any model output is seen.
The cohort's target state is zero deselects, and a task that needs one is a
worse task than one that does not.

## Candidate ladder

Qualified in order, stopping once at least six tasks cover the required axes:

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

The ladder's role column describes work shape. It is not the manifest's `role`
enum: everything between the floor anchor and the stretch task is `medium`
there, distinguished by `axes` rather than by a position on a single line from
small diff to large. Diff size is descriptive, never the selection criterion.

The autowiring entry preserves facts already verified: parent `816403b`; 67
hidden autowiring tests reject the parent during collection because
`svcs.autowire` and `svcs.aautowire` do not exist; those tests pass on the
target in 0.06 s. Its preservation figure is corrected to 130 tests passing with
Pyramid included, measured in the frozen union environment.

## Error handling

**Failure is recorded, not swept.** A task failing a gate becomes
`status = "disqualified"` in its own `qualification.json`, with the failing gate
named and observed-versus-declared values kept. It stays in
`workloads/svcs/tasks/`. `cohort.toml` carries explicit included and excluded
lists with a reason per exclusion, so "record every exclusion" is a property of
the data layout rather than something to remember.

**Teardown is unconditional.** Every workspace is created through a context
manager and removed on the way out, including on exception.

**Drift fails hard.** An oracle file whose content hash differs from
`oracle.files_sha256` is an error, never a silent re-baseline. Same for
`environment.lock_sha256`.

## Testing

`tests/test_workload.py` builds a small synthetic git repository — a base commit
and a target commit adding one function plus its test — and runs the whole
pipeline against it offline in milliseconds. The cases that earn their keep:

- base preservation passes; target passes preservation and oracle
- oracle rejects base, and a fixture whose base fails for the *wrong* reason
  class is disqualified rather than admitted
- the candidate workspace never contains an oracle file at any point
- `git cat-file -e <target_sha>` **fails** inside a materialized workspace — the
  seal asserted as a fact, not assumed from policy
- a deliberately flaky fixture test is caught by the three-run stability gate
- an oracle hash mismatch raises
- a mid-pipeline exception still removes every workspace

A small number of integration tests touch the real clone cache and skip when it
is absent, so the suite never depends on upstream availability.

## Acceptance

- At least six qualified tasks: one floor anchor, three medium tasks on
  *different* difficulty axes, one stretch, and the autowiring ceiling.
- Every qualified task: base preservation green, base rejection matching its
  pre-registered fingerprint, target green on both suites, all four conditions
  three-run stable at node level in fresh materializations, and validation under
  the enforced sub-minute threshold.
- A committed `uv.lock`, a verified 3.14.2 interpreter, and every preservation
  count in this document re-measured against them.
- A committed `qualification.json` per task; `cohort.toml` lists inclusions and
  exclusions with reasons.
- Zero deselects. Every qualified task runs its base's full preservation suite
  in the frozen union environment. Any deselect that does prove necessary
  carries a written justification and is frozen before any attempt.
- Phase 7-pre renaming complete; no two documents claim the same cycle number.
- Unit suite passes offline with no `svcs` clone present.

## Model cost

The roadmap records this cycle's model cost as *None*. That is true of
qualification, which makes no model calls at all, but not of the cycle: the
firewalled contract author is a model, roughly ten authoring calls plus human
correction passes. Small, but it should not appear as zero in the phase's cost
accounting.

## Out of scope

Stated so the work cannot drift into it: no envelope runs, no screening
attempts, no candidate delivery, no gates or component admission, no planner
study. This cycle ends when a frozen, qualified cohort exists and nothing has
yet been asked of a model executor.

## Risks

**The cohort lands at floor or ceiling.** Qualification proves each task is
well-formed; it cannot prove the cohort discriminates. That only becomes visible
in the next cycle's screen. The roadmap's stop rule applies: a universal floor
or ceiling means the reset is reconsidered, not that thresholds are adjusted.

**Training contamination.** `svcs` history is public. Holding the target diff
out of the agent's context does not hold it out of model training. Recent 2026
commits reduce the concern without eliminating it; the limitation is recorded
alongside every result.

**Library, not application.** No `svcs` result licenses a claim about general
application coding. That claim waits for the postponed application cohort, and
no Phase 7 write-up may generalize past the cohort it measured.

**Diff-informed contracts.** The baseline contracts are corrected by someone who
has seen the target diff. Any comparison built on them measures the value of
diff-informed correction, not the value of blind human contract authoring. The
blind variant is deferred, and the deferral must appear wherever the contract
arm is reported.

**Union-environment fidelity.** Historical bases are validated against
dependency versions newer than they shipped with. Fair across arms, slightly
unfaithful to history.

**A layout invariant is not confinement.** The workspace history invariant and
the packet layout make the answer hard to stumble into. They do not stop a
process that goes looking for it. Any claim about what an executor *could not*
reach belongs to the executor cycle, after the containment guard re-earns
admission.
