# Phase 12 — The Engine, Packaged Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the engine a real pi package — `pi install git:github.com/pauleveritt/local-ai-pi@v0.1.0` — with a dedicated package home (`packages/engine/`) as the single source of truth, the loop breaker folded into the engine, and the deferred re-org (directory rename, closure rewire, vocabulary sweep) landed.

**Architecture:** Four cycles, one commit each. (1) The package: move the two installable files into `packages/engine/`, add the package manifest, the root git-install seam, the symlinks that keep a checkout zero-install, and rewire the harness path + pinning tests. (2) The loop-breaker merge: delete the standalone copy, retarget replay/pinning at the engine bundle, rewrite the docs. (3) The re-org: `extensions/orchestration/` → `extensions/implementer/`, the closure rewire + pinned-test updates, the `author_contract.py` vocabulary sweep. (4) Verification + docs: a fresh-agent-dir install test, the `pi install` docs, the tag.

**Tech Stack:** TypeScript (bun test, jiti-loaded Pi extensions), Python (harness, pytest, ruff, pyrefly), pi packages (`pi install`, `pi manifest`), git tags. No new dependencies.

**Spec:** [`docs/superpowers/specs/2026-08-14-phase12-engine-packaged-design.md`](../specs/2026-08-14-phase12-engine-packaged-design.md)

## Global Constraints

(Copy these verbatim into review — every task inherits them.)

- **The package is the single source of truth.** The installable files live in `packages/engine/` (`engine.ts`, `orchestrator.ts`); `.pi/extensions/` holds symlinks to them (D2). No second copy.
- **The root manifest is the git-install seam only** (D3): the root `package.json`'s `pi.extensions` points at exactly `./packages/engine/engine.ts` and `./packages/engine/orchestrator.ts` — nothing else; the research `extensions/` tree never loads.
- **No implementer bundling.** The package is the extensions; `/implement` keeps shelling out to `tools/deliver_candidate` from a checkout (D7).
- **No npm.** Git-only, tagged `v0.1.0` (D4).
- **The loop breaker is part of the engine** (D5): no standalone install path survives.
- **Historical phases keep their terms** — do not rewrite the Phase 9/10 plans or research records.
- **No new dependencies.** Nothing added to `pyproject.toml`; the package has no runtime deps.
- **Quality gates green before each commit:** `uv run ruff check .`, `uv run ruff format --diff`, `uv run pyrefly check`, `uv run pytest`, `bun test`, Sphinx `-W`.
- **Working style:** branch `phase12-engine-packaged` off `main`, worktree in `.worktrees/`. One commit per task, test-first, messages in repo style (`feat(phase12): …`, `docs(phase12): …`).
- **Verify, don't assert.**

---

### Task 1: The package

**Files:**
- Move: `.pi/extensions/engine.ts` → `packages/engine/engine.ts`; `.pi/extensions/orchestrator.ts` → `packages/engine/orchestrator.ts` (git move, so history follows)
- Create: `packages/engine/package.json` (the pi package manifest)
- Modify: `package.json` (root — the git-install seam)
- Modify: `.pi/extensions/` (engine.ts + orchestrator.ts become symlinks to `packages/engine/`)
- Modify: `harness/runner.py` (`ENGINE_EXTENSIONS` → `packages/engine/engine.ts`)
- Modify: `tests/test_engine_doc.py`, `tests/test_orchestrator_command.py` (paths + install pins)
- Modify: `docs/engine/index.md`, `docs/engine/architecture.md`, `docs/glossary.md`, `docs/engine/usage.md` (the engine's path/install references)

**Interfaces:**
- Consumes: `.pi/extensions/engine.ts` + `orchestrator.ts` (the installable files), the harness's `ENGINE_EXTENSIONS`, the drift/pinning tests, the docs that name `.pi/extensions/engine.ts`.
- Produces: `packages/engine/` (the source of truth), the root seam, symlinked `.pi/extensions/`, all paths rewired.

- [ ] **Step 1: Write the failing path tests**

Extend `tests/test_engine_doc.py` and `tests/test_orchestrator_command.py` so they assert the new home: `PACKAGE_ENGINE = REPO_ROOT / "packages" / "engine" / "engine.ts"` (and `PACKAGE_ORCHESTRATOR` likewise); the README's copy command becomes `cp packages/engine/engine.ts packages/engine/orchestrator.ts ~/.pi/agent/extensions/` (the interim install form — the `pi install` one-liner replaces it in Task 4). Add the symlink property test:

```python
def test_the_project_local_entries_are_symlinks():
    # A checkout must load the engine with zero install, and the package
    # must stay the single source of truth — so .pi/extensions holds
    # symlinks, not copies.
    assert ENGINE.is_symlink()
    assert ORCHESTRATOR.is_symlink()
    assert ENGINE.resolve() == PACKAGE_ENGINE.resolve()
    assert ORCHESTRATOR.resolve() == PACKAGE_ORCHESTRATOR.resolve()
```

Run: `uv run pytest tests/test_engine_doc.py tests/test_orchestrator_command.py -v` → FAIL (the package files don't exist; the symlinks don't exist).

- [ ] **Step 2: Move the files and write the package manifest**

```bash
mkdir -p packages/engine
git mv .pi/extensions/engine.ts packages/engine/engine.ts
git mv .pi/extensions/orchestrator.ts packages/engine/orchestrator.ts
```

`packages/engine/package.json`:

```json
{
	"name": "agent-engine",
	"version": "0.1.0",
	"keywords": ["pi-package"],
	"type": "module",
	"pi": {
		"extensions": ["./engine.ts", "./orchestrator.ts"]
	}
}
```

(No runtime dependencies — the guards are dependency-free.)

- [ ] **Step 3: The root manifest (the git seam)**

The root `package.json` gains the `pi` seam (D3), so `pi install git:…` finds the engine and does not auto-discover the research `extensions/` tree:

```json
"pi": {
	"extensions": ["./packages/engine/engine.ts", "./packages/engine/orchestrator.ts"]
}
```

- [ ] **Step 4: The symlinks**

```bash
ln -s packages/engine/engine.ts .pi/extensions/engine.ts
ln -s packages/engine/orchestrator.ts .pi/extensions/orchestrator.ts
git add .pi/extensions/engine.ts .pi/extensions/orchestrator.ts
```

- [ ] **Step 5: Rewire the harness and the tests**

`harness/runner.py:134`: `ENGINE_EXTENSIONS = (REPO_ROOT / "packages" / "engine" / "engine.ts",)`. Update `tests/test_engine_doc.py` (the install command now references `packages/engine/`), `tests/test_orchestrator_command.py` (the ORCHESTRATOR path), and the docs' install references (`docs/engine/index.md`, `docs/engine/architecture.md`, `docs/engine/usage.md`, `docs/glossary.md`).

- [ ] **Step 6: Verify and commit**

`uv run pytest tests/test_engine_doc.py tests/test_orchestrator_command.py -v` → PASS. Then `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --diff`, `uv run pyrefly check`, `bun test extensions/`, Sphinx `-W` — all green. Commit:

```bash
git add packages/engine package.json harness/runner.py tests/ docs/
git commit -m "feat(phase12): the engine is a package — packages/engine with a pi manifest"
```

---

### Task 2: The loop breaker merges into the engine

**Files:**
- Delete: `.pi/extensions/loop-breaker.ts` (the standalone install copy)
- Modify: `tools/replay_guards.mjs` (retarget at the engine bundle)
- Modify: `extensions/guards/guards.test.ts` (the "two artifacts" block pins the engine bundle)
- Modify: `docs/engine/loop-breaker.md`, `README.md`, `docs/engine/usage.md` (the loop breaker is part of the engine; no standalone install)
- Modify: `tests/test_loop_breaker_doc.py` (the page it pins — still exists; the doc's content changes)
- Modify: `tools/build_export.py` if it lists `.pi/extensions/loop-breaker.ts` in the export closure

**Interfaces:**
- Consumes: `tools/replay_guards.mjs` (imports the standalone by path), `guards.test.ts` (pins the standalone against the source), the docs' standalone install sections.
- Produces: the engine bundle as the shipped artifact for replay/pinning; docs where the loop breaker is part of the engine.

- [ ] **Step 1: Retarget replay at the engine bundle (failing)**

`tools/replay_guards.mjs` line 34 imports `.pi/extensions/loop-breaker.ts` directly. Change the path to `packages/engine/engine.ts` — the engine bundle is the shipped artifact now, and it self-registers both guards. Its default export is `function (pi)`, so the replay's import-and-drive pattern changes: the engine bundle's guards register on `pi.on("tool_call")`, so replay must drive the registered handler (pass a fake `pi`, capture the `tool_call` handler, feed it the recorded calls). Update the replay's docstring ("the replay therefore tests the artifact" — now the engine bundle, not the standalone loop-breaker copy).

- [ ] **Step 2: Update the pinning test (failing)**

`extensions/guards/guards.test.ts`'s "the two loop-breaker artifacts" describe block reads `.pi/extensions/loop-breaker.ts`. Retarget it to `packages/engine/engine.ts`: pin that the engine bundle's loop-breaker behavior and constants agree with `extensions/guards/loop-breaker.ts`, and that the engine bundle stays free of local imports (the property the standalone previously pinned). The pairwise pinning the block enforced becomes "the engine bundle vs the guard source."

- [ ] **Step 3: Delete the standalone and rewrite the docs**

Delete `.pi/extensions/loop-breaker.ts`. Rewrite:
- `docs/engine/loop-breaker.md` — drop the "install it alone" section; the page is now "the loop breaker, part of the engine" (its behavior, tuning, and the subagent gotcha stay; the install points at the engine).
- `README.md` — the "(Only want guard #1? … installs the loop breaker alone)" note goes away; the engine includes the loop breaker.
- `docs/engine/usage.md` — the "Only the loop breaker" section becomes "part of the engine."

Update `tests/test_loop_breaker_doc.py` if its pinned assertions reference the standalone install.

- [ ] **Step 4: Verify and commit**

`bun test extensions/` → PASS (the retargeted pinning). `uv run pytest -q`, ruff/pyrefly, Sphinx `-W` — green. Commit:

```bash
git add .pi/extensions/loop-breaker.ts tools/replay_guards.mjs extensions/guards/guards.test.ts docs/ tools/build_export.py
git commit -m "feat(phase12): fold the loop breaker into the engine — no standalone install"
```

---

### Task 3: The deferred re-org

**Files:**
- Rename: `extensions/orchestration/` → `extensions/implementer/` (git move)
- Modify: `tools/deliver_candidate.py` (`IMPLEMENTER_EXTENSION` + `IMPLEMENTER_EXTENSION_CLOSURE` paths)
- Modify: `tools/build_export.py`, `harness/typed_contract.py` (paths that name `orchestration/`)
- Modify: `tools/author_contract.py` (the model-facing "executor" prose)
- Modify: `tests/test_deliver_candidate.py` (the closure-digest assertions)

**Interfaces:**
- Consumes: the current `extensions/orchestration/` paths in the closure, build_export, typed_contract; the digest-pinned closure tests; `author_contract.py`'s prose.
- Produces: `extensions/implementer/`; the closure rewired with its pinned tests updated (the unfreeze); the vocabulary sweep.

- [ ] **Step 1: The rename**

```bash
git mv extensions/orchestration extensions/implementer
```

- [ ] **Step 2: Rewire the paths**

`tools/deliver_candidate.py`: `_EXTENSIONS_ROOT / "orchestration" / …` → `"implementer" / …` (both `IMPLEMENTER_EXTENSION` and the closure tuple). `tools/build_export.py` and `harness/typed_contract.py`: same. Grep for any other `orchestration/` path references in code (none should remain).

- [ ] **Step 3: Update the digest-pinned closure tests**

`tests/test_deliver_candidate.py` asserts the closure (e.g., `seen == set(deliver_candidate.IMPLEMENTER_EXTENSION_CLOSURE)`) and its digests. The rewire changes the digests (the unfreeze): update the expected values so the suite is green, and confirm the closure still names the same files under their new paths. If a test asserts a hardcoded digest, recompute it from the rewired closure.

- [ ] **Step 4: The vocabulary sweep**

`tools/author_contract.py`: the five "executor" occurrences (lines 50, 98, 142, 143, 151 — including the model-facing f-string at 151, "The executor may only change files matching:") → "implementer". This is a user-facing/model-facing string change only; no behavior change.

- [ ] **Step 5: Verify and commit**

`uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --diff`, `uv run pyrefly check`, `bun test extensions/`, Sphinx `-W` — all green. Commit:

```bash
git add extensions/ tools/ harness/ tests/
git commit -m "feat(phase12): rename orchestration to implementer, unfreeze the closure"
```

---

### Task 4: Verification + docs

**Files:**
- Create: `tests/test_package_install.py` (a fresh-agent-dir install test, live-gated)
- Modify: `README.md`, `docs/engine/usage.md` (the `pi install` one-liner)
- Modify: `docs/glossary.md` (the Engine entry names the package)
- Tag: `v0.1.0`

**Interfaces:**
- Consumes: the package (`packages/engine/`), `pi install`, the fresh-agent-dir seam (`PI_CODING_AGENT_DIR`).
- Produces: a verified package install; the documented one-line install; the tag.

- [ ] **Step 1: Write the fresh-agent-dir install test**

`tests/test_package_install.py`, modeled on the repo's live-gated tests (`SATYRN_LIVE` guard, `tests/test_extensions.py` pattern). It installs the package into a fresh agent dir (`PI_CODING_AGENT_DIR` pointed at a temp dir) and asserts the guards load and `/implement` registers. Skipped without `SATYRN_LIVE=1` (needs Pi). A hermetic companion asserts the root manifest lists exactly the two package files (the "research tree never loads" property):

```python
def test_the_root_manifest_lists_only_the_package_files():
    import json
    root = json.load(open(REPO_ROOT / "package.json"))
    extensions = root["pi"]["extensions"]
    assert extensions == [
        "./packages/engine/engine.ts",
        "./packages/engine/orchestrator.ts",
    ]
```

- [ ] **Step 2: Document the one-line install**

README engine section + `docs/engine/usage.md`: the install is now `pi install git:github.com/pauleveritt/local-ai-pi@v0.1.0` (from a checkout, or the local equivalent). Keep the symlink note (a checkout needs nothing). The `docs/glossary.md` Engine entry names the package.

- [ ] **Step 3: The tag**

```bash
git tag v0.1.0
```

(Note: the tag lands when the branch merges — the commit message and the docs reference `v0.1.0`.)

- [ ] **Step 4: Verify and commit**

`uv run pytest -q` (the new hermetic test passes; the live test skips), Sphinx `-W`, ruff/pyrefly/bun — green. Commit:

```bash
git add tests/test_package_install.py README.md docs/engine/usage.md docs/glossary.md
git commit -m "docs(phase12): the one-line pi install, verified on a fresh agent dir"
```

---

## Definition of done (from the spec)

- `pi install git:github.com/pauleveritt/local-ai-pi@v0.1.0` (or the local equivalent) puts the engine in a fresh agent dir: the guards load and `/implement` registers, verified, not asserted.
- A trusted checkout loads the engine with zero install (the symlinks).
- `extensions/implementer/` exists, the closure resolves with its pinned tests green, and `author_contract.py` speaks "implementer".
- The loop breaker is documented as part of the engine; no standalone install path remains.
- All gates green.

## Self-review notes

- **Spec coverage:** Section 1 (package) → Task 1; Section 2 (loop-breaker merge) → Task 2; Section 3 (re-org) → Task 3; Section 4 (verification + docs) → Task 4.
- **Placeholders:** every step carries concrete content; the digest recomputation in Task 3 names the test to update rather than hardcoding a value.
- **Type consistency:** `ENGINE_EXTENSIONS` → `packages/engine/engine.ts` matches the harness's `Improvement`/`RunConditions` machinery; the symlink assertions resolve to the package paths; the closure rewire names the same files under `implementer/`.
