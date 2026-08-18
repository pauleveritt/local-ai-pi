# The two-repo rewrite: a Python engine and an evals reboot

**Date:** 2026-08-16  
**Status:** planning record — direction and sequence, not an implementation spec  
**Repositories:** `satyrn-engine` and `satyrn-evals`

## Outcome

Start two new repositories. Treat this repository as evidence, not as source to
move.

Use Python for the engine core and keep the Pi integration as a thin TypeScript
adapter. Prove that boundary in the second engine slice. Until that proof
passes on POSIX and Windows, Python is a working decision rather than an
irreversible commitment.

Start with one Python process per operation. Do not build a persistent sidecar,
pool, supervisor, circuit breaker, subinterpreter pool, or general JSON-RPC
layer. A one-request/one-response subprocess is slower but much smaller, has no
session lifetime, and is adequate until measurement says otherwise.

Keep the existing always-on guards in TypeScript and out of the initial
roadmap. They fired zero times in the recorded 24-run comparison, and moving
them would put Python on every ordinary Pi tool call. They have not earned that
cost.

Build `satyrn-evals` as a diagnostic loop first. Statistical claims,
pre-registration, confidence intervals, condition enforcement, model canaries,
and A/B publication machinery are later layers with later consumers.

## 1. What the two products are

### `satyrn-engine`

The engine turns a bounded contract into a candidate change without modifying
the caller's working tree.

It owns:

- the Python library and CLI;
- contract parsing and validation;
- writable-path and revision enforcement;
- candidate worktree, validation, commit-or-discard, and receipt behavior;
- the Pi package and its TypeScript adapter;
- the internal Pi-adapter protocol and its compatibility fixtures.

It does not own workloads, grading, repeated runs, comparison statistics, or
contract authoring.

### `satyrn-evals`

Evals captures a Python-development task, invokes an attempt command, preserves
what happened, and grades the result offline.

It owns:

- task capture and task manifests;
- known-good and known-broken fixtures;
- patch application, oracle execution, and grading;
- transcript, patch, receipt, and conditions recording;
- summaries of failure reasons and thrashing behavior.

It does not import engine internals. Its engine seam is an executable attempt
command run inside an eval-owned disposable worktree. Evals sets that
worktree as the command's current directory, appends the absolute contract
path as the final argument, and captures stdout, stderr, and the resulting Git
diff. The command needs no eval-specific SDK. A fake command must satisfy the
same seam so eval development never waits for the real engine.

### The boundary

There is no shared third package.

- The engine owns contracts and receipts.
- Evals owns tasks and grades.
- An attempt command receives one positional contract path, writes only in its
  current working tree, and reports through stdout and stderr.
- Engine delivery runs an attempt command inside an engine-owned worktree and
  turns the result into a candidate ref. Evals runs the same seam inside an
  eval-owned worktree and captures the resulting patch.
- An engine receipt, when present, is retained by evals as an opaque
  additional artifact.
- Evals records `protocol_version`, engine version, and an immutable engine
  identity: a package digest for an installed artifact or a Git commit for a
  source checkout.

Do not migrate the old `extensions_sha256` cells. They remain valid historical
records in this repository. The new repositories start a new record format;
no compatibility sentinel is needed because no old checkpoint is rewritten or
resumed.

## 2. Harvest rules

The valuable output of this repository is the record of plausible ideas that
failed.

### Carry forward

- Index gotchas by the symptom a contributor sees, not by the mechanism that
  caused it.
- Preserve retractions, silent-zero incidents, instrument defects, and the
  do-not-re-derive list.
- Keep pure decision functions where they buy both replay and unit tests.
- Keep process boundaries injectable. A test seam is the extension seam; do
  not add a second plugin system.
- Keep capture separate from grading. A saved patch and transcript must be
  regradable without another model call.
- Keep the known-good/known-broken evidence floor for every grader.
- Keep worktree isolation, dirty-tree refusal, process-group teardown for
  model and validation commands, and results written outside model-controlled
  stdout.
- Keep a repository-weight budget and a concept budget from the first phase.

### Leave behind

- The current module layout and import graph. Re-implement behavior from tests
  and incidents; do not transplant `harness/`.
- Recorded workload corpora and generated screen artifacts.
- `Suite`, `Improvement`, `RunConditions`, cells, condition equality, void and
  retry accounting, intervals, and pilot/confirmatory machinery.
- `inspectContract` and generalized checker frameworks.
- Automatic commit mining before three tasks have been captured manually.
- A persistent Python sidecar before per-operation startup is measured as a
  material cost.
- A subinterpreter pool. The initial caller is sequential.
- Contract authoring. It remains a main-agent skill, not engine machinery.
- Model canaries, A/B orchestration, and publishable-claim machinery.

### Enforceable simplicity rules

1. No framework before three concrete implementations need the same shape.
2. Product code never imports the eval laboratory.
3. Evals invokes the engine only through its published command.
4. Every phase adds one user-visible behavior and names its exclusions.
5. Default tests use no model, network, or subprocess. Process behavior lives
   in a small marked integration tier.
6. A refusal test has a sibling success test so rejection cannot pass
   vacuously.

## 3. Engine architecture

### Python core, TypeScript adapter

Pi requires a TypeScript extension. Everything else should be Python so the
engine is also usable as a library, a CLI, in CI, and by Python tooling that
does not use Pi.

The TypeScript adapter should translate Pi events and tool calls. It should
not duplicate contract policy, writable-path matching, mutation rules, or
delivery behavior.

### Start with a one-shot protocol

For an engine operation, the adapter:

1. starts the configured engine executable;
2. writes one versioned JSON request to stdin;
3. closes stdin;
4. reads one JSON response;
5. waits for the process to exit;
6. converts every transport failure into a named refusal.

The request contains the operation, workspace root, workspace-relative paths,
contract, and prior revision state. The Python process reads file bodies from
the workspace and returns the next revision state. The protocol therefore has
no hidden process state and no need for correlation IDs or concurrent request
handling.

Start with one operation. Add another only when a vertical slice consumes it.
Do not design a four-method protocol in advance.

Required adapter behavior:

- a deadline around the whole subprocess;
- a maximum response size;
- stderr captured for diagnosis but never parsed as protocol;
- malformed JSON, extra stdout, non-zero exit, timeout, and missing executable
  all become refusals rather than thrown extension errors;
- the child receives only the environment it needs;
- killing the Pi parent leaves no engine process behind;
- an adapter operation never spawns grandchildren. Delivery and validation
  commands use the engine's separate process-group lifecycle.

If startup becomes material after a real batch, keep the same request and
response objects and add a persistent transport then. Do not pre-build that
transport now.

### Interpreter and installation seam

Early slices receive an explicit engine executable path. This avoids guessing
from `PATH`, `VIRTUAL_ENV`, Volta, or a user's shell.

The packaged default is deliberately deferred until the packaged end-to-end
slice. That slice must choose and test one user story—such as a pinned `uvx`
command or an installed `uv tool` executable—on POSIX and Windows. The
adapter keeps one override for tests and nonstandard installations.

### Local Pi findings that constrain the adapter

Verified against the clean local Pi checkout at commit `914cf1472` (v0.84.2):

- Extension handlers are awaited sequentially and have no host deadline.
- `emitToolCall()` has no `try/catch`; an adapter error can escape the turn.
- Print mode emits `session_start`, then attaches its JSON subscriber. Startup
  effects happen, but output emitted during startup is not observable there.
- Print mode emits `session_shutdown` on normal completion, errors, SIGTERM,
  and SIGHUP. It does not install a SIGINT handler, and SIGKILL cannot clean
  up.
- `ctx.shutdown()` is a no-op in print mode.

These facts require the adapter's deadline and exception boundary. They do not
justify a session-scoped process. A one-shot child avoids the lifecycle
question entirely.

## 4. Evals architecture

### Diagnosis before claims

The first product answers: what failed, where did it fail, and did an engine
change alter that failure?

Record:

- accepted or rejected, with the reason;
- patch and transcript;
- turns and tool-call counts;
- repeated identical calls;
- repeated writes to the same target with different content;
- context processed, incomplete attempts, and timeouts;
- task digest, attempt-command identity, engine identity, and model string.

Record drift; do not abort a diagnostic batch because conditions changed.
Condition enforcement belongs to a future claims layer.

Never compare wall-clock time between contiguous arms. Two figures in this
repository were retracted for that mistake. Initial summaries use counts, not
seconds.

### Capture manually before mining

Start with a synthetic revert and one manually selected real commit. A task is
admitted only when deterministic checks prove:

- the base passes preservation tests;
- the oracle rejects the base;
- the target passes preservation and oracle tests;
- the target diff, restricted to writable paths, is accepted.

A human writes only the behavioral brief and writable paths. The tool derives
commits, patches, commands, and observed oracle outcomes.

Do not scan arbitrary Git history yet. After three manually captured tasks,
compare their selection steps. Automate only the steps that actually repeat.

### Validity is not discriminating power

The four checks above prove a task is *valid*: it is not already done, and it
is winnable. They say nothing about whether a model can fail it. A task can be
un-done at base and still be solved by any model on the first attempt.

Cycle 7 paid for that distinction. It spent 64 attempts to learn that three of
its four tasks carried no comparative information: `flask-extensions` 8/8 in
both arms, `local-pings` 7/8 in both, `autowire` 0/8 in both. One task
discriminated.

So capture takes a fifth check, and it is the only one that spends model time:

- **Baseline probe.** Run the baseline attempt command at n=4–6 and record the
  rate on the task. This is a recorded property of the task, not a result, and
  it is measured once.

Its verdicts:

| Baseline rate | Meaning | Use |
|---|---|---|
| at or near ceiling | any model passes it | smoke only; cannot diagnose |
| at floor | a capability wall, not something an engine change moves | keep, labeled; do not read a null as evidence |
| in between | the failure can move | this is where diagnosis lives |

### Two selection rules, because there are two jobs

These were previously conflated, and the conflation picks the wrong artifact
for both jobs.

**A grader fixture** proves the grading machinery discriminates. No model
runs, so headroom is irrelevant. It must grade offline and deterministically,
with no network and no third-party dependencies.

By that rule the V1 bundled task is `examples/duration/`: `spec.md`, an
acceptance suite, a known-good `reference/duration.py`, and a known-broken
`broken/duration.py`, importing only `pytest` and the module under test.
`examples/agentclinic/phase-1/` has the same shape but needs FastAPI, Jinja2,
and turbohtml, so it does not qualify. `workloads/svcs/` cannot qualify: it
requires a network clone and a real dependency resolve.

**A diagnostic workload** must be able to show a difference. It requires the
baseline probe, and a mid-range rate. By that rule `duration` and
`agentclinic-phase-1` are both disqualified — bare Pi scored 16/16 on
`agentclinic-phase-1` — and so is `agentclinic-phase-1-user-story`, whose
headroom was consumed by supplying two facts (0/16 → 15/16).

`examples/agentclinic/` still earns its place in the lessons file rather than
the task set. The user-story variant is the only recorded workload where the
bare model refuses to engage at all: one turn, zero tool calls, restate the
spec, ask a human. That is the agency floor, and it is a failure mode worth
naming.

### The unsolved problem: a suite with headroom

Nothing in this repository reliably produces tasks in the middle band. Every
suite it built saturated, and the two svcs tasks that discriminated —
`stringified-annotations` and `async-cm-enter` — were found by running batches,
not by design.

This is a prerequisite for the diagnostic loop being worth running, and it is
not a build step. It needs its own design work, before or alongside V5:

- What property of a task predicts a mid-range baseline? Cycle 3's envelope
  screen found two hard walls — no enumeration tool, and output tokens smaller
  than the target file — that put tasks at the floor for reasons unrelated to
  difficulty. Those are engine limits masquerading as task difficulty.
- Is difficulty a task property at all, or a task-plus-engine property? If the
  latter, the baseline probe must be re-run whenever the engine changes
  materially, and a task's band is not permanent.
- Does a suite need a difficulty *spread* rather than a target band, so that
  ceiling and floor tasks are present deliberately as controls?

Until that is designed, the diagnostic loop should be pointed at the two
recorded discriminating tasks and honest that the sample is two.

### Offline grading is the center

Every attempt persists its patch and transcript before cleanup. Grading reads
those artifacts and can be rerun without a model or engine.

The default unit suite uses committed artifacts. Real Git, environment
materialization, model invocation, and oracle execution are integration tests
and are marked explicitly.

## 5. Roadmap

Each phase ends with a command a contributor can run and evidence that names a
success fixture and a failure fixture. A phase does not include publishing,
polish, or abstractions needed only by a later phase.

### `satyrn-engine`

| # | Delivers | Done when | Explicitly out |
|---|---|---|---|
| E1 | `satyrn-engine check --repo REPO CONTRACT` | A checkout install accepts one valid contract and refuses invalid YAML, an impossible path, and a missing required field with distinct stable exit codes; no process or model is started | Pi, delivery, mutation, publishing |
| E2 | `/implement CONTRACT` reaches E1 through the TypeScript adapter | A real Pi print-mode fixture receives the same named refusal; success, missing executable, malformed output, non-zero exit, timeout, and parent-death orphan cases pass on POSIX and Windows | Persistent process, mutation, model call |
| E3 | `satyrn-engine deliver --repo REPO --contract CONTRACT -- ATTEMPT...` creates or discards a candidate ref | Delivery runs `ATTEMPT... CONTRACT` in its isolated worktree; a trivial executable produces a valid patch and candidate ref; dirty-tree, linked-worktree, timeout, and validation-failure paths leave the caller's tree and HEAD unchanged | Pi child, grading, measurement |
| E4 | One bounded file replacement runs through Pi → TypeScript → Python | A fixture replacement succeeds; stale revision, undeclared path, missing anchor, and ambiguous anchor refuse; the adapter never throws | General edit language, symbol analysis, guards |
| E5 | `satyrn-engine attempt CONTRACT` and `/implement CONTRACT` complete one named task from a source checkout | `attempt` writes only inside its current disposable worktree; `/implement` supplies E3's isolation around the same command; one real model attempt uses E4's bounded replacement and leaves a candidate ref plus transcript and receipt | Packaging, multiple tasks, performance claims |
| E6 | The same `/implement` is packaged | It works outside either source checkout on POSIX and Windows and records an immutable engine identity | Auto-update, publishing claims |

E2 is the architecture gate. If it cannot keep failures bounded and legible on
both platforms without growing a supervisor, stop and reconsider TypeScript
before building E3–E6.

E4 deliberately implements one replacement operation. The existing mutation
engine's no-op edit, symbol-loss, cross-file move, and oversized-proposal rules
are candidates for later slices, not one large port.

### `satyrn-evals`

| # | Delivers | Done when | Explicitly out |
|---|---|---|---|
| V1 | `satyrn-evals grade TASK PATCH` | One bundled task accepts its named good patch and rejects its named broken patch; regrading is offline and deterministic | Capture, model, engine |
| V2 | `satyrn-evals capture --revert SHA` | The generated synthetic task is winnable by construction: its source diff grades accepted, while the reverted base is rejected | History mining, prose generation |
| V3 | `satyrn-evals attempt TASK -- COMMAND...` persists an attempt | Evals runs `COMMAND... CONTRACT` in its disposable worktree, captures stdout, stderr, and the Git diff, and can regrade a fake command's retained artifacts offline | Real engine, repetition |
| V4 | One real engine attempt | E5's `satyrn-engine attempt` runs against the bundled task and produces the same artifact set as V3; failure leaves enough evidence to diagnose without rerunning | Batch, A/B, claims |
| V5 | `satyrn-evals run --n 8` and a diagnostic summary | Interrupted output remains readable; every attempt records identities and artifacts; the summary reports verdict reasons, repeated calls, churn, tool calls, context, and timeouts | Confidence intervals, condition enforcement, canary, publication |

V1–V3 can proceed independently of the engine because V3 uses a fake command.
V4 depends on E5, not on a packaged or published engine.

V5 has a prerequisite that is design work, not a phase: a suite with headroom.
Its summary is only informative on tasks whose baseline rate can move, and
nothing here reliably produces those yet. Run V5 against the two recorded
discriminating tasks, and treat the sample size as two until that design
exists.

The baseline probe belongs to V2 and V3, since it is a capture step. It is the
only capture step that spends model time, so an afternoon of capture is four
free checks plus one paid one.

Automated commit mining, paired A/B, resumable large batches, and a claims
layer are future proposals. Add each only after the preceding diagnostic loop
has a user who needs it.

## 6. Oversights this plan closes

### The old split table was not a migration plan

The previous draft assigned selected modules to each repository while leaving
`cell.py`, `cell_resolution.py`, `liveness.py`, `model_config.py`, and
`workload_plugin.py` unassigned. It also ignored imports crossing both
directions. That framing invited a partial transplant.

There is now no file-move manifest. Each phase re-earns behavior from a named
fixture and incident. Unscheduled modules stay behind.

### One version is not provenance

A mutable version label is weaker than the old byte digest. New eval records
therefore carry a version plus an immutable artifact identity. Historical
cells are archived, not invalidated.

### The contract does not get declared in three languages

Python owns contract validation. TypeScript transports a versioned request and
does not maintain a second policy type by hand. Compatibility is tested with
engine-owned JSON fixtures. Evals does not parse the engine contract.

### Per-call children still need lifecycle control

They avoid pooling and reaping, but they still need a deadline, output bound,
termination, EOF behavior, and an exception boundary. E2 proves all five
before mutation work starts.

### Task mining was premature

The earlier roadmap promised a general Git-history miner and a task yield
before the selection rule was known. V2 starts with construction by revert;
manual real-task capture must produce three examples before a miner is
designed.

### Shared formats need owners

The engine owns its public protocol, contract, and receipt fixtures. Evals
owns task and grade fixtures and treats the engine receipt as an artifact.
There is no hand-synced shared schema repository.

## 7. Remaining decisions, scheduled at their consumer

1. **E3 — linked worktrees:** support them by resolving the common Git dir, or
   refuse with a specific message. Decide from the smallest implementation,
   not by carrying the current `.git`-directory assumption.
2. **E4 — replacement representation:** choose the smallest request that
   supports the success fixture and three anchor refusals. Do not design a
   general edit algebra.
3. **E6 — installation:** choose one pinned default command and one override,
   then test the complete install on POSIX and Windows. Do not choose `uvx`,
   bundled Python, or `PATH` lookup only from desk research.
4. **V2 — environment eligibility:** the first capture format must state and
   verify its supported floor: deterministic, sub-minute, lockable, and one
   environment usable at base and target.

Everything else is deferred, not open. A deferred idea does not shape the
initial APIs.

## 8. Negative record to carry into the new briefs

- Facts about the task beat rules of conduct in the prompt.
- A correct fact that cannot be found by the symptom is operationally absent.
- User-scope Pi resources contaminated the supposedly hermetic child and
  caused the runaway; removing them removed the pathology.
- A model server can exit cleanly while doing nothing. Liveness must prove a
  real completion, not merely list a model.
- Model-authored stdout and process exit codes are not trustworthy verdicts.
- A grader that rejects by default needs paired acceptance evidence.
- The target's restricted diff is the cheapest winnability proof.
- Capturing patch and transcript matters more than preserving a grade.
- Workload and environment bytes can leak the answer through Git metadata,
  timestamps, sibling workspaces, caches, and archival substitutions.
- Contiguous arm timing is not comparable under changing machine load.
- Machinery built before a consumer becomes the project.

This list is the minimum seed. The new briefs should link each item to its
incident and index it under the contributor-visible symptom.

## 9. What this record does not claim

- It does not claim Python is permanently chosen. E2 is the explicit reversal
  point.
- It does not claim one-shot subprocess cost is negligible. It chooses the
  smaller design until a real batch measures otherwise.
- It does not claim the first engine improves a model. The engine roadmap
  proves bounded behavior; the evals roadmap diagnoses outcomes.
- It does not claim arbitrary Python repositories can be captured. V2 defines
  and enforces a narrow eligibility floor first.
- It does not claim the old evidence is comparable with new runs. The old
  repository remains an archive; the new record series starts cleanly.
