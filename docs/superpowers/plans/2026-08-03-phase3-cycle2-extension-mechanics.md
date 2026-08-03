# Phase 3, Cycle 2 — Extension mechanics implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach a contributor how a Pi extension actually works — including `registerTool`, demonstrated with a small extension of our own — and record the gotchas this project has paid to discover.

**Architecture:** Documentation plus one small TypeScript file. Pi's shipped subagent extension is read as a worked example and never enabled. No harness behaviour changes.

**Tech Stack:** Python 3.14, pytest, ruff, pyrefly, Sphinx (MyST), `@earendil-works/pi-coding-agent` 0.82.0.

**Design:** `docs/superpowers/specs/2026-08-03-phase3-cycle2-extension-mechanics-design.md`

## Global Constraints

- Python `>=3.14,<3.15`. No new runtime dependencies. No Node toolchain, no `package.json`, no `tsconfig.json`.
- Gates, all four before any commit: `uv run pytest`, `uv run ruff check .`, `uv run pyrefly check`, `uv run sphinx-build -W -b html docs docs/_build/html`.
- Ruff lint selects `E,F,I,UP,B,SIM`; `E501` ignored. Import sorting enforced.
- **No harness behaviour changes.** `harness/runner.py`, `harness/telemetry.py`, and `harness/checkpoint.py` are not modified. The teaching extension is never added to `EXTENSIONS`.
- **Runs are sequential, never concurrent** — one shared local model has no isolation. Never launch a Pi run while another is in flight, and never abandon one: an orphaned run stays queued and makes the *next* run look hung.
- Model server liveness before any live run: `uv run python -c "from harness.liveness import check_model_server_alive; check_model_server_alive(); print('alive')"`.
- Every new doc must be in a toctree in `docs/superpowers/index.md` or strict Sphinx fails.
- Work happens on branch `phase3` in the worktree at `.worktrees/phase3`.
- Cite installed Pi as `dist/`-relative for `core/`, `modes/`, `cli/` paths, and package-root-relative for `node_modules/` paths. The installed package is at `~/.volta/tools/image/packages/@earendil-works/pi-coding-agent/lib/node_modules/@earendil-works/pi-coding-agent/`.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `examples/extensions/word-count.ts` | The teaching extension: one tool, nothing else | Create |
| `examples/extensions/README.md` | What this directory is, and that the harness never loads it | Create |
| `docs/superpowers/research/2026-08-03-phase3-cycle2-pi-gotchas.md` | The gotchas record | Create |
| `docs/superpowers/chapters/pi-extension-mechanics.md` | The chapter | Create |
| `tests/test_doc_quotes.py` | Quoted code from owned files matches those files | Create |
| `tests/test_extensions.py` | The teaching extension loads and registers under Pi | Create |
| `docs/superpowers/index.md`, `ROADMAP.md` | Indexing and closing the cycle | Modify |

---

## Task 1: The teaching extension

**Files:**
- Create: `examples/extensions/word-count.ts`
- Create: `examples/extensions/README.md`
- Create: `tests/test_extensions.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `examples/extensions/word-count.ts`, an extension registering a single tool named `word_count` taking `{text: string}` and returning the word count as text with `details: {words: number}`. Tasks 2 and 3 quote it.

**This code is verified working**, not sketched: it was run against Pi 0.82.0 and `omlx/gemma-4-12B-it-MLX-8bit` during planning, and the model called the tool. Write it as given.

- [ ] **Step 1: Write the extension**

Create `examples/extensions/word-count.ts`:

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

Three things about this file are load-bearing and belong in the chapter:

- `import { Type } from "typebox"` is a **bare specifier resolved through Pi's own module graph**, not through any `node_modules` beside this file. There is no `node_modules` in this repository and this import works anyway — verified by running.
- `parameters` takes a TypeBox schema (`ToolDefinition.parameters: TParams extends TSchema`, `core/extensions/types.d.ts:355`).
- `execute` returns an `AgentToolResult`: `content` goes to the model, `details` is arbitrary structured data for logs and UI (`node_modules/@earendil-works/pi-agent-core/dist/types.d.ts:310-316`).

- [ ] **Step 2: Write the directory README**

Create `examples/extensions/README.md`:

```markdown
# Teaching extensions

Extensions written to demonstrate one mechanism each. **The harness never
loads these** — `harness/runner.py` loads only `.pi/extensions/hello-world.ts`,
and adding anything here to a run would change its recorded conditions.

Run one by hand:

```bash
pi -e examples/extensions/word-count.ts
```

- `word-count.ts` — registering a tool. One tool, no state, no session
  writes, no child processes. If it grows a second responsibility it has
  stopped being a teaching artifact.
```

- [ ] **Step 3: Write the failing live test**

Create `tests/test_extensions.py`:

```python
"""The teaching extensions load under the installed Pi.

This replaces a type-check. There is no `tsc` and no Node toolchain in this
Python repository, and getting one means either a network install per test
run or a `package.json` plus a TypeScript devDependency. Loading the
extension under Pi tests the real question -- does Pi accept this file --
rather than a proxy for it.

Live-gated: it needs the model server, because the only way to see a tool
actually register is to let a model call it.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WORD_COUNT = REPO_ROOT / "examples" / "extensions" / "word-count.ts"


def test_the_teaching_extension_exists():
    # Not vacuous: the live test below skips without SATYRN_LIVE, so
    # without this the file could vanish and the suite stay green.
    assert WORD_COUNT.is_file()


@pytest.mark.skipif(
    os.environ.get("SATYRN_LIVE") != "1",
    reason="set SATYRN_LIVE=1 to require an actual Pi/model run",
)
def test_the_word_count_extension_registers_its_tool():
    command = [
        "pi", "--print", "--mode", "json", "--no-session",
        "--model", "omlx/gemma-4-12B-it-MLX-8bit",
        "--no-extensions", "--extension", str(WORD_COUNT),
        "--no-skills", "--no-prompt-templates", "--no-themes",
        "--no-context-files", "--approve",
        "Use the word_count tool on the text 'one two three'. "
        "Reply with only the number.",
    ]
    result = subprocess.run(
        command, cwd=tempfile.mkdtemp(), capture_output=True, text=True, timeout=300
    )

    assert "Extension error" not in result.stderr
    called = []
    for line in result.stdout.split("\n"):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "tool_execution_end":
            called.append(event.get("toolName"))
    assert "word_count" in called
```

- [ ] **Step 4: Run the non-live test**

Run: `uv run pytest tests/test_extensions.py -v`
Expected: `test_the_teaching_extension_exists` PASSES, the live test SKIPS.

- [ ] **Step 5: Verify the model server, then run the live test**

Run: `uv run python -c "from harness.liveness import check_model_server_alive; check_model_server_alive(); print('alive')"`
Expected: `alive`.

Then: `SATYRN_LIVE=1 uv run pytest tests/test_extensions.py -v`
Expected: both PASS.

If the model declines to call the tool, that is a prompt problem rather than an extension problem — the `Extension error` assertion already proves the file loaded. Retry once; if it still declines, report rather than loosening the assertion.

- [ ] **Step 6: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
Expected: all pass.

- [ ] **Step 7: Commit**

```bash
git add examples/extensions tests/test_extensions.py
git commit -m "feat(phase3-cycle2): a teaching extension that registers one tool

Demonstrates registerTool concretely, because a chapter explaining it
without a contributor ever running one produces confident wrong beliefs.
Never loaded by the harness.

Verified live: Pi resolves the bare 'typebox' import through its own
module graph, with no node_modules beside the file.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 2: The gotchas record

**Files:**
- Create: `docs/superpowers/research/2026-08-03-phase3-cycle2-pi-gotchas.md`
- Modify: `docs/superpowers/index.md`

**Interfaces:**
- Consumes: the extension from Task 1 (one gotcha is about its import).
- Produces: the record. Task 3's chapter links to it.

- [ ] **Step 1: Write the record**

Create the file. Each gotcha gets: what it is, the file:line citation into installed 0.82.0, a label of **read** or **run** for how it was established, and **what it cost us** — a price makes a gotcha memorable and its absence makes one skimmable.

The ten to include, all already paid for:

1. **The json-mode stdout subscriber attaches after `session_start` is emitted and awaited.** `modes/print-mode.js:50` and `:80`; `core/agent-session.js:1766`; `_emit` iterates synchronously with no replay at `:285-289`. **read**, confirmed **run**. Cost: 80 recorded runs producing nothing observable, and a wrong recorded cause that survived until a run disagreed.
2. **`--approve` is not an isolation flag.** "Trust project-local files for this run", `cli/args.js:263`. It widens trust. What excludes a model-written `.pi/extensions/*.ts` is `--no-extensions`. **read**. Cost: a flag sat in the harness's "isolation flags" list for two phases with its meaning inverted.
3. **`--no-extensions` spares explicitly passed `--extension` paths.** `core/resource-loader.js:315-317`, and again at `:408-410`; help text at `cli/args.js:252`. **read**. Cost: nothing yet — but the citation for it was wrong in two documents until 2026-08-03, pointing at project-trust code.
4. **A spawned subagent child inherits none of the parent's isolation flags.** `examples/extensions/subagent/index.ts:294` — `["--mode","json","-p","--no-session"]`, plus the agent's model and tools. **read**. Cost: it invalidated a whole cycle's design.
5. **`PI_CODING_AGENT_DIR` relocates the agent directory, and spawned children inherit it.** `dist/config.js:411-417`; the extension's `spawn` passes no `env:`. **read**, confirmed **run**.
6. **Pointing that variable at an empty directory makes Pi bootstrap.** It `git clone`s a third-party repository and runs npm installs. **run only** — this is not findable in `dist/`, and it may be settings-dependent rather than a constant of Pi. Cost: a five-minute apparent hang that looked like a broken model server.
7. **Project-scope agents are discovered by walking up from cwd.** `examples/extensions/subagent/agents.ts:85-99`. A repo-committed `.pi/agents/` is invisible to a process running in a temp directory. **read**.
8. **An agent file without `model:` in its frontmatter spawns a child on Pi's default model.** `examples/extensions/subagent/index.ts:295` — `if (agent.model)`. **read**. Cost: nothing, because it was caught while writing a spec; it would have cost a measurement of a local model silently acquiring a cloud one.
9. **`ctx.ui.notify` has no destination under `--no-themes`.** Print mode supplies a no-op UI context, `core/extensions/runner.js:88-92`; interactive mode supplies a real one, `modes/interactive/interactive-mode.js:1670`. **read**.
10. **An extension's bare imports resolve through Pi's module graph.** `import { Type } from "typebox"` works from a file in this repository with no `node_modules` beside it. **run**. This is why a teaching extension needs no build step.

Add a short preamble stating the read/run convention and why it exists: this project's recurring injury is claims justified by reading alone, so every claim here says which it is.

- [ ] **Step 2: Add to the toctree and the visible list**

In `docs/superpowers/index.md`, add to the `:caption: Research` toctree:

```
research/2026-08-03-phase3-cycle2-pi-gotchas
```

and a matching bullet in the visible `## Research` list, following its neighbours' style.

- [ ] **Step 3: Verify each citation resolves**

For every `file:line` in the record, open that file at that line in the installed package and confirm it says what the record claims. This is not optional and it is not a formality: a wrong citation shipped in two documents for a full cycle, and a review confirmed it as exact.

Fix anything that does not resolve, and if a claim turns out to be wrong rather than merely miscited, change the claim.

- [ ] **Step 4: Verify the docs build**

Run: `rm -rf docs/_build && uv run sphinx-build -W -b html docs docs/_build/html`
Expected: `build succeeded.`

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/research/2026-08-03-phase3-cycle2-pi-gotchas.md docs/superpowers/index.md
git commit -m "docs(phase3-cycle2): the Pi gotchas record

Ten findings this project paid to discover, each with a citation into
installed 0.82.0, each labelled read or run, and each with what it cost.
A gotcha with a price attached is remembered; one without is skimmed.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 3: The chapter

**Files:**
- Create: `docs/superpowers/chapters/pi-extension-mechanics.md`
- Modify: `docs/superpowers/index.md`

**Interfaces:**
- Consumes: the extension from Task 1, the record from Task 2.
- Produces: the chapter. Task 4's test checks its quoted blocks.

- [ ] **Step 1: Read the existing chapter first**

Read `docs/superpowers/chapters/hello-agent.md` in full. It already covers what an extension is, the seven-handler lifecycle, `notify`'s silence, and the subscribe-ordering finding. **This chapter must not repeat it.** Where they overlap, link.

- [ ] **Step 2: Write the chapter**

Create `docs/superpowers/chapters/pi-extension-mechanics.md`, covering, in this order:

- **How Pi finds an extension** — user scope (`~/.pi/agent/extensions/`), project scope (`.pi/extensions/`), and an explicit `--extension` path; which of those `--no-extensions` suppresses and which it spares, with the corrected citation.
- **Registering a tool**, taught from `examples/extensions/word-count.ts`. Quote the file. Explain `name`, `label`, `description`, `parameters`, and `execute`'s return — `content` goes to the model, `details` does not. Say that the `typebox` import needs no install and why.
- **Running it by hand** — `pi -e examples/extensions/word-count.ts`, and what the tool call looks like in `--mode json`.
- **Pi's shipped subagent extension, read as a worked example.** Where it is; that it is ~1015 lines of which roughly 410 are TUI renderers dead under `--no-themes`; how it registers its tool, discovers agent files, and spawns a child `pi`. **State plainly that this project does not enable it**, and link the withdrawn spec for why. The contributor skill being taught is *reading* a real extension.
- **The gotchas**, summarised in a sentence each with a link to the record rather than restated in full.

Honour `BRIEF.md`'s concept budget: a 5–10 h/wk contributor must be able to absorb it. Cite installed Pi by file:line for every behavioural claim, and do not assert anything you have not checked.

- [ ] **Step 3: Add to the toctree and the Chapters list**

In `docs/superpowers/index.md`, add `chapters/pi-extension-mechanics` to the `:caption: Chapters` toctree, and a bullet to the visible `## Chapters` list beside "Hello, agent".

- [ ] **Step 4: Verify the docs build**

Run: `rm -rf docs/_build && uv run sphinx-build -W -b html docs docs/_build/html`
Expected: `build succeeded.`

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/chapters/pi-extension-mechanics.md docs/superpowers/index.md
git commit -m "docs(phase3-cycle2): the extension mechanics chapter

How Pi finds an extension, how registerTool works with a worked example a
contributor can run, and Pi's shipped subagent extension read rather than
adopted -- reading a real extension is the skill being taught.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 4: The quote check, and closing the cycle

**Files:**
- Create: `tests/test_doc_quotes.py`
- Modify: `ROADMAP.md`, `docs/superpowers/index.md`

**Interfaces:**
- Consumes: the chapter from Task 3, the extension from Task 1.
- Produces: the finished cycle.

**The boundary this test draws is the point.** It checks quoted code from files *this project owns*, in chapters and research notes only. It deliberately does **not** check quotations from installed Pi: such a test would fail on any contributor whose Pi differs, for a reason they cannot fix in this repository, and would turn a routine upgrade into a red suite with no in-repo remedy. What guards those instead is a version pin in the prose and the read/run labels in the gotchas record — weaker, and the docstring must say so.

- [ ] **Step 1: Write the failing test**

Create `tests/test_doc_quotes.py`:

```python
"""Code quoted from files this project owns must match those files.

**What a green run does and does not mean.** It means every fenced block in
a checked document that was declared to come from one of this project's own
files appears verbatim in that file. It does NOT mean the document is
correct: quotations from the installed Pi package are deliberately not
checked here, because a test asserting on a third-party file's contents
would fail on any contributor whose Pi version differs, for a reason they
could not fix in this repository. Those claims are guarded only by the
version stated in the prose and by the read/run labels in the gotchas
record -- which is weaker, and is said here rather than implied.

Only chapters and research notes are checked -- specs and plans are
historical records that quote code as it was proposed, and gating them
would force rewriting history. A block is checked when the paragraph
introducing it names a repository path. That keeps the convention visible in the prose a reader sees, rather
than in a marker only the test knows about.
"""

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# Only the living teaching documents. Specs and plans are historical
# records: they quote code as it was *proposed*, and a plan whose snippet
# no longer matches the file is accurate about what was planned, not
# wrong. Gating them would force either rewriting history or watering
# this check down to nothing.
CHECKED_DIRS = (
    REPO_ROOT / "docs" / "superpowers" / "chapters",
    REPO_ROOT / "docs" / "superpowers" / "research",
)

# A fenced block, plus the text just before it, so we can see which file
# the prose said it came from.
_BLOCK = re.compile(r"(?P<intro>[^\n]*)\n+```[a-z]*\n(?P<body>.*?)```", re.DOTALL)
_OWNED = re.compile(r"`((?:examples|harness|tests|\.pi)/[\w./-]+)`")


def quoted_blocks(text: str) -> list[tuple[str, str]]:
    """Return (repo_path, quoted_body) for blocks introduced by a repo path."""
    found = []
    for match in _BLOCK.finditer(text):
        owned = _OWNED.search(match.group("intro"))
        if owned:
            found.append((owned.group(1), match.group("body")))
    return found


def test_the_extractor_finds_a_block_introduced_by_a_repo_path():
    text = "See `harness/runner.py`:\n\n```python\nx = 1\n```\n"

    assert quoted_blocks(text) == [("harness/runner.py", "x = 1\n")]


def test_the_extractor_ignores_a_block_with_no_repo_path():
    text = "Some prose:\n\n```python\nx = 1\n```\n"

    assert quoted_blocks(text) == []


def _documents() -> list[Path]:
    return sorted(doc for directory in CHECKED_DIRS for doc in directory.glob("*.md"))


def _checkable() -> list[tuple[Path, str, str]]:
    cases = []
    for doc in _documents():
        for repo_path, body in quoted_blocks(doc.read_text()):
            source = REPO_ROOT / repo_path
            if source.is_file():
                cases.append((doc, repo_path, body))
    return cases


def test_at_least_five_blocks_are_checked():
    # Without this, a regression in the extractor would make every
    # parametrised case below vanish and the suite still pass -- the
    # failure mode tests/test_research_records.py guards the same way.
    assert len(_checkable()) >= 5


@pytest.mark.parametrize(
    ("doc", "repo_path", "body"),
    _checkable(),
    ids=lambda value: value.name if isinstance(value, Path) else "",
)
def test_a_quoted_block_matches_its_source(doc: Path, repo_path: str, body: str):
    source = (REPO_ROOT / repo_path).read_text()

    assert body.strip() in source, (
        f"{doc.name} quotes {repo_path}, but that text is not in the file"
    )
```

- [ ] **Step 2: Run it and expect real failures**

Run: `uv run pytest tests/test_doc_quotes.py -v`

Expected: the two extractor tests PASS. The parametrised cases will likely include some that FAIL — existing chapters quote files with elisions or reflowed whitespace.

**Each failure is a decision, not a nuisance.** For each one, either fix the document so its quotation is verbatim, or reword the introducing prose so it no longer claims to be quoting that file. Do not weaken the assertion to make failures disappear — that would convert a real check into a decorative one. If `test_at_least_five_blocks_are_checked` fails, the extractor is too strict; fix the extractor.

- [ ] **Step 3: Run the full gates**

Run: `uv run pytest && uv run ruff check . && uv run pyrefly check`
then `rm -rf docs/_build && uv run sphinx-build -W -b html docs docs/_build/html`
Expected: all pass, `build succeeded.`

- [ ] **Step 4: Close the cycle in the roadmap**

In `ROADMAP.md`, change the Phase 3 cycle 2 row's **State** from `Specced` to `Done`, and add a link to this plan beside the existing spec link.

- [ ] **Step 5: Add this plan to the toctree**

In `docs/superpowers/index.md`, add to the `:caption: Plans` toctree:

```
plans/2026-08-03-phase3-cycle2-extension-mechanics
```

- [ ] **Step 6: Verify the docs build and commit**

Run: `rm -rf docs/_build && uv run sphinx-build -W -b html docs docs/_build/html`
Expected: `build succeeded.`

```bash
git add tests/test_doc_quotes.py ROADMAP.md docs/superpowers/index.md docs/superpowers/chapters
git commit -m "test(phase3-cycle2): quoted code from our own files must match

Checks fenced blocks whose introducing prose names a repository path.
Quotations from installed Pi are deliberately not checked: that test would
fail on any contributor whose Pi differs, for a reason they could not fix
here. Those claims are guarded by a version pin and a read/run label
instead, which is weaker, and the docstring says so.

Closes Phase 3 cycle 2.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Done when

- `examples/extensions/word-count.ts` registers one tool, a live run shows a model calling it, and the harness still loads only `hello-world.ts`
- The gotchas record documents ten findings, each cited into installed 0.82.0, each labelled **read** or **run**, each with what it cost
- Every citation in the record resolves to what it claims
- The chapter teaches extension discovery, `registerTool` from a runnable example, and the shipped subagent extension read rather than adopted
- Quoted code from this project's own files is checked, and the boundary excluding installed Pi is stated rather than implied
- No file in `harness/` changed
- All four gates pass
