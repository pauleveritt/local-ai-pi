# Phase 3, Cycle 1 — Observable extension

**Phase:** 3 — Build the extension half
**Status:** design, awaiting plan

## Why this cycle

`BRIEF.md` defines the product as "a Pi *extension* (not a fork of Pi) plus an
eval harness." Phases 1 and 2 built the harness. `.pi/extensions/hello-world.ts`
has been loaded on every one of 48 recorded runs and has produced **nothing
observable** in any of them.

This cycle makes one custom entry travel extension → captured stdout →
`read_telemetry`, and closes the two questions cycle 2 would otherwise have to
answer before it could start.

### The finding: the recorded cause was wrong

`ROADMAP.md` states the extension is inert because `--no-session` leaves
`appendEntry` nowhere to write and `--print --no-themes` leaves `ctx.ui.notify`
no TUI. The second half is true. The first half is not, and reading the
installed 0.82.0 package shows why:

| Step | Where | What actually happens |
|---|---|---|
| `pi.appendEntry(type, data)` | `core/agent-session.js:1869` | Appends the entry, then emits `{type: "entry_appended", entry}` |
| `appendCustomEntry` | `core/session-manager.js:820` | Stores the entry in an **in-memory** map (`byId`). Disk persistence is a separate concern |
| json mode output | `modes/print-mode.js:80` | `session.subscribe(event => writeRawStdout(JSON.stringify(event)))` — **every** session event reaches stdout |
| the gap | `modes/print-mode.js:50`, `core/agent-session.js:1766` | `bindExtensions()` **awaits the `session_start` emission**. `session.subscribe` is only wired up *after* `bindExtensions` returns |

So the `entry_appended` emitted from our `session_start` handler is emitted with
**no subscriber attached**, and dropped. It is a subscribe-ordering problem, not
a persistence problem. `tests/fixtures/pi-run-0.82.0.jsonl` agrees: no
`entry_appended`, and its first line is the `session` header — nothing from
`session_start` survives.

The consequence is that `appendEntry` called from any event *after* the
subscribe boundary should already reach stdout today, with no new API and no
change to how Pi is invoked.

### The hazard: changing the extension does not change run conditions

`RunConditions.pi_command` records the whole normalized command
(`harness/runner.py:112`), so extension **paths** are already recorded. It never
records extension **contents**. Editing `hello-world.ts` therefore leaves
`RunConditions` byte-identical, and `run_batch`'s conditions check
(`harness/runner.py:166-167`) would resume a checkpoint whose earlier runs used
a different extension — silently.

`ROADMAP.md` asserts that changing the extension changes run conditions. Today
it does not. This cycle is the one that makes the assertion true, and it is the
cheapest moment to do it: Phase 2 cycle 3's clean baseline has not been run, so
no checkpoint is lost.

## What this cycle is not

- **Not a file copy.** `.pi/extensions/hello-world.ts` is already byte-identical
  to the prior project's. The transplant already happened; what is missing is
  the part that works in the mode we actually run.
- **Not `registerTool`.** Proving the tool path needs the model to *choose* to
  call a tool — the first non-deterministic, model-dependent proof in Phase 3.
  Cycle 2 proves it anyway, with the real subagent tool, where the proof counts.
- **Not an orchestrator.** Pi ships one at `examples/extensions/subagent/`.
- **Not a plugin system.** The extension seam is one parameter with one caller.

## Design

### 1. `.pi/extensions/hello-world.ts`

Move the `appendEntry` call from `session_start` to `agent_start`.

`agent_start` fires during `session.prompt()`, well after `session.subscribe`,
and fires exactly once per run regardless of what the model does — it does not
depend on tool calls, turn counts, or the model succeeding.

Drop `Date.now()` from the payload. The session entry already carries its own
`timestamp`, and a second wall-clock value in captured stdout makes every
fixture diff noisy for no gain.

The seven `notify` handlers stay. They are the teaching artifact's lifecycle
tour, and their invisibility under `--no-themes` is a documented finding rather
than a bug to fix.

### 2. `harness/telemetry.py`

`RunTelemetry` gains:

```python
custom_entries: tuple[str, ...]  # customType of each entry_appended, in order
```

Types only, not payloads. Proving the path requires the name to arrive; an
untyped JSON blob inside a frozen dataclass buys nothing until something reads
it, and `BRIEF.md` bars machinery ahead of the contract it serves.

Parsing follows the module's existing discipline — tolerant, never inventive. An
`entry_appended` whose `entry.type` is not `"custom"`, or whose `customType` is
not a string, is skipped rather than guessed at. `appendEntry` is not the only
thing that appends an entry, and a label change is not evidence.

`custom_entries` has no bearing on `complete`, on `RunResult.accepted`, or on
grading. The extension observes; it must never be able to fail a run the model
actually completed. It can still fail a *test* — that is where the assertion
belongs.

### 3. `harness/runner.py` — the extension seam

`EXTENSION: Path` becomes `EXTENSIONS: tuple[Path, ...]`, and `_pi_command`
emits one `--extension` per entry, order preserved.

This is `BRIEF.md`'s "seams, not hardcodes" applied one cycle before cycle 2
needs it. Cycle 2 must load Pi's shipped subagent extension alongside or instead
of ours; the single hardcoded constant is exactly the shape that cost the prior
project.

### 4. `RunConditions.extension_digests`

New field, `tuple[str, ...]` — one SHA-256 per extension in `EXTENSIONS`, in
order, mirroring the existing `task_spec_sha256`.

The digest helper accepts a **file** and **raises on a directory**. Pi's
subagent extension is a directory (`index.ts`, `agents/`, `prompts/`); cycle 2
should be forced to decide how a tree is hashed rather than inherit a plausible
wrong answer from us.

`_conditions` runs before any model work, so a missing extension file raises
there rather than 600 seconds later.

**Accepted consequence:** this invalidates every existing checkpoint. Resuming
one raises "checkpoint conditions do not match this batch". That is the field
doing its job.

## Data flow

`session.prompt()` → Pi emits `agent_start` to the extension runner → our
handler calls `pi.appendEntry("evidence")` → `agent-session.js` appends a
`custom` entry and emits `entry_appended` → print mode's subscriber serializes
it to stdout → `run_process` captures it into `RunResult.pi_stdout` → the
checkpoint persists that stdout verbatim → `read_telemetry` parses it into
`custom_entries`.

Every hop already exists. The only reason it does not work today is *where* the
call sits.

## Recorded outputs

### The event vocabulary

`docs/superpowers/research/2026-08-02-phase3-cycle1-event-vocabulary.md` — what
an extension can and cannot emit under
`--print --mode json --no-session --no-themes`:

- Everything the session emits **after** `session.subscribe` reaches stdout.
  That is the whole contract, not a per-event allowlist.
- The subscribe boundary sits after `bindExtensions`, which awaits
  `session_start`. Anything emitted during `session_start` is dropped for want
  of a subscriber. This is the real cause of 48 inert runs.
- `ctx.ui.notify` has no destination under `--no-themes`. It is not an evidence
  channel.
- `pi.sendMessage` reaches stdout but can enter LLM context
  (`registerEntryRenderer`'s own documentation contrasts custom *entries*, which
  "do not participate in LLM context"). Barred from the harness on those
  grounds: injecting anything into the model's context to prove observability
  would corrupt the runs the harness measures.

Cycle 3 attributes a delegated run's cost and needs to know where a delegation
becomes visible. This note is what stops it from starting with a guess.

### Corrections to the record

`ROADMAP.md`'s Phase 3 entry and its cycle 1 row both assert the
`--no-session`/`appendEntry` cause, and the entry asserts that changing the
extension changes run conditions. Both are corrected in place. This is Phase 2
cycle 4's claim-checking discipline applied to our own roadmap: a claim
justified by reading rather than by a run, retired once a run disagrees.

### The teaching artifact

Transplant the prior chapter from
`.worktrees/pre-restructure/docs/section-1-hello-agent/` with a drift audit
against installed 0.82.0 — the known-stale `appendEntry({type, data})` signature
against the installed `appendEntry(customType, data?)`, plus whatever else the
audit turns up. Per `BRIEF.md`'s gardening rule it is a candidate: read, argued,
and rewritten where it is wrong, not copied.

## Testing

One live test, then fixtures forever — the pattern Phase 1 cycles 3–7
established.

**Gating spike (live, first).** One real `pi` run against the model server
asserting `entry_appended` reaches stdout. Its captured output becomes
`tests/fixtures/pi-run-0.82.0-entry-appended.jsonl`. If the spike falsifies the
hypothesis, the cycle re-plans rather than proceeding — and the finding is still
worth its own record.

**Fixture-only, no model in the loop:**

- `read_telemetry` puts `entry_appended` into `custom_entries` in order
- `read_telemetry` skips a non-`custom` entry and a non-string `customType`
- `read_telemetry` on the existing `pi-run-0.82.0.jsonl` yields empty
  `custom_entries` — a regression guard on the old, inert behaviour
- `_pi_command` emits one `--extension` per path, order preserved
- `_conditions` digests change with file content, raise on a missing file, and
  raise on a directory
- `run_batch` refuses a checkpoint recorded under a different extension digest

## Gates

`uv run pytest && uv run ruff check . && uv run pyrefly check`, plus a clean
strict Sphinx build.

Never `git commit` while a `run_batch()` is in flight.

## What this unblocks

| Cycle | What it inherits |
|---|---|
| 2 | The extension seam — a second extension can be loaded without touching `_pi_command`'s shape |
| 2 | The event vocabulary — where a registered tool's activity becomes visible |
| 3 | A parsed, tested route from an extension-emitted event to a `RunTelemetry` field |
| 4 | Run conditions that actually change when the extension changes, so a before/after comparison is honest |
