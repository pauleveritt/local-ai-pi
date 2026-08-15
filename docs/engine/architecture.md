# The engine: architecture

**Two problems, two guards, one installable file, and the orchestrator
underneath.** This page traces the engine in execution order — the shape
of a guard, how the bundle wires them, and where the orchestrator picks
up — naming the real file at each stage. It links to
`docs/engine/deliver-candidate.md` for the orchestrator rather than re-explaining it.

## The problems being solved

Both guards exist because of a recorded failure, not a hypothetical.

**Looping.** One recorded run of this project executed 261 tool calls, of
which **245 were the identical command `ls -R`**, each returning no
output because the workspace was genuinely empty. It never concluded
that it should create files. Pi ships no turn cap, no loop detection,
and no tool-call budget; upstream points users at extensions. The loop
breaker is that extension: it refuses an unchanged call once the model
has made it several times in a row, and it fires whether or not the
calls succeeded — every one of those 245 succeeded, so a breaker that
counted only failing repeats would never have fired.

**Symbol deletion.** In a recorded 4-run batch, three runs failed the
same way. Asked to *add* a `/contact` route to a working site, the model
issued an edit that replaced the existing `/about` route with it —
treating "add a route" as "transform the nearest similar route". Three
acceptance tests failed from that one deletion. This is not the
stale-anchor failure: the anchor matched perfectly, so the failure had
moved from mechanics to intent. Preserve-symbols is the guard for that
intent — an edit that names a symbol on the way in and not on the way
out is a deletion, whatever the model meant by it.

## The shape of a guard

A guard is a pure decision function over a tool call:

```
ToolCall → Decision
```

`ToolCall` is a tool name, an argument payload, and an optional target
path; `Decision` is either a `Block` (a refusal with a steering reason
and a telemetry entry) or `undefined` — "no opinion, let it through".
One file per concern, `extensions/guards/loop-breaker.ts` and
`extensions/guards/preserve-symbols.ts`, with the shared types in
`extensions/guards/types.ts`.

Making the decision a pure function is the replay seam. The same
`inspect(call)` that runs live can be driven from a recorded transcript,
so the guards are tested two ways: `bun test` exercises them directly,
and `tools/replay_guards.mjs` replays committed fixtures through the
file a contributor actually installs.

The loop breaker remembers a window of calls keyed by tool and
arguments, and refuses once the same key repeats past its threshold.
Preserve-symbols watches `edit` only and compares the symbols named in
an edit's old text against the union of its new text — the union is
load-bearing, because moving a function by deleting it in one entry and
re-adding it in another is refactoring, not destroying.

## The bundle

`packages/engine/engine.ts` is the installable artifact (`.pi/extensions/` holds a symlink to it, so a checkout loads the engine with zero install). The two guards
are copied into it verbatim, policy inlined, with the shared types
folded in, so the file imports nothing local and a `cp` is a complete
install. A thin adapter — the default export — registers both guards on
`tool_call` in order, converts Pi's event shape to a `ToolCall`, and on
a block appends the guard's telemetry entry and returns the refusal to
the model.

The copies are pinned to their sources. `extensions/guards/guards.test.ts`
("the engine bundle artifact") holds the artifact's `WINDOW` and
`THRESHOLD` to the guard sources, checks it stays free of local imports,
and replays the recorded destructive and additive edits through it, so
the one file you install cannot drift silently from the guards that were
measured.

## Underneath: the orchestrator

The engine's two faces are independent, and the orchestrator is the
second one. It is the explicit front you invoke: not part of the bundle,
it runs from a checkout, pre-chews a task into a handoff packet, and
drives the implementer — the bounded worker — which shares only the
guards' source files through its extension closure. Its path is handoff
packet → mutation engine → preservation validation → candidate ref, and
it is traced end to end, in execution order, in
`docs/engine/deliver-candidate.md`. The guards ride along there
contract-blind by design; here they are the whole product.

## What is deliberately out of scope

- **Planning.** Neither guard plans; the orchestrator's typed-contract
  bridge is scoped to four tasks and refuses the rest at the command
  line.
- **Shell oversight.** Preserve-symbols governs `edit` alone, on
  purpose — `write` and heredocs bypass it, and the one passing run in
  that 4-run batch recovered through a heredoc rewrite.
- **Turn caps.** A model doing varied work for a long time is untouched;
  the loop breaker targets repetition specifically.
