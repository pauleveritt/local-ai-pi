# Phase 3, Cycle 1 — The event vocabulary

What a Pi extension can and cannot emit under the harness's actual invocation
mode, `--print --mode json --no-session --no-themes`.

Established 2026-08-02 by reading installed Pi 0.82.0 and then confirming the
conclusion with one live model run. Citations below are relative to
`~/.volta/tools/image/packages/@earendil-works/pi-coding-agent/lib/node_modules/@earendil-works/pi-coding-agent/`
— `dist/…` for Pi's own compiled source, and `node_modules/…` for the nested
`pi-agent-core` package, which sits beside `dist/` rather than inside it.

*(An earlier version of this line said every path was relative to `dist/`.
Following it landed on a nonexistent `dist/node_modules/…` — the same
mislocation this note's own correction, below, is about.)*

Cycle 3 has to attribute a delegated run's cost, and a delegated child is
spawned as `pi --mode json -p --no-session`, so a delegation arrives in the
parent's stream as a `tool_execution_start` / `tool_execution_end` pair, which
carries `toolName`. Before that can be measured, something has to
establish that the *parent's own extension activity* is visible on that same
stream. That is what this note is for: cycle 3 should not start from a guess
about where a delegation becomes observable.

*This paragraph previously said a delegation "arrives in the parent's stream as
a tool call." That was wrong: `tool_call` is delivered to extensions only and
never reaches stdout (row 7 of the drift table below;
`core/agent-session.js:214-224`, `:234-247`, and zero occurrences in the
157-line fixture). It was retired by the audit in this same note. The inherited
conclusion is unaffected — a delegation is still observable in the parent's
stream — but it is the execution events that carry it.*

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

## The subscribe boundary, and the real cause of 80 inert runs

Print mode's `rebindSession` calls `await session.bindExtensions(…)` at
`modes/print-mode.js:50`, and only wires the subscriber at
`modes/print-mode.js:80`, after that await returns. `bindExtensions` emits `session_start` before returning:

```js
await this._extensionRunner.emit(this._sessionStartEvent);
```

— `core/agent-session.js:1766`.

Therefore anything an extension emits from a `session_start` handler is emitted
with **no subscriber attached**. The drop is irrecoverable rather than delayed:
`_emit` iterates the listener list synchronously at the moment of emission and
there is no buffer and no replay (`core/agent-session.js:285-289`).

**This is the real cause of the 80 recorded runs in which
`.pi/extensions/hello-world.ts` produced nothing observable, and it is not
`--no-session`.** The extension called `appendEntry` from `session_start`; the
call worked, the entry was appended, the event was emitted, and nobody was
listening yet.

*(This note first said 48, and so did four other documents. The figure was
the size of Phase 2 cycle 2's precision baseline, not a census of recorded
runs — cycle 3's clean baseline had already added 32 more. Verified by
loading every checkpoint in `~/local-ai-pi-evidence/` and recomputing:
16 + 32 + 13 + 19 = 80 runs, every one of them loading `hello-world.ts`,
every one of them yielding `custom_entries == ()`. The correction is
recorded here rather than quietly applied because the same cycle had
already corrected a related cost claim three paragraphs from this one and
left this figure standing — which is the whole reason it survived seven
reviews.)*

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
documents. That drift is real; it is row 1 of the audit in "Drift found against
0.82.0" below.

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
  `session_start` appears between them — but that absence is not evidence of a
  drop. Task 1 moved the `appendEntry` call to `agent_start`, so nothing was
  emitted at `session_start` at all in this run; the handler that remains
  there only calls `ctx.ui.notify` (`.pi/extensions/hello-world.ts:5-7`),
  which is inert for the unrelated reason covered below. The absence here is
  the expected consequence of the code change. The evidence for the drop is
  the control fixture, next.
- **Line 3 is Pi's own `agent_start` event.** The extension's handler runs, and
  its emission is serialized, *before* the event that triggered it reaches
  stdout. Ordering in the stream reflects emission order, not causal order, and
  anything reading the stream should not assume otherwise.

The pre-cycle-1 capture `tests/fixtures/pi-run-0.82.0.jsonl` (123 lines) is the
control: it contains zero `entry_appended` events, from the same extension file
with the call in the other handler.

`agent_start` fires during `session.prompt()`, at least once per run and before
any model-dependent behaviour. It is not *exactly* once — Pi retries after some
agent errors (`agent_end` carries `willRetry`, `core/agent-session.js:353`) —
and **a retry does re-fire `agent_start`.** Read, the chain resolves: the retry
loop calls `await this.agent.continue()` (`core/agent-session.js:748-749`);
`continue()` (`pi-agent-core/dist/agent.js:229`) falls through to
`runContinuation()` (`:270-272`), which calls `runAgentLoopContinue`; and that
function's first emission is `await emit({ type: "agent_start" })`
(`pi-agent-core/dist/agent-loop.js:67`). The operational conclusion is
unchanged and now better supported: anything asserting on the resulting entries
must test membership, not length.

*This paragraph previously called the retry behaviour "plausible but
unverified," on the grounds that `@earendil-works/pi-agent-core` was "not
present under the installed package tree." That second claim was false, and so
the first was unnecessary. `pi-agent-core` is present, nested one level down at
`<installed-package>/node_modules/@earendil-works/pi-agent-core/` at the same
0.82.0 version; it is simply not a sibling in the top-level `node_modules`,
which is how a directory listing made it look absent. Reading it retired the
hedge. Recording the manner of the error as well as the error: this note was
written in a cycle that exists because a claim had been confidently asserted
from reading rather than running. Asserting unverifiability from a directory
listing rather than a search is the same failure in humbler dress.*

## `ctx.ui.notify` is not an evidence channel

The extension runner supplies a `noOpUIContext` whose `notify` is an empty
function (`core/extensions/runner.js:88-92`). Under `--print` there is no
TUI for it to reach and no fallback to stdout. The operational half of
`ROADMAP.md`'s original claim — that `notify` is not an evidence channel
here — was correct.

*(Corrected 2026-08-03: this section said "under `--no-themes`", and credited
that half of the original claim as correct without qualification. The
conclusion holds but the named cause was wrong, and it was wrong in 0.82.0
too — this is not line drift the header's version pin excuses. `--no-themes`
governs theme discovery only (`cli/args.js:258`); what silences `notify` is
`--print`, because print mode's `bindExtensions({…})` passes no `uiContext`
and `setUIContext(undefined)` falls back to `noOpUIContext`. The four-hop
chain is gotcha 9 of
[the cycle 2 Pi gotchas record](2026-08-03-phase3-cycle2-pi-gotchas.md).)*

The seven `notify` handlers in `hello-world.ts` stay anyway. They are the
teaching artifact's lifecycle tour, and their invisibility in this mode is a
documented finding, not a defect to repair.

## `pi.sendMessage` is barred from the harness

`pi.sendMessage` does reach stdout. It is barred for a different reason.

Pi's own documentation states this outright rather than leaving it to
inference: `docs/extensions.md:1561` says of `registerMessageRenderer` that
"Custom messages are created with `pi.sendMessage()` and participate in LLM
context." The installed `types.d.ts` corroborates by contrast:
`registerEntryRenderer` is annotated "Custom entries do not participate in
LLM context" (`core/extensions/types.d.ts:900`), sitting directly beside
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

— `core/resource-loader.js:315-317` (and again at `:408-410`). *(Corrected
2026-08-03: this note and the chapter both cited `:267-269`, which is
project-trust code. The claim was always true — `cli/args.js:252` states it —
but the line reference was not, and a light review caught what an earlier
review had confirmed as exact.)* The `noExtensions` branch keeps
`cliEnabledExtensions`; it drops only the discovered set.

This is why the harness can run with ambient extensions disabled — its isolation
requirement — while still loading its own. It was worth checking rather than
assuming, because the opposite behaviour would have forced a choice between
isolation and instrumentation.

## What cycle 3 inherits

- A delegation is visible in the parent's stream as a `tool_execution_start` /
  `tool_execution_end` pair carrying `toolName`, and the child is itself
  `pi --mode json`. Read the execution events, **not** `tool_call` — `tool_call`
  goes to extensions only and never reaches stdout (row 7 below). *This bullet
  previously named `tool_call`; the drift audit in this note retired that.*
- The parent's extension activity is visible on that same stream, provided the
  emission happens after the subscribe boundary — which every event from
  `agent_start` onward does.
- `entry_appended` is the channel to use for it, because it is observable and
  cannot reach the model.

Cycle 3 can therefore start by deciding *what* to attribute, not by
re-establishing whether attribution is observable at all.

## Drift found against 0.82.0

The pre-restructure worktree carries a spec, plan, and chapter for this same
material at `.worktrees/pre-restructure/docs/section-1-hello-agent/` (chapter
222 lines, spec 170, plan 486). Per `BRIEF.md`'s gardening rule they are
candidates, not a manifest. Cycle 1's chapter was written against the installed
package rather than copied, and this is the audit that decided which parts
could not be carried over. Recording it means the next transplant from that
worktree starts from a known state instead of re-deriving these.

Citations are relative to the installed package `dist/` root named at the top
of this note.

Not every row is drift. Nine rows (1–4, 6–10) are genuine divergences of the
prior work from installed 0.82.0. Three are not, and say so in place: two are
hygiene or enrichment on claims that were not wrong, and one was never claimed
by the prior work at all. Read the parenthetical label on rows 5, 11, and 12
before treating them as things the prior work got wrong.

| # | Prior claim | Installed 0.82.0 | Evidence |
|---|---|---|---|
| 1 | `pi.appendEntry({type, data})` — one object argument | `appendEntry<T = unknown>(customType: string, data?: T): void` — a string ID, then optional data | `core/extensions/types.d.ts:915` |
| 2 | `appendEntry` "writes directly into the session's JSONL file" | Appends to an **in-memory** map and emits `entry_appended`; disk persistence is a separate step gated on session persistence and is not on this path | `core/session-manager.js:820-831`, `core/agent-session.js:1869-1874` |
| 3 | Verify with `grep "session_start" ~/.pi/agent/sessions/<dir>/<id>.jsonl`, looking for `"type":"evidence"` | Under `--no-session` there is no such file at all; and the entry's `type` is `"custom"` — the string you passed lands in `customType` | fixture line 2; `core/session-manager.js:240-246` |
| 4 | The `appendEntry` call belongs in the `session_start` handler | That placement drops the entry: the json-mode subscriber is attached only after `bindExtensions` returns, and `bindExtensions` emits `session_start` before returning | `modes/print-mode.js:50` vs `:80`, `core/agent-session.js:1766`; body of this note |
| 5 | (not a divergence — hygiene, recorded for completeness) Payload includes `timestamp: Date.now()` | Redundant — the entry carries its own `timestamp` — and it makes every captured stdout differ from the last for no gain | fixture line 2 |
| 6 | "Restart Pi … you'll see a notification flash" | True in an interactive session; under the harness's **`--print`** mode `notify` is a no-op function *(this row read `--no-themes` until 2026-08-03; see the `ctx.ui.notify` section above and gotcha 9)* | `core/extensions/runner.js:88-92`, `modes/print-mode.js:50-78` |
| 7 | `tool_call` is presented alongside `tool_execution_*` as an observable lifecycle event | `tool_call` is delivered to **extensions only**, via the agent's `beforeToolCall` hook, and is never passed to `_emit`. It appears zero times in the 157-line fixture. `tool_result` behaves the same way | `core/agent-session.js:214-224` and `:234-247`; fixture |
| 8 | The lifecycle diagram treats "the event" as a single thing | The extension event and the stdout event are **separately constructed objects**. A `turn_end` handler receives `turnIndex`; the `turn_end` line on stdout has only `type`, `message`, `toolResults` | `core/agent-session.js:427-451`; fixture |
| 9 | Seven events named as the lifecycle | 0.82.0 also emits `turn_start`, `message_start` / `message_update` / `message_end`, `tool_execution_update`, and `agent_settled` on the same stream. The tour is a selection, not a census | fixture event sequence; `core/extensions/types.d.ts:847-880` |
| 10 | Spec: "If a handler throws, Pi catches and logs; the extension stays loaded" | Not true of `tool_call` handlers — a throw propagates and blocks tool execution, by design | `core/agent-session.js:226-233` |
| 11 | (not a divergence — an addition found while auditing) `tool_call` is where you "inspect or block", which is correct as far as it goes | Also where you *patch*: `event.input` is mutable in 0.82.0 and later handlers see earlier mutations, with no re-validation | `core/extensions/types.d.ts:679-683` |
| 12 | (not claimed, recorded for completeness) | The `agent_end` line on stdout carries a `willRetry` field added at emission that the published `AgentEndEvent` type does not declare — the type is incomplete against the stream | `core/agent-session.js:353` vs `core/extensions/types.d.ts:534-537`; fixture line 156 |

Two things the prior work got right and were carried over unchanged: the
default-export factory shape (`ExtensionFactory = (pi: ExtensionAPI) => void |
Promise<void>`, `core/extensions/types.d.ts:1076`), and the `-e` short flag for
`--extension`, confirmed against `pi --help` on the installed binary.
