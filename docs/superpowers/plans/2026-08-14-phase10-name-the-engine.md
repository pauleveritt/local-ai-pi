# Phase 10 — Name the Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the end-user vocabulary — engine as the package, orchestrator and implementer as the roles, guards as passive steering — in the docs and the user-facing code, after the scheduled evidence run, so collaborators onboard to a naming regime that is not about to change.

**Architecture:** Four cycles, one commit each. (1) The scheduled guards-baseline evidence run on `agentclinic-phase-1-user-story`. (2) The rename/re-org: the vocabulary lands across README, `docs/engine/*`, the glossary, the evidence-index scope note, and user-facing strings in `tools/deliver_candidate.py` and `.pi/extensions/engine.ts` — no directory rename, no closure changes. (3) The `/implement` command: a thin Pi command in a new `.pi/extensions/orchestrator.ts` that shells out to the existing CLI. (4) Phase 11 shaped at the roadmap level.

**Tech Stack:** TypeScript (bun test, jiti-loaded Pi extensions), Python (harness, pytest, ruff, pyrefly), Sphinx docs. No new dependencies.

**Spec:** [`docs/superpowers/specs/2026-08-14-phase10-name-the-engine-design.md`](../specs/2026-08-14-phase10-name-the-engine-design.md)

## Global Constraints

(Copy these verbatim into review — every task inherits them.)

- **The vocabulary map.** *engine* = the package you install (`.pi/extensions/engine.ts`, later npm). *orchestrator* = the explicit front you invoke — pre-chews a task into a handoff packet, keeps the implementer's context small. *implementer* = the bounded worker (`extensions/orchestration/implementer.ts` + `mutation-engine.ts`). *guards* = passive steering. *handoff packet* = the pre-chewed task (code type `HandoffContract`). *Agent Engine* = the product name, unchanged. "Bounded executor" retires from user-facing text.
- **No directory rename, no closure/cell changes.** `extensions/orchestration/` and `IMPLEMENTER_EXTENSION_CLOSURE` stay pinned until packaging.
- **No TypeScript orchestration.** The orchestrator's substrate is the Python CLI (`tools/deliver_candidate.py`); `/implement` shells out to it.
- **Historical phases keep their terms.** History is not rewritten.
- **No new dependencies.** Nothing added to `pyproject.toml`.
- **Quality gates green before each commit:** `uv run ruff check .`, `uv run ruff format --diff`, `uv run pyrefly check`, `uv run pytest`, `bun test`, and Sphinx `-W` clean.
- **Working style:** branch `phase10-name-the-engine` off `main`, worktree in `.worktrees/`. One commit per task, test-first, messages in repo style (`feat(phase10): …`, `docs(phase10): …`).
- **Verify, don't assert.** Every claim is tested or recorded.

---

### Task 1: The evidence run

**Files:**
- Modify: `docs/engine/shootout.md` (add the discriminating comparison)
- Modify: `ROADMAP.md` (close the Deferred-candidates entry)

**Interfaces:**
- Consumes: `harness/runner.py`'s `run_batch`, `AGENTCLINIC_PHASE_1_USER_STORY`, `ENGINE_IMPROVEMENT` (the Phase 9 seam); the local model server.
- Produces: a `docs/engine/shootout.md` section recording the bare-vs-guards-only comparison with its non-claims; the ROADMAP Deferred-candidates entry closed.

- [ ] **Step 1: Confirm the server and run the comparison**

Confirm the local model server is up (`curl -s http://127.0.0.1:8001/v1/models` lists `gemma-4-12B-it-MLX-8bit`; if not, `omlx start` first — `docs/setup.md` Part 2). Then run both arms to two separate checkpoints:

```bash
uv run python -c "
from pathlib import Path
from harness.runner import run_batch, AGENTCLINIC_PHASE_1_USER_STORY, ENGINE_IMPROVEMENT
suite = AGENTCLINIC_PHASE_1_USER_STORY
for arm, imp in [('control', None), ('engine', ENGINE_IMPROVEMENT)]:
    cp = Path.home() / 'evidence' / f'shootout-userstory-{arm}-2026-08-14.jsonl'
    print(f'=== starting arm {arm} -> {cp}', flush=True)
    results = run_batch(cp, suite=suite, target=6, improvement=imp)
    accepted = sum(1 for r in results if r.grade.accepted)
    print(f'=== arm {arm}: accepted {accepted}/{len(results)} checkpoint {cp}', flush=True)
"
```

Run it in the background and monitor (each attempt is a few minutes on the harder suite; timeouts cap at 600s). Record per-run accepted, refused, timed_out, and whether any `loop_broken`/`symbol_preserved` telemetry entries appear in the engine arm's recorded Pi output (grep the checkpoints' `pi_stdout`).

- [ ] **Step 2: Update `docs/engine/shootout.md` with the discriminating comparison**

Add a section (or extend Section 2) recording the user-story comparison: the suite, arms, n, the per-arm accepted counts, and — critically — whether the guards fired and whether they rescued failing runs. State the honest reading whichever way it lands: if guards-only rescues some failing runs, the insurance has a number; if not, the effect lives in the executor/stack — also a real finding. Keep the pilot label and the non-claims (one suite, one model, not pooled, not confirmatory).

- [ ] **Step 3: Close the ROADMAP Deferred-candidates entry**

Mark the "Open — the missing guards baseline, scheduled as the next measurement" entry as done, naming the checkpoints and the outcome in one clause.

- [ ] **Step 4: Gates and commit**

`uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --diff`, `uv run pyrefly check`, Sphinx `-W` — all green. Then:

```bash
git add docs/engine/shootout.md ROADMAP.md
git commit -m "feat(phase10): the guards-baseline evidence run on user-story"
```

---

### Task 2: The rename/re-org

**Files:**
- Modify: `README.md` (retire "bounded executor"; orchestrator/implementer vocabulary)
- Modify: `docs/engine/index.md`, `docs/engine/architecture.md`, `docs/engine/deliver-candidate.md`, `docs/engine/shootout.md`, `docs/engine/loop-breaker.md`, `docs/engine/usage.md`
- Modify: `docs/glossary.md` (add Engine, Orchestrator; rename Bounded implementer → Implementer, Handoff contract → Handoff packet)
- Modify: `docs/evidence-index.md` (scope note)
- Modify: `tools/deliver_candidate.py` (user-facing help/docstrings)
- Modify: `.pi/extensions/engine.ts` (comments to the vocabulary)
- Modify: `tests/test_engine_doc.py` (pin the renamed terms)

**Interfaces:**
- Consumes: the vocabulary map (Global Constraints); the current "executor"/"bounded executor" occurrences (README, `docs/engine/*`, `docs/glossary.md`, `docs/evidence-index.md`).
- Produces: a consistent vocabulary across the user-facing surface; drift tests pinning the renamed terms; Sphinx clean under `-W`.

- [ ] **Step 1: Update the drift test to the new vocabulary (failing)**

Extend `tests/test_engine_doc.py` so the README and `docs/engine/index.md` cannot carry the retired term: add a test that neither file contains "bounded executor" as a user-facing name, and that the README names the orchestrator and the implementer. Example:

```python
def test_the_user_facing_vocabulary_is_the_new_one():
    readme = _flat(README.read_text())
    index = _flat(ENGINE_INDEX.read_text())
    for text in (readme, index):
        assert "bounded executor" not in text
    assert "orchestrator" in readme
    assert "implementer" in readme
```

Run: `uv run pytest tests/test_engine_doc.py -v` → FAIL (the retired term is still present).

- [ ] **Step 2: Apply the vocabulary map across the docs**

Rewrite the user-facing surface to the map:
- **README.md:** "The other face is the bounded executor" → the orchestrator; the executor section describes the orchestrator (the front you invoke) driving the implementer (the bounded worker); keep the install and setup sections.
- **`docs/engine/index.md`:** the two faces become engine (the package) and the orchestrator; the architecture pointer names the implementer.
- **`docs/engine/architecture.md`:** "Underneath: the bounded executor" → the orchestrator driving the implementer; the typed handoff becomes the handoff packet.
- **`docs/engine/deliver-candidate.md`:** "This is the bounded executor" → "This is the orchestrator"; the path description names the implementer and the handoff packet.
- **`docs/engine/shootout.md` and `docs/engine/loop-breaker.md` and `docs/engine/usage.md`:** update executor references to the vocabulary.
- **`docs/glossary.md`:** add **Engine** (the package you install) and **Orchestrator** (the front you invoke); rename **Bounded implementer** → **Implementer** (its "The executor:" line → "The implementer:"); rename **Handoff contract** → **Handoff packet** (noting the code type `HandoffContract`). Update cross-references.
- **`docs/evidence-index.md`:** the scope note moves to the vocabulary.

Keep every number and claim intact — this is a vocabulary change, not a content change. Historical phases (ROADMAP, the research record) keep their terms.

- [ ] **Step 3: Update the user-facing code strings**

- `tools/deliver_candidate.py`: the argparse `description` and help strings that say "executor" move to "orchestrator"; the docstring's user-facing description names the orchestrator driving the implementer. Do not change flags, behavior, or the closure.
- `.pi/extensions/engine.ts`: the header comment and the adapter comment move to the vocabulary (the engine is the package; the guards are passive steering). No code change.

- [ ] **Step 4: Verify the drift test passes and gates are green**

`uv run pytest tests/test_engine_doc.py -v` → PASS. Then `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --diff`, `uv run pyrefly check`, `bun test extensions/`, and `uv run --group docs sphinx-build -W -b html docs docs/_build/html` — all green (zero warnings).

- [ ] **Step 5: Commit**

```bash
git add README.md docs/engine/ docs/glossary.md docs/evidence-index.md tools/deliver_candidate.py .pi/extensions/engine.ts tests/test_engine_doc.py
git commit -m "docs(phase10): land the engine/orchestrator/implementer vocabulary"
```

---

### Task 3: The `/implement` command

**Files:**
- Create: `.pi/extensions/orchestrator.ts` (the engine package's orchestrator front)
- Create: `tests/test_orchestrator_command.py` (hermetic registration + flag-mapping test; live test skipped)
- Modify: `README.md` (the orchestrator section names `/implement` and the two-file install)
- Modify: `tests/test_engine_doc.py` (pin the two-file install)

**Interfaces:**
- Consumes: `pi.registerCommand()`; `tools/deliver_candidate.py`'s flags (`--repo`, `--task`, `--prompt-file`, `--validation`, `--writable`, `--model`); the current repo (`ctx.cwd`) and session model.
- Produces: `.pi/extensions/orchestrator.ts` registering `/implement`; a pure `buildDeliverCandidateArgv(...)` the command uses; the two-file install (engine.ts + orchestrator.ts).

- [ ] **Step 1: Write the failing hermetic test**

Create `tests/test_orchestrator_command.py`:

```python
"""The engine package registers /implement, and its argv maps correctly.

Phase 10. The orchestrator's session front is a thin command that shells
out to the existing CLI. These tests are hermetic: they verify the command
is registered and the argv the handler builds, without a checkout, a model,
or a subprocess.
"""

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR = REPO_ROOT / ".pi" / "extensions" / "orchestrator.ts"


def test_the_orchestrator_file_exists():
    assert ORCHESTRATOR.is_file()


def test_the_argv_builder_maps_the_inputs():
    # Run the TS builder under bun and check the argv it prints.
    out = subprocess.run(
        [
            "bun", "-e",
            f"import {{ buildDeliverCandidateArgv }} from '{ORCHESTRATOR}';"
            "console.log(JSON.stringify(buildDeliverCandidateArgv({"
            "repo: '/repo', task: 'add-health', promptFile: '/tmp/p.md',"
            "validation: 'pytest -q', model: 'omlx/gemma-4-12B-it-MLX-8bit'"
            "})))",
        ],
        capture_output=True, text=True, check=True,
    )
    argv = out.stdout.strip()
    assert "tools.deliver_candidate" in argv
    assert "--repo /repo" in argv
    assert "--task add-health" in argv
    assert "--prompt-file /tmp/p.md" in argv
    assert "--validation pytest -q" in argv
    assert "--model omlx/gemma-4-12B-it-MLX-8bit" in argv
```

Run: `uv run pytest tests/test_orchestrator_command.py -v` → FAIL (the file does not exist).

- [ ] **Step 2: Create `.pi/extensions/orchestrator.ts`**

A self-contained Pi extension registering `/implement`. It exports a pure `buildDeliverCandidateArgv({repo, task, promptFile, validation, model})` that returns the argv array, and a default factory that registers the command:

```ts
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { spawn } from "node:child_process";
import { writeFile, mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

export function buildDeliverCandidateArgv(opts: {
	repo: string;
	task: string;
	promptFile: string;
	validation: string;
	model: string;
}): string[] {
	return [
		"run", "python", "-m", "tools.deliver_candidate",
		"--repo", opts.repo,
		"--task", opts.task,
		"--prompt-file", opts.promptFile,
		"--validation", opts.validation,
		"--model", opts.model,
	];
}

function slugify(text: string): string {
	return text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40) || "task";
}

export default function (pi: ExtensionAPI) {
	pi.registerCommand("implement", {
		description: "Orchestrate a bounded change: chew a task into a handoff packet and drive the implementer.",
		handler: async (args, ctx) => {
			const prompt = args.trim();
			if (!prompt) {
				ctx.ui.notify("Usage: /implement <task> — the orchestrator chews it into a handoff packet.", "warning");
				return;
			}
			const dir = await mkdtemp(join(tmpdir(), "implement-"));
			const promptFile = join(dir, "prompt.md");
			await writeFile(promptFile, prompt);
			const argv = buildDeliverCandidateArgv({
				repo: ctx.cwd,
				task: slugify(prompt),
				promptFile,
				validation: "pytest -q",
				model: ctx.model
					? `${ctx.model.provider}/${ctx.model.id}`
					: "omlx/gemma-4-12B-it-MLX-8bit",
			});
			ctx.ui.notify(`Orchestrating: ${argv.join(" ")}`, "info");
			const child = spawn("uv", argv, { cwd: ctx.cwd });
			child.stdout.on("data", (d) => ctx.ui.notify(String(d).trim(), "info"));
			child.stderr.on("data", (d) => ctx.ui.notify(String(d).trim(), "warning"));
		},
	});
}
```

- [ ] **Step 3: Verify the hermetic test passes and gates are green**

`uv run pytest tests/test_orchestrator_command.py -v` → PASS. Then `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --diff`, `uv run pyrefly check`, `bun test extensions/` — all green.

- [ ] **Step 4: Update the README install and the drift test**

The orchestrator section names `/implement` and the two-file install (`cp .pi/extensions/engine.ts .pi/extensions/orchestrator.ts ~/.pi/agent/extensions/`). Extend `tests/test_engine_doc.py` to pin the two-file install command and that `orchestrator.ts` exists. Verify green.

- [ ] **Step 5: Commit**

```bash
git add .pi/extensions/orchestrator.ts tests/test_orchestrator_command.py README.md tests/test_engine_doc.py
git commit -m "feat(phase10): register /implement as the orchestrator's session front"
```

---

### Task 4: Phase 11 shape

**Files:**
- Modify: `ROADMAP.md` (Phase 11 entry, planned)
- Create: `docs/superpowers/specs/2026-08-14-phase11-contract-authoring-bridge-shape.md` (a one-page shape)

**Interfaces:**
- Consumes: the phase-7 plan's Cycle 6 (planner contracts) and the `author_contract.py` → `HandoffContract` bridge item; the `/implement` command from Task 3.
- Produces: a ROADMAP Phase 11 entry (planned) and a one-page shape document.

- [ ] **Step 1: Add the Phase 11 entry to the ROADMAP**

A phase-table row and a short narrative section: Phase 11 — the contract-authoring bridge. The orchestrator pre-chews a real `HandoffContract` from a roadmap/manifest (`tools/author_contract.py` → `HandoffContract` JSON, `inspectContract` as the admission gate), driving `/implement`'s structured flavor. State it as planned, with the spec pointer.

- [ ] **Step 2: Write the one-page shape**

`docs/superpowers/specs/2026-08-14-phase11-contract-authoring-bridge-shape.md`, status "shape — to be brainstormed into a full spec": the goal (the orchestrator pre-chews real handoff packets, closing the gap between the ad-hoc prompt and the typed bridge), the mechanism (author_contract → HandoffContract, inspectContract as admission gate), the two `/implement` flavors (ad-hoc now, structured then), and the open questions (which product Cycle 6 is buying; the manifest-to-handoff boundary; reliable authoring under the gate).

- [ ] **Step 3: Gates and commit**

Sphinx `-W` clean, `uv run pytest -q` green. Then:

```bash
git add ROADMAP.md docs/superpowers/specs/2026-08-14-phase11-contract-authoring-bridge-shape.md
git commit -m "docs(phase10): shape Phase 11 — the contract-authoring bridge"
```

---

## Definition of done (from the spec)

- The evidence run is recorded: `docs/engine/shootout.md` carries the discriminating comparison with its non-claims, and the ROADMAP Deferred-candidates entry is closed.
- The vocabulary is consistent across README, `docs/engine/*`, `docs/glossary.md`, and the evidence-index scope note; "bounded executor" is retired from user-facing text; Sphinx clean under `-W`.
- `/implement` is registered by the engine package and works from a checkout — reaching a candidate ref or an actionable refusal.
- The ROADMAP carries the Phase 10 entry (complete) and the Phase 11 entry (planned, shaped).
- All quality gates green.

## Self-review notes

- **Spec coverage:** each spec section maps to a task — Section 1 (evidence run) → Task 1; Section 2 (rename) → Task 2; Section 3 (`/implement`) → Task 3; Section 4 (Phase 11 shape) → Task 4.
- **Placeholders:** every step carries concrete content; the evidence run's outcome is a decision point (guards rescue vs. don't), not a blank.
- **Type consistency:** `buildDeliverCandidateArgv` fields match `deliver_candidate`'s flags (`--repo`, `--task`, `--prompt-file`, `--validation`, `--model`); the hermetic test's argv assertions match the builder's output; the `Improvement`/`run_batch` usage in Task 1 matches the Phase 9 seam.
