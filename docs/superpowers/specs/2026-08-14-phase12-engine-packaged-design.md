# Phase 12 — The engine, packaged

**Date:** 2026-08-14
**Status:** design — approved before any cycle
**Supersedes** the same-date shape document; the shape was the sketch, this
is the contract the cycles implement.

## Direction, one sentence

> Make the engine a real pi package — `pi install
> git:github.com/pauleveritt/local-ai-pi@v0.1.0` — with a dedicated package
> home as the single source of truth, the loop breaker folded into the
> engine, and the deferred re-org (directory rename, closure rewire,
> vocabulary sweep) landed.

## Why this phase, and why now

The engine installs by copying two files into user scope. The npm package
was deferred to "the packaging effort" in Phase 9 and again in Phase 10;
the loop breaker still has a standalone install story the user wants gone;
and `extensions/orchestration/` collides with the orchestrator role the
Phase 10 vocabulary named. This phase makes the install one line, removes
the redundant standalone artifact, and lands the re-org that was parked
"at packaging time" twice. Collaborators onboarding to the renamed product
should find an engine that installs like a package, not a copy-paste.

## What this phase is not

- **Not the whole repo as the package.** The installable files get a
  dedicated home (`packages/engine/`); the repo-root manifest is only the
  git-install discovery seam.
- **Not npm publishing.** Git-only for this phase; npm is a one-command
  addition later if a user ever needs it.
- **Not bundling the implementer into the package.** `/implement` keeps
  shelling out to the CLI from a checkout; the implementer machinery stays
  in the repo. Phase 11 (the contract-authoring bridge) owns that
  territory.
- **Not the contract-authoring bridge** (Phase 11), not new guards, not new
  evidence, not the difficulty-ladder runs.

## Decisions locked in brainstorming

**D1 — A dedicated package home is the source of truth.** The installable
files move to `packages/engine/` (`engine.ts`, `orchestrator.ts`,
`package.json`). No whole-repo-as-package.

**D2 — `.pi/extensions/` keeps thin references.** `engine.ts` and
`orchestrator.ts` there become symlinks to the package files, so a trusted
checkout still loads the engine with zero install. One copy of the policy,
no drift. `hello-world.ts` stays (the harness `EXTENSIONS` default).

**D3 — The repo-root manifest is the git-install seam.** The root
`package.json` gains `"pi": { "extensions": ["./packages/engine/engine.ts",
"./packages/engine/orchestrator.ts"] }` — this disables Pi's
convention-directory auto-discovery (which would otherwise load the
research `extensions/` tree) and points git installs at the package.

**D4 — Git-only for this phase.** The story is
`pi install git:github.com/pauleveritt/local-ai-pi@v0.1.0`, pinned by a
tag. npm publishing is deferred.

**D5 — The loop breaker merges into the engine.** The standalone
`.pi/extensions/loop-breaker.ts` install copy is deleted; the replay
harness (`tools/replay_guards.mjs`) and the artifact pinning
(`guards.test.ts`) retarget the engine bundle (the shipped artifact); the
docs present the loop breaker as part of the engine, with no standalone
install path.

**D6 — The re-org is rename + rewire only.** `extensions/orchestration/` →
`extensions/implementer/`; `IMPLEMENTER_EXTENSION_CLOSURE` rewired and its
digest-pinned tests updated (the "unfree the pins" approved in Phase 10);
`tools/author_contract.py`'s model-facing "executor" prose swept to
"implementer". No bundling of the implementer into the package.

**D7 — `/implement` keeps its shell-out.** It continues to delegate to
`uv run python -m tools.deliver_candidate` from a checkout; the README
already notes this and Phase 11 owns the structured flavor.

**D8 — Verification on a fresh agent dir.** The install is proven against
`PI_CODING_AGENT_DIR` / a fresh agent dir, not asserted.

## Section 1 — The package (`packages/engine/`)

- **Files:** `engine.ts` (moved from `.pi/extensions/`), `orchestrator.ts`
  (moved), `package.json` (`name: "engine"` or similar, `keywords:
  ["pi-package"]`, a `pi` manifest listing the two files, no runtime
  dependencies — the guards are dependency-free).
- **The root manifest** (`package.json`): the D3 `pi` seam.
- **The symlinks:** `.pi/extensions/engine.ts` and `orchestrator.ts` →
  `packages/engine/…`, so a checkout needs nothing (D2).
- **The harness rewire:** `ENGINE_IMPROVEMENT` in `harness/runner.py`
  points at `packages/engine/engine.ts` (was `.pi/extensions/engine.ts`);
  the pinning tests (`tests/test_engine_doc.py`,
  `tests/test_orchestrator_command.py`) and the drift pins follow the
  paths.

## Section 2 — The loop breaker merges into the engine

- Delete `.pi/extensions/loop-breaker.ts` (the standalone install copy).
- Retarget `tools/replay_guards.mjs` at the engine bundle, and update the
  `guards.test.ts` "two artifacts" pinning to pin the engine bundle against
  the guard source (the loop breaker is now shipped inside the engine).
- Rewrite the docs: `docs/engine/loop-breaker.md` (drop the "install it
  alone" section; the page becomes "the loop breaker, part of the engine"),
  the README's "only want guard #1?" note, and `docs/engine/usage.md`'s
  "only the loop breaker" section.

## Section 3 — The deferred re-org

- `extensions/orchestration/` → `extensions/implementer/` (update the
  imports/closure that reference the old paths).
- `IMPLEMENTER_EXTENSION_CLOSURE` rewired to the new paths; the
  digest-pinned tests that name the closure are updated to the new
  digests — the unfreeze, proven by the suite (the closure still pins the
  same files, under their new names).
- `tools/author_contract.py`'s "executor" prose → "implementer" (the
  model-facing vocabulary sweep deferred by the Phase 10 final review).

## Section 4 — Install and verification

- Tag `v0.1.0`; the README and `docs/engine/usage.md` document the one-line
  install: `pi install git:github.com/pauleveritt/local-ai-pi@v0.1.0`.
- Verification on a fresh agent dir: the package installs, the guards load,
  `/implement` registers — via the `PI_CODING_AGENT_DIR` seam, not asserted.

## Section 5 — Cycles (one commit each)

1. **The package** — move the two files, write `packages/engine/package.json`,
   the root manifest, the symlinks, rewire `ENGINE_IMPROVEMENT` and the
   pinning/drift tests.
2. **The loop-breaker merge** — delete the standalone, retarget
   replay/pinning, rewrite the docs.
3. **The re-org** — the directory rename, the closure rewire + pinned-test
   updates, the `author_contract.py` vocabulary sweep.
4. **Verification + docs** — the fresh-agent-dir install test, the `pi
   install` docs, the tag.

## Test strategy

- Hermetic throughout; no live Pi, no model, no network.
- **Cycle 1:** the pinning/drift tests follow the moved files; a test
  asserts the `.pi/extensions/` entries are symlinks to the package files;
  a test asserts the root manifest names exactly the two package files
  (the "research tree never loads" property).
- **Cycle 2:** the retargeted replay/pinning tests drive the engine bundle;
  a drift test pins that no user-facing page presents a standalone
  loop-breaker install.
- **Cycle 3:** the closure tests pass against the renamed directory (the
  rewire is proven, not assumed).
- **Cycle 4:** a fresh-agent-dir test installs the package and asserts the
  guards load and `/implement` registers; skipped without Pi, like the
  existing live-gated tests.

## Constraints and norms

- **No new dependencies.** Nothing added to `pyproject.toml`; the package
  has no runtime deps.
- **Git-only, tagged.** `v0.1.0`; no npm.
- **No implementer bundling.** The package is the extensions; `/implement`
  keeps shelling out from a checkout.
- **One source of truth.** The package files are the copies; `.pi/extensions/`
  holds symlinks only.
- **Historical phases keep their terms.**
- **Quality gates:** `uv run ruff check .`, `uv run ruff format --diff`,
  `uv run pyrefly check`, `uv run pytest`, `bun test`, Sphinx `-W` — green
  before each commit.
- **Working style:** branch `phase12-engine-packaged` off `main`, worktree
  in `.worktrees/`. One commit per cycle, test-first, messages in repo
  style (`feat(phase12): …`, `docs(phase12): …`).
- **Verify, don't assert.**

## Definition of done

- `pi install git:github.com/pauleveritt/local-ai-pi@v0.1.0` (or the local
  equivalent) puts the engine in a fresh agent dir: the guards load and
  `/implement` registers, verified, not asserted.
- A trusted checkout loads the engine with zero install (the symlinks).
- `extensions/implementer/` exists, the closure resolves with its pinned
  tests green, and `author_contract.py` speaks "implementer".
- The loop breaker is documented as part of the engine; no standalone
  install path remains.
- All gates green.
