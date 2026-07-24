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
grep "session_start" ~/.pi/agent/sessions/<project-dir>/<session-id>.jsonl
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
