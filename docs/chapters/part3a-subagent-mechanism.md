(part3a-subagent-mechanism)=

# The Subagent Mechanism

In Part II you measured the unsteered SLM — 0/8 on Phase 1 alone. Now you'll
give it help: a specialist implementer that receives a tight packet instead of a
rambling roadmap, and a parent prompted to construct those packets. But first you
need to understand the mechanism that makes delegation possible.

Pi has no runtime subagent primitive. Unlike OpenCode — where a subagent is a
declarative config the runtime enforces — a Pi subagent is a **shipped extension**
you install plus **specialist files** you author. The mechanism comes from Pi's
examples directory; the specialization comes from you.

## What Pi ships

Pi's installed package includes a complete subagent extension at
`examples/extensions/subagent/`. Locate it from the `pi` binary:

```bash
PI_PACKAGE=$(dirname $(dirname $(which pi)))/lib/node_modules/@earendil-works/pi-coding-agent
echo $PI_PACKAGE/examples/extensions/subagent/index.ts
```

The extension is a single 900-line TypeScript file (`index.ts`) with a companion
`agents.ts` for specialist discovery. It also ships sample specialists in
`agents/` and workflow prompt templates in `prompts/`.

## Loading the extension

Pass the extension path to pi:

```bash
pi --extension "$PI_PACKAGE/examples/extensions/subagent/index.ts" \
   --model omlx/gemma-4-12B-it-MLX-8bit \
   --no-extensions
```

The extension registers a `subagent` tool. You can verify it loaded by asking the
model "What tools are available?" — `subagent` should appear in the list.

```{note}
Pi's package resource types are extensions, skills, prompts, and themes.
`agents/*.md` files are **not** installed by `pi install`. Specialists are data
you author, not code that comes with the extension. This is the two-part
structure: mechanism = extension (shipped), specialists = data (you own).
```

## The first delegation — and the first failure

Try a delegation before creating any specialist files:

```
Call the subagent tool with agent: "scout", task: "list the files in the current directory"
```

The model will attempt the call, but the tool responds:

```
Unknown agent: "scout". Available agents: none.
```

The extension's `discoverAgents` function scans for `.md` files in
`~/.pi/agent/agents/` (user-level) and `.pi/agents/` (project-local), searching
upward from the current working directory. With no agent files, discovery comes
back empty. The mechanism works — it just has no specialists to find.

## How the mechanism works

The shipped `index.ts` does three things:

**1. Registers the tool.** `pi.registerTool({ name: "subagent", ... })` makes
`subagent` callable. Its `execute` function is TypeScript that spawns a child pi
process — the delegation itself is just a tool call, observable and governable
through the same event hooks as any tool.

**2. Discovers specialists.** `agents.ts` scans directories for `.md` files with
YAML frontmatter:

```markdown
---
name: my-agent
description: What it does
tools: read, grep, find
model: omlx/gemma-4-12B-it-MLX-8bit
---

System prompt for the agent. The frontmatter is stripped before
passing to the child process via --append-system-prompt.
```

The `name` and `description` fields are required. `tools` restricts the child's
tool surface (passed as `--tools`). `model` overrides the child's model. The body
is the specialist's system prompt.

Scopes:
- `"user"` — only `~/.pi/agent/agents/`
- `"project"` — only `.pi/agents/` (walking up from CWD)
- `"both"` — union, project takes priority on name collision

The **default is `"user"`**. You must pass `agentScope: "both"` on every
delegation to reach project-local specialists.

**3. Spawns the child.** For each delegation, the extension spawns
`pi --mode json -p --no-session` with the specialist's system prompt as
`--append-system-prompt`, the specialist's tools as `--tools`, and the task as a
positional argument. It streams the child's JSONL events, collects usage
statistics, and returns the final output to the parent.

## Creating your first specialist

Create `.pi/agents/scout.md`:

```markdown
---
name: scout
description: Fast codebase recon. Returns what it finds, no analysis.
tools: read, ls, find, grep
model: omlx/gemma-4-12B-it-MLX-8bit
---

You are a scout. Read files, list directories, find patterns.
Report what you find. Do not analyze, suggest, or plan.
```

Now retry the delegation:

```
Call the subagent tool with agent: "scout", agentScope: "both",
task: "list the files in the current directory"
```

The tool discovers the specialist, spawns a child pi process with the scout
prompt and restricted tools, and returns what the scout found.

## What you built

A working subagent delegation. You loaded Pi's shipped extension, authored a
specialist file, and watched the parent dispatch a task to a child process. In
the next chapter you'll author a real implementer specialist and an orchestrator
parent prompt — then measure whether it beats the SP1 baseline.
