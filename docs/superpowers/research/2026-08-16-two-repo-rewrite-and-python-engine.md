# The two-repo rewrite: a Python engine, and an evals reboot

**Date:** 2026-08-16
**Status:** research — a conversation record. Some decisions are recorded as
decided (marked inline); nothing here is a spec, and nothing has been built or
measured.
**Covers:** the `satyrn-engine` / `satyrn-evals` split (§1–3), whether the
engine becomes Python (§4), how Pi supports a long-running sidecar (§5–6), the
evals reboot (§6.5), and proposed roadmaps for both repos (§7).
**Purpose:** capture a design conversation *before* it is lost. This project
has a recorded failure mode where a correct fact was never retrieved by the
cycle that needed it (Phase 5 cycle 8 spent a full cycle — spec, build, pilot,
research record — on a premise two committed documents already refuted). It
also has a live instance: the decision to move the engine to Python was
discussed within the last three days, concluded "good idea but too disruptive
right now," and **was never written down**. A search of every branch, every
doc, and every commit message across all refs found nothing. This document
exists so that does not happen twice.

---

## 1. The direction

Split into two repositories: **`satyrn-engine`** and **`satyrn-evals`**.

This is not a `git mv` exercise. This repository becomes a **harvest source**:
its lessons are mined into a proposed SDD brief and roadmap for the two new
projects, which start fresh. That is the same move as `restructure` off
`user-story-batch` — `BRIEF.md`'s "a clean slate that gets gardened, not a
clean-room rewrite."

The owner's framing: *"This project was a great experiment, discovered all
kinds of needs, really valuable."* The experiment's output is knowledge, and
the knowledge is the deliverable.

### 1.1 Two north stars for the harvest

Agreed in conversation, and both are constraints on the *format* of the brief,
not just its content.

**The negative record is the highest-value content.** The retractions, the
seven instrument defects, the four silent zeros, the ten-item
do-not-re-derive list, the stop-list. Those cost real cycles and none of them
are recoverable from reading the source. The code is mostly re-derivable; the
knowledge of *which plausible thing is false* is not.

**Index by symptom, not by mechanism.** Phase 5 cycle 8's diagnosis was that
the gotchas record filed a fact under *what a child inherits* while the cycle
was searching for *how to reach a child*. A well-organized document that
organizes by mechanism will lose the same way. This is the single format
constraint most likely to be dropped by writing a tidy brief.

### 1.2 A budget, not just a list

Three prior attempts died of orchestration sprawl. This one is ending at
**10,901 lines** of non-test source, **15.3 MiB** of tracked `workloads/` +
`examples/` artifacts, and **fourteen unmerged branches** (12 local, 2
remote-only). A harvest that carries forward everything valuable reproduces
exactly that. The brief likely needs an explicit ceiling — a line count or
concept count the new repos may not exceed without a deliberate decision.

Recompute, do not transcribe:

```
git ls-files 'harness/*.py' | xargs wc -l | tail -1          # 6065
git ls-files 'extensions/**/*.ts' | grep -v '\.test\.ts' \
  | xargs wc -l | tail -1                                     # 1426
git ls-files 'tools/*' | xargs wc -l | tail -1                # 3410
```

> **Corrected twice, and wrong both times before this.** The first version
> said "roughly six thousand lines of engine/tool/test code, ninety-seven
> mebibytes, five unmerged branches" — all three wrong. The correction then
> published **5,894** for the same three directories, which is also wrong and
> is not reconstructible from any commit; the true figure is 10,901, and the
> corrected sentence was internally inconsistent with its own "~23k with
> tests" clause.
>
> The pattern is now established across two independent reviews: **this
> document is line-citation-accurate wherever it cites Pi or SDK source, and
> unreliable on every statistic describing this repository.** That is an
> inversion of the usual failure mode. The structural fix, adopted above, is
> to carry the command rather than the number — which is the same instinct
> that makes `telemetry.py` a recomputable view rather than storage.
>
> The claim these numbers support is unaffected: the harness at 6,065 lines
> is far larger than the engine it measures (`packages/engine/` non-test is
> **340** lines; with `extensions/` it is 1,766).

---

### 1.3 Modular by construction — a third brief-level constraint

Alongside the two north stars and the budget: **build both repos so they are
easy for us to develop and easy for others to extend.** Stated as a constraint
rather than an aspiration, because this project has evidence about which kinds
of modularity worked and which produced the sprawl.

**What worked here, and should be carried as patterns:**

- **Pure decision functions.** `ToolCall → Decision`. `docs/engine/architecture.md`
  names the payoff directly: *"Making the decision a pure function is the
  replay seam"* — the same `inspect(call)` runs live and from a recorded
  transcript. Purity bought testability, replayability and extensibility at
  once.
- **The injected callable is the extension point.** `deliver()` takes
  `run_model`, so every branch is testable with no model. That parameter is
  *already* the plugin seam — a third party supplies a different model runner
  by passing one. **Rule: if you inject it to test it, that is the extension
  boundary. Do not invent a second one.**
- **Data over code.** A workload is a directory (`manifest.toml`, `brief.md`);
  a contract is a markdown file; a guard fixture is committed JSON. Extending
  means adding a file, not subclassing. This is already the shape and it
  should be the default answer.
- **One file per concern, with a shared types module.** `guards/types.ts` +
  one file per guard.
- **Lazily-resolved registries.** `IMPROVEMENTS` maps names to *factories,
  never results*, so `import harness.runner` succeeds on a machine with no Pi.
  A registry whose values are already-constructed objects imports the world.
- **A protocol is a plugin boundary.** The JSON-lines bridge (§6.2) means a
  third party can replace the Python side wholesale without touching
  TypeScript.

**What failed here — all four are boundary failures, not missing
abstraction:**

- **A framework built before its plugins.** `inspectContract` shipped
  `Packet`/`Finding`/`CheckerReport`/`Inspection`, severities, advisory
  findings and per-criterion timing — roughly 365 lines hosting five criteria,
  of which **one fifteen-line rule survived**. Adopt the rule of three: no
  framework until three real implementations exist and are pulling in the same
  direction.
- **Import direction violated silently.** `harness/typed_contract.py:36`
  imports `harness.workload`, dragging a 35 KB lab module onto the shipped
  path. Nothing caught it.
- **A module that had to be surgically extracted.** `cell_resolution.py` was
  cut out of `screen.py` precisely so the product path would stop importing
  the screening lab — the same disease, treated after the fact.
- **Two functions with one name and different semantics.** Two `run_suite`s,
  two `_out_of_scope`s, because no boundary said which layer owned what.

**So the enforceable rules:**

1. **Import direction is one-way and mechanically checked.** A test fails the
   build if the product path imports the lab, or if evals imports engine
   internals rather than its published surface. Cheap, and it is exactly the
   failure that already happened twice.
2. **No framework before three implementations.**
3. **Extension points are test seams**, and there is only one of each.
4. **A name is owned by one layer.** Two functions with the same name in one
   package is a boundary bug, not a coincidence.

**And the honest tension**, worth writing into the brief rather than
discovering: modularity is itself a concept cost. Every seam is a term a
5-h/wk contributor must hold, and `BRIEF.md`'s trap is machinery outgrowing
anyone's head. The resolution is that these seams pay for themselves *twice* —
each one is also a test seam — and any proposed seam that is not also a test
seam should be refused.

## 2. Shape of the plan

Owner's requirement: **tiny shippable steps for both repos.**

- **Phase 1 (each repo): getting set up.** Must end with a command that runs
  and a test that passes — not a README and a directory tree. This project's
  own first recorded decision was that "a phase named after a document invites
  producing a document rather than a working engine."
- **Phase 2 (each repo): ship exactly one thing** in the candidate
  architecture. Small is fine; **vertical is not optional**. The recorded
  failure mode is machinery ahead of its contract: `inspectContract` reached
  862 lines before it had a consumer, and 380 survived.

Candidate slices, not yet decided:

- **Engine:** the refusal path alone — contract file in, parse, lint, refuse,
  name the cause, **zero model calls**, ~0.1s. It exercises CLI, parser, lint
  and command surface end to end and runs in CI on a machine with no GPU.
  Already demonstrated on `phase11-contract-file` (exit 2, 0.109s).
- **Evals:** one suite, one run, one hermetic verdict, proven against a
  known-good and a known-broken fixture. This is `BRIEF.md`'s original
  Phase 1, and the reason it worked: reproduce a number you already trust, so
  a bad result indicts the engine rather than the model.

**Ordering.** Phase 1 of each is independent and can run in parallel. Engine's
Phase 2 should land before evals' Phase 2, because if evals consumes the
engine as an installed artifact, its first slice needs something to install.

Three amendments from review:

- **If the engine is Python, Phase 2's refusal must round-trip through the
  bridge** — spawn, one request, refusal, teardown, EOF-orphan test —
  otherwise the slice is vertical through the wrong stack and proves nothing
  about the architecture's riskiest joint. If the engine stays TypeScript, the
  slice is fine as written.
- **The evals slice must reproduce a number that is invariant under the
  split.** Section 3 says the split invalidates every recorded cell: the
  known-good/known-broken *fixtures* survive, but recorded *batch statistics*
  may not. Aim at a hermetic grading verdict on a fixture, not a recorded rate.
- **The print-mode probe belongs in engine Phase 1**, not a backlog. It is a
  test that passes, which is Phase 1's own definition of done.

---

## 3. What the split actually costs

The repo already has two nearly-disjoint import graphs, so the cut is mostly
clean:

| To `satyrn-engine` | To `satyrn-evals` |
|---|---|
| `packages/engine/` | `harness/{runner,grading,grading_plugin,checkpoint,cli}.py` |
| `extensions/implementer/` | `harness/{telemetry,precision,intervals}.py` |
| `extensions/guards/` | `harness/{workload,qualification,screen,validity,similarity,reconstruction}.py` |
| `harness/{candidate,contract_file,contract_lint,typed_contract}.py` | `examples/`, `workloads/` |
| `harness/{pi_invocation,processes,workspace}.py` | `docs/evals/` |
| `tools/deliver_candidate.py`, `docs/engine/` | |

Three things resist it:

1. **`candidate.deliver()` is on both sides.** The eval batch driver imports
   it and monkeypatches it to inject `validation_env`. That is the real
   coupling, and it is the same question Phase 13's open question 1 asks. A
   split forces the answer: **evals consumes the engine as an installed
   artifact, not as an import.**
2. **Cells pin extension bytes across the boundary.** `extensions_sha256`
   hashes an ordered eight-file closure that would live in the other repo.
   Post-split, evals must pin an engine *version* instead — better
   provenance, but it invalidates every recorded cell and checkpoint. Needs a
   sentinel, the way `("<pre-cycle1>",)` handled it before.
3. **`HandoffContract` is one wire format with two hand-synced
   declarations.** Today drift surfaces as the child rejecting at
   `isContract()`. Across repos, nothing can see both sides at once. This gets
   worse before it gets better.
4. **An import runs the wrong way, on the shipped path.** Added after review:
   `harness/typed_contract.py:36` does `from harness.workload import Manifest,
   load_manifest` — an engine-column module pulling the 35 KB evals-column
   `workload.py` into the product's import closure via
   `tools/deliver_candidate.py`. This is the same disease `cell_resolution.py`
   was surgically extracted from `screen.py` to cure. **Cut it before the
   split, not during.**

Two corrections to this section's framing, both from review:

- **"Two nearly-disjoint import graphs" is refuted.** The evals column imports
  the engine column well beyond `candidate.deliver`: `runner.py` →
  `pi_invocation`/`processes`/`workspace`; `screen.py` → four engine-column
  modules; `workload.py`, `grading.py`, `cli.py` similarly. Most are
  engine-as-library uses that the "installed artifact" answer handles — but it
  means the artifact's **Python API surface is several modules, not one
  function**.
- **The table above is a sketch, not a manifest.** Five load-bearing modules
  appear in neither column: `cell_resolution.py`, `cell.py`, `liveness.py`,
  `model_config.py`, `workload_plugin.py`.
- On the monkeypatch: the batch driver patches **two** attributes
  (`harness.candidate.deliver` and `tools.deliver_candidate.deliver`) and
  restores both in a `finally`. The conclusion stands, with a consequence —
  the installed artifact needs `validation_env` as a **real parameter of its
  public surface**, since monkeypatching dies with the import.

---

## 4. The big architectural question: is the engine Python?

### 4.1 Status

Discussed in a session within the last three days. Consensus recorded here
from the owner's recollection, since nothing was committed:

> **Good idea, but too disruptive right now.**

An accompanying analysis asked how much of the TypeScript actually *needs* to
be TypeScript. The answer: **not much — essentially just `implementer.ts`,
the part that connects into the Pi lifecycle.**

**The split changes the "too disruptive" judgment.** That was a statement
about *this* repository, which carries a frozen 64-attempt cell, a pinned
eight-file digest closure, and recorded batches that must stay comparable. A
greenfield `satyrn-engine` carries none of that. The decision that was
correctly deferred becomes cheap at exactly the moment the repos split.

### 4.2 What is irreducibly TypeScript

The Pi lifecycle binding: the extension module Pi loads, which registers
`agent_start` / `before_agent_start` / `turn_start` / `tool_call` /
`tool_result` handlers, replaces `write`/`edit` via `pi.registerTool`, and
registers `/implement` via `pi.registerCommand`.

Everything else is a choice:

- `mutation-engine.ts` (385 lines) — pure sha/edit/symbol logic, no Pi coupling
- `implementer-policy.ts`, `tool-target.ts`, `handoff-contract.ts` — same
- `packages/engine/core/*.ts` from the `ts-engine-core` spike — the delivery
  lifecycle, which **already exists in Python** as `harness/candidate.py`

The catch: those all run *inside* the child process, called synchronously from
tool handlers. Making them Python requires a bridge.

### 4.3 Three problems that are artifacts of the boundary, not of either language

**Corrected after review — this section originally overstated the case for
Python.** A *single-language* engine collapses all three. A **Python core does
not**: the TS shim still parses tool inputs, still holds `isContract()`, and
now adds a wire protocol — so the hand-synced declaration count goes from two
to three. Only TypeScript-everywhere actually collapses them, because
TypeScript is the language Pi forces on one end. The three problems are real;
they are an argument for one language, not for Python.

- **`fnmatch` parity.** Python's `fnmatch` lets `*` cross `/`, so `src/*`
  matches `src/a/b.py`; minimatch, picomatch and `Bun.Glob` all disagree. The
  `ts-engine-core` plan calls this "the one place where a 'reasonable' Node
  idiom silently changes behavior." The spike hand-ported
  `fnmatch.translate()`; a 357-pair differential test passed and **still**
  missed a bracket class starting with `]`, and a second ~1,500-pair sweep
  found reversed ranges (`[z-a]`) throwing an uncaught `SyntaxError` out of
  the scope check.
- **`HandoffContract` declared twice by hand**, with no generator and no test
  that can see both sides.
- **The digest closure** must enumerate eight files in order to notice a
  behavior change — a gap that was real through commit `432a3e3`, when the
  digest covered only `implementer.ts` and an edit to `mutation-engine.ts`
  changed arm behavior invisibly.

### 4.3a The steelman for staying in TypeScript

Added after review, because the original section 4 framed Python as the
default and TypeScript as the thing needing justification. The reverse is
better supported:

- **Distribution is the whole argument.** Pi extensions *are* TypeScript. A
  shipped pi package cannot assume `uv` or a checkout. The owner's own
  constraint — users must not start a server — generalizes to *users must not
  provision a runtime*. A Python core makes every install carry a working
  Python-location story; a TS engine makes install a directory copy.
- **The port is measured and small.** The `ts-engine-core` spike is **575
  lines of production code** (1,123 with tests), transcribing
  `harness/candidate.py`'s lifecycle commit by commit. *(This document
  originally said "~700 lines"; that figure appears nowhere in the plan.)*
- **The recorded Python-boundary pain is on the parent, not the child.**
  `pi_env` stripping, pytest replaced in the harness venv, volta lying — all
  of it lives in the parent harness, which the split ships to `satyrn-evals`
  regardless. Putting Python inside the child *adds* a second instance of a
  seam that does not exist there today.

Against that, the spike carries unfixed defects: `[z-a]` in a writable pattern
throws an uncaught `SyntaxError` out of `outOfScope` → `deliver` → `/implement`
**crashes with a stack trace instead of refusing** (reproduced live against
the branch during review, still unfixed), and receipt fields (`prompt_sha256`,
timings) were dropped, so TS-path candidate commits are not byte-identical to
Python-path ones. The fnmatch tax is also permanent: every Python-idiom
dependency must be hand-ported and differentially tested.

**Review's verdict:** for the engine repo, TypeScript should be the default
and Python the option that must earn its way in.

### 4.3b Why Python, restated by the owner — and why it answers the steelman

Added after the review. Both the document and the review scoped "distribution"
as *how does this install into Pi*. The owner's framing is different, and it
inverts several conclusions:

1. **The engine must work outside Pi.** As a library, a CLI, in CI, from
   someone else's harness. If the engine is TypeScript, a standalone engine is
   a Node/Bun program — and a Python-community audience cannot use it. The
   review's "install is a directory copy" advantage evaporates the moment Pi
   stops being the only consumer.
2. **This is the Python community.** Audience alignment is a real
   requirement, not a preference, for a project whose stated purpose is
   "keeping small local models on track during **real Python development**"
   for volunteer Python developers.
3. **The evals side is easier in Python, and can run without Pi at all.**
   Grading, workload qualification, validity, and the intervals math are
   already Python and already model-free. Most of the harness runs with no Pi
   in the picture. Sharing the candidate lifecycle across both repos in one
   language is genuine reuse.

**This reframes the wire protocol.** Section 4.3 counts it as a third
hand-synced declaration. Under "Pi is one consumer among several," it is
instead **the adapter boundary that exists anyway once there are two
consumers** — and `implementer.ts` becomes an adapter rather than a wart.

**And it must support Windows** — a new hard constraint, which turns out to
settle the transport question rather than complicate it (§6.2).

**Standing decision: keep exploring Python until it looks impractical.**
§6.3 records the check.

### 4.4 The counterweight

Every piece of recorded pain in this project sits on the Python-process
boundary: `pi_env` stripping `VIRTUAL_ENV` and `SSH_AUTH_SOCK`, the model
`pip install`ing into the harness venv and replacing pinned pytest 8.3.4 with
9.1.1, `which pi` lying under volta, `SATYRN_PI_PACKAGE` existing because "the
obvious lookups lie." A Python bridge lives directly on that seam.

---

## 5. How Pi supports a long-running external process

Researched 2026-08-16 against the local Pi clone at `~/PycharmProjects/pi` and
four third-party extensions.

### 5.1 The sanctioned pattern, from Pi's own docs

`docs/extensions.md:220-224`:

> Extension factories may run in invocations that never start a session. Do not
> start background resources such as processes, sockets, file watchers, or
> timers from the factory. Defer background resource startup until
> `session_start` or the command/tool/event that needs the resource. Register
> an idempotent `session_shutdown` handler to close any session-scoped
> resources you start.

`session_shutdown` fires on quit (Ctrl+C/D, SIGHUP, SIGTERM), `/reload`,
`/new`, `/resume`, and `/fork`. There is **no** `AsyncDisposable`, no
finalizer, and **no guarantee on hard crash** (uncaught exception, SIGKILL,
OOM).

### 5.2 Two hazards in Pi's dispatch, both landing on our seam

Confirmed in `packages/coding-agent/src/core/extensions/runner.ts`:

1. **There is no timeout anywhere in extension dispatch.** No `Promise.race`,
   no `AbortController` around the handler call, no per-handler deadline.
   Handlers are awaited sequentially from the agent loop (`emit()`, line
   801-833), so a hung handler stalls the whole turn indefinitely.
   `ctx.signal` is cooperative only — Pi never forcibly cancels a stuck
   handler.
2. **`emitToolCall()` (932-953) has no `try/catch`**, unlike `emit()`,
   `emitToolResult()` and `emitUserBash()`. A throw in a `tool_call` handler
   propagates rather than being logged and skipped.

`tool_call` is exactly where the guards and the mutation engine live.
`BRIEF.md` says of the old orchestration layer that "every hang and timeout
lived here." **The bridge's own timeout and its own `try/catch` are therefore
part of the design, not polish.**

### 5.3 Shipping a Python payload works, and is proven

A directory package declares `"pi": {"extensions": ["./index.ts"]}`. Only the
declared entries are treated as extension modules; **everything else in the
directory is just data the extension reads at runtime.** `doom-overlay/` ships
a WASM engine and its `.wad` assets this way.

Asset resolution is `dirname(fileURLToPath(import.meta.url))` — or, as
`pi-lens` does it, `getPackageRoot(import.meta.url)` walking up to the nearest
`package.json`. `pi-lens` documents *why*: `process.cwd()` points at the
**user's project**, not the extension. That is the exact trap a bundled Python
payload would fall into.

Extensions are loaded via **jiti** (`loader.ts:17`, `444-455`), with
`moduleCache: false` so `/reload` gets a fresh module. Imports from
`node_modules/` resolve normally.

### 5.4 What four real extensions do

| Extension | Owns the process? | Starts it | Protocol |
|---|---|---|---|
| `pi-lsp-client` | yes | **lazy**, first tool call | JSON-RPC/stdio (`vscode-jsonrpc`) |
| `pi-lens` | yes | **lazy**; `session_start` only warms a dynamic `import()` | JSON-RPC/stdio (`vscode-jsonrpc`) |
| `pi-mcp-adapter` | yes | **lazy** default; `eager`/`keep-alive` are opt-in config | MCP SDK stdio / HTTP / a hand-rolled Unix-socket transport |
| `pi-llama-cpp` | **no** | n/a — assumes an already-running server | HTTP + SSE |

`pi-lsp` itself is published (`pi-lsp@0.1.7`) but carries no `repository`
field and no matching source could be found; `pi-lsp-client` is its port and
was read instead.

**Consensus shape** across the three that own a process:

- `spawn` with `stdio: ["pipe","pipe","pipe"]`, `detached: true` on POSIX so
  the child gets a process group for tree-kill
- a registry keyed by identity (workspace root + server id, or server name)
  holding one process per key, with a shared `initPromise` / `connectPromises`
  map so concurrent callers never double-spawn
- `.unref()` on the child and its stdio streams, so a live child never keeps
  the Pi process alive
- an `.unref()`'d `setInterval` reaper gated on refcount / in-flight count
- `session_shutdown` → graceful protocol shutdown → `SIGTERM` → ~5s →
  `SIGKILL`
- **all three are lazy**; none eager-spawns at `session_start`

**Two patterns worth stealing directly:**

- **Typed crash retry, narrowly scoped.** `pi-lsp-client` retries exactly
  once, only on a typed dead-connection error, and only for a whitelist of
  **read-only** tools. This maps precisely onto our surface: `read` is safely
  retryable, `write`/`edit` are not, because the mutation engine's contract is
  a revision baseline and a blind retry after a partial write is the
  stale-revision failure it exists to refuse.
- **Circuit breaker instead of a supervisor.** `pi-lens` counts exits in a
  rolling window and trips `broken` / `permanentlyBroken` to stop respawning a
  server that keeps dying. There is no background watchdog: a dead client is
  evicted from the pool and the next tool call respawns it.

**The ceiling of complexity**, for reference rather than as a target:
`pi-lens` keeps a filesystem instance registry (`~/.pi-lens/instances.json`)
recording every spawned child's pid and a per-session marker, sweeps orphans
on every `session_start`, verifies identity against live command lines before
killing anything (pids get recycled), and runs a second binary-name-based
backstop sweep for children the registry lost. That survives the Pi host
process itself crashing.

One teardown subtlety: on the `processExiting` path `pi-lens` deliberately
does **not** spawn a killer process, because doing so aborts a closing libuv
loop. Shutdown-time teardown must be direct handle-kill only.

### 5.5 Print mode is unverified, and this project has been bitten there

Every extension studied targets interactive sessions. The implementer child is
`pi --print --no-session`, living 23–900s for at most 30 tool calls — so
"persistent" there means one Python process per child session, the same
pattern at a shorter timescale.

But this repository's **gotcha #1** (not #2, which is `--approve`) is that an
entry appended during `session_start` is *dropped* in print mode: print mode
attaches its JSON subscriber only after `bindExtensions()` returns, while
`bindExtensions()` emits `session_start` before returning. Eighty recorded
runs produced nothing observable because of it.

**Partially retired by review, at source level.** `runPrintMode`'s `finally`
always calls `runtimeHost.dispose()` (`print-mode.ts:162-167`), and
`dispose()` emits `session_shutdown` with reason `"quit"`
(`agent-session-runtime.ts:398-405`). Print mode also installs SIGTERM/SIGHUP
handlers routing through the same dispose (`print-mode.ts:50-66`). So
`session_shutdown` **does** fire in print mode on normal exit, on thrown
errors, and on SIGTERM/SIGHUP.

Two gaps remain: **SIGINT has no print-mode handler** (default termination, no
shutdown event), and SIGKILL never fires one — which is why stdin-EOF stays
the load-bearing orphan mechanism rather than a backstop. Also confirmed:
`ctx.shutdown()` is wired to a default no-op (`runner.ts:294`) and only
interactive mode installs a real handler.

And a hazard in the same place: **shutdown handlers are awaited through
`emit()` with no timeout**, so a hanging shutdown handler blocks Pi's exit
forever. The shim's shutdown path needs its own deadline.

The ~20-line runtime probe is still worth running against the pinned Pi
version — source reading predicts the result; the probe confirms it.

### 5.6 The hazard analysis covers only half the surface

`write` and `edit` do not run through the `emitToolCall` path analyzed in
5.2 — they are `pi.registerTool` executors, and their errors go through the
agent loop rather than the extension runner. The two `runner.ts` hazards are
real, but a full picture needs the tool-executor side traced as well. Not yet
done.

---

## 6. The constraint the owner has set

> **Avoid asking users to start an HTTP server.** Find something solid that Pi
> manages.

This rules out the `pi-llama-cpp` shape (thin client to a process the user
starts), which was otherwise attractive because it deletes the entire
supervision problem. The engine must own its sidecar's lifecycle, which means
inheriting the spawn / pool / reap / crash-retry work described above.

Prior art the owner brings from another project: **a thin Python main process
managing a pool of Python 3.14 subinterpreters.**

**Review's verdict: machinery ahead of its contract, here.** The sidecar has
exactly one client making strictly sequential calls — the implementer child is
single-threaded by construction. A subinterpreter pool buys concurrency and
isolation no caller can exercise. If a concurrency case ever appears it is on
the evals side (parallel children), and there the isolation unit is already
the OS process: each child gets its own sidecar. Keep the prior art in the
drawer; the contract for slice one is *one process, four methods, dies on
EOF*.

### 6.1 The decision that actually settles the sidecar shape

Not raised in the first draft, and it is the real decider — not transport.

**Where does per-session mutable state live?** The state the engine carries
across tool calls is tiny and fully serializable: the `revisions` map (path →
sha256, one per baseline file), the loop-breaker window, `failedMutationCalls`,
and a turn counter. Everything else is pure computation — sha256, diff, symbol
scan — over local files.

**So keep all state in the TypeScript shim and make every Python call a pure
request → response.** Consequences:

- A crashed sidecar loses nothing. "Respawn" is the entire crash story.
- Per-call subprocess and persistent sidecar become *the same protocol at
  different latency*. You can ship the former and upgrade to the latter with
  no redesign.
- Even mutations become safe to re-issue on the model's next turn, because the
  shim's `revisions` map survived.

Letting state migrate into Python is the one decision that would force real
supervision machinery.

### 6.2 The recommended shape, if Python is chosen

Ranked by review: **(a) lazy persistent sidecar, newline-delimited JSON-RPC
over stdio, stateless protocol.** Then (c) subprocess-per-call as an
acceptable first implementation, (b) Unix socket rejected, (d) in-process
embedding ruled out.

- **Spawn lazily on first engine-touching call**, behind a shared
  `initPromise`. Never in the factory (Pi forbids it), and **never in
  `session_start`** — lazy spawn sidesteps the print-mode question entirely.
- **stdio beats a Unix socket specifically because of orphans.** The Python
  loop reads stdin; when Pi dies — SIGKILL included — the pipe closes, the read
  returns EOF, and the sidecar exits. Orphan cleanup is intrinsic to the
  transport. A listening socket daemon does not die when its client does
  unless you code it. Belt-and-braces: poll `os.getppid()`.
- **Hand-roll the protocol (~60 lines each side).** Four methods:
  `readReceipt`, `propose`, `proposeEdits`, `shutdown`. `vscode-jsonrpc` would
  triple the engine's dependency count — currently one (`typebox`) at the
  workspace root, **zero** in `packages/engine/package.json` — to buy
  header-framed transport that is pointless at concurrency 1.
- **Bound hangs in the bridge** with a per-request `Promise.race` deadline
  (5–10s is generous for millisecond-scale operations); on expiry SIGKILL the
  process group and return a refusal naming the cause. Keep the existing
  `try/catch` around the `tool_call` handler body and treat *"the bridge never
  throws"* as a tested invariant.
- **Circuit breaker, no watchdog.** Dead → evict → next call respawns; N
  deaths in a rolling window → trip permanently and refuse with the sidecar
  named as the cause.
- **Locate the interpreter by one explicit seam**, never `which python`,
  never `PATH`, never `VIRTUAL_ENV` — all three are recorded liars here. A
  `SATYRN_PYTHON` env var injected by whoever spawns the session, falling back
  to `uv run --project <payloadRoot>`. This mirrors the two seams that already
  work: `SATYRN_PI_PACKAGE` and `PI_CODING_AGENT_DIR`.
- **Ship the Python payload as package data** (the doom-overlay pattern) and
  resolve it by walking up from `import.meta.url` — never `process.cwd()`,
  which points at the user's project.

**A de-risking fact the first draft missed: the parent already bounds the
hang.** `harness/candidate.py` enforces a 900s wall clock and kills the
process group. A sidecar hang is therefore *already* bounded from outside; the
bridge timeout improves the failure's legibility, not its boundedness.

**Windows settles the transport, it does not complicate it.** A Unix-socket
daemon is not viable cross-platform on the Python side: CPython's exposure of
`socket.AF_UNIX` on Windows is unresolved (tracking issue open; the stdlib
docs say to feature-detect rather than assume), leaving named pipes via a
dependency or TCP loopback — which is the server shape the owner ruled out,
plus firewall prompts. stdio works identically on both platforms. Windows
deltas: `detached` is POSIX-only, tree-kill is `taskkill /F /T /PID`, and
`spawn` needs `.cmd`/`.ps1` shim handling — which `cross-spawn` provides in
one dependency.

### 6.2a How often does Python actually start? Three tiers.

The engine is not one call-frequency. Distinguishing the tiers dissolves most
of the cost argument:

| Tier | Frequency | Where Python fits |
|---|---|---|
| **Guards** (everyday steering) | every tool call, all day, long-lived interactive session | one sidecar per **session** |
| **Implementer engine** (mutation, policy) | only during `/implement`, ≤30 calls per delivery (`implementer-policy.ts:31`) | one sidecar per **implementer child** |
| **Delivery lifecycle** (worktree, validation, ref) | once per `/implement` | a plain subprocess; already exactly this today |

So under the recommended shape Python starts **once per session** and **once
per delivery** — not once per tool call. This is also the final reason the
subinterpreter pool does not apply: it would amortize a startup that already
happens once, for a caller that is strictly sequential.

### 6.2b Guards: latency was the wrong worry; blast radius is the right one

An earlier draft called the guard path "hot" and concluded guards must stay
TypeScript. **That was wrong on the stated grounds.** Tool calls in an agent
session are separated by model generation — seconds apart — and a
newline-delimited JSON round-trip to a warm local process is single-digit
milliseconds. It is a *frequent* path, not a *fast* one.

The real objection is that guards run inside `emitToolCall`, which has no
timeout and no `try/catch` (§5.2). A hung or dead sidecar there does not slow
the session; it **breaks every tool call in it**, in a user's ordinary work.

> **Decided 2026-08-16: guards stay TypeScript for now.** Not because the
> latency argument held — it did not — but because of the five non-transport
> risks below. The sidecar therefore exists **only during `/implement`**, a
> deliberate operation that can reasonably carry a prerequisite, and never in
> a user's ordinary session. Consequences, all simplifying:
>
> - `engine.ts` keeps its one-file, zero-dependency, `cp`-is-a-complete-install
>   property, and the always-on feature acquires no runtime prerequisite.
> - **The fail-open policy is no longer needed.** Everything on the sidecar is
>   fail-closed, which is what mutations require anyway. One policy, not two.
> - The `tools/replay_guards.mjs` harness stays exactly as it is, still
>   replaying committed fixtures through the shipped artifact.
> - No `uvx` cold start can ever stall a user's first tool call.
> - The tier table in §6.2a collapses from three rows to two.
>
> The analysis below is kept because it is the argument that would have to be
> answered if guards are ever revisited — and because the reasoning that
> *latency* forbids it is wrong and should not be re-derived.

**The failure policy, had guards moved — kept for the record:**

- **Guards fail open.** No answer within a few milliseconds, or no sidecar
  running → allow the call. Defensible on this project's own evidence: the
  docs already state guards are steering, not a sandbox (`write` and shell
  heredocs deliberately bypass `preserve-symbols`), and the shootout measured
  **zero guard firings across all 24 runs** with load verified by extension
  digest. A guard that fails open loses approximately nothing.
- **Mutations fail closed.** The mutation engine is not on this path — it runs
  inside the registered `write`/`edit` executors, where refusal is the entire
  point and a bridge failure must surface as a tool error.

One sidecar, two policies.

### 6.3 Practicality check — passed

Criteria were **pre-registered before** the transport internals were read, per
this project's own discipline.

*Practical if:* transport under ~100 lines per side; Windows a bounded known
workaround; orphan cleanup intrinsic; crash handled by respawn; one
interpreter seam. *Impractical if:* buffer limits force an awkward second
channel; Windows needs per-case shim resolution; backpressure needs real
handling; anything forces state into Python.

**Result: all five practical criteria met, none of the impractical
conditions fired.** Verified against `modelcontextprotocol/typescript-sdk`
(v2.0.0) and `modelcontextprotocol/python-sdk`:

- **Framing is trivial.** `serializeMessage` is `JSON.stringify(m) + "\n"`;
  `ReadBuffer` is ~25 lines; correlation is a monotonic counter plus a `Map`;
  close is ~20 lines. Total new surface ~150–200 lines across both sides.
- **The size worry was unfounded, and the earlier figure was wrong.** The
  64 KB limit came from *ACP's* Python SDK inheriting asyncio's default
  `StreamReader` cap. **MCP has no such limit**: the TS side's only guard is
  `STDIO_DEFAULT_MAX_BUFFER_SIZE = 10 * 1024 * 1024` (a whole-buffer cap, not
  per-message), and the Python side has **no cap at all**. Our ≤32 KiB
  payloads are nowhere near. File bodies may travel inline; moving them to a
  side channel is now an option, not a forced move.
- **Backpressure is five lines** — check `write()`'s boolean return, await
  `'drain'`. Both SDKs do exactly this.
- **Windows is solved and bounded:** `cross-spawn` + `shell: false` +
  `windowsHide` on win32.
- **Crash handling is respawn.** On transport close both SDKs reject every
  pending request (`ConnectionClosed`); with state in the shim, nothing is
  lost.

Two patterns to carry, both cheap:

- **`ReadBuffer` skips lines that fail `JSON.parse`.** This protects the wire
  from the Python child's own stray stdout — logging, warnings, a traceback.
  Exactly the failure mode that is otherwise maddening to debug.
- **The TS SDK has a real orphan gap** (no `detached`, no Job Object), while
  the Python SDK is stronger: `start_new_session=True` with group-kill on
  POSIX, and a Windows **Job Object with `KILL_ON_JOB_CLOSE`**. Since we own
  the Python side, the read loop exiting on **stdin EOF** covers it — and our
  sidecar spawns no children of its own, so there is no tree to kill.

Shutdown escalation to mirror: close stdin → ~2s → SIGTERM → ~2s → SIGKILL
(both SDKs, independently).

### 6.4 `uv` answers the interpreter question — and `uvx` may remove it

The last open practicality risk was locating a Python interpreter on a
stranger's machine. `uv` is already a hard dependency of this project
(`ensure_cohort_env` shells `uv sync --locked`; everything runs under
`uv run`; there is a committed `uv.lock`).

- **uv installs CPython itself**, so the user needs no pre-existing Python —
  which matters for "engine works outside Pi" and for a Pi user who is not a
  Python developer.
- **One static binary** on macOS, Linux and Windows, so it does not
  reintroduce the platform problem.
- **`uvx satyrn-engine` gives zero-install.** The shim's spawn becomes
  `uvx satyrn-engine@<version>`, and the ship-a-payload-as-package-data
  apparatus (§5.3) disappears entirely.

Two constraints on using it:

1. **Pin the version exactly.** An unpinned `uvx` resolves from the network at
   spawn time, so engine behavior could change between two runs with no local
   change. That is fatal on the evals side — `RunConditions` exists to make
   precisely that impossible, and `extensions_sha256` was added *because* an
   invisible behavior change had already happened once. Product path:
   `uvx satyrn-engine==<exact>`. Measured batches: a locked local install,
   never a floating resolve.
2. **Warm the cache in preflight.** First `uvx` of a version downloads and
   builds; a cold cache mid-batch is a multi-second stall and a network
   dependency inside a measurement. The harness already has a `preflight`
   subcommand checking the model server and Pi version; this belongs there.

**Residual:** locating `uv` itself — the same class of problem one level up,
but far better behaved (one binary, no venv ambiguity, no shim indirection).
Still deserves an explicit seam rather than `which uv`, given this repo's
recorded finding that the obvious lookups lie.

---

## 6.5 The evals side

### The diagnosis it must serve

The requirement, in the owner's words: *a way for contributors to capture a
Python development workflow, run it, find the problems using evidence, and
work on engine fixes* — plus a home for lessons about eval problems and
gotchas.

### How it got out of control, stated plainly

`harness/` is **6,065 lines across 27 files** — against `packages/engine/`'s
340 non-test lines, so **the harness is roughly eighteen times the size of the
engine it measures** — and its durable output is roughly five sentences: facts
beat
rules of conduct; guards are inert; machine-made bounds confine a 12B
implementer; packet content moves outcomes on one or two tasks; no wall-clock
number is trustworthy. Nearly everything else came back ceiling-tied,
floor-tied, or noise.

The specific sprawl:

- **Two systems wearing one name.** The Phase 1–5 suite harness and the
  Phase 7+ commit-replay system share almost nothing, and the collision shows
  in **two different `run_suite` functions** and **two different
  `_out_of_scope` helpers** with different semantics.
- **Three results formats** — `grading_plugin`'s `nodeid\toutcome`,
  `workload_plugin`'s `T`/`C`-prefixed four-field lines, then checkpoints,
  attempt payloads and receipts on top. The second exists because widening the
  first would have invalidated banked evidence.
- **Eight grading-rule versions**, and `RunConditions` with 13 fields and 5
  back-compat sentinels, because every added field invalidates every recorded
  checkpoint.
- **The apparatus became the subject.** Seven instrument defects from one
  external review; four silent zeros; `inspectContract` 862 → 380 → mostly
  deleted.
- **97% of repository weight was a corpus nothing reads** — 570 files,
  104.7 MiB, untracked after the fact, making a first checkout 123 MiB.

### The split: diagnosis is the product, claims are a later layer

This is the decision that governs the rest. A contributor asking *"did my
engine fix help, and if not, why"* needs to know what broke and where. They do
not need a confidence interval. Conflating the two is arguably what got out of
control.

- **Core — the diagnostic loop.** Capture, run at **n=8**, core metrics, a
  legible failure. No denominators.
- **Optional later layer — claims.** Pre-registration, intervals, cells,
  conditions-enforcement, rule 8. Most contributors never touch it.

**n=8 is cheap; comparability-by-construction is what was expensive.**
Repetition is a loop; the checkpoint is ~50 lines and already tolerates a
truncated final line; `telemetry.py` is a recomputable view over retained
stdout, so its numbers recompute over any batch ever recorded. The costly part
was `RunConditions`, cells, `resolve_cell`, `extensions_sha256`, void
semantics and retry accounting — all of which exist to make two batches
comparable by construction.

**So: record conditions, do not enforce them.** Capture model string, engine
version and git rev in every record, and *show* drift rather than aborting.
Enforcement moves to the claims layer. This also removes a live footgun —
"a commit aborts a running batch" is one of the three documented things that
will bite you, and it is `harness_revision` inside a condition-equality check.
The honest cost: enforcement is what caught the 4.4× ratio retraction and the
batch that drifted 27.3 → ~15 tok/s and was filed `CONTAMINATED`.

### The metrics, and an inversion worth noting

`accepted`/`rejected` **with its reason** (a signal, not a rate); **turns**;
**repeated identical tool calls** (the runaway — 245 × `ls -R`); **churn**
(same target, differing content — deliberately a separate concept, and the
loop breaker mostly misses it); **tool calls**; **context processed**;
**incomplete / timed out**.

These are the *thrash metrics*, which sat in the Backlog since Phase 5, never
built, gated on "a batch where the bare arm actually thrashes." That gate
fired long ago. **The metric repeatedly deferred as a research nicety is the
one the contributor loop most needs** — which is a good sign the
diagnosis/claims split is real.

### Capture: keep commit-replay's artifacts, delete its ceremony

**The finding that reframes it:** both cohort disqualifications were made by
*machine* checks, not by the ceremony. `register-value-enter` died because the
base passes its own oracle — one deterministic run. `suppress-context-exit`
died because the target's own diff, restricted to writable paths, fails
preservation — the ceiling replay, also deterministic, no model. Neither was
caught by the five prose attestations, the 3-repeat stability fingerprint, or
the frozen-cohort accounting.

**The phase was not expensive because the checks are expensive. It was
expensive because the cheap disqualifiers ran last, after the human
ceremony** — and because the manifest makes a human hand-author ~20 fields a
tool can compute.

**Decided:** `capture` points at the contributor's own repository, mines
`git log` for commits where source and tests move together, and per candidate
runs four model-free checks — base passes preservation; oracle rejects base
(recording the observed rejection fingerprint rather than requiring it
pre-declared); target passes both; and the **ceiling replay**, where
`git diff base..target` restricted to writable must grade `accepted`. That
last one is the winnability proof, and history supplies it free.

- **Human writes exactly two things:** a ten-line brief and the writable glob.
  The tool writes the rest. The brief is the irreducible cost — "behavior not
  structure" is a judgment, and a brief derived from the commit message either
  leaks the diff or says "fix #123."
- **Cost:** ~5–6 min compute per candidate, ~10 min human per survivor. **An
  afternoon yields 5–8 tasks** on a healthy repo.
- **Tier 0, nearly free: synthetic revert** — un-apply a commit's source
  change, keep its tests. Winnable by construction, minutes to generate. That
  the tasks are easy is fine: the pathologies being diagnosed fire on trivial
  work. The 261-turn run was 245 × `ls -R` **against an empty directory**.
- **The honest floor, to be published rather than discovered:** this works for
  repos with a deterministic, sub-minute, uv-lockable suite whose base and
  target run under one lock. Otherwise it is a day or more, and the miner
  should measure and say so per commit, up front.

### One task format, two capture paths — retire the `Suite` machinery

A prompt→acceptance suite **is** a commit-replay task whose base is an empty
tree, whose oracle is the hand-written acceptance file, and whose target is
the reference fixture. `writing-evals.md`'s evidence floor — known-good
passes, known-broken fails — is literally `target_oracle` + `base_oracle`
under other names. The workload-side grading is strictly stronger:
patch-include subsumes allowlist-copy, `classify` subsumes exit-code reading,
and `_REFUSED_CONFIG`'s job is done by never applying non-writable paths.

Carry across `grading.py`'s one unique idea: the refused-config list as
**recorded evidence of what the model attempted**, folded into the
out-of-scope report.

### Unit of comparison

**Paired A/B of two engine versions over one frozen task set, read per-task,
counts never seconds**, with a bare no-engine arm available as a third
comparator. A single run is triage, and is still interpretable alone because
every task carries internal anchors (`base_passed`, `oracle_delta`,
`gap_closed`). Two hard rules from the record: never pool across a task-set
edit (`manifest_sha256` already keys this), and never compare wall-clock
between contiguous arm blocks — two published figures were retracted for
exactly that. The diagnostic metrics are counts, which survive load.

### Testing: fast and cheap, enforced

Baseline to beat: **595 tests collected, 146 seconds** for a full run
(`uv run pytest --collect-only -q | tail -1`; the 146s was measured at 552
tests earlier the same day). Averaged, that is a quarter-second per test for
mostly pure code — nearly all of it subprocess spawns.

- **Default tier: no subprocess, no git, no network, no model.** Every process
  boundary is an injected callable, the way `deliver()` already takes
  `run_model`. Fixtures are committed artifacts — patches, transcripts,
  results files — replayed through shipped code. Target: whole suite in
  single-digit seconds. **Enforced mechanically**, not by convention: a
  fixture fails the build if a default-tier test spawns a process.
- **Integration tier: marked, opt-in, and out of CI.** Not optional as a
  concept — cycle 8's first live run hit **three bugs invisible to
  fixture-only tests** (missing `Authorization` header, the `--` separator Pi
  rejects, `__pycache__` in the diff), none of which exist without a real
  server and a real process. Each such test should name the class of failure
  it exists to catch.
- **One prebuilt fixture repo materialized once per session**, not `git init`
  per test.
- **Non-vacuity by construction.** The recurring hazard is that most of this
  code tests a *rejection*, and rejection is the default outcome of most
  failures, so a broken test passes. Generalize the evidence floor from
  graders to tests: **a test asserting a refusal must have a sibling asserting
  the acceptance.**

### Keep, with the incident behind each

- **Verdict never from stdout or an exit code** — hook-written results file.
  Predecessor graders were defeated by `addopts = --collect-only` and an
  import-time `os._exit(0)`.
- **`materialize` / `export_tree` / `_undo_export_subst` / `_normalize_mtimes`.**
  `git archive` stamps the *commit timestamp*, which identifies the base
  commit nearly as precisely as the SHA; `.git_archival.txt` expands into the
  exact commit. Both free to close, invisible if missed.
- **The capture→grade split.** Patch and transcript saved; grading pure and
  replayable offline. Every grading defect in this project's history was
  re-scored without re-running a model. **This property matters more than any
  capture shape.**
- **`grade_candidate`'s three materializations**, `apply_candidate(include=writable)`
  (stops self-grading), `_out_of_scope` with its `test_paths` third category,
  `_node_census`/`_vanished` for position-keyed (Sybil) nodes,
  `_oracle_shortfall`, and `GRADING_RULE_VERSION` recorded on every grade.
  Eight rule-versions of accumulated correctness; a rewrite re-earns them
  through incidents.
- **`validity.assess`** as a tripwire — the recorded reason is Phase 7 cycle
  1's `autowire` copying the target implementation out of a stale sibling
  workspace and deleting the traces. Generalize `OFF_LIMITS`, which currently
  names svcs paths. Keep its docstring's honesty: it is a tripwire, not a
  sandbox, and does not catch `cd ..`, globs, `find`, or network.
- **`stale_workspaces()`** — same incident.
- **`reference_overlap`**, recorded and never rejecting. It flagged that theft
  before anyone read a transcript.
- **`check_model_served`, not just `check_model_server_alive`.** `/v1/models`
  advertises models whose weights are gone; the 404s produced a clean-looking
  0/8 in 0.4s each that read as "authoring is the bottleneck." Verify with a
  real completion, not a model listing.

### How tied are results to the model? Completely — and that needs an instrument

Every rate this project ever produced is `gemma-4-12B-it-MLX-8bit`, and every
non-claims section says transfer to another model is not established. The
record shows two distinct ways this bites:

- **Weights vanished underneath the work.** `Qwen3.6-27B-8bit` authored the
  contracts measuring 8/8 and then stopped existing on the machine, leaving
  Phase 14 with what its own entry condition calls "a permanent confound."
- **Silent substitution reads as a result.** The 404s above. And Pi itself
  moved 0.84.1 → 0.84.2 mid-session, confounding the no-op re-run.

**The tie is unavoidable for claims and much weaker for diagnosis.** A rate
belongs to one model, one quantization, one server build — nothing fixes that.
But the pathologies are SLM-general rather than gemma-specific: 261-turn
`ls -R` loops, churn, stopping to ask instead of writing, no-op edits.
Counting *those* is robust even when absolute rates move. This is a further
argument for a metric set built from pathology counts rather than accept
rates.

**Build: a model canary.** A fixed prompt at temperature 0, short
deterministic output, hashed and recorded with every batch. If the model
silently changes — different weights, different quantization, a server
upgrade, an edited `maxTokens` — the hash moves and the record says so,
instead of the change surfacing months later as an unexplained rate shift.

Cells pin the model *string*, and a string is precisely what did **not** change
when the weights disappeared. The canary closes that gap for a few tokens per
batch.

Evidence it will work on this stack: the echo probe reproduced **2,031
characters byte-identically, 40/40, across two channels** — this server is
deterministic enough at temperature 0 for a canary hash to be meaningful.
Worth confirming across a server restart before relying on it.

**Interleave the arms.** Proposed originally against wall-clock drift, it also
protects here: if the model or the machine changes mid-batch, interleaved arms
share the damage instead of one arm absorbing it. Since A/B compares two
engine versions against the same model, interleaving controls the model almost
entirely.
- **The `--deselect` logic for base-vs-target assertion conflicts.** When a
  target diff *changes* an existing assertion, the base test is guaranteed to
  fail against any correct fix, because the model may only write source while
  tests stay at base. Caused a false 0/4 on `flask-extensions`.
- **`run_process`'s process-group teardown** — new session, SIGTERM, 5s drain,
  SIGKILL — and `disposable_dir`'s unconditional cleanup.
- **A repo-weight policy from day one**, before a corpus exists.
- **Docs excluded from formatters** — `ruff format` over `docs/` would
  silently edit preserved research records.
- **The concept budget.** Decided: carried forward as a practice. It is the
  cheapest discipline in the repo and it caught real sprawl. Carry the lapse
  too: it fell twelve cycles behind and was paid off in one lump, and the
  existing test deliberately does *not* demand it keep pace, because that
  would create pressure to invent vocabulary to satisfy a test.

### Build, because it does not exist

**Transcript and patch persistence.** `run_process` captures stdout only in
memory and `disposable_dir` deletes worktrees unconditionally, so the Cycle 7
archive holds **65 receipts and nothing to replay** — no transcripts, no
diffs. This is a documented gap, not a feature to carry over, and it is
non-negotiable for a diagnostic loop whose primary artifact is the transcript
rather than the grade.

### Leave out

- **`Suite` / `Improvement` / `RunConditions` / `SUITES` / `IMPROVEMENTS`** and
  the whole second lifecycle. Also the `improvements/` seed-dir mechanism —
  A/B on engine versions replaces the `improvement` concept entirely.
- **`REQUIRED_ATTESTATIONS` as hard failures.** Five prose items per task, the
  largest human line-item, and they caught neither disqualification.
- **`MIN_REPEATS = 3` and cross-repeat stability fingerprints.** Run once at
  capture; re-run a condition only when a grade looks suspicious — the
  instrument-fault discipline that already survived its own delete rules.
  `MAX_SECONDS_CEILING` becomes a warning, not a refusal.
- **Cells, `resolve_cell`, `extensions_sha256`** → an engine version.
- **Frozen-cohort accounting, `role`/`axes`, `contract_version`,
  pre-registration, intervals, precision, void-and-retry semantics, rule 8's
  pilot/confirmatory distinction.** All claims apparatus.
- **`leak_probe`** — model-based, 3 samples at 2-of-3 agreement, and it
  produced a full leaked→clean flip on *identical bytes* for two tasks.
  `reference_overlap` gives most of the signal deterministically.
- **The contract-authoring machinery** (`author_contract`,
  `reauthor_until_clean`, the authoring predictions) — that role moved to the
  main agent via a skill.
- **`inspectContract` in any form.** Already deleted under pre-registered
  rules; do not let it back in.
- **The evidence-archive checksum apparatus.** Claims layer — and its own
  correction (neither bundle's `CHECKSUMS.sha256` covered its `MANIFEST.md`)
  shows the maintenance cost.
- **The screen corpus tracked in git.**

### The lessons home

`docs/evals/slm-struggles.md` — 24 failure modes, each with a source pointer —
is already the thing the owner asked for. In the rewrite it is a **first-class
deliverable**, not a page someone found time for. It is also the natural home
for the eval-side gotchas, indexed **by symptom** per §1.1.

## 7. Proposed roadmaps

Proposed, not decided. Each phase delivers **one thing that actually works**,
small enough to hold in one head. The sizing rule is `BRIEF.md`'s: the scarce
resource is the ability to hold the design in mind, not speed.

Three patterns are mined forward from what demonstrably worked here:

- **Prove the machinery on something already established, before using it on
  something new.** Phase 4 cycle 1 and Phase 6 cycle 1 both did this
  deliberately, so that the first *new* thing was not also the first test of
  the apparatus judging it.
- **Inject the model.** `deliver()` takes `run_model` as a parameter, so every
  branch is testable at zero cost. Generalize to every process boundary.
- **The evidence floor.** Nothing is done until it has accepted a known-good
  and rejected a known-broken input.

> **Revised after review.** The first draft had seven phases a side and put
> the bridge at E5 — which **violated this document's own §2 amendment**, the
> one added in response to the previous review, saying that if the engine is
> Python the refusal must round-trip through the bridge or the slice is
> vertical through the wrong stack. Scheduling the riskiest joint fifth meant
> four phases of Python work silently assuming it would be fine. The bridge is
> now E3, fused with the refusal so it has a user-visible deliverable.
> Publishing was also evicted from phase 1 (see below), and E1+E3 / V1+V2 were
> merged. Six phases a side.

### 7.1 `satyrn-engine`

| # | Phase | Delivers | Done when |
|---|---|---|---|
| E1 | **It installs and refuses** | `satyrn-engine check <contract.md>` — parse, validate, path-lint, refuse with a named cause | A clean CI machine runs `uv tool install . && satyrn-engine --version` exit 0; exits 0/2/4 distinguished; a refusal makes **zero model calls**, asserted by a test that fails if the model is invoked; the default tier passes in <10s; **a planted process-spawning test fails the build**, demonstrated once and kept as a fixture; the print-mode probe passes |
| E2 | **The guards ship** *(no ordering dependency — may run first)* | `pi install` → both guards active in every session | Replay fixtures drive the **shipped bundle**; one fires, one stays silent; `engine.ts` imports nothing local |
| E3 | **The bridge, carrying the refusal into a real Pi child** | `/implement <contract.md>` refuses, with a named cause, from inside Pi | Windows **and** POSIX CI green; killing the parent leaves no orphan (stdin-EOF); a non-JSON line on stdout is skipped, not fatal; **for each failure fixture — dead process, hang past deadline, garbage stdout, non-zero exit, missing interpreter — the shim returns a refusal rather than throwing**; Pi version pinned |
| E4 | **The delivery lifecycle** | `satyrn-engine deliver --model-cmd <any executable>` produces a candidate ref using a trivial shell script as the model — no Pi, no server | Every outcome branch tested with an injected model; the receipt carries the **engine version**; a test snapshots `git status --porcelain` + HEAD before and after and asserts byte-equality |
| E5 | **The mutation engine behind the bridge** | Bounded `write`/`edit` with revision checking, inside a real Pi child | Exactly six refusal cases pass — stale revision, no-op edit, ambiguous anchor, undeclared symbol loss, cross-file move, oversized proposal — **and nothing else is in scope** |
| E6 | **`/implement` end to end, packaged** | `pi install` + `uvx satyrn-engine@<pin>` drives a contract to a candidate ref in a **named** external repository | Works outside a checkout with no `tools/` on disk; the external repo is named in the spec, not chosen after the fact |

**Why this order.** E1 is the proven slice — the refusal path measured at
0.109s, needing no model — fused with install because a phase whose only
output is a version string is the anti-pattern `BRIEF.md` names. E2 is nearly
free and off the critical path: `packages/engine/` has zero dependencies and
`engine.ts` imports nothing local, so shipping it is a directory copy, and the
replay fixtures mechanically block the real risk (improving the guards in
transit). E3 front-loads the bridge per §2. E4's deliverable is a *real* no-model
run, not a test double — an arbitrary executable stands in for the model.

**Evicted from phase 1, deliberately:** publishing to an index and a
three-OS matrix. `uvx satyrn-engine` requires a published package — a name, an
index, a release pipeline — which is E6-class infrastructure fronted into E1
for no phase-1 value. Phase 1 installs from a checkout. Windows lands at E3,
where the entire Windows analysis (§6.2) actually applies.

**E5 is the scope-blowup risk.** It stacks a Python port of
`mutation-engine.ts`, the bridge under real `tool_call` dispatch (the
no-timeout, no-`try/catch` zone of §5.2), the untraced `registerTool` executor
path, and six refusal cases. Pre-emptive cuts: the six recorded refusals are
the **entire** scope — no loop breaker, no churn detection, nothing not on the
list — and open question 2 gets resolved by reading *before* the phase starts,
not inside it. One tax disappears here: porting TS→Python inverts the fnmatch
problem, because Python's `fnmatch` becomes the reference semantics and the
differential-test burden dies with the TS side.

**Not in this roadmap:** contract *authoring* (a skill, and the main agent's
job), any measurement, and any claim about whether the engine helps.

### 7.2 `satyrn-evals`

| # | Phase | Delivers | Done when |
|---|---|---|---|
| V1 | **It installs and grades** | `satyrn-evals grade <task> <patch.diff>` — offline, no model, no network | `uv tool install .` on clean CI, exit 0; against one **bundled example task** the known-good patch is accepted and the known-broken rejected, each asserted **by naming the fixture**; the bundled task pins its environment with a committed lockfile; the known-good/known-broken assertions run in the **fast tier against committed oracle results**, the full grade in the **marked integration tier**; planted-spawn tripwire as E1 |
| V2 | **Capture, tier 0: synthetic revert** | `satyrn-evals capture --revert <sha>` makes a task in minutes | The generated task is winnable by construction — its own reverted diff grades `accepted` |
| V3 | **Capture, tier 1: mine the repo** | A reporter: candidate commits, four model-free checks, per-commit rejection reasons, tasks emitted in V2's format | Run against a **named fixture repository**: the two recorded disqualifiers (base passes its own oracle; target's own diff restricted to writable fails preservation) are caught automatically, before any human writes prose |
| V4 | **One attempt against an engine** | A single run, graded, with **transcript and patch persisted** | Fully replayable offline — re-grading needs no model; the plumbing is proven against a **fake engine replaying a committed transcript**, with the real engine as one configuration of the same seam |
| V5 | **The diagnostic loop** | `run --n 8` plus a summary: accept/reject with reason, turns, repeated identical calls, churn, tool calls, context, timeouts | Conditions **recorded, not enforced**; a mid-batch commit does not abort the run; the model canary is recorded per batch |
| V6 | **A/B two engine versions** | "Did my fix help" — paired, per-task, counts only | Arms interleaved; never pools across a task-set edit; **the results schema contains no seconds field** |

**Why this order.** V1 grades against a committed example task before any
capture exists — the prove-the-machinery-on-something-established pattern.
V2 before V3 because a synthetic revert is winnable by construction, so it
tests the task format without also testing the miner's judgment. V4 before V5
because n=8 of a run you cannot inspect is worse than one run you can.

**V3 is the V-side blowup risk**, pre-cut to a *reporter*: candidates, the
four checks, rejection reasons, emission in an already-proven format, and no
polish. The earlier draft promised "5–8 tasks in an afternoon" as a
deliverable; that figure comes from one hand-curated repository — svcs went
10 → 8 *after* curation — so it is an expectation to test, not a commitment,
and it has been moved out of the deliverable.

**Resumability is deliberately not in V5's done-when.** For batches of eight
short runs it is claims-layer instinct leaking back. Carry the ~50-line
checkpoint verbatim if it transplants cleanly; do not rebuild it.

**Two keep-list items are scheduled to their consumer rather than day one**,
per no-machinery-ahead-of-contract: `_node_census`/`_vanished` arrives with
the first Sybil position-keyed task; `materialize` / `_undo_export_subst` /
`_normalize_mtimes` arrives with V2/V3, since the leak channel it closes only
exists once tasks come from real repositories.

**Running throughout, not a phase:** the lessons file. Every phase that finds
a gotcha writes it up, **indexed by symptom** (§1.1). It is a first-class
deliverable, not a page someone finds time for.

**Not in this roadmap:** pre-registration, intervals, cells, void semantics,
the pilot/confirmatory distinction. Those are the claims layer, and they
arrive when someone first needs to publish a number — not before.

### 7.3 The dependencies between them

**Corrected after review — the first draft said "V5 needs E7," which
conflated two different needs.** V4 needs *an invocable thing that produces a
patch, a transcript and a receipt*. That is **E4**, or even this repository's
current engine as a stand-in — a checkout invoked by the harness is how
everything here has always run. E6 (packaged, published, works outside a
checkout) gates only the *contributor-facing* story, not development.

Better still: define the evals-side seam as **"an attempt command."** Then V4's
plumbing is provable against a fake engine replaying a committed transcript —
the inject-the-model pattern, one level up — and the real engine is one
configuration of it. That cuts roughly half the serialization between the two
repos.

**A second edge the first draft omitted entirely.** The task manifest, the
contract file, the patch, the receipt and the transcript are all read from
both sides, and **no phase in either roadmap owns pinning them.** This is
`HandoffContract`'s two-hand-synced-declarations problem reborn at repository
scale — §3 item 3 predicts it and then nothing schedules it. Cheapest fix: the
formats live as **committed fixtures in the engine repo**, and V1's bundled
example task *is* one of them, so there is one source of truth exercised from
both sides.

Open question 8 still lands here: if V6 requires two engine versions installed
side by side, that is a packaging requirement on `satyrn-engine`, discovered
from the evals side and worth knowing before E1 fixes the install shape.

## 8. Open questions

**Still open:**

1. What replaces `extensions_sha256` for cross-repo provenance — an engine
   version, a lockfile digest, or something else — and what sentinel retires
   the existing cells? Interacts with §6.4's pinning requirement.
2. Does the tool-executor error path (`pi.registerTool`) carry the same
   hazards as the `emitToolCall` path? Half the surface is untraced (§5.6).
3. How is `uv` itself located — an explicit seam, and what is the fallback
   when it is absent? (§6.4 residual.)
4. ~~Does the Python engine ship the guards too?~~ **Decided: guards stay
   TypeScript** (§6.2b). Revisit only if the everyday path gains a
   Python prerequisite for some other reason.
5. What is the actual protocol surface? Four methods were sketched
   (`readReceipt`, `propose`, `proposeEdits`, `shutdown`) for the mutation
   tier; the guard tier needs its own, and the delivery tier may need none.
6. Do file bodies travel inline (now permitted — §6.3) or does the sidecar
   read the workspace itself? The latter is smaller on the wire and the
   sidecar is on the same machine anyway.
7. **Evals:** what exactly does the `capture` miner filter on to find
   "commits where source and tests move together," and what is its expected
   hit rate on an arbitrary repo? svcs went 10 → 8 *after* hand-curation. The
   design answer is to make rejection cost minutes of compute rather than an
   afternoon of prose — not to raise the hit rate — but the rate still sets
   the contributor's experience.
8. **Evals:** does the diagnostic loop need to hold two engine artifacts at
   once for A/B (§6.5), and if so how are they installed side by side? This is
   a packaging requirement on `satyrn-engine`, discovered from the evals side.
9. **Evals:** environment reconstruction is the hidden cost of "any Python
   repo." How does `capture` decide a repo qualifies, and does it refuse
   loudly or degrade?
10. **Evals:** is the model canary actually stable? It must be verified
    across a **server restart**, not just within one session — the 40/40 echo
    evidence is same-session. If it drifts on restart it is a false alarm
    generator and must be dropped rather than tuned. Also open: what does a
    canary mismatch *do* — refuse the batch, or record and continue? For
    diagnosis, recording and continuing is probably right; for claims it
    should refuse.

**Leaning toward Python, not yet decided.** §4.3a's steelman for TypeScript
was answered by §4.3b's three requirements — outside-Pi use, audience, and
evals reuse — none of which the review had in view. The practicality check
(§6.3) passed. What remains is a decision, not an investigation.

**Answered, with the lean recorded** — questions 2–6 of the first draft. The
document already contained the evidence to answer them, and recording the lean
rather than re-deriving it next cycle is the entire point of this file:

- *Print-mode lifecycle* → `session_shutdown` fires on normal exit, errors,
  SIGTERM/SIGHUP; not on SIGINT or SIGKILL (§5.5). Probe to confirm on the
  pinned version.
- *Per-call vs persistent* → same protocol either way if state stays in the
  shim (§6.1). Ship per-call, upgrade on measurement. The ~50ms hop estimate
  was optimistic — a real engine importing its modules is more like 100–300ms,
  so ~3–9s across 30 calls: negligible against a 900s run, ~25% against a 23s
  one. Measure before promoting.
- *Wire protocol* → hand-rolled newline-delimited JSON-RPC, four methods; not
  `vscode-jsonrpc` (§6.2).
- *Subinterpreter pool* → machinery ahead of its contract here (§6).
- *Interpreter location* → one explicit env seam with a `uv run` fallback
  (§6.2).

---

## 9. What this document does not establish

- No decision has been made about Python. Section 4 records an argument and a
  changed cost, not a conclusion.
- The Pi API findings are from reading source and docs, not from running
  anything. The print-mode question in particular is explicitly unverified.
- Nothing here is measured. No rate, no timing, no comparison. The ~50ms
  per-subprocess-hop figure in open question 3 is an estimate used to size a
  decision, not an observation.
- The third-party extension survey is four packages found by npm keyword and
  GitHub search. It is not a census, and `pi-lsp` itself could not be read.
  **Review could not verify any of it** — none of the four packages are on
  this machine, and the clones live only in a session scratchpad. Treat the
  survey as reported, not confirmed.
- **The ~1,500-pair fnmatch sweep has no committed evidence.** Section 4.3
  cites it as recorded history; it is not. The `[z-a]` behavior it describes
  *was* reproduced live against the `ts-engine-core` branch during review, and
  the defect is **still unfixed** — but the sweep itself is currently
  unfalsifiable. The 357-pair harness that caught `[]a]` was likewise never
  committed; only its narrowed regression survives in `scope.test.ts`.
- The Python-embedding assessment (option d) is reasoned from general
  knowledge, not verified locally. Its decisive point — that Pi ships as a
  Bun-compiled single binary (`bun build --compile`, verified) — makes
  third-party N-API addons an unsupported seam regardless.
- Startup-cost figures for a Python hop are estimates used to size a decision,
  not measurements. The same applies to the "single-digit millisecond"
  round-trip figure in §6.2b: the only source found for it self-describes as
  "engineering estimates assembled from published benchmarks... not measured
  production telemetry."
- The MCP SDK findings in §6.3 **were** verified from source (both repos
  cloned, constants and line numbers checked). The ACP findings and the
  four-extension survey were not.
- CPython's `AF_UNIX`-on-Windows status is **uncertain, not settled**. An
  earlier draft of this file asserted it was unsupported; the tracking issue
  appears open and the stdlib docs say to feature-detect. The transport
  conclusion does not depend on resolving it.
- No measurement exists for any of this. Nothing here has been built or run.
