# Phase 3, Cycle 2 — The Pi gotchas record

Ten things about Pi that this project paid to discover. Each is non-obvious,
each is invisible from Pi's own documentation, and each cost something —
recorded here with the price, because a gotcha with a price attached is
remembered and one without is skimmed.

## How to read a citation here

**The version is 0.83.0, not 0.82.0.** Every line number below was opened and
confirmed on 2026-08-03 against the installed
`@earendil-works/pi-coding-agent` at
`~/.volta/tools/image/packages/@earendil-works/pi-coding-agent/lib/node_modules/@earendil-works/pi-coding-agent/`,
whose `package.json` reads `"version": "0.83.0"` and whose binary answers
`pi --version` with `0.83.0`. There is one such package under Volta.

This matters, and not as pedantry. This cycle's own spec and plan,
[the cycle 1 event vocabulary note](2026-08-02-phase3-cycle1-event-vocabulary.md),
and [`chapters/hello-agent.md`](../chapters/hello-agent.md) all said
0.82.0 when this was written — correctly, at the time. In the day since, the
installed package moved, and **one citation moved with it by five lines**
(gotcha 1 below). A `file:line` into a compiled `dist/` is only meaningful
against a stated version, and a record that names the wrong version is a
record whose citations will silently rot. Read every number here as *0.83.0*.

*(Updated 2026-08-03, later the same day. This paragraph reported the same
five-line drift as "present, uncorrected" in the chapter, and gotcha 9 below
reported two further chapter errors the same way. **The chapter has since been
fixed in place** — every citation in
[`chapters/hello-agent.md`](../chapters/hello-agent.md) was re-opened against
0.83.0, eight had drifted, and the chapter now states 0.83.0 and carries its
own correction notes. The other documents named in the paragraph above were
corrected separately and later, not by that pass. This record's chapter
references are given without line numbers from here on, since the chapter's
own lines move when it is corrected.)*

Paths: `core/…`, `modes/…`, `cli/…` and `config.js` are relative to `dist/`.
`examples/extensions/subagent/…` is relative to the *package root* — it is
the shipped TypeScript example, which sits beside `dist/`, not inside it.
`pi-agent-core/…` likewise sits beside `dist/`, nested one level down in the
package's own `node_modules/`.

## Read, or run

Every gotcha carries a label: **read** if it was established by reading Pi's
source, **run** if by running Pi and observing what happened.

The convention exists because this project's recurring injury is a claim
justified by reading rather than by running. The cause of 80 inert runs was
read off the source, was plausible, and was wrong. A claim about whether Pi
retries `agent_start` was declared unverifiable on the strength of a
directory listing. A `file:line` for `--no-extensions` was wrong in two
documents for a full cycle, and an external review confirmed it as *exact*
before a lighter one caught it.

So: **read** is not a lesser label, but it is a different one. A read-only
claim says "the source says this and I have not watched it happen." A
**run** claim says "I watched it happen." Where a claim is read *and*
confirmed by a run, both are stated. Where a claim has never been read out of
`dist/` at all, that is said outright rather than dressed up in a citation
that does not exist — see gotcha 6.

---

## 1. The json-mode stdout subscriber attaches after `session_start` is emitted and awaited

**read**, confirmed **run**.

Print mode's `rebindSession` awaits `session.bindExtensions({…})` at
`modes/print-mode.js:50`, and only then attaches the subscriber that
serializes events to stdout, at `modes/print-mode.js:80`. But
`bindExtensions` emits `session_start` before it returns —
`core/agent-session.js:1761`, the second-to-last statement of a method that
begins at `:1741` and closes at `:1763`:

```js
this._applyExtensionBindings(this._extensionRunner);
await this._extensionRunner.emit(this._sessionStartEvent);
```

So anything an extension emits from a `session_start` handler is emitted with
**no subscriber attached**, and the drop is irrecoverable rather than
deferred: `_emit` iterates the listener list synchronously at the moment of
emission, with no buffer and no replay (`core/agent-session.js:285-289`).

**Cost:** 80 recorded runs in which `.pi/extensions/hello-world.ts` produced
nothing observable — and, worse, a *wrong recorded cause* for those runs
(`--no-session` was blamed) that survived in `ROADMAP.md` until a run
disagreed with it. The full reconstruction is in
[the event vocabulary note](2026-08-02-phase3-cycle1-event-vocabulary.md),
including how the run count itself was wrong at 48 in five documents.

*Corrected here 2026-08-03: this citation was written as
`core/agent-session.js:1766`, which is correct for 0.82.0 and, in 0.83.0,
lands on a bare `return;` inside `extendResourcesFromExtensions` — a
different method entirely. Five lines of drift, one minor version.*

## 2. `--approve` is not an isolation flag

**read.**

Pi's own help text defines it, at `cli/args.js:263`:

```
  --approve, -a                  Trust project-local files for this run
```

It **widens** trust rather than narrowing it. Its opposite number,
`--no-approve, -na`, is one line below at `:264`. What actually excludes a
model-written `.pi/extensions/*.ts` from being loaded is `--no-extensions`.

**Cost:** the flag sat in this harness's "isolation flags" list for two phases
with its meaning exactly inverted. `harness/runner.py:122-126` now carries the
correction as a comment beside the flag, so the next reader of that argv is
told before they infer.

## 3. `--no-extensions` spares explicitly passed `--extension` paths

**read.**

It suppresses *discovery*, not explicit loading. The `noExtensions` branch
keeps `cliEnabledExtensions` and drops only the discovered set:

```js
const extensionPaths = this.noExtensions
    ? cliEnabledExtensions
    : this.mergePaths(cliEnabledExtensions, enabledExtensions);
```

— `core/resource-loader.js:315-317`, and again, verbatim, at `:408-410`.
`noExtensions` appears nowhere else in that file. The help text says so too,
at `cli/args.js:252`: "Disable extension discovery (explicit -e paths still
work)".

This is what lets a harness be isolated and instrumented at the same time.
The opposite behaviour would have forced a choice between the two.

**Cost:** nothing operational — but the *citation* for it was wrong in two
documents until 2026-08-03, pointing at `:267-269`, which is project-trust
code. It was confirmed as exact by one review before a lighter one caught it.
That episode is the reason step 3 of this record's own task exists.

## 4. A spawned subagent child inherits none of the parent's isolation flags

**read.**

Pi's shipped subagent example builds the child's argv as a fixed list, at
`examples/extensions/subagent/index.ts:294-296`:

```ts
const args: string[] = ["--mode", "json", "-p", "--no-session"];
if (agent.model) args.push("--model", agent.model);
if (agent.tools && agent.tools.length > 0) args.push("--tools", agent.tools.join(","));
```

That is the whole of it. No `--no-extensions`, no `--no-skills`, no
`--no-context-files`, no `--no-themes` — whatever the parent was invoked
with. On a machine with ambient extensions in `~/.pi/agent/extensions/`, a
delegated child loads them.

**Cost:** it invalidated an entire cycle's design. The withdrawn
[specialized subagent spec](../specs/2026-08-03-phase3-cycle2-specialized-subagent-design.md)
had assumed a child measured under the parent's isolation.

## 5. `PI_CODING_AGENT_DIR` relocates the agent directory, and spawned children inherit it

**read.** (No note or test pins a run for this one; unlike gotcha 1's linked
note or gotcha 10's named test, there is no pointer to check the run half
against, so the label does not claim it.)

`getAgentDir()` consults the environment before falling back to `~/.pi/agent`
(`config.js:412-417`):

```js
export function getAgentDir() {
    const envDir = process.env[ENV_AGENT_DIR];
    if (envDir) {
        return expandTildePath(envDir);
    }
    return join(homedir(), CONFIG_DIR_NAME, "agent");
}
```

The variable's *name* is not a literal. It is built from the app name at
`config.js:397` — ``const ENV_AGENT_DIR = `${APP_NAME.toUpperCase()}_CODING_AGENT_DIR` `` —
so it reads `PI_CODING_AGENT_DIR` only because `piConfig.name` is unset and
`APP_NAME` falls back to `"pi"` (`config.js:390-392`). A rebranded build reads
a differently named variable. Grepping `dist/` for the literal string finds
only a comment.

Children inherit it because the subagent extension's `spawn` passes **no
`env:`** — `examples/extensions/subagent/index.ts:335-339` sets only `cwd`,
`shell`, and `stdio`, so Node hands the child `process.env` unchanged.

Together these make the one lever that isolates a child whose spawn you do
not control: point the parent at a provisioned agent directory whose
`extensions/` is empty, and the child, inheriting the variable, finds nothing
ambient to load.

## 6. Pointing that variable at an empty directory makes Pi bootstrap

**run only.**

Pi will `git clone` a third-party repository and run npm installs to populate
a missing agent directory.

**This one has no citation, and the absence is the point.** It is not
findable in `dist/` — no amount of reading the compiled source produced the
code path, and the behaviour may well be *settings-dependent* (a bootstrap
configured in the real agent directory this machine already has) rather than
a constant of Pi. It is recorded because it was observed, exactly once, and
because the consequence is expensive; it is not recorded as documented
behaviour, and nothing here should be read as saying every Pi installation
does this.

**Cost:** a five-minute apparent hang that looked like a broken model server —
which is the worst kind of failure, because it points the investigation at
the wrong component. Pre-provision the directory, or do not relocate.

## 7. Project-scope agents are discovered by walking up from cwd

**read.**

`examples/extensions/subagent/agents.ts:85-95`:

```ts
function findNearestProjectAgentsDir(cwd: string): string | null {
	let currentDir = cwd;
	while (true) {
		const candidate = path.join(currentDir, CONFIG_DIR_NAME, "agents");
		if (isDirectory(candidate)) return candidate;

		const parentDir = path.dirname(currentDir);
		if (parentDir === currentDir) return null;
		currentDir = parentDir;
	}
}
```

and it is consulted at `:99`, beside the user-scope directory at `:98`, which
comes from `getAgentDir()` — gotcha 5's function.

So a repo-committed `.pi/agents/` is **invisible** to a process running in a
temp directory, because the walk starts at cwd and never reaches the repo.
The user scope has no such problem, which is why relocating
`PI_CODING_AGENT_DIR` is the way to make an agent findable from a disposable
workspace.

## 8. An agent file without `model:` in its frontmatter spawns a child on Pi's default model

**read.**

`examples/extensions/subagent/index.ts:295` is a plain conditional:

```ts
if (agent.model) args.push("--model", agent.model);
```

No `--model` reaches the child unless the agent file names one. The child
then resolves Pi's configured default.

**Cost:** nothing, because it was caught while writing a spec rather than
after a batch. Had it not been, it would have cost a measurement: a run whose
whole purpose is to characterize a small *local* model, in which the
delegated half silently ran on a cloud one, with the resulting numbers
looking entirely plausible.

## 9. `ctx.ui.notify` has no destination in print mode

**read.**

*This gotcha's own statement is corrected here.* It was previously written as
"no destination under `--no-themes`", in this project's spec, in
[the cycle 1 note](2026-08-02-phase3-cycle1-event-vocabulary.md), and in
[`chapters/hello-agent.md`](../chapters/hello-agent.md) — the
reader-facing chapter, the one most likely to be taken as authoritative
(corrected there 2026-08-03). The
operational conclusion holds — `notify` is not an evidence channel under the
harness's invocation — but the named cause was wrong. `--no-themes` disables
theme *discovery* (`cli/args.js:258`). The no-op UI has nothing to do with it.

The real chain is four hops, all readable:

1. The extension runner's UI context defaults to `noOpUIContext`
   (`core/extensions/runner.js:153`), a table of empty functions whose
   `notify: () => { }` sits at `:92` within the object declared at `:88`.
2. It is replaced only by `setUIContext`, which falls back to the no-op when
   handed `undefined`: `this.uiContext = uiContext ?? noOpUIContext`
   (`core/extensions/runner.js:268`).
3. The only caller is `_applyExtensionBindings`, passing
   `this._extensionUIContext` (`core/agent-session.js:1805`), which is set
   only when `bindExtensions` receives one (`core/agent-session.js:1742-1744`).
4. **Print mode never passes one.** Its `bindExtensions({…})` object spans
   `modes/print-mode.js:50-78` and contains `mode`, `commandContextActions`,
   and `onError` — no `uiContext` key. Interactive mode does:
   `modes/interactive/interactive-mode.js:1218-1219` passes `uiContext`, built
   by `createExtensionUIContext` at `:1674-1679`, whose `notify` routes to
   `showExtensionNotify`.

So it is `--print` that silences `notify`, and it would be silent with themes
fully enabled.

*A second correction, smaller: not the cycle 1 note, which never cites this
line, but [`chapters/hello-agent.md`](../chapters/hello-agent.md) (corrected
there 2026-08-03) and this cycle's own
[extension-mechanics plan, line 236](../plans/2026-08-03-phase3-cycle2-extension-mechanics.md)
cited `modes/interactive/interactive-mode.js:1670` for interactive mode's
"real one." Line 1670 is `notify: ui.notify` inside
`createProjectTrustContext` — a different context, for project-trust prompts,
that merely borrows the same four callbacks. The extension-facing definition
is at `:1679`. The citation resolved to a line containing the word `notify`,
which is exactly how a wrong citation survives a review.*

## 10. An extension's bare imports resolve — but only from a fixed allowlist

**run**, then **read**.

`examples/extensions/word-count.ts` in this repository begins:

```ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";
```

There is no `node_modules` beside it, no `package.json`, and no build step,
and it loads. That was established by running it (Task 1 of this cycle, live
against the model server, `tests/test_extensions.py`) — which is why a
teaching extension in this Python repository needs no Node toolchain.

**The mechanism is narrower than "Pi's module graph", and the correction
matters.** Pi loads extensions through jiti anchored at its own module URL —
`createJiti(import.meta.url, {…})`, `core/extensions/loader.js:325-331` — and
hands it an **explicit alias table** on top of that anchor; the table, not
the anchor, is what guarantees these twenty specifiers. That table is
twenty entries, built at `core/extensions/loader.js:62-108`, and it covers
exactly: `@earendil-works/pi-coding-agent`, `…/pi-agent-core`, `…/pi-tui`,
`…/pi-ai` (plus its `/compat`, `/oauth`, `/providers/all` subpaths), the same
seven again under the legacy `@mariozechner/…` scope, and `typebox` with its
`/compile` and `/value` subpaths — aliased under both the bare name and
`@sinclair/typebox`.

`typebox` works because it is on that list. An arbitrary bare import is not
covered by anything read here, and should not be assumed to resolve.

---

## What this record is not

It is not a summary of
[the cycle 1 event vocabulary note](2026-08-02-phase3-cycle1-event-vocabulary.md).
That note argues, at length, about what an extension can emit and where; this
one is the compact citable form of ten discrete findings, several of which it
established. Where they overlap — gotchas 1, 3, and 9 — the note has the
narrative and the fixture evidence, and this record has the checked citation.
Follow the link rather than trusting a restatement.
