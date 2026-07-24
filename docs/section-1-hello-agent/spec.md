# SP0 — "Hello, Agent" (Part I: Pi Extension Basics)

Date: 2026-07-23
Status: approved

This is the detailed spec for sub-project 0: the hello-world extension and its
tour-style chapter. It implements Part I of the master course design
([`2026-07-23-course-design.md`](../superpowers/specs/2026-07-23-course-design.md)).

## Purpose

Give the reader a working Pi extension and a tour of the 7 lifecycle events the
rest of the course uses. The chapter is discovery-style ("Hello, agent"): each
event is encountered as a surprise, with a brief "why this matters" preface
before the code and output. No theory, no infrastructure — just watching the
engine run.

## Deliverables

1. `.pi/extensions/hello-world.ts` — a single-file TypeScript extension
2. `docs/chapters/part1-hello-agent.md` — a MyST chapter

## Extension: `.pi/extensions/hello-world.ts`

### Design

A single TypeScript file, no subdirectory, no `package.json`. The only import is
`ExtensionAPI` from `@earendil-works/pi-coding-agent` (shipped with Pi; no
install needed). Each handler does one thing — notify — plus a comment noting the
event's purpose. The `session_start` handler additionally calls
`pi.appendEntry()` to demonstrate evidence writing, which Part II's telemetry
reader consumes.

### Events hooked

| Event | Behavior |
|---|---|
| `session_start` | `ctx.ui.notify("Session started!", "info")` + `pi.appendEntry(...)` |
| `agent_start` | `ctx.ui.notify("Agent started — LLM turn beginning")` |
| `tool_call` | `ctx.ui.notify(`Tool called: ${event.toolName}`)` |
| `tool_execution_start` | `ctx.ui.notify(`Executing: ${event.toolName}`)` |
| `tool_execution_end` | `ctx.ui.notify(`Done: ${event.toolName}`)` — include `event.isError` if true |
| `turn_end` | `ctx.ui.notify(`Turn ${event.turnIndex + 1} complete`)` |
| `agent_end` | `ctx.ui.notify("Agent finished")` |

### `appendEntry` call

```typescript
pi.appendEntry({
  type: "evidence",
  data: { event: "session_start", timestamp: Date.now() },
});
```

This is the only handler with a second line. It is the teaching beat: evidence
gets written into the session JSONL, and Part II's telemetry reader will surface
it.

### Non-functional

- **Error handling:** None needed. No network, no filesystem, no promises. If a
  handler throws, Pi catches and logs; the extension stays loaded.
- **Testing:** Not included. This is a 30-line tour artifact. The test is: load
  it, type a prompt, watch the notifications. Formal testing arrives in Part II.

### Loading

The reader loads it with `pi -e .pi/extensions/hello-world.ts`. The chapter does
not teach auto-discovery (`.pi/extensions/` project-local loading) — that's a
later note when the guardrails are built in Part IV and are auto-loaded.

## Chapter: `docs/chapters/part1-hello-agent.md`

### Tone and structure

Discovery-style, "Hello, agent" framing. Each event section opens with a "Why
this matters" paragraph (1-3 sentences) before showing the code and describing
the output. The reader encounters each event as a surprise — here's what fires,
here's why it exists, here's what you see.

TypeScript is shown inline with annotations explaining the Pi API surface. The
chapter does not teach TypeScript; it assumes the reader can follow the code.

### Section plan

1. **Why extensions?**
   - Pi is an agent harness. Everything it does — every tool call, every turn,
     every session boundary — emits an event. An extension is just a listener.
   - This chapter plugs into 7 of those events. By the end you'll have seen the
     full lifecycle of a single agent turn. No theory, just watching the engine run.

2. **Setup**
   - Create the file skeleton (import, default export, the factory shape).
   - Load with `pi -e .pi/extensions/hello-world.ts`.
   - The only section without a deep "why" — it's a speed bump.

3. **`session_start` — where you begin**
   - *Why:* every session has a birth moment. If you want to set up state, load
     config, or write evidence before anything else happens, this is the hook.
   - *Code:* notify + `appendEntry`. Explain that `appendEntry` writes into the
     session JSONL — this is how evidence gets recorded. Part II will read it.
   - *Output:* notification in the TUI.

4. **`agent_start` — the LLM wakes up**
   - *Why:* when you hit enter on a prompt, the agent loop begins. This is the
     signal that real work is about to happen.
   - *Code:* notify.
   - *Output:* notification fires immediately after the user prompt.

5. **Tools in flight: `tool_call`, `tool_execution_start`, `tool_execution_end`**
   - *Why:* tools are how the agent touches your filesystem. These three events
     bracket every tool execution. The distinction matters: `tool_call` lets you
     block or inspect before execution; `tool_execution_end` gives you the result
     and error status.
   - *Code:* three handlers, one for each event. Show the `toolName` and
     `isError` fields.
   - *Output:* three notifications in rapid sequence per tool call.

6. **`turn_end` — the LLM pauses**
   - *Why:* one prompt can trigger many tool calls in a loop. `turn_end` is the
     seam between loops — where you can count turns, cap them, or inject a
     correction (all Part IV topics).
   - *Code:* notify with `turnIndex + 1`.
   - *Output:* notification with turn number.

7. **`agent_end` — the LLM rests**
   - *Why:* the agent finished its run. The counterpart to `agent_start` — if you
     set something up there, this is where you tear it down.
   - *Code:* notify.
   - *Output:* notification.

8. **The full picture**
   - The Pi lifecycle diagram (from the extensions docs), with each hooked event
     highlighted or annotated.
   - A single run traced start to finish: "You typed a prompt → session_start
     fired → agent_start fired → tool_call/exec_start/exec_end cycled twice →
     turn_end fired → agent_end fired."

9. **What's next**
   - Teaser: "We've seen the events fire. Now we need to measure them. In Part
     II we'll build a telemetry reader that captures turns, tokens, timing, and
     our custom evidence — and we'll run a baseline that shows what happens when
     an untuned SLM drives real development."
   - Link to Part II chapter (placeholder).

## Non-functional

- **Chapter format:** MyST (`docs/chapters/part1-hello-agent.md`), rendered by
  Sphinx + Furo.
- **Images:** Notification screenshots or terminal output examples where helpful,
  but the chapter should work without them (text descriptions suffice).
- **Word count:** Target 800-1200 words. Tour-style, not exhaustive.

## Success criteria

1. A reader creates the file, loads it with `-e`, types a prompt, and sees all 7
   events fire as notifications.
2. After `session_start`, a custom entry is written to the session JSONL
   (verify with `jq` or by reading the file).
3. The chapter leads every section with "why" before showing code or output.
4. The chapter ends with a clear forward reference to Part II.
5. Nothing requires a forked or patched Pi — the globally-installed `pi` binary
   is the runtime.

## Out of scope

- Teaching TypeScript.
- Auto-discovery of project-local extensions (`.pi/extensions/` without `-e`).
- Any guardrail, measurement, or subagent logic — those are SP1-SP3.
- Formal tests for the extension.
