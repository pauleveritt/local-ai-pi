# Hello, agent

This project ships **a Pi extension, not a fork of Pi**. That sentence is in
`BRIEF.md`, and this chapter is where it stops being a slogan. By the end you
will have read the whole extension we actually run — 57 lines of TypeScript at
`.pi/extensions/hello-world.ts` — and you will know which of the things it does
are visible to the harness and which are not.

The second half is the part worth your time. The extension was in the tree for
80 recorded runs producing nothing observable, and the reason turned out to be
one line's *placement*, not any missing API.

Everything below cites the installed Pi 0.82.0 by file and line. Paths beginning
`core/` or `modes/` are relative to the installed package's `dist/` directory;
paths beginning `node_modules/` are relative to the package root, where the
nested `pi-agent-core` package sits beside `dist/`:

```text
~/.volta/tools/image/packages/@earendil-works/pi-coding-agent/
  lib/node_modules/@earendil-works/pi-coding-agent/dist/
```

## An extension is a function

A Pi extension is one file with one default export: a function that takes an
`ExtensionAPI` object and registers handlers on it.

```typescript
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.on("agent_start", async (_event, ctx) => {
    // ...
  });
}
```

That is the whole contract. The type is
`ExtensionFactory = (pi: ExtensionAPI) => void | Promise<void>`
(`core/extensions/types.d.ts:1076`). Pi calls it once at startup and keeps
whatever you registered.

The import is `import type`, so it is erased before anything runs — no
`npm install`, no build step, no `package.json`. The TypeScript is there for
your editor's benefit.

You do not need to know TypeScript well to work on this. If you can read
Python, the handlers below read the same way.

### How this project loads it

The harness passes the path explicitly:

```python
EXTENSIONS: tuple[Path, ...] = (REPO_ROOT / ".pi" / "extensions" / "hello-world.ts",)
```

— `harness/runner.py:15`, and `_pi_command` emits one `--extension` flag per
entry (`harness/runner.py:120-121`).

The full invocation is:

```text
pi --print --mode json --no-session --model <model> --no-extensions
   --extension .pi/extensions/hello-world.ts
   --no-skills --no-prompt-templates --no-themes --no-context-files
   --approve <prompt>
```

`--no-extensions` and `--extension` together look contradictory and are not.
`--no-extensions` suppresses only *discovered* extensions; paths passed
explicitly survive it. Pi's own help text says so — "Disable extension
discovery (explicit -e paths still work)" — and the code agrees at
`core/resource-loader.js:267-269`. That is what lets the harness run isolated
from whatever else is installed on your machine while still loading its own
instrument.

To try one by hand outside the harness, `-e` is the short form:

```bash
pi -e .pi/extensions/hello-world.ts
```

## The seven handlers, and the lifecycle they tour

`hello-world.ts` registers seven handlers. Six of them do nothing but call
`ctx.ui.notify`. The seventh also appends an entry. Here is the tour:

| Handler | When it fires |
|---|---|
| `session_start` | the session is created, resumed, or reloaded |
| `agent_start` | the agent loop begins, once you send a prompt |
| `tool_call` | a tool is about to run — the one place you can block it |
| `tool_execution_start` | the tool begins executing |
| `tool_execution_end` | the tool finished; `event.isError` says how |
| `turn_end` | one think-act-observe cycle closed |
| `agent_end` | the agent loop finished |

One prompt drives many turns. In the captured run at
`tests/fixtures/pi-run-0.82.0-entry-appended.jsonl`, a single prompt produced
seven `turn_start` / `turn_end` pairs, six tool executions, and one `agent_end`.

`agent_start` is the useful anchor: it fires during `session.prompt()`, before
anything the model does can influence it. It is not exactly once per run — Pi
retries after some agent errors, and **a retry does fire it again** — so
anything asserting on the entries it produces should test membership, not
count.

That last part is read, not guessed. The retry loop calls
`await this.agent.continue()` (`core/agent-session.js:748-749`); `continue()`
falls through to `runContinuation()`
(`node_modules/@earendil-works/pi-agent-core/dist/agent.js:229`, `:270-272`),
which calls `runAgentLoopContinue`; and that function's first act is
`await emit({ type: "agent_start" })`
(`node_modules/@earendil-works/pi-agent-core/dist/agent-loop.js:67`).

Note the path: `pi-agent-core` is a *nested* dependency of the installed
package, at the same 0.82.0 version. It is not a sibling in the top-level
`node_modules`, which is why a directory listing can make it look absent.

## `ctx.ui.notify` shows you nothing here

Run the harness and you will see none of those seven notifications. This is not
broken.

Pi's extension runner supplies a no-op UI context whose `notify` is an empty
function (`core/extensions/runner.js:88-92`). Under `--no-themes` there is no
terminal UI for a notification to reach, and there is no fallback to stdout.
The handler runs; the message goes nowhere.

The right way to hold this: `notify` is a property of *how Pi was invoked*, not
a capability the extension does or does not have. Load the same file in an
interactive `pi` session and the notifications appear: interactive mode builds
its extension UI context with a real implementation,
`notify: (message, type) => this.showExtensionNotify(message, type)`
(`modes/interactive/interactive-mode.js:1670`). The harness deliberately runs
without a UI, so it deliberately gets no notifications.

The seven handlers stay anyway. They are the lifecycle tour, and their silence in
this mode is a recorded finding rather than a defect to fix.

## Where you emit decides whether anything hears it

This is the finding this cycle exists to teach.

In `--mode json`, print mode attaches exactly one subscriber and serializes
whatever that subscriber receives:

```js
unsubscribe = session.subscribe((event) => {
    if (mode === "json") {
        writeRawStdout(`${JSON.stringify(event)}\n`);
    }
});
```

— `modes/print-mode.js:80-84`. There is no allowlist of permitted event types.
Everything the session emits after that line runs reaches stdout.

The trap is *when* that line runs. Print mode first awaits
`session.bindExtensions(…)` at `modes/print-mode.js:50`, and only wires the
subscriber at `modes/print-mode.js:80`, once the await returns. And
`bindExtensions` emits `session_start` before it returns:

```js
await this._extensionRunner.emit(this._sessionStartEvent);
```

— `core/agent-session.js:1766`.

So anything an extension emits from inside a `session_start` handler is emitted
with no subscriber attached. The loss is permanent, not delayed: `_emit`
walks the listener list synchronously at the moment of emission, with no buffer
and no replay (`core/agent-session.js:285-289`).

That is the whole explanation for 80 runs that produced nothing. The extension
called `appendEntry` from `session_start`. The call worked. The entry was
appended. The event was emitted. Nobody was listening yet.

```text
bindExtensions()
  └─ session_start emitted   ◀── no subscriber yet; anything here is dropped
     (await returns)
session.subscribe(...)       ◀── stdout writer attached here
  └─ agent_start, turn_start, tool_execution_*, turn_end, agent_end
                             ◀── all of these reach stdout
```

The fix was to move one line from one handler to another. No new API, no change
to how Pi is invoked.

## `appendEntry`, and the one entry that travels

```typescript
pi.appendEntry("evidence", { event: "agent_start" });
```

The signature is
`appendEntry<T = unknown>(customType: string, data?: T): void`
(`core/extensions/types.d.ts:915`) — a string type ID, then optional data.

Despite the name, it does not write to disk on this path. It appends to an
in-memory map (`core/session-manager.js:820-831`) and emits
`{type: "entry_appended", entry}` (`core/agent-session.js:1869-1874`). Writing
to disk is a separate step gated on session persistence, and nothing in that
chain touches it — which is why `--no-session` does not interfere.

The payload carries no timestamp of its own. The entry already has one, and a
second wall-clock value would make every captured stdout differ from the last
for no gain.

Here is what arrives. Line 2 of
`tests/fixtures/pi-run-0.82.0-entry-appended.jsonl`, verbatim:

```json
{"type":"entry_appended","entry":{"type":"custom","customType":"evidence","data":{"event":"agent_start"},"id":"65c59a3a","parentId":"da342777","timestamp":"2026-08-02T19:20:33.911Z"}}
```

Note the shape: the entry's `type` is `"custom"`, and the string you passed
lands in `customType`. `harness/telemetry.py` reads exactly that field into
`custom_entries`.

Note also the placement. Line 1 is the session header; line 2 is our entry;
line 3 is Pi's own `agent_start` event. The handler ran, and its emission was
serialized, *before* the event that triggered it. Ordering in this stream is
emission order, not causal order. Do not read it as a timeline.

The control is `tests/fixtures/pi-run-0.82.0.jsonl`, captured from the same
extension file with the call in the other handler. It contains zero
`entry_appended` events.

## Two things the stream does not tell you

Worth knowing before you write a handler and then go looking for its effect in
a capture.

**The event your handler sees is not the event on stdout.** They are built
separately. `_emitExtensionEvent` constructs a fresh object for the extension
runner and the session emits its own to subscribers
(`core/agent-session.js:427-451`). The visible consequence: a `turn_end`
handler receives `turnIndex`, but the `turn_end` line written to stdout has
only `type`, `message`, and `toolResults` — no `turnIndex` at all. Verified
against the fixture.

**`tool_call` never appears on the stream.** It is delivered to extensions only,
through the agent's `beforeToolCall` hook (`core/agent-session.js:214-224`),
and is never passed to `_emit`. The fixture's 157 lines contain no `tool_call`.
Its sibling `tool_result` works the same way. Both are still real, but they are
not interchangeable. `tool_call` is "fired before a tool executes. Can block."
(`core/extensions/types.d.ts:679`) — inspect it, block it, or patch it, since
`event.input` is mutable in 0.82.0 and a handler can rewrite a tool's arguments
in place (`core/extensions/types.d.ts:679-683`). `tool_result` is "fired after
a tool executes. Can modify result." (`core/extensions/types.d.ts:726`) — by
then the tool has run, and the hook can only substitute `content`, `details`,
`isError`, and `usage` (`core/agent-session.js:250-257`). Blocking is
`tool_call`'s alone. And if you want a record of either, you have to append an
entry for it.

There is one more asymmetry in the other direction: the `agent_end` line on
stdout carries a `willRetry` field, added at emission
(`core/agent-session.js:353`), that the published `AgentEndEvent` type does not
declare.

## What this buys the next cycle

`entry_appended` is a channel that is observable in the harness's real
invocation mode and cannot reach the model — custom entries do not participate
in LLM context (`core/extensions/types.d.ts:900`). That combination is what
makes it usable for measurement: an observation channel that could alter the
model's context would change the very runs it exists to measure.

The details behind every claim here, including the correction of an earlier
wrong explanation for those 80 runs — and the correction of the count itself,
which this chapter first gave as 48 — are in
[the event vocabulary note](../research/2026-08-02-phase3-cycle1-event-vocabulary.md).
