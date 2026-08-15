# Phase 12 — The engine, packaged (shape)

**Date:** 2026-08-14
**Status:** shape — to be brainstormed into a full spec
**Predecessors:** Phase 9 shipped the engine bundle and the two-file interim install; Phase 10 landed the vocabulary and `/implement`; both deferred the npm package and the re-org "to the packaging effort."

## Goal, one sentence

> Make the engine a real pi package — `pi install` from a git repo or npm — so the two-file copy becomes a one-line install, and land the deferred re-org (the directory rename, orchestration consolidation, and the closure unfreeze) at the same time.

## The mechanism

Pi already ships the install path: `pi install git:github.com/pauleveritt/local-ai-pi@<ref>` (and `npm:@org/engine`, local paths, and `pi -e` to try without installing). What the repo lacks is the manifest that makes that command install the *right* thing:

- **The `pi` manifest** in the root `package.json` pointing at exactly the two installable files — `.pi/extensions/engine.ts` and `.pi/extensions/orchestrator.ts`. The manifest disables Pi's convention-directory auto-discovery, so a raw `extensions/` tree (the research caps, the orchestration internals that import typebox) never loads into a user session.
- **A pinned ref** (`v0.1.0` tag) so `pi update --extensions` reconciles to a stable version.
- The engine is dependency-free at runtime (no typebox, no node_modules), so `npm install` in the clone is trivial.

## The deferred re-org, landed here

Phase 9 and Phase 10 both parked these at "packaging time":

1. **The directory rename** — `extensions/orchestration/` → `extensions/implementer/` (the directory name collides with the orchestrator role the vocabulary now names).
2. **Orchestration consolidation into the engine package** — the bounded implementer joins the installable surface (the digest-pinned `IMPLEMENTER_EXTENSION_CLOSURE` gets unfrozen and rewired).
3. **The model-facing vocabulary sweep** — `tools/author_contract.py`'s "executor" prose → "implementer" (deferred by the Phase 10 final review).

## The "already works in this repo" fact, documented

The repo's own `.pi/extensions/` is Pi's project-local extension directory, so anyone working *inside* the clone already gets the guards + `/implement` at project scope with zero install. That fact is true today and undocumented; this phase writes it down (it is also a nice onboarding fact for collaborators). The packaging phase also decides whether `.pi/extensions/` keeps its double duty (project-local load source *and* package source) or splits.

## Open questions (for the brainstorm)

- **npm vs git-only.** `pi install git:` needs no publishing; npm needs an account and a name. Which is the first ship?
- **The `.pi/extensions/` double duty.** Project-local auto-load is what makes "works in this repo" true; the package manifest points at the same files. Do they stay coupled, or does the package get its own directory?
- **The closure unfreeze.** Rewiring `IMPLEMENTER_EXTENSION_CLOSURE` touches the digest-pinned cells and tests — the cost Phase 9 deferred. Confirm the tests that pin it and how the rename is verified.

## Not this phase

- The contract-authoring bridge (Phase 11) — the structured flavor of `/implement`.
- Any new guard, new evidence, or the difficulty-ladder runs.

## Definition of done (sketch)

- `pi install git:github.com/pauleveritt/local-ai-pi@v0.1.0` (or the npm equivalent) puts engine + orchestrator in user scope, verified on a fresh agent dir.
- The re-org landed: `extensions/implementer/`, the closure rewired with its pinned tests updated, the `author_contract.py` vocabulary swept.
- The "works in this repo" fact is documented in `docs/engine/usage.md` (and the README install section).
- All gates green (ruff, pyrefly, pytest, bun, Sphinx `-W`).
