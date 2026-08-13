# Phase 9 — Engine Onboarding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the engine adoptable by a Python developer running a small local model in Pi: a one-file install that puts the guards in every session, a README whose setup section serves both the engine and the evals, a `docs/engine/` section, and an honest pilot number for what the guards change.

**Architecture:** Four cycles, one commit each. (1) `.pi/extensions/engine.ts` — a self-contained Pi extension inlining the two existing guards' policy plus a thin adapter, pinned against the guard sources by test. (2) README rebuilt into four parts (why; the engine; shared setup; the evals). (3) `docs/engine/` user-facing pages (`index.md`, `architecture.md`) wired into Sphinx. (4) A small harness seam (`ENGINE_IMPROVEMENT`) plus a pilot comparison of with-engine versus without on one suite, written up as pilot evidence.

**Tech Stack:** TypeScript (bun test, jiti-loaded Pi extensions), Python (harness, pytest, ruff, pyrefly), Sphinx docs. No new dependencies — nothing added to `pyproject.toml`.

**Spec:** [`docs/superpowers/specs/2026-08-13-phase9-engine-onboarding-design.md`](../specs/2026-08-13-phase9-engine-onboarding-design.md)

## Global Constraints

(Copy these verbatim into review — every task inherits them.)

- **No new dependencies.** Nothing added to `pyproject.toml`; jiti (Pi's loader) does the rest — no bundler, no compile step.
- **No new guards; no executor changes.** The bundle ships `loop-breaker` and `preserve-symbols` as they exist; `deliver_candidate`'s `IMPLEMENTER_EXTENSION_CLOSURE`, its digest-pinned tests, and `harness/cell_resolution.py` are untouched.
- **The bundle lives at `.pi/extensions/engine.ts`.** Not `extensions/engine.ts`; the `extensions/guards/*` sources stay exactly where they are and remain what the executor closure imports.
- **Phase 8 seams respected.** No registry/CLI work here; the README eval section documents what exists today and does not pre-empt Phase 8's `harness.cli` or `docs/evals.md`.
- **Quality gates green before commit:** `uv run ruff check .`, `uv run ruff format --diff`, `uv run pyrefly check`, `uv run pytest`, `bun test`, and Sphinx `-W` clean.
- **Working style:** branch `engine-onboarding` off `main`, worktree in `.worktrees/`. One commit per task, test-first, messages in repo style (`feat(phase9): …`, `docs(phase9): …`).
- **Verify, don't assert.** Every claim is tested or recorded, never asserted.

---

### Task 1: The engine bundle — `.pi/extensions/engine.ts`

**Files:**
- Create: `.pi/extensions/engine.ts` (self-contained extension; ~300 lines)
- Modify: `extensions/guards/guards.test.ts` (add an "engine bundle artifact" `describe` block)

**Interfaces:**
- Consumes: `extensions/guards/loop-breaker.ts` exports `WINDOW = 20`, `THRESHOLD = 5`, `callKey(toolName, input)`, `createLoopBreaker(window?, threshold?) → Guard`; `extensions/guards/preserve-symbols.ts` exports `symbolsIn(text)`, `deletedSymbols(input)`, `createPreserveSymbols() → Guard`; `extensions/guards/types.ts` exports `ToolCall`, `Block`, `Decision`, `Guard`; the Pi SDK type `ExtensionAPI`.
- Produces: `.pi/extensions/engine.ts` — a module whose **default export is `function (pi: ExtensionAPI)`** (the Pi extension factory) that registers `loop-breaker` and `preserve-symbols` on `tool_call`; module-level exports `WINDOW`, `THRESHOLD`, `callKey`, `createLoopBreaker`, `createPreserveSymbols` so tests can pin agreement with the sources. Installable by `cp .pi/extensions/engine.ts ~/.pi/agent/extensions/`.

- [ ] **Step 1: Write the failing artifact tests**

Append a new `describe("the engine bundle artifact", ...)` block to `extensions/guards/guards.test.ts`, after the existing "the two loop-breaker artifacts" block. It imports the artifact by file URL (the same mechanism `tools/replay_guards.mjs` uses):

```ts
import { pathToFileURL } from "node:url";
import { readFile } from "node:fs/promises";

const ENGINE = new URL("../../.pi/extensions/engine.ts", import.meta.url);
const ENGINE_SOURCE = await readFile(ENGINE, "utf8");
const engineModule = await import(ENGINE.href);

const loopFixture = { toolName: "bash", input: { command: "ls -R" } };
function fakePi() {
	const handlers = new Map<string, (event: any) => unknown>();
	const entries: Array<[string, unknown]> = [];
	const pi = {
		on: (event: string, handler: (event: any) => unknown) => {
			handlers.set(event, handler);
		},
		appendEntry: (kind: string, data: unknown) => {
			entries.push([kind, data]);
		},
	} as any;
	return { pi, handlers, entries };
}
```

Tests (each a `test(...)`):

- `"the artifact stays free of local imports"` — assert `ENGINE_SOURCE` has no `import` line whose specifier starts with `./` or `../` (mirror the existing loop-breaker test at "the standalone extension stays free of local imports").
- `"the artifact's constants agree with the Guard sources"` — assert `engineModule.WINDOW === WINDOW` and `engineModule.THRESHOLD === THRESHOLD`, importing `WINDOW`/`THRESHOLD` from `./loop-breaker` (already imported at the top of the file).
- `"the artifact's loop breaker fires on the repeated call and reasons like the Guard"` — drive both the artifact's `createLoopBreaker()` and the source's `createLoopBreaker()` through the same sequence: 5 admitted calls of `loopFixture`, then the 6th must return `{ block: true }` (`THRESHOLD = 5` admits the first five; the fixture `loop-breaker-runaway.json` confirms 6 calls → 1 block); assert both `reason` strings are identical.
- `"the artifact's preserve-symbols fires on the recorded destructive edit and stays silent on the additive edit"` — the `destructive`/`additive` edit objects are declared inside the existing "preserve-symbols" `describe` block, so redeclare them (copy them verbatim) in this block; drive the artifact's `createPreserveSymbols()` and assert the same decisions as the source's (`destructive` blocks with `deleted` equal to `["function:about", "route:/about"]`; `additive` returns `undefined`), and that the `reason` strings are identical.
- `"the default export registers both guards on tool_call"` — `engineModule.default(fakePi().pi)`; assert `handlers.has("tool_call")`; then with a fresh fake pi, call the registered handler 6 times with `loopFixture`; assert the 6th call's return is `{ block: true }` with a `reason` containing "You have already run this exact bash call", and `entries` contains one `["loop_broken", ...]`. Then drive a fresh fake pi with the destructive-edit event once; assert the return is `{ block: true }` and `entries` has one `["symbol_preserved", ...]`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `bun test extensions/guards/guards.test.ts`
Expected: FAIL — the import of `.pi/extensions/engine.ts` throws (`ERR_MODULE_NOT_FOUND` / `ENOENT`), and the constant-agreement tests fail because the module has no `WINDOW`/`THRESHOLD` exports.

- [ ] **Step 3: Create `.pi/extensions/engine.ts`**

A single self-contained file. Assemble it in three parts:

**Part A — types (inlined from `extensions/guards/types.ts`).** Copy `ToolCall`, `Block`, `Decision`, `Guard` verbatim. These are interfaces/types only — no runtime cost.

**Part B — the two guards' policy, copied verbatim from the sources.** Copy from `extensions/guards/loop-breaker.ts`: `WINDOW`, `THRESHOLD`, `callKey`, `createLoopBreaker`, and any local helpers they call (including `describe`/`stable` helpers, `FoundSymbol`-style local types). Copy from `extensions/guards/preserve-symbols.ts`: `EDIT_TOOLS`, `SYMBOL_PATTERNS`, `FoundSymbol`, `EditPayload`, `symbolsIn`, `deletedSymbols`, the `describe` helper, `createPreserveSymbols`. Delete their `import type { ... } from "./types"` lines — the types are now inlined above. Do not rename anything; the pinning tests in Step 1 compare `reason` strings and constants against the sources, so the copies must be byte-faithful in behavior.

**Part C — the adapter.** At the bottom:

```ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const loopBreaker = createLoopBreaker();
const preserveSymbols = createPreserveSymbols();
const GUARDS: Guard[] = [loopBreaker, preserveSymbols];

export default function (pi: ExtensionAPI) {
	pi.on("tool_call", async (event) => {
		const call: ToolCall = {
			toolName: event.toolName,
			input: event.input,
			target:
				event.input && typeof event.input === "object" && "path" in event.input
					? (event.input as { path?: string }).path ?? null
					: null,
		};
		for (const guard of GUARDS) {
			const decision = guard.inspect(call);
			if (decision?.block) {
				pi.appendEntry(decision.entry.kind, decision.entry.data);
				return { block: true, reason: decision.reason };
			}
		}
	});
}
```

Notes: the `import type { ExtensionAPI }` line is the artifact's **only** import — Part B inlines everything else, which is what "stays free of local imports" pins. Module-level `const loopBreaker = createLoopBreaker()` is safe at import time (the pure factories hold no Pi reference; registration happens only when the default factory runs, exactly like the loop-breaker standalone today). The refusal text must be identical to the sources — the Step 1 tests assert it.

- [ ] **Step 4: Run the artifact tests to verify they pass**

Run: `bun test extensions/guards/guards.test.ts`
Expected: PASS, including the new "engine bundle artifact" block. Then run the whole bun suite: `bun test extensions/` — all green (the existing guard and orchestration tests must not regress).

- [ ] **Step 5: Run the Python suite**

Run: `uv run pytest -q`
Expected: all green (495+ tests; the 4 live-model skips stay skipped). The bundle must not disturb `deliver_candidate`'s closure tests or anything else.

- [ ] **Step 6: Commit**

```bash
git add .pi/extensions/engine.ts extensions/guards/guards.test.ts
git commit -m "feat(phase9): ship the engine bundle as a one-file extension"
```

---

### Task 2: README restructure

**Files:**
- Modify: `README.md` (rebuilt into four parts)
- Create: `tests/test_engine_doc.py` (drift test, modeled on `tests/test_loop_breaker_doc.py`)

**Interfaces:**
- Consumes: `.pi/extensions/engine.ts` (the artifact from Task 1 — the install command and quoted constants are pinned against it); `docs/setup.md` (the long-form setup the shared section points at); `docs/loop-breaker.md` (the deep page for guard #1).
- Produces: a README a stranger can follow from zero to installed engine; `tests/test_engine_doc.py` proving the engine section cannot drift from the artifact.

- [ ] **Step 1: Write the failing drift test**

Create `tests/test_engine_doc.py`, modeled on `tests/test_loop_breaker_doc.py` (read that file first — same `_flat` whitespace-collapse helper and same rationale: a page that tells a stranger to copy a file and set constants has the same obligation as the loop-breaker page). The test:

```python
"""The README's engine section must not drift from the bundle.

Phase 9. The README tells a stranger to copy `.pi/extensions/engine.ts`
into user scope. The loop-breaker page has a drift test for the same
reason; the engine section is the front door for the same artifact plus
preserve-symbols. Constants and refusal text quoted in the README are
pinned here so the instructions cannot keep saying what used to be true.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
ENGINE = REPO_ROOT / ".pi" / "extensions" / "engine.ts"


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_the_engine_install_command_is_one_line():
    readme = _flat(README.read_text())
    command = "cp .pi/extensions/engine.ts ~/.pi/agent/extensions/"
    assert command in readme


def test_the_engine_artifact_exists():
    # Not vacuous: nothing else here imports the artifact, so without this
    # the file could vanish and the suite stay green.
    assert ENGINE.is_file()


def test_the_engine_section_points_at_docs_engine_index():
    readme = _flat(README.read_text())
    assert "docs/engine/index.md" in readme


def test_quoted_loop_breaker_constants_match_the_artifact():
    source = ENGINE.read_text()
    readme = README.read_text()
    for name in ("WINDOW", "THRESHOLD"):
        match = re.search(rf"^export const {name} = (\d+)", source, re.MULTILINE)
        assert match, f"{name} missing from {ENGINE}"
        # Any README mention of the constant must carry the artifact's value.
        for mention in re.finditer(rf"{name}[^0-9]*(\d+)", readme):
            assert mention.group(1) == match.group(1)
```

- [ ] **Step 2: Run the drift test to verify it fails**

Run: `uv run pytest tests/test_engine_doc.py -v`
Expected: FAIL — the README does not yet contain the install command or the `docs/engine/index.md` link.

- [ ] **Step 3: Rewrite the README into four parts**

Keep the current opening ("Can a small local model do real Python work…"), then restructure the body into four sections:

1. **## The engine** — why/how/what in a few sentences (a Pi extension that steers small models in everyday sessions: the loop breaker refusing repeated identical calls, and preserve-symbols refusing edits that delete public symbols). Minimal install:

   ```bash
   mkdir -p ~/.pi/agent/extensions
   cp .pi/extensions/engine.ts ~/.pi/agent/extensions/
   ```

   Then the two faces: everyday steering (the copy above — active in every session, including delegated children; one line on the user-scope gotcha with a link to `docs/loop-breaker.md`), and the bounded executor from a checkout:

   ```bash
   uv sync
   uv run python -m tools.deliver_candidate \
     --repo . --task add-iter \
     --prompt-file docs/example-brief.md \
     --validation "pytest -q" --writable "src/**" \
     --model your-provider/your-model
   ```

   Link: "More, including what the engine is and isn't: `docs/engine/index.md`."

2. **## Setup (applies to the engine and the evals)** — `uv`; the quality gates `ruff` / `pyrefly` / `pytest`; the local model and local server (`omlx start`, the `base_url` gotcha). One short paragraph each, then "the long form: `docs/setup.md`".

3. **## The evals** — what the evals measure (three suites: `agentclinic-phase-1`, `agentclinic-phase-1-user-story`, `duration`), the evidence index link, and that running one today goes through the harness in `docs/setup.md` (Phase 8's CLI is the planned entry point — do not document a command you have not verified).

4. **## The evidence** — keep the existing "What the evidence actually says" content (the Phase 7 confirmatory result) and "What's still experimental" as-is, moved under this heading.

Retire the old "Install the loop breaker" section into one line under The engine ("only want guard #1? `docs/loop-breaker.md` installs it alone"). Keep "Where to go next", "How this project works", and "Layout" as-is, adding `docs/engine/index.md` to the table.

- [ ] **Step 4: Verify the drift test passes and gates are green**

Run: `uv run pytest tests/test_engine_doc.py -v` → PASS. Then `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --diff`, `uv run pyrefly check`, `bun test extensions/`, and `uv run --group docs sphinx-build -W -b html docs docs/_build/html` — all green. (The Sphinx build must be clean under `-W`: this task does **not** touch `docs/index.md`; the engine link and toctree land in Task 3, where the pages exist.)

- [ ] **Step 5: Commit**

```bash
git add README.md docs/index.md tests/test_engine_doc.py
git commit -m "docs(phase9): rebuild the README around the engine, shared setup, and evals"
```

---

### Task 3: `docs/engine/`

**Files:**
- Create: `docs/engine/index.md`, `docs/engine/architecture.md`
- Modify: `docs/index.md` (Sphinx home — engine link and toctree, added here where the pages exist)
- Modify: `tests/test_engine_doc.py` (extend the drift pins to the new pages)

**Interfaces:**
- Consumes: `.pi/extensions/engine.ts`; `extensions/guards/loop-breaker.ts` and `preserve-symbols.ts` docstrings (the problems with numbers); `docs/architecture.md` (the bounded-implementer path, linked not duplicated); `docs/loop-breaker.md`, `docs/setup.md`, `docs/evidence-index.md` (cross-links).
- Produces: the user-facing section the README points at; Sphinx toctree entries; drift pins on any quoted constants/refusal text.

- [ ] **Step 1: Write the failing drift pins**

Extend `tests/test_engine_doc.py` so the pages that quote the artifact cannot drift: add `ENGINE_INDEX = REPO_ROOT / "docs" / "engine" / "index.md"` and a test that any `WINDOW`/`THRESHOLD` mention in `docs/engine/index.md` carries the artifact's value (same regex approach as Task 2), plus a test that `docs/engine/index.md` exists and contains the install command's destination `~/.pi/agent/extensions/`.

Run: `uv run pytest tests/test_engine_doc.py -v`
Expected: FAIL — the pages do not exist yet.

- [ ] **Step 2: Write `docs/engine/index.md`**

The detailed why/how/what, in this order:
- What the engine is: a Pi extension — one file — that steers a small local model while you work.
- The two faces: install it for everyday steering (the one-copy install, user-scope placement and why); run the bounded executor for a reviewed candidate (from a checkout, with the `deliver_candidate` one-liner).
- What it is not: not a planner, not a godbox; the typed-contract bridge is four-task-scoped; the executor is the evidenced path.
- The evidence in one paragraph: the loop-breaker's 261-turn run, the preserved-symbol edit, and the pilot shootout link.
- Where to go next: setup, architecture, loop-breaker, glossary, evidence index.

Keep it user-facing and short (~150 lines max). Do **not** duplicate `docs/loop-breaker.md` or `docs/architecture.md` — link to them. Quote constants only where the drift test pins them.

- [ ] **Step 3: Write `docs/engine/architecture.md`**

The problems being solved, with their numbers (from the guard docstrings): the 261-turn / 245×`ls -R` loop run (loop-breaker); the `/about`-route-deleting edit that failed three acceptance tests (preserve-symbols). Then the architecture, in the repo's "trace the path in execution order" style:
- Guards as pure decision functions over a tool call (`ToolCall → Decision`), one file per concern, the replay seam that drives the shipped artifact.
- The bundle: `.pi/extensions/engine.ts` — policy inlined, a thin adapter registering both guards on `tool_call`, pinned against the sources.
- Underneath, the bounded executor (linked to `docs/architecture.md` rather than re-explained): typed handoff → mutation engine → preservation validation → candidate ref.

- [ ] **Step 4: Wire the engine into `docs/index.md` and build**

Under the "What you can use today" section, add a one-line engine link ("the engine — why/how/what" pointing at `engine/index.md`); and add a toctree:

```markdown
```{toctree}
:maxdepth: 1
:caption: The engine

engine/index
engine/architecture
```
```

Then build:

```bash
uv run --group docs sphinx-build -W -b html docs docs/_build/html
```

Expected: clean under `-W` (this is the phase's standing gate; it was already green for the README-only commit in Task 2). Also run `uv run pytest tests/test_engine_doc.py -v` → PASS.

- [ ] **Step 5: Full gates**

Run: `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --diff`, `uv run pyrefly check`, `bun test extensions/` — all green.

- [ ] **Step 6: Commit**

```bash
git add docs/engine/index.md docs/engine/architecture.md docs/index.md tests/test_engine_doc.py
git commit -m "docs(phase9): add the engine section — why/how/what and architecture"
```

---

### Task 4: The shootout pilot

**Files:**
- Modify: `harness/runner.py` (the seam — `ENGINE_EXTENSIONS` + `ENGINE_IMPROVEMENT`)
- Create: `tests/test_engine_arm.py` (hermetic seam test)
- Create: `docs/engine/shootout.md` (the pilot write-up, labeled pilot)
- Modify: `docs/evidence-index.md` (index the pilot)

**Interfaces:**
- Consumes: `harness/runner.py`'s `Improvement` (fields `name`, `seed_dir: Path | None`, `extensions: tuple[Path, ...]`, `system_prompt: Path | None`), `_conditions` (records `improvement_name` and `extension_digests`), `run_batch(checkpoint_path, *, suite, target, model, improvement, timeout)`; `.pi/extensions/engine.ts` (Task 1).
- Produces: `ENGINE_IMPROVEMENT` — an extension-only improvement loading the engine artifact, usable as the with-engine arm of a `run_batch` comparison.

- [ ] **Step 1: Write the failing seam test**

Create `tests/test_engine_arm.py`:

```python
"""The engine arm is a well-formed, hermetic Improvement.

Phase 9. The shootout compares a suite with the engine loaded versus
without it. The seam is an extension-only Improvement so the comparison
reuses the harness's existing arm machinery: same task, same prompt, same
model, engine extensions added. These tests are hermetic — no model
server, no Pi run.
"""

from pathlib import Path

from harness import runner

ENGINE_FILE = runner.REPO_ROOT / ".pi" / "extensions" / "engine.ts"


def test_the_engine_improvement_is_extension_only():
    imp = runner.ENGINE_IMPROVEMENT
    assert imp.name == "engine"
    assert imp.seed_dir is None
    assert imp.system_prompt is None
    assert imp.extensions == (ENGINE_FILE,)


def test_the_engine_file_exists_and_digests_stably():
    assert ENGINE_FILE.is_file()
    digest = runner._path_digest(ENGINE_FILE)
    assert isinstance(digest, str) and len(digest) == 64
    assert runner._path_digest(ENGINE_FILE) == digest


def test_conditions_record_the_arm_without_a_model(monkeypatch):
    # _conditions shells out to git and pi --version; stub both so the
    # test stays hermetic on any machine.
    import subprocess

    def fake_run(cmd, **kwargs):
        out = "fake" if cmd[:2] == ["git", "rev-parse"] else "0.84.1"
        return subprocess.CompletedProcess(cmd, 0, stdout=out)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    conditions = runner._conditions(
        runner.AGENTCLINIC_PHASE_1,
        runner.DEFAULT_MODEL,
        ["pi", "--print", "<task-spec>"],
        600,
        extensions=runner.ENGINE_EXTENSIONS,
        improvement=runner.ENGINE_IMPROVEMENT,
    )
    assert conditions.improvement_name == "engine"
    assert runner._path_digest(ENGINE_FILE) in conditions.extension_digests
```

- [ ] **Step 2: Run the seam test to verify it fails**

Run: `uv run pytest tests/test_engine_arm.py -v`
Expected: FAIL — `runner.ENGINE_IMPROVEMENT` does not exist.

- [ ] **Step 3: Add the seam to `harness/runner.py`**

After the `Improvement` class (near line 113), add:

```python
# The engine arm (Phase 9 shootout): the shipped bundle as an
# extension-only improvement, so a comparison reuses the harness's arm
# machinery -- same task, same prompt, same model, engine loaded. No
# seed_dir (nothing to place), no system_prompt (the guards steer; they
# do not instruct). `improvement_name="engine"` and the extension digest
# record the arm in the checkpoint.
ENGINE_EXTENSIONS: tuple[Path, ...] = (
    REPO_ROOT / ".pi" / "extensions" / "engine.ts",
)
ENGINE_IMPROVEMENT = Improvement(
    name="engine",
    seed_dir=None,
    extensions=ENGINE_EXTENSIONS,
    system_prompt=None,
)
```

- [ ] **Step 4: Verify the seam test passes and gates are green**

Run: `uv run pytest tests/test_engine_arm.py -v` → PASS. Then `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --diff`, `uv run pyrefly check` — all green (bun untouched this task).

- [ ] **Step 5: Run the pilot**

With the owner, choose one suite from `harness/runner.py` (`AGENTCLINIC_PHASE_1`, `AGENTCLINIC_PHASE_1_USER_STORY`, or `DURATION`) — the one whose failure modes the guards address. Confirm the local model server is up (`docs/setup.md` Part 2), then run both arms to two separate checkpoints (they must not share a checkpoint — `improvement_name` differs, so a shared file would trip the conditions guard):

```bash
uv run python -c "
from pathlib import Path
from harness.runner import run_batch, AGENTCLINIC_PHASE_1, ENGINE_IMPROVEMENT
suite = AGENTCLINIC_PHASE_1  # chosen with the owner
for arm, imp in [('control', None), ('engine', ENGINE_IMPROVEMENT)]:
    cp = Path.home() / 'evidence' / f'shootout-{arm}-2026-08-13.jsonl'
    results = run_batch(cp, suite=suite, target=6, improvement=imp)
    accepted = sum(1 for r in results if r.grade.accepted)
    print(arm, accepted, '/', len(results), cp)
"
```

Adjust `AGENTCLINIC_PHASE_1` to the chosen suite and `target` to the agreed attempts-per-arm (4–6). Record the raw checkpoints where `docs/engine/shootout.md` names them.

- [ ] **Step 6: Write up the pilot as pilot evidence**

Create `docs/engine/shootout.md` following the research-record style of `docs/superpowers/research/2026-08-11-phase7-cycle7-confirmatory-result.md`:
- Question, suite, arms, attempts, model, date; the with-engine arm is the guard bundle via `ENGINE_IMPROVEMENT`.
- The numbers: accepted per arm; **pilot** label prominent; what it does and does **not** establish (no pooling with the Phase 7 confirmatory result; no claim about orchestration or the executor).
- If the run surfaced a harness or validation defect: fix and re-run before writing. If the number is disappointing: record it honestly.

Add a row to `docs/evidence-index.md` for the pilot, categorized pilot, pointing at `docs/engine/shootout.md`.

- [ ] **Step 7: Commit**

```bash
git add harness/runner.py tests/test_engine_arm.py docs/engine/shootout.md docs/evidence-index.md
git commit -m "feat(phase9): engine arm seam and pilot shootout, recorded as pilot"
```

---

## Definition of done (from the spec)

- A developer following only the README can: (a) install the engine with one copy command into user scope; (b) set up uv, the quality gates, and the local model/server via the shared setup section; (c) run an eval; and (d) read an honest pilot number in `docs/engine/shootout.md`.
- `.pi/extensions/engine.ts` exists, is self-contained, is checked in, fires on the recorded loop fixture, and stays silent on a clean run — pinned against the guard sources by test.
- The README has the four parts; `docs/engine/` exists with index and architecture; both front doors (README and `docs/index.md`) agree on the product path.
- The pilot is run, written up as pilot, and indexed in `evidence-index.md`; `ROADMAP.md` carries the Phase 9 entry with its four cycles.
- `uv run pytest` green, all quality gates green, Sphinx clean under `-W`.

## Self-review notes

- **Spec coverage:** each spec section maps to a task — Section 1 (bundle) → Task 1; Section 2 (README) → Task 2; Section 3 (docs/engine) → Task 3; Section 4 (shootout) → Task 4. The spec's test-strategy bullets map to concrete tests in each task. The drift-test obligation is split: bun-side pinning in Task 1 (`guards.test.ts`), Python-side drift in Tasks 2–3 (`test_engine_doc.py`).
- **Placeholders:** every step carries concrete content; the two places where the owner must choose (suite, attempts) are explicit decision points, not blanks.
- **Type consistency:** `ENGINE_IMPROVEMENT` fields match `Improvement`'s dataclass (`name`, `seed_dir: Path | None`, `extensions: tuple[Path, ...]`, `system_prompt: Path | None`); `_conditions`'s `extensions=` and `improvement=` parameters match its signature; `run_batch`'s `improvement=` and `target=` match.
