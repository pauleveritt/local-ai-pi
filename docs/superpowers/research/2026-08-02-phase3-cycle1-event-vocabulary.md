# Phase 3, Cycle 1 — The event vocabulary

What a Pi extension can and cannot emit under the harness's actual invocation
mode, `--print --mode json --no-session --no-themes`.

Established 2026-08-02 by reading installed Pi 0.82.0 and then confirming the
conclusion with one live model run. Every citation below is relative to the
installed package root
`~/.volta/tools/image/packages/@earendil-works/pi-coding-agent/lib/node_modules/@earendil-works/pi-coding-agent/dist/`.

Cycle 3 has to attribute a delegated run's cost, and a delegated child is
spawned as `pi --mode json -p --no-session`, so a delegation arrives in the
parent's stream as a tool call. Before that can be measured, something has to
establish that the *parent's own extension activity* is visible on that same
stream. That is what this note is for: cycle 3 should not start from a guess
about where a delegation becomes observable.

## The contract, stated once

There is no per-event allowlist. In `--mode json`, print mode attaches a single
subscriber and serializes whatever it receives:

```js
unsubscribe = session.subscribe((event) => {
    if (mode === "json") {
        writeRawStdout(`${JSON.stringify(event)}\n`);
    }
});
```

— `modes/print-mode.js:80-84`.

So the rule is one sentence: **everything the session emits after
`session.subscribe` reaches stdout.** The question is never *which* event type
is permitted. It is only whether the emission happens on the right side of the
subscribe boundary.

## The subscribe boundary, and the real cause of 48 inert runs

Print mode's `rebindSession` calls `await session.bindExtensions(…)` at
`modes/print-mode.js:50`, and only wires the subscriber at
`modes/print-mode.js:80`, after that await returns. `bindExtensions` ends by
awaiting the `session_start` emission:

```js
await this._extensionRunner.emit(this._sessionStartEvent);
```

— `core/agent-session.js:1766`.

Therefore anything an extension emits from a `session_start` handler is emitted
with **no subscriber attached**. The drop is irrecoverable rather than delayed:
`_emit` iterates the listener list synchronously at the moment of emission and
there is no buffer and no replay (`core/agent-session.js:285-289`).

**This is the real cause of the 48 recorded runs in which
`.pi/extensions/hello-world.ts` produced nothing observable, and it is not
`--no-session`.** The extension called `appendEntry` from `session_start`; the
call worked, the entry was appended, the event was emitted, and nobody was
listening yet.

`ROADMAP.md` had recorded a different cause — that `--no-session` left
`appendEntry` nowhere to write. That claim was arrived at by reading, was
plausible, and was wrong. It is corrected there, and the correction is recorded
as such rather than quietly edited.

## `appendEntry` works, and where

The call chain has no persistence in it:

| Step | Where | What happens |
|---|---|---|
| `pi.appendEntry(customType, data?)` | `core/agent-session.js:1869-1874` | Appends the entry, then emits `{type: "entry_appended", entry}` |
| `appendCustomEntry` | `core/session-manager.js:820-831` | Builds a `custom` entry and stores it in an **in-memory** map |
| serialization | `modes/print-mode.js:80-84` | Whatever the subscriber receives is written to stdout |

Writing to disk is a separate `_persist` step gated on session persistence.
Nothing in the path above touches it, which is why `--no-session` is irrelevant
here.

The installed signature is
`appendEntry<T = unknown>(customType: string, data?: T): void`
(`core/extensions/types.d.ts:915`) — one string type ID plus optional data, not
the single-object `appendEntry({type, data})` the prior project's chapter
documents. That drift is real and is audited in this cycle's chapter.

Called from `agent_start` or any later event, `appendEntry` reaches stdout with
no new API and no change to how Pi is invoked.

## Confirmed live, not only by reading

Task 1 moved the `appendEntry` call from `session_start` to `agent_start` and
ran one real `pi` invocation against the model server. Its captured stdout is
committed verbatim at `tests/fixtures/pi-run-0.82.0-entry-appended.jsonl`, 157
lines. Line 2 is:

```json
{"type":"entry_appended","entry":{"type":"custom","customType":"evidence","data":{"event":"agent_start"},"id":"65c59a3a","parentId":"da342777","timestamp":"2026-08-02T19:20:33.911Z"}}
```

Two details in that placement are worth recording:

- **Line 1 is the `session` header and line 2 is the entry.** Nothing from
  `session_start` appears between them, which is the dropped emission showing up
  as an absence.
- **Line 3 is Pi's own `agent_start` event.** The extension's handler runs, and
  its emission is serialized, *before* the event that triggered it reaches
  stdout. Ordering in the stream reflects emission order, not causal order, and
  anything reading the stream should not assume otherwise.

The pre-cycle-1 capture `tests/fixtures/pi-run-0.82.0.jsonl` (123 lines) is the
control: it contains zero `entry_appended` events, from the same extension file
with the call in the other handler.

`agent_start` fires during `session.prompt()`, at least once per run and before
any model-dependent behaviour. It is not *exactly* once — Pi retries after some
agent errors (`agent_end` carries `willRetry`, `core/agent-session.js:353`), and
a retry fires `agent_start` again. Anything asserting on the resulting entries
must test membership, not length.

## `ctx.ui.notify` is not an evidence channel

The extension runner supplies a `noOpUIContext` whose `notify` is an empty
function (`core/extensions/runner.js:88-92`). Under `--no-themes` there is no
TUI for it to reach and no fallback to stdout. This half of `ROADMAP.md`'s
original claim was correct.

The seven `notify` handlers in `hello-world.ts` stay anyway. They are the
teaching artifact's lifecycle tour, and their invisibility in this mode is a
documented finding, not a defect to repair.

## `pi.sendMessage` is barred from the harness

`pi.sendMessage` does reach stdout. It is barred for a different reason.

Pi's own documentation draws the line: `registerEntryRenderer` is annotated
"Custom entries do not participate in LLM context"
(`core/extensions/types.d.ts:900`), sitting directly beside
`registerMessageRenderer` for `CustomMessageEntry`, which carries no such
disclaimer. Custom *messages* can enter the model's context; custom *entries*
cannot.

That rules `sendMessage` out here on measurement grounds rather than style:
injecting anything into the model's context in order to prove observability
would change the very runs the harness exists to measure. The observation
channel must not be able to alter the observation.

## A useful negative result: `--no-extensions` does not cancel `--extension`

`--no-extensions` suppresses *ambient* extensions only. Explicitly passed
`--extension` paths survive it:

```js
const extensionPaths = this.noExtensions
    ? cliEnabledExtensions
    : this.mergePaths(cliEnabledExtensions, enabledExtensions);
```

— `core/resource-loader.js:267-269`. The `noExtensions` branch keeps
`cliEnabledExtensions`; it drops only the discovered set.

This is why the harness can run with ambient extensions disabled — its isolation
requirement — while still loading its own. It was worth checking rather than
assuming, because the opposite behaviour would have forced a choice between
isolation and instrumentation.

## What cycle 3 inherits

- A delegation is a tool call in the parent's stream, and the child is itself
  `pi --mode json`.
- The parent's extension activity is visible on that same stream, provided the
  emission happens after the subscribe boundary — which every event from
  `agent_start` onward does.
- `entry_appended` is the channel to use for it, because it is observable and
  cannot reach the model.

Cycle 3 can therefore start by deciding *what* to attribute, not by
re-establishing whether attribution is observable at all.
