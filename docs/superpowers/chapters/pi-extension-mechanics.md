# Extension mechanics

[Hello, agent](hello-agent.md) answered *what is a Pi extension* by reading the
one this project runs. This chapter answers the three questions that come next
and are not covered there:

1. **How does Pi find an extension at all?**
2. **How do you give the model a new tool?** — taught from a 20-line file you
   can run.
3. **What does a real, large extension look like?** — Pi ships one, and reading
   it is the skill.

Nothing here repeats the lifecycle handlers, `notify`'s silence, or the
subscribe-ordering finding. Those are in the previous chapter; where this one
touches them it links.

Everything below cites the installed Pi **0.83.0** by file and line. Paths
beginning `core/`, `modes/`, `cli/` are relative to the installed package's
`dist/` directory. `examples/extensions/subagent/…` is relative to the package
*root* — it is shipped TypeScript, and it sits beside `dist/`, not inside it.
`pi-agent-core/…` likewise sits beside `dist/`, nested one level down in the
package's own `node_modules/`.

```text
~/.volta/tools/image/packages/@earendil-works/pi-coding-agent/
  lib/node_modules/@earendil-works/pi-coding-agent/
```

## How Pi finds an extension

There are three ways in, and they behave differently.

| Way in | Where | Survives `--no-extensions`? |
|---|---|---|
| User scope | `~/.pi/agent/extensions/` | no |
| Project scope | `<cwd>/.pi/extensions/` | no |
| Explicit path | `pi -e <path>` | **yes** |

**User scope** is `agentDir/extensions/`, where `agentDir` is `~/.pi/agent`
unless relocated. That directory is scanned unconditionally
(`core/package-manager.js:1930` for the path, `:1973` for the scan); the
`agentDir` it is joined onto is `this.agentDir` (`:709`), which comes from
`getAgentDir()` (`config.js:412-417`).

**Project scope** is `<cwd>/.pi/extensions/` (`core/package-manager.js:1936`,
built from `join(this.cwd, CONFIG_DIR_NAME)` at `:710`). Unlike user scope it
is **conditional**: the scan sits inside `if (projectTrusted)` at `:1953-1955`,
and `projectTrusted` is
`this.settingsManager.isProjectTrusted()` (`:1942`). That is the flag
`--approve` sets — "Trust project-local files for this run"
(`cli/args.js:263`). So `--approve` is not a hardening flag; it *widens* what
gets loaded. [Hello, agent](hello-agent.md) has the same warning attached to
this harness's argv, and `harness/runner.py:122-126` carries it as a comment
beside the flag.

**An explicit path** is `--extension <path>`, short form `-e`, and it may be
repeated (`cli/args.js:251`).

`--no-extensions` (short `-ne`) suppresses **discovery only**. Pi's own help
says so — "Disable extension discovery (explicit -e paths still work)"
(`cli/args.js:252`) — and the code agrees:

```js
const extensionPaths = this.noExtensions
    ? cliEnabledExtensions
    : this.mergePaths(cliEnabledExtensions, enabledExtensions);
```

— `core/resource-loader.js:315-317`, and verbatim again at `:408-410`.
`noExtensions` is used nowhere else in that file beyond the field declaration
and constructor assignment that store the option (`:120`, `:169`). The explicitly-passed paths
are kept; the discovered ones are dropped.

That combination is the whole reason this project's harness can be both
isolated and instrumented: `--no-extensions` closes the two discovery doors, and
`--extension` walks its own instrument in through the third.

A discovered directory yields `*.ts` and `*.js` files, plus subdirectories that
declare an entry point (`core/extensions/loader.js:489-509`). An extension is
therefore one file, or one directory — not necessarily a package.

## Registering a tool

`registerTool` is how an extension gives the model something new to call. Here
is the entire teaching example, `examples/extensions/word-count.ts` in this
repository:

```typescript
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "word_count",
    label: "Word count",
    description: "Count the words in a piece of text.",
    parameters: Type.Object({
      text: Type.String({ description: "Text to count the words in" }),
    }),
    async execute(_toolCallId, params) {
      const words = params.text.trim().split(/\s+/).filter(Boolean).length;
      return {
        content: [{ type: "text", text: String(words) }],
        details: { words },
      };
    },
  });
}
```

Twenty lines, and every one of the five required fields is in there. Pi's own
type declares them, with comments (`core/extensions/types.d.ts:343-375`):

- **`name`** — "Tool name (used in LLM tool calls)" (`:345`). This is the
  string the model emits. Keep it in the shape other tool names take.
- **`label`** — "Human-readable label for UI" (`:347`). Never seen by the
  model.
- **`description`** — "Description for LLM" (`:349`). This *is* seen by the
  model, and it is the only thing telling it when to reach for the tool. It is
  prompt text, not a docstring.
- **`parameters`** — "Parameter schema (TypeBox)" (`:355`). A schema built with
  `Type.*`, describing the arguments. The per-field `description` is read by
  the model too.
- **`execute`** — the function that runs (`:371`). Its first argument is the
  tool-call id, its second the validated parameters. `word-count.ts` ignores
  the first, hence the leading underscore.

### `content` goes to the model; `details` does not

The return value is an `AgentToolResult`, and its first two fields have
different audiences. Pi's type says it outright
(`node_modules/@earendil-works/pi-agent-core/dist/types.d.ts:310-314`):

```ts
export interface AgentToolResult<T> {
    /** Text or image content returned to the model. */
    content: (TextContent | ImageContent)[];
    /** Arbitrary structured details for logs or UI rendering. */
    details: T;
```

So `word_count` hands the model the string `"3"`, and puts the machine-readable
`{ words: 3 }` in `details`. The consumer of `details` is `renderResult`, an
optional display hook on the same tool definition
(`core/extensions/types.d.ts:375`).

This is worth internalising before you write a tool that matters. Anything you
put in `content` becomes context the model must read and pay for. Anything you
put in `details` does not.

### The `typebox` import needs no install

There is no `node_modules` beside `word-count.ts`, no `package.json`, and no
build step — and `import { Type } from "typebox"` resolves anyway.

That is not TypeScript magic and it is not "Pi's module graph". Pi loads
extensions through jiti anchored at its own module URL
(`core/extensions/loader.js:325-331`) and hands it an **explicit alias table**
built at `core/extensions/loader.js:62-108`. The table has twenty entries.
`typebox` is one of them, aliased under both the bare name and
`@sinclair/typebox`, along with the `/compile` and `/value` subpaths. The rest
are Pi's own packages under two scopes.

The practical rule: **the twenty specifiers on that list resolve; nothing else
is promised.** An arbitrary bare import is not covered by anything readable
here, and should not be assumed to work. This is
[gotcha 10](../research/2026-08-03-phase3-cycle2-pi-gotchas.md), and it is the
reason a teaching extension can live in a Python repository with no Node
toolchain at all.

`import type { ExtensionAPI }` is a *type-only* import, erased before anything
runs, so it needs nothing from that table — but it is on it regardless.

## Running it by hand

```bash
pi -e examples/extensions/word-count.ts
```

Then ask for a word count. In an interactive session you will see the tool run.

Under `--mode json` there is no UI; every event the session emits is serialized
to stdout instead (`modes/print-mode.js:80-84`). A tool call shows up as a pair
of lines. Here is that pair for the built-in `bash` tool, verbatim from
`tests/fixtures/pi-run-0.82.0-entry-appended.jsonl` lines 12 and 14:

```json
{"type":"tool_execution_start","toolCallId":"call_434c6318","toolName":"bash","args":{"command":"mkdir -p templates tests"}}
{"type":"tool_execution_end","toolCallId":"call_434c6318","toolName":"bash","result":{"content":[{"type":"text","text":"(no output)"}]},"isError":false}
```

A registered tool appears in exactly that shape, with `toolName` set to the
`name` you gave it. That is what `tests/test_extensions.py` checks: it runs
`word-count.ts` against the live model server and asserts that some
`tool_execution_end` line carries `"toolName": "word_count"`. The fixture pair
above is from a built-in tool because no `word_count` capture is committed —
the run happens live, under `SATYRN_LIVE=1`, and is not recorded.

The full invocation that test uses is the harness's own, minus the harness:

```text
pi --print --mode json --no-session --model <model> --no-extensions
   --extension examples/extensions/word-count.ts
   --no-skills --no-prompt-templates --no-themes --no-context-files
   --approve <prompt>
```

`--no-extensions` beside `--extension` is the pattern from the table above, not
a contradiction.

## Reading Pi's shipped subagent extension

**This project does not enable this extension, and is not going to.** The
design that would have used it was
[approved and withdrawn on the same day](../specs/2026-08-03-phase3-cycle2-specialized-subagent-design.md),
when the owner asked whether Phase 3 should be getting into orchestration at
all. It should not have been. Read that spec for the argument.

What survives is the reading. This is the largest extension anyone ships with
Pi, and being able to open a real one and find your way around it is a skill
worth more than any single fact in it.

It lives at `examples/extensions/subagent/` in the package root, next to
`dist/`: `index.ts` (1015 lines), `agents.ts` (126 lines), a `README.md`, and
`agents/` and `prompts/` directories.

**First: most of it is display code.** `renderCall` and `renderResult` run from
`index.ts:700` to `:1013` — 314 lines, close to a third of the file — and they
are the tool's terminal-UI rendering. They never run in print mode.
`renderCall` has two consumers in `dist/` outside the built-in tools:
`modes/interactive/components/tool-execution.js:59-64`, the interactive-mode
renderer, and `core/export-html/tool-renderer.js:58-65`, reached only through
`--export` (`cli/args.js:260`), which converts a saved session file to HTML
after the fact. Neither runs during `--print` — one is interactive-only, the
other a separate offline conversion — so the display code still never
executes in the print-mode path this chapter cares about. About a hundred more
lines of display formatting at `:38-137` feed them. **Skip them on a first read.** A
large extension is not necessarily a complicated one; this one is a moderate
tool wearing a large coat.

**Second: it is the same shape as `word-count.ts`.** One default export
(`index.ts:460`), one `registerTool` call (`:461`), the same five fields
(`:462-470`), and the same `execute` (`:472`). Everything in this chapter's
previous section applies unchanged. It only *looks* different because its
`parameters` schema is built up from named pieces above it (`:448-458`) instead
of inline.

**Third: how it finds agents.** An "agent" here is a markdown file with
frontmatter. `agents.ts:97-99` looks in two places: a user directory,
`getAgentDir()/agents` — the same `getAgentDir()` that decides where extensions
are discovered from — and a project directory found by walking **up** from the
current working directory:

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

— `agents.ts:85-95`. Walking up from cwd means a repo-committed `.pi/agents/`
is invisible to a process running in a temporary directory, which is exactly
how this project runs everything.

**Fourth: how it spawns a child.** It builds an argv and runs another `pi`:

```ts
const args: string[] = ["--mode", "json", "-p", "--no-session"];
if (agent.model) args.push("--model", agent.model);
if (agent.tools && agent.tools.length > 0) args.push("--tools", agent.tools.join(","));
```

— `index.ts:294-296`, then `spawn(invocation.command, invocation.args, {…})` at
`:335-339` passing only `cwd`, `shell`, and `stdio`.

Read that fixed list closely, because two things follow from it and neither is
obvious:

- **The child inherits none of the parent's isolation flags.** No
  `--no-extensions`, no `--no-skills`, no `--no-context-files`, whatever the
  parent was invoked with. On a machine with extensions in
  `~/.pi/agent/extensions/`, the child loads them. That is the finding that
  invalidated the withdrawn design.
- **It inherits the parent's environment entirely**, because `spawn` is passed
  no `env:` and Node then hands over `process.env` unchanged.

Those two together are worth the whole reading exercise. A fixed argv is easy
to skim past and it decides what a delegated run is actually measuring.

## The gotchas, in one line each

Ten things this project paid to learn about Pi are recorded, with citations and
with what each one cost, in
[the Pi gotchas record](../research/2026-08-03-phase3-cycle2-pi-gotchas.md).
Summarised, not restated — follow the link rather than trusting the summary:

1. **In `--mode json`, the stdout subscriber attaches *after* `session_start`.**
   Anything emitted from a `session_start` handler is dropped. Cost: 80 inert
   runs. Covered at length in [Hello, agent](hello-agent.md).
2. **`--approve` widens trust, it does not narrow it.** It is what turns
   project-scope discovery on.
3. **`--no-extensions` spares explicit `-e` paths.** The table above.
4. **A spawned subagent child inherits none of the parent's isolation flags.**
5. **`PI_CODING_AGENT_DIR` relocates the agent directory, and children inherit
   it** — the one lever that isolates a child whose spawn you do not control.
6. **Pointing that variable at an empty directory makes Pi bootstrap** — a
   `git clone` and npm installs, observed once, with no citation, and the
   record says so plainly.
7. **Project-scope agents are discovered by walking up from cwd**, so a
   committed `.pi/agents/` is invisible from a temp workspace.
8. **An agent file with no `model:` spawns a child on Pi's default model** —
   which could silently put a cloud model inside a local-model measurement.
9. **`ctx.ui.notify` is silenced by `--print`, not by `--no-themes`.** The
   record corrected this one, and [Hello, agent](hello-agent.md) carries the
   correction too.
10. **An extension's bare imports resolve from a fixed twenty-entry table.**
    The `typebox` section above.

Numbers 3, 4, 5, 7, 8, and 10 are the ones this chapter used directly. The
record has the citation for each, and a **read** or **run** label saying whether
anyone watched it happen.
