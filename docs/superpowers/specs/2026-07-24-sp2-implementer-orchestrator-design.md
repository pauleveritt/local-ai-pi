# SP2 — Part III (SDD on Pi) Design

**Date**: 2026-07-24
**Status**: approved in brainstorming, reframed after review against shipped Pi subagent example; revised after deep review (Fable, 2026-07-24)
**Parent**: [course-design](2026-07-23-course-design.md) Part III

**Deep-review revisions (2026-07-24):** the reframe's premise held (the example
ships inside the installed package), but two findings would have failed on first
contact and are now fixed in this document: every delegation must pass
`agentScope: "both"` (the default `"user"` scope never reads `.pi/agents/`),
and the SP1 harness needs a defined SP2 invocation profile (its hardcoded
`--no-extensions --extension hello-world.ts` would have made every SP2 run an
SP1 rerun). Also: `pi install` does not install `agents/*.md` (Chapter 1 gains
a locate/copy recipe); citations pin to the installed copy, which is newer than
the checkout; the orchestrator prompt moved out of `.pi/agents/` so it cannot be
self-delegated to; success is decided by the harness's own pytest + diff, never
the child's self-report; and packet fidelity (verbatim literals) is now a
measured drift metric.

## Purpose

Teach the Pi subagent mechanism and the roadmap-and-packet method by installing
the **shipped** Pi subagent extension and specializing it for the AgentClinic
workload. Part III's deliverables are an `implementer` specialist, a parent
orchestrator system prompt, and a measured comparison against the SP1 0/8
baseline.

**Reframing (SP2 review):** The original master spec described a separate
"orchestrator subagent" built as a registered tool from scratch. Pi already ships
a complete subagent extension (`examples/extensions/subagent/`) that provides the
mechanism. The course installs and specializes it rather than rebuilding it.
This is truer to the "built-in Pi only" constraint and more honest with the
reader — the mechanism comes from Pi, the specialization comes from the course.

## Non-negotiable constraints

- **Built-in Pi only.** The subagent mechanism comes from Pi's shipped example
  extension. No fork, no patch, no reimplementation.
- **Evidence-gated.** Chapters 2 and 3 each produce a dated report comparing
  against the SP1 0/8 baseline. The implementer specialist ships; the planner
  and fleet are evidence-gated (see course design).
- **Same model for parent and child.** Both run
  `omlx/gemma-4-12B-it-MLX-8bit`. No bigger-model planner yet — the planner is
  evidence-gated in the roadmap backlog, not a scheduled follow-on.
- **The AgentClinic app is fixed.** Same workload as SP1, same Phase 1-3
  roadmap, same acceptance criteria.
- **Phase-agnostic.** The same implementer specialist and orchestrator prompt
  work for all three phases by extracting each phase from the roadmap in turn.

## Architecture

```
Parent pi session (SLM, prompted as orchestrator)
  │  Loads: shipped subagent extension (installed via pi install)
  │  System prompt: agents/orchestrator.md
  │  ┌─────────────────────────────────────────────┐
  │  │ "Build Phase 1 of the AgentClinic app.      │
  │  │  Use the subagent tool with the implementer │
  │  │  specialist."                                │
  │  └─────────────────────────────────────────────┘
  │
  └─ Tool call: subagent({ agent: "implementer", task: "<packet>",
                            agentScope: "both" })
      │
      └─ Child pi --mode json -p --no-session
           --append-system-prompt <temp file: frontmatter-stripped
                                   implementer.md body>
           --tools read,write,bash
           Task: <packet>
```

**`agentScope: "both"` is load-bearing, not optional.** The tool's default is
`agentScope ?? "user"` (installed `index.ts:473`), and under `"user"` scope
discovery never reads `.pi/agents/` at all (`agents.ts:101-102`) — the call
above without it returns `Unknown agent: "implementer"`. The orchestrator
prompt must therefore mandate the parameter on every delegation, and the
Chapter 1 walkthrough must show the failure mode (omit it, watch discovery
come back empty) so the reader understands why it is there.

Note also the `--append-system-prompt` mechanics: the extension does not pass
an `@file` reference. It strips the specialist's frontmatter and writes the
body to a temp file, then passes that path (installed `index.ts:294-327`).

### What the shipped extension provides (no code to write)

| Capability | How |
|-----------|-----|
| `subagent` tool registration | `pi.registerTool({ name: "subagent", ... })` in `index.ts` |
| Specialist discovery | `agents.ts` scans `~/.pi/agent/agents/` and `.pi/agents/` for `.md` files with frontmatter (`name`, `description`, `tools`, `model`) |
| Child process spawning | `spawn(pi, ["--mode", "json", "-p", "--no-session", ...])` with `--append-system-prompt` from specialist body |
| Tool restriction | `--tools` flag built from specialist frontmatter `tools:` field |
| Streaming output | JSONL line-by-line parsing, `message_end`/`tool_result_end` collection |
| Usage tracking | Turns, input/output tokens, cache, cost — aggregated from the child's JSONL `message_end` events and surfaced in the parent tool result |
| Result size cap | The installed version caps each task's collected output at 50KB — packet and result design must stay well under it |
| Abort handling | SIGTERM → SIGKILL cascade |
| Security model | Project-local agents require `agentScope: "both"` + a confirmation prompt — **but the confirmation only fires when a UI is present** (`ctx.hasUI`). Headless runs, including every measurement run in this Part, silently bypass it. The chapter states this plainly rather than implying a protection the runs don't have. |

### What the course authors (two files, no TypeScript)

| File | What |
|------|------|
| `.pi/agents/implementer.md` | Specialist: frontmatter (`name: implementer`, `tools: read,write,bash`, `model: omlx/gemma-4-12B-it-MLX-8bit`) + system prompt teaching the implementer to accept packets and build exactly what's specified |
| `prompts/orchestrator.md` | Parent system prompt: teaches the parent to extract phases from the roadmap, construct packets with the right format, dispatch via the subagent tool (always with `agentScope: "both"`), and verify results. Loaded via `--append-system-prompt prompts/orchestrator.md` on the parent invocation. |

The orchestrator prompt deliberately does **not** live in `.pi/agents/`. Any
`.md` file there carrying `name:`/`description:` frontmatter is discovered as a
*callable specialist* (`agents.ts:54`) — an SLM parent could then self-delegate
to "orchestrator", nesting with no depth cap. Keeping it in a plain repo
directory and loading it by flag makes it a prompt, not a delegation target.

### The packet format

The orchestrator prompt teaches the parent to construct packets with this shape:

```
## Task
<extracted phase from roadmap>

## Allowed Files
- app.py
- templates/base.html
- templates/home.html (Phase 1 only)
- tests/test_app.py

## Acceptance Strings
- "Come in. Sit down. Tell us about your human."  (Phase 1)
- "Scope creep never ends."  (Phase 2)

## Validation
uv run pytest -q
```

The implementer specialist is taught to read the packet, build exactly what it
specifies, not explore or redesign, and report success/failure to the parent.

### The implementer specialist (`agents/implementer.md`)

Bakes LESSONS #1 and #4 into a focused system prompt:

- "You are an implementer. Build exactly what the packet specifies."
- "Do not explore, plan, or redesign. Do not read files not listed in Allowed Files."
- "Acceptance strings must appear verbatim in the output."
- "Run validation (uv run pytest) before reporting completion."
- Tools: `read`, `write`, `bash` (no `edit`, no `grep`, no recursion via extensions)
- Model: `omlx/gemma-4-12B-it-MLX-8bit`

## Chapter outline

### Chapter 1 — "The Subagent Mechanism"

Obtain and load the shipped subagent extension. This is a real recipe, not a
one-liner, and the chapter must be honest about both steps:

1. **Locate.** The example ships *inside the installed package*, not on the
   reader's PATH. The chapter gives a command to find it from the `pi` binary's
   own install location (e.g. resolving the package root from
   `$(which pi)` and looking under
   `…/@earendil-works/pi-coding-agent/examples/extensions/subagent/`). No
   source checkout is required — this keeps the "reader without the checkout"
   constraint intact.
2. **Install the extension, then author the agent.** `pi install <that path>`
   (or `--extension <that path>` per run) loads the *extension* — but pi's
   package resource types are extensions/skills/prompts/themes only:
   **`agents/*.md` files are not installed by `pi install`.** With an empty
   `~/.pi/agent/agents/` and default `"user"` scope, the tool reports
   `Available agents: none`. The chapter has the reader copy or author one
   specialist file as an explicit step, and shows the empty-discovery failure
   first so the two-part structure (mechanism = extension, specialists = data
   you own) is learned rather than tripped over.

Then run a trivial delegation ("summarize this spec") to observe the event
flow, and dissect `index.ts` and `agents.ts` to teach the registered-tool
pattern, specialist discovery, and child process mechanics.

**All dissection and `file:line` citations pin to the installed copy**, not the
development checkout — the installed example is newer (it adds, among other
things, the 50KB per-task result cap) and line numbers differ. Citing the
checkout would give readers references they cannot follow.

End-to-end: the reader loads the extension, sees a tool call spawn a child, and
reads the result. No AgentClinic build yet — just the mechanism.

### Chapter 2 — "The Implementer + Orchestrator"

Author the `implementer.md` specialist and `orchestrator.md` system prompt. The
parent loads the orchestrator prompt and the subagent extension, then builds all
three AgentClinic phases by dispatching packets to the implementer tool.

Measurement: n=8 runs of "Build Phase 1" through the implementer. The harness
measures per-phase success rate (the parent's session JSONL shows the subagent
tool call and its result). Compare to SP1's 0/8 per-phase baseline.
Expected: 0/8 — the packet-quality problem is real — but the data is richer
than SP1 because we can see whether the failure is at the packet, implementer,
or test level.

### Chapter 3 — "Lessons from the Handoff"

Examine the Ch2 failures. The packet format, parent prompt, and implementer
guardrails are tuned based on specific failure patterns:
- Packet too vague → tighten the format (more precise allowed-files, exact
  strings)
- Implementer goes off-script → strengthen specialist prompt
- Handoff drift → enforce packet template in parent prompt

Re-measure: n=8 with the tuned configuration. This chapter demonstrates the
"structure beats strings" principle live — the failure drives the fix — and
establishes a pattern for Part IV (where the fixes are mechanism-level
guardrails, not just prompt tuning).

**Boundary with SP3:** This chapter is scoped to **prompt/packet tuning only**.
Mechanism-level fixes (turn cap, output cap, path guard, repeat breaker) are
Part IV territory and are not built here. If a failure needs a mechanism-level
fix to progress, it becomes the motivating evidence for the corresponding SP3
chapter.

## Data flow

```
AgentClinic specs (roadmap.md)
        │
        ▼
Parent pi session (orchestrator prompt)
  │ Extract phase contract
  │ Construct packet
  │ Call subagent({ agent: "implementer", task: "<packet>" })
        │
        ▼
Child pi session (implementer specialist)
  │ --tools read,write,bash
  │ --append-system-prompt <temp file: stripped implementer.md body>
  │ Task: <packet>
  │ → Writes code
  │ → Runs uv run pytest
  │ → Returns result
        │
        ▼
Parent receives result
  │ exit code, changed files, test pass, output
  │ (visible in parent's JSONL as tool_execution_end)
        │
        ▼
SP1 harness (extended — see "Harness delta" below)
  │ run_baseline against parent session
  │ produces SessionResult from parent JSONL
        │
        ▼
research/YYYY-MM-DD-sp2-baseline-phase-N.md
```

## Harness delta (required work, not assumed reuse)

The SP1 harness **cannot run SP2 as-is**. `harness/session.py:85-86` hardcodes
`--no-extensions --extension .pi/extensions/hello-world.ts` and passes no system
prompt — invoked unchanged, the parent has no subagent tool and no orchestrator
prompt, and every "SP2 run" would silently be an SP1 rerun. The harness gains a
parameterized invocation profile; the SP2 profile is:

- `--no-extensions` retained, plus `--extension <path-to-installed-subagent>`
  (the explicit path found by the Chapter 1 locate recipe) — the subagent tool
  and nothing else.
- `--append-system-prompt prompts/orchestrator.md`.
- The same `--model omlx/gemma-4-12B-it-MLX-8bit`, `-p`, `--mode json`,
  `--no-session`, `stdin=DEVNULL` discipline as SP1.
- Timeout raised from 300s: each parent run now nests a full child pi run.
  Starting value 900s, tuned from observed Chapter 2 wall times.

A run that produced zero `subagent` tool calls in the parent JSONL is recorded
as outcome `no-delegation`, not merely as a failure — it is
indistinguishable from an SP1 baseline run and must not be averaged into the
delegation data as if the mechanism had been exercised.

## Testing strategy

| Layer | Scope | Fixture | Gate |
|-------|-------|---------|------|
| Subagent mechanism | Does the shipped extension load and register the tool? | `pi --extension ... --no-session -p "test"` | Manual (no unit test harness for extensions) |
| `implementer.md` syntax | Valid frontmatter (`name`, `description`, `tools`, `model` present and well-formed) | `agents.ts` discovery | Unit: pytest parses the YAML frontmatter block directly (the course's test stack is Python; `parseFrontmatter` is the extension's own TS API and is not invoked from tests) |
| `orchestrator.md` content | Contains packet format spec, phase extraction instructions | N/A | Manual review |
| End-to-end | n=8 parent session with subagent tool calls | Real `pi` + model | Gated by `PI_AVAILABLE` |

The TypeScript extension itself is **not tested by the course** — it's shipped
and trusted. The course's tests cover the files the course authors.

## Measurement strategy

### Per-phase measurement (matches SP1)

Each baseline run: start a parent pi session with the orchestrator prompt +
subagent extension, prompt "Build Phase N using the implementer specialist,"
capture the parent's JSONL. **Success is decided exactly as in SP1: the
harness runs the acceptance pytest itself and diffs the workspace.** The
implementer's self-reported result is recorded as a separate field but never
trusted for the success bit — an agent's report is not evidence (LESSONS #2),
and disagreement between the self-report and the harness verdict is itself a
metric worth keeping. n=8 per phase. Compare to SP1's 0/8.

### Additional metrics

Beyond SP1's metrics, collect:
- **Subagent invocations per run** — does the parent delegate once or fragment?
- **Packet size** — from the parent's tool_call args (the `task` field)
- **Packet fidelity (paraphrase drift)** — does the packet carry the phase's
  acceptance strings and allowed-files list *verbatim* from the roadmap, or did
  the parent paraphrase them? Checked mechanically per delegation (exact
  substring match per required literal). This is the measured form of the
  handoff-drift commitment from the master spec — size alone does not capture
  it.
- **Implementer turns per delegation** — from the child's result (surfaced by the shipped extension in the parent's tool result details)
- **Self-report vs harness verdict agreement** — see above.

### Phase escalation

Same as SP1: if Phase 1 passes consistently, escalate to Phase 2, then Phase 3.
The smoking gun is the first phase that fails — same rule.

## Out of scope

- Building a TypeScript extension from scratch (use the shipped one)
- Planner specialist with oracle derivation (evidence-gated, roadmap backlog)
- Guardrail extensions (SP3 / Part IV)
- Multi-phase chaining inside the implementer (single-phase per delegation)
- Turn cap, output cap, path guard, repeat breaker (Part IV)
- `--system-prompt` replacement (use `--append-system-prompt` — the implementer needs the base coding prompt)

## Source material

- Pi shipped subagent example:
  `@earendil-works/pi-coding-agent/examples/extensions/subagent/index.ts` (34.3K, 900+ lines)
- `agents.ts` — specialist discovery with frontmatter parsing
- `agents/worker.md` — sample specialist (base template)
- AgentClinic roadmap: `examples/agentclinic/specs/roadmap.md` (Phase 1-3)
- SP1 harness: `harness/session.py`, `harness/runner.py` (reused for measurement)
- SP1 baseline: `docs/superpowers/research/2026-07-23-baseline-phase-1.md` (0/8)
- LESSONS.md #1 ("structure beats strings"), #4 ("separate orchestration, implementation, and verification")
