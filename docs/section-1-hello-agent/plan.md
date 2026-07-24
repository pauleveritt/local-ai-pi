# SP0 — "Hello, Agent" Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Part I hello-world extension and discovery-style chapter that walks through 7 Pi lifecycle events.

**Architecture:** A single-file TypeScript extension (`.pi/extensions/hello-world.ts`) hooks 7 lifecycle events with `ctx.ui.notify` calls, plus one `pi.appendEntry` in `session_start` to demonstrate evidence writing. A MyST chapter (`docs/chapters/part1-hello-agent.md`) tours each event with a "why-first" structure.

**Tech Stack:** TypeScript (loaded via Pi's jiti), MyST Markdown, Sphinx + Furo

**Spec:** [`spec.md`](spec.md)

## Global Constraints

- Runtime is the globally-installed `pi` binary (0.81.1), not a checkout
- No forked or patched Pi — every mechanism is built-in
- TypeScript shown inline in chapters; reader expected to follow, not taught TS
- Chapters are MyST, built with Sphinx + Furo
- No formal tests for the extension; test is load it, type a prompt, watch

---

### Task 1: Create the hello-world extension

**Files:**
- Create: `.pi/extensions/hello-world.ts`

**Interfaces:**
- Produces: A Pi extension that hooks 7 lifecycle events and writes one `appendEntry` evidence record

- [ ] **Step 1: Create the extension directory**

```bash
mkdir -p .pi/extensions
```

- [ ] **Step 2: Write `.pi/extensions/hello-world.ts`**

```typescript
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // ── session_start: the session comes to life ──────────────────────
  pi.on("session_start", async (_event, ctx) => {
    ctx.ui.notify("Session started!", "info");

    // Write an evidence entry into the session JSONL.
    // Part II's telemetry reader will surface this.
    pi.appendEntry({
      type: "evidence",
      data: { event: "session_start", timestamp: Date.now() },
    });
  });

  // ── agent_start: the LLM wakes up ─────────────────────────────────
  pi.on("agent_start", async (_event, ctx) => {
    ctx.ui.notify("Agent started — LLM turn beginning", "info");
  });

  // ── tool_call: a tool is about to execute (can block here) ────────
  pi.on("tool_call", async (event, ctx) => {
    ctx.ui.notify(`Tool called: ${event.toolName}`, "info");
  });

  // ── tool_execution_start: execution begins ────────────────────────
  pi.on("tool_execution_start", async (event, ctx) => {
    ctx.ui.notify(`Executing: ${event.toolName}`, "info");
  });

  // ── tool_execution_end: execution finished ────────────────────────
  pi.on("tool_execution_end", async (event, ctx) => {
    const status = event.isError ? " (FAILED)" : "";
    ctx.ui.notify(`Done: ${event.toolName}${status}`, "info");
  });

  // ── turn_end: the LLM pauses between tool loops ───────────────────
  pi.on("turn_end", async (event, ctx) => {
    ctx.ui.notify(`Turn ${event.turnIndex + 1} complete`, "info");
  });

  // ── agent_end: the LLM rests ──────────────────────────────────────
  pi.on("agent_end", async (_event, ctx) => {
    ctx.ui.notify("Agent finished", "info");
  });
}
```

- [ ] **Step 3: Verify the extension loads without errors**

```bash
pi -e .pi/extensions/hello-world.ts -p "hello" < /dev/null
```

Expected: Pi starts, processes the prompt, no extension errors. Notifications won't be visible in `-p` mode, but errors would surface. The session JSONL will contain the `appendEntry` evidence.

- [ ] **Step 4: Verify the appendEntry evidence is written**

```bash
ls -t ~/.pi/agent/sessions/*.jsonl | head -1 | xargs grep "session_start"
```

Expected: A line containing `"type":"evidence"` and `"data":{"event":"session_start"`.

- [ ] **Step 5: Commit**

```bash
git add .pi/extensions/hello-world.ts
git commit -m "feat: add hello-world extension (7 lifecycle events + appendEntry)"
```

---

### Task 2: Write the chapter

**Files:**
- Create: `docs/chapters/part1-hello-agent.md`

**Interfaces:**
- Consumes: `.pi/extensions/hello-world.ts` (referenced in prose, not imported)
- Produces: A MyST chapter that Sphinx renders as part of the course

- [ ] **Step 1: Write `docs/chapters/part1-hello-agent.md`**

````markdown
(part1-hello-agent)=

# Part I — Hello, Agent

## Why extensions?

Pi is an agent harness. Everything it does — every tool call, every turn, every
session boundary — **emits an event**. An extension is just a listener.

In this chapter we'll write a tiny TypeScript file that plugs into seven of
those events. By the end you'll have seen the full lifecycle of a single agent
turn — no theory, no infrastructure, just watching the engine run while you type
a prompt.

TypeScript is the language Pi extensions are written in. You don't need to know
it deeply; the snippets are short and annotated. If you can read Python, you can
follow along.

## Setup

Create `.pi/extensions/hello-world.ts` with the skeleton:

```typescript
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  // Event handlers go here
}
```

The import comes from Pi itself — no `npm install` needed. The default export is
a factory function Pi calls at startup, passing in `pi` — your handle for
subscribing to events, registering tools, and writing evidence.

Load it with the `-e` flag:

```bash
pi -e .pi/extensions/hello-world.ts
```

Nothing happens yet. The factory runs but we haven't hooked any events. Let's
fix that.

## `session_start` — where you begin

**Why this matters.** Every session has a birth moment. When Pi starts, when you
run `/new`, when you resume a conversation — `session_start` fires. If you ever
need to set up state, load configuration, or write a checkpoint *before anything
else happens*, this is the hook.

Add this inside the factory function:

```typescript
pi.on("session_start", async (_event, ctx) => {
  ctx.ui.notify("Session started!", "info");
});
```

Restart Pi. The moment the session loads, you'll see a notification flash:
**"Session started!"** That's your first event.

### Writing evidence

Notifications are ephemeral. If you want to record something permanent — a
measurement, a marker, a breadcrumb — use `pi.appendEntry()`. It writes directly
into the session's JSONL file, where later tooling can read it.

Add a second line to the handler:

```typescript
pi.on("session_start", async (_event, ctx) => {
  ctx.ui.notify("Session started!", "info");
  pi.appendEntry({
    type: "evidence",
    data: { event: "session_start", timestamp: Date.now() },
  });
});
```

After your next session, peek at the session file:

```bash
grep "session_start" ~/.pi/agent/sessions/<session-id>.jsonl
```

You'll see a line with `"type":"evidence"` wrapping your data. In Part II we'll
build a reader that surfaces these entries as structured evidence. For now,
you've written your first breadcrumb.

## `agent_start` — the LLM wakes up

**Why this matters.** The moment you send a prompt, Pi enters the agent loop.
`agent_start` is the signal that the LLM is about to start reasoning. If you
were building a stopwatch, this is where you'd start it.

```typescript
pi.on("agent_start", async (_event, ctx) => {
  ctx.ui.notify("Agent started — LLM turn beginning", "info");
});
```

Send any prompt — "hello" will do — and watch the notification fire.

## Tools in flight

The LLM acts on your filesystem through **tools** — `bash`, `read`, `write`,
`edit`, and any custom tools registered by extensions. Every tool execution is
bracketed by three events. The distinction between them matters:

- `tool_call` fires *before* execution — this is where you inspect or block.
- `tool_execution_start` fires when execution *begins*.
- `tool_execution_end` fires when execution *finishes*, carrying the result and
  an `isError` flag.

### `tool_call`

**Why this matters.** If you want to block a dangerous command or inspect
arguments before they run, this is the only point where you can. In Part IV
we'll use this hook to guard protected paths and enforce output limits.

```typescript
pi.on("tool_call", async (event, ctx) => {
  ctx.ui.notify(`Tool called: ${event.toolName}`, "info");
});
```

### `tool_execution_start`

**Why this matters.** The tool is now running. If you're tracking timing, this
is your start marker.

```typescript
pi.on("tool_execution_start", async (event, ctx) => {
  ctx.ui.notify(`Executing: ${event.toolName}`, "info");
});
```

### `tool_execution_end`

**Why this matters.** The tool finished. The `event.isError` flag tells you
whether it succeeded. If you're collecting evidence, this is where you record
the outcome.

```typescript
pi.on("tool_execution_end", async (event, ctx) => {
  const status = event.isError ? " (FAILED)" : "";
  ctx.ui.notify(`Done: ${event.toolName}${status}`, "info");
});
```

Try a prompt that makes the agent use a tool — "read the README" or "list files
in the project". You'll see all three notifications fire in rapid sequence for
each tool call.

## `turn_end` — the LLM pauses

**Why this matters.** One prompt can trigger *many* tool calls in a loop. The
agent thinks, calls tools, sees results, thinks again — and each cycle is a
**turn**. `turn_end` is the seam between cycles. In Part IV we'll use it to cap
runaway turns and inject corrections.

```typescript
pi.on("turn_end", async (event, ctx) => {
  ctx.ui.notify(`Turn ${event.turnIndex + 1} complete`, "info");
});
```

The `turnIndex` is zero-based, so we add 1 for readability. Send a prompt that
needs a couple of tool calls and watch the turn counter tick.

## `agent_end` — the LLM rests

**Why this matters.** The agent finished its run. This is the counterpart to
`agent_start` — if you set something up there (a timer, a state flag), this is
where you tear it down. In headless mode (Part II), this event tells the harness
the run is over.

```typescript
pi.on("agent_end", async (_event, ctx) => {
  ctx.ui.notify("Agent finished", "info");
});
```

## The full picture

Here's the Pi lifecycle, with the seven events we hooked highlighted. A single
prompt traces this path:

```
pi starts
  └─► session_start ◀── evidence written here
      ...
user sends prompt
  ├─► agent_start
  │
  │   ┌─── turn ──────────────────────────┐
  │   │  tool_call ◀── inspect arguments   │
  │   │  tool_execution_start ◀── stopwatch │
  │   │  tool_execution_end  ◀── result     │
  │   └─── turn_end     ◀── seam           │
  │
  └─► agent_end ◀── run complete
```

In one session: you typed a prompt → `session_start` had already fired →
`agent_start` fired → `tool_call` / `exec_start` / `exec_end` cycled for each
tool → `turn_end` fired → `agent_end` fired.

You've now seen the entire heartbeat of an agent run.

## What's next

We've seen the events fire. Now we need to *measure* them.

In **Part II — Measurement** we'll build a telemetry reader that captures turns,
tokens, timing, and our custom evidence entries. Then we'll run a baseline — an
out-of-the-box small local model attempting actual Python development with no
steering at all — and record exactly what happens.

That baseline is the smoking gun the rest of the course answers. And our little
extension? Its `appendEntry` pattern is the first brick of the evidence ledger
that proves every improvement really helped.
````

- [ ] **Step 2: Build the docs to verify the chapter renders**

```bash
cd docs && rtk uv run sphinx-build -b html . _build -W 2>&1
```

Expected: Build succeeds with no warnings. The chapter appears in the HTML output at `_build/chapters/part1-hello-agent.html`.

- [ ] **Step 3: Commit**

```bash
git add docs/chapters/part1-hello-agent.md
git commit -m "docs: add Part I hello-agent discovery chapter"
```

---

### Task 3: Wire the chapter into the toctree

**Files:**
- Modify: `docs/chapters/index.md`

**Interfaces:**
- Consumes: `docs/chapters/part1-hello-agent.md` (filename for toctree entry)

- [ ] **Step 1: Update `docs/chapters/index.md`**

Replace the file contents with the updated index that includes the new chapter in the toctree and marks Part I as done:

```markdown
# Chapters

The course is built one Part at a time. Chapters appear here as each sub-project
lands. See the [roadmap](../superpowers/roadmap.md) for status.

- **Part I — Pi extension basics.** A hello-world extension and the event
  lifecycle. :white_check_mark:
- **Part II — Measurement (the smoking gun).** Telemetry, a minimal eval
  harness, and the out-of-the-box baseline. *(queued)*
- **Part III — Spec-driven development on Pi.** Roadmap-and-packet, an
  orchestrator subagent, and an evidence-gated fleet. *(queued)*
- **Part IV — Keeping the SLM on track.** The improvements catalog. *(queued)*

```{toctree}
:maxdepth: 1
:hidden:

part1-hello-agent
```
```

- [ ] **Step 2: Rebuild docs to verify toctree**

```bash
cd docs && rtk uv run sphinx-build -b html . _build -W 2>&1
```

Expected: Build succeeds with no warnings. The toctree now includes the Part I chapter.

- [ ] **Step 3: Commit**

```bash
git add docs/chapters/index.md
git commit -m "docs: wire Part I chapter into toctree, mark complete"
```

---

### Task 4: Update the roadmap

**Files:**
- Modify: `docs/superpowers/roadmap.md`

**Interfaces:**
- Consumes: `docs/superpowespec.md` (spec link)

- [ ] **Step 1: Update SP0 row and next-phase pointer in `docs/superpowers/roadmap.md`**

Two edits needed:

**Edit 1:** Change SP0 status from "In progress" to "Done" and add the spec link:

Replace:
```
| SP0 | Scaffold + Part I (repo skeleton, docs toolchain, roadmap, LESSONS, example spec triple, hello-world extension) | **In progress** (handed off from brainstorming) | [course-design](specs/2026-07-23-course-design.md) | — | — |
```

With:
```
| SP0 | Scaffold + Part I (repo skeleton, docs toolchain, roadmap, LESSONS, example spec triple, hello-world extension) | **Done** | [course-design](specs/2026-07-23-course-design.md), [sp0-hello-agent](spec.md) | — | — |
```

**Edit 2:** Update "Next phase" from SP1 to a note that SP0 is done:

Replace:
```
**Next phase:** Sub-project 1 — Part II (Measurement). Brainstorm → spec → plan →
build. It is next because Parts III and IV cannot be evaluated without the harness
and baseline it produces.
```

With:
```
**Current phase:** Sub-project 1 — Part II (Measurement). This is next because
Parts III and IV cannot be evaluated without the harness and baseline it
produces. SP0 is complete.
```

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/roadmap.md
git commit -m "roadmap: mark SP0 done, update next-phase pointer"
```

---

### Task 5: Final verification and commit

- [ ] **Step 1: Run the full docs build one final time**

```bash
cd docs && rtk uv run sphinx-build -b html . _build -W 2>&1
```

Expected: Clean build, zero warnings.

- [ ] **Step 2: Verify the complete extension loads and all events fire**

Start Pi with the extension loaded, send a prompt like "read the README", and confirm all 7 notifications appear in sequence.

- [ ] **Step 3: Verify git status is clean**

```bash
git status
```

Expected: All changes committed, working tree clean.
