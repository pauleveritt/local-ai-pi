# Phase 3, Cycle 2 — Specialized subagent

**Phase:** 3 — Build the extension half
**Status:** design, awaiting plan

## Why this cycle

Cycle 1 made the extension observable. This cycle makes one *delegation*
happen: a parent Pi run that spawns a child Pi run, with a specialist this
project wrote, under conditions this project controls.

Cycle 3 attributes cost between parent and child. Cycle 4 finally tests the
handoff-packet claim that justified building telemetry at all. Neither can
start until a delegation exists to measure.

**No TypeScript is written.** Pi ships a complete subagent extension at
`examples/extensions/subagent/` (`index.ts` 1015 lines, `agents.ts` 127,
plus sample `agents/` and `prompts/`). This cycle enables it, isolates it,
and specializes it with data.

## The two problems, and the one lever that solves both

### Problem 1: the child inherits none of the harness's isolation

The child is spawned with exactly

```js
const args = ["--mode", "json", "-p", "--no-session"];
```

— `examples/extensions/subagent/index.ts:294` — plus `--model` and `--tools`
from the agent's frontmatter and `--append-system-prompt`. The parent, as
`harness/runner.py` invokes it, also passes `--no-extensions --no-skills
--no-prompt-templates --no-themes --no-context-files --approve`. The child
gets none of them.

On the owner's machine this is not hypothetical. `~/.pi/agent/extensions/`
contains `rtk.ts` and `ds4-laguna-s-greedy.ts`, and `~/.pi/agent/AGENTS.md`
exists. `rtk.ts` rewrites bash commands — landing directly on what cycle 4
sets out to measure.

### Problem 2: project agents are undiscoverable from the harness's workspace

`agents.ts`'s `findNearestProjectAgentsDir` finds `.pi/agents/` by walking
**up from cwd**. The harness runs Pi in a disposable temp workspace, so the
walk goes from `/var/folders/…` to `/` and finds nothing. An
`.pi/agents/implementer.md` committed in this repo is invisible to the run
that would use it.

### The lever

`getAgentDir()` honours the environment variable `PI_CODING_AGENT_DIR`
(`dist/config.js:412-418`, name constructed at `:397`). `index.ts` contains
no `process.env` reads and its `spawn` passes no `env:`, so **the child
inherits the parent's environment**.

One variable therefore does both jobs: it relocates where parent *and* child
look for extensions, agents, and `AGENTS.md`, and it puts `implementer.md`
somewhere the child finds as a **user-scope** agent, independent of cwd.

**Verified by running, not only by reading.** With the variable pointed at a
pre-provisioned directory, `pi --print --mode json …` exits 0 and produces
normal output, with and without `PI_OFFLINE=1`.

**And a cost found the same way.** Pointed at an *empty* directory, Pi
bootstraps: it `git clone`s `obra/superpowers` and runs npm installs. That is
slow, network-dependent, and clones a third party's HEAD — non-deterministic
by construction. The controlled directory must be **pre-provisioned and
reused**, never created per run, and a missing one must fail loudly rather
than letting Pi bootstrap.

## Why not fork the shipped extension

The owner proposed forking it. Rejected, on one argument that would hold even
if the roadmap had said the opposite:

**A fork makes drift silent; using the shipped tree makes drift loud.** The
example imports `ExtensionAPI`, `getAgentDir`, `CONFIG_DIR_NAME`,
`parseFrontmatter`, `pi-tui` components, `pi-ai` types, and
`pi-agent-core`'s `AgentToolResult`. A vendored copy freezes our code against
a substrate that keeps moving — the worst posture available, and one this
project has already been bitten by twice (Phase 2 cycle 1's 0.81.1 beliefs
false in 0.82.0; Phase 3 cycle 1's stale `appendEntry` signature). Whereas if
the shipped tree is referenced by path and **digested into `RunConditions`**,
a Pi upgrade changes the digest and `run_batch` refuses to resume the
checkpoint. The existing drift discipline fires automatically.

Supporting reasons:

- Of the example's 1015 lines, roughly 410 are TUI renderers that are dead
  under `--no-themes`, ~200 are parallel and chain modes this project does
  not want, and the actual machine is ~250 lines plus 127 for discovery. So
  "fork the example" and "write the ~150-line tool the example taught us to
  write" are different proposals wearing one word.
- `BRIEF.md`'s central warning is that three prior attempts died by becoming
  engineering efforts about orchestration. The example *is* an orchestrator —
  parallel and chain modes, concurrency caps, a `{previous}` chaining DSL.
  Today all of it is Pi's and this project answers for none of it.

**What the fork would genuinely buy**, and the cheaper substitute:
deleting `parallel` and `chain` from the model-facing tool schema. Parallel
mode would put up to four children on the single-threaded local model at
once, violating `BRIEF.md`'s sequential-runs rule from *inside* a run. Single
mode preserves that property by construction, since the parent blocks on the
tool call. The substitute is a **refusal check**, not a fork — see below.

The ~150-line own tool goes to the backlog behind an explicit evidence gate:
adopt it when a measured run shows the shipped extension contaminating or
losing a measurement. That is `BRIEF.md`'s own rule — no machinery ahead of
the contract it serves — applied to the one delta a fork offers.

## Design

### 1. The controlled agent directory

A skeleton committed in-repo, copied into place before a run:

- `agents/implementer.md` — the specialist, frontmatter `name` and
  `description`, body is the system prompt
- `extensions/` — empty. This is what excludes `rtk.ts`.
- model and provider settings sufficient to reach
  `omlx/gemma-4-12B-it-MLX-8bit`
- **no `AGENTS.md`**
- settings that do **not** set `defaultProjectTrust`

The harness sets `PI_CODING_AGENT_DIR` to the provisioned copy for the parent
invocation; the child inherits it.

### 2. Directory digests — the decision cycle 1 deferred

Cycle 1's `_extension_digest` raises on a directory, deliberately, so that
"cycle 2 should be forced to decide how a tree is hashed rather than inherit
a plausible wrong answer." This cycle decides: **sorted relative paths, each
with its file's SHA-256, hashed together.**

Two things get digested into `RunConditions`: the shipped extension tree, and
the provisioned agent directory. **The implementer's system prompt is a run
condition exactly as the task spec is** — a batch must refuse to resume
across an edited `implementer.md`.

The shipped extension lives at a machine-specific path, so the harness
resolves it from the installed package rather than hardcoding it. The
**digest is the identity; the path is provenance.**

### 3. The refusal check

A run whose delegation shows `mode != "single"`, or an unexpected number of
delegations, is refused — the same posture as the grader's refusal of
model-written config. This is what keeps one-model-no-isolation intact inside
a run, and it converts the parallel-mode risk into evidence: if a measured run
shows the model reaching for parallel despite the prompt, that is the gate
opening for the own-tool.

### 4. The specialist and the orchestrator prompt

`implementer.md` plus an orchestrator prompt that gives the parent a reason to
delegate. The tool's `agentScope` stays at its `"user"` default.

## Proving it

**A gating spike first, as in cycle 1**, because one claim is only
half-established. The parent's `tool_execution_end` event does reach stdout
carrying `result` — confirmed in this project's own fixture
`tests/fixtures/pi-run-0.82.0-entry-appended.jsonl`, where every such event
has keys `["isError","result","toolCallId","toolName","type"]`. But for those
builtin tools `result` contains only `content`. Whether the **subagent** tool's
`details` — the child's messages, turns, and usage — survives into the raw
event is plausible from the types and **unproven**. Cycle 3's attribution
depends on it.

So the spike answers one question: does a real delegation put the child's
usage into the parent's captured stdout? If yes, cycle 3 is a reader over data
already present. If no, cycle 3 needs a different route and this cycle's
finding is that.

Then the evidence, committed as a fixture the way cycle 1's was: a parent
stream containing a `tool_execution_start`/`tool_execution_end` pair with
`toolName: "subagent"`, whose result shows our `implementer` was the agent
that ran.

## What this cycle refuses to do

- Write or vendor any TypeScript
- Modify the shipped example in place
- Pass `agentScope` other than `"user"`
- Add per-child timeouts, retries, or capture machinery cycle 3 has not asked
  for
- Attribute cost between parent and child — that is cycle 3

## A hazard found while doing this, recorded because it outlives the cycle

`--approve` is **not** an isolation flag, despite its company in
`_pi_command`. Pi's help defines it as "Trust project-local files for this
run" (`cli/args.js:263`); it widens trust and has nothing to do with
approving tool calls. The reason a model cannot write `.pi/extensions/evil.ts`
into its workspace and have it load is `--no-extensions`. Drop that flag and
`--approve` makes model-written extensions loadable. Corrected in
`harness/runner.py` and in cycle 1's chapter.

## Gates

`uv run pytest && uv run ruff check . && uv run pyrefly check`, plus a clean
strict Sphinx build. Runs are sequential, never concurrent. Never `git commit`
while a `run_batch()` is in flight.
