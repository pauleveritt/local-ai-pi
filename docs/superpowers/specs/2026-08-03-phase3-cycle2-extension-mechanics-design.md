# Phase 3, Cycle 2 — Extension mechanics, and the gotchas we paid for

**Phase:** 3 — Build the extension half
**Status:** design, awaiting plan

## Why this cycle

`BRIEF.md` names contributors as the priority audience, and the product as "a
Pi *extension* (not a fork of Pi) plus an eval harness." Cycle 1 proved this
project's extension can emit evidence. A contributor who wants to write the
next one still has nothing to learn from except source.

Meanwhile this project has been paying, repeatedly, to discover how Pi
actually behaves — and every one of those findings was expensive, non-obvious,
and invisible from the documentation. They are currently scattered across a
research note, a chapter, a withdrawn spec, and one commit message. This cycle
gathers them and teaches the mechanics they belong to.

**This cycle replaces a withdrawn one.** The original cycle 2 was *specialized
subagent* — a real specialist, a real orchestrator prompt, a real delegation.
It was withdrawn on the owner's challenge that Phase 3 was not going to get
into orchestration, which the Backlog had already recorded. Its findings about
Pi's behaviour survive and are a large part of what this cycle teaches; its
machinery does not. See the banner on
`docs/superpowers/specs/2026-08-03-phase3-cycle2-specialized-subagent-design.md`.

## What this cycle is not

- **Not an orchestrator, and not a delegation in the harness.** Pi's shipped
  subagent extension is *read as a worked example*. It is not enabled, not
  loaded, not specialized, and not measured.
- **Not a harness change.** No new `RunConditions` field, no telemetry field,
  no refusal check, no `agentdir/`, no change to `_pi_command`. The one
  exception is stated below and is a comment, not behaviour.
- **Not a Pi tutorial.** It teaches what this project needed and what bit it,
  not the whole API surface.

## Design

### 1. The chapter

`docs/superpowers/chapters/pi-extension-mechanics.md`, aimed at the 5–10 h/wk
contributor `BRIEF.md` describes:

- **What an extension is** — a default-exported function receiving an
  `ExtensionAPI`; how Pi finds one; user scope versus project scope versus an
  explicit `--extension` path.
- **The event lifecycle**, taught from `.pi/extensions/hello-world.ts`, which
  the contributor already has and which cycle 1's chapter already covers at
  the level of one entry travelling. This chapter covers the shape of the
  handler set rather than repeating that story.
- **Registering a tool**, taught from a small extension of our own (below).
  This is the mechanism the shipped subagent example is built on, and it
  cannot be learned by reading alone.
- **Pi's shipped subagent extension, read as a worked example.** How
  `registerTool` is used at scale, how agent files are discovered and parsed,
  and how it spawns a child `pi`. Read, cited, and explained — not adopted.
  It is the best available demonstration of a real extension, and being able
  to read it is a contributor skill worth teaching directly.

### 2. One teaching extension of our own

`examples/extensions/` — a small extension that registers exactly one trivial
tool, loaded by hand, never by the harness.

Its job is to make `registerTool` concrete: the schema, the handler, what the
model sees, and what the tool call looks like in `--mode json` output. A
chapter that explains `registerTool` without a contributor ever running one
produces confident wrong beliefs, which is the failure mode this project keeps
paying for.

It is also the cheapest way to find the next gotcha. This session found four
in an afternoon of poking; the supply is not exhausted.

**Scope discipline:** one tool, no state, no session writes, no child
processes. If it grows a second responsibility it has stopped being a teaching
artifact.

### 3. The gotchas record

`docs/superpowers/research/2026-08-03-phase3-cycle2-pi-gotchas.md` — each with
a file:line citation into installed 0.82.0, and each labelled by how it was
established: **read**, or **run**.

The ones already paid for:

| Gotcha | Why it bites |
|---|---|
| The json-mode stdout subscriber attaches *after* `session_start` is emitted and awaited | Anything an extension emits from a `session_start` handler is dropped, irrecoverably. Cost: 80 runs producing nothing observable. |
| `--approve` is not an isolation flag | Pi defines it as "Trust project-local files for this run" — it *widens* trust. What actually excludes a model-written `.pi/extensions/*.ts` is `--no-extensions`. |
| `--no-extensions` spares explicit `--extension` paths | Looks contradictory, is not, and is what lets a harness be isolated and instrumented at once. |
| A spawned subagent child inherits **none** of the parent's isolation flags | Its args are `["--mode","json","-p","--no-session"]` plus the agent's model and tools. On a machine with ambient extensions, a delegated child loads them. |
| `PI_CODING_AGENT_DIR` relocates the agent directory, and children inherit it | The one lever that isolates a child you do not control the spawn of. |
| Pointing that variable at an *empty* directory makes Pi bootstrap | It `git clone`s a third-party repository and runs npm installs — slow, network-dependent, and pinned to nobody's revision. Pre-provision or don't relocate. |
| Project-scope agents are discovered by walking **up from cwd** | A repo-committed `.pi/agents/` is invisible to a process running in a temp directory. |
| An agent file without `model:` in its frontmatter spawns a child on Pi's *default* model | `--model` reaches the child only `if (agent.model)`. A measurement of a local model can silently acquire a cloud one. |
| `ctx.ui.notify` has no destination under `--no-themes` | Print mode supplies a no-op UI context. It is not an evidence channel. |

Each entry states what it cost us, because a gotcha with a price attached is
remembered and one without is skimmed.

### 4. The one harness touch

`harness/runner.py` already carries a comment, added while investigating this,
explaining that `--approve` widens trust. That comment stays and the chapter
links to it. Nothing else in `harness/` changes.

## Testing

There is almost nothing to test, and pretending otherwise would be worse than
saying so. What can be tested is tested:

- The teaching extension **type-checks against the installed Pi types**, so a
  0.82.0 → 0.83 drift breaks the build rather than the reader's trust. This
  is the cycle's only new machinery, and it exists because the chapter's
  central promise is that its code is true of the installed version.
- Every fenced code block in the chapter that claims to be from a real file
  matches that file. Where a claim cites installed Pi by file:line, the
  citation resolves.

The existing suite must stay green, and strict Sphinx must build.

## Deliberate exclusions

- **No `registerCommand`, `registerShortcut`, or `registerFlag` coverage.**
  Real parts of the API, but this project has not used them, and teaching an
  API surface nobody here has exercised is how a chapter acquires claims
  nobody has checked.
- **No coverage of what the subagent extension's `details` carries.** The
  withdrawn plan's Task 1 was a live spike to answer that. It is a real
  question, it is unanswered, and it belongs to the deferred
  orchestration-cost experiment rather than to a teaching cycle.
- **No second teaching extension.** One tool, one mechanism.

## Gates

`uv run pytest && uv run ruff check . && uv run pyrefly check`, plus a clean
strict Sphinx build. Runs are sequential, never concurrent.
