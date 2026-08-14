# Phase 10 — Name the engine

**Date:** 2026-08-14
**Status:** design — approved before any cycle

## Direction, one sentence

> Land the end-user vocabulary — **engine** as the package, **orchestrator**
> and **implementer** as the roles, **guards** as passive steering — in the
> docs and the user-facing code, after the scheduled evidence run, so
> collaborators onboard to a naming regime that is not about to change.

## Why this phase, and why now

Phase 9 shipped the engine bundle and its docs, and the product's second
face is called "the bounded executor" — mechanism-speak the owner wants
gone. The intended vocabulary is the one the project has used internally
all along: the engine is what you install; the orchestrator is the front
you invoke; the implementer is the bounded worker it drives; the guards
steer passively. Onboarding collaborators before this rename would teach
them a naming regime that is about to change, so the rename happens first.

The scheduled evidence run goes first, under the current names, so the
rename afterward is a pure vocabulary change — the evidence and the code
are settled before the words move. Phase 11 — the contract-authoring
bridge, where the orchestrator pre-chews real handoff packets — is the
follow-up; this phase shapes it at the roadmap level so collaborators
arrive knowing what comes next.

## What this phase is not

- **Not the directory rename.** `extensions/orchestration/` stays where it
  is; the digest-pinned `IMPLEMENTER_EXTENSION_CLOSURE` and the cell
  machinery stay pinned. The pins are unfrozen later, at packaging time —
  not in a naming phase.
- **Not in-session TypeScript orchestration.** The orchestrator's substrate
  is the Python CLI (`tools/deliver_candidate.py`); no TypeScript
  orchestration is planned, and it may never happen.
- **Not the contract-authoring bridge.** Pre-chewing real handoff packets
  is Phase 11.
- **Not the npm package.** Still the packaging phase's destination.
- **Not new guards and not new evidence machinery** beyond the scheduled
  run.

## Decisions locked in brainstorming

**D1 — The vocabulary map.** *engine* = the package you install
(`.pi/extensions/engine.ts` today, the npm package later). *orchestrator* =
the explicit front you invoke — it pre-chews a task into a handoff packet
and keeps the implementer's context small. *implementer* = the bounded
worker that executes the packet inside tight budgets. *guards* = passive
steering (fire on `tool_call`). *handoff packet* = what the orchestrator
chews a task into for the implementer. *Agent Engine* = the project/product
name, unchanged. "Bounded executor" retires as the user-facing name for the
second face.

**D2 — The invocation model.** Refusals are passive (the guards fire on
`tool_call` — proven, safe). Actions are explicit (the implementer does
work only when invoked). Small-model skill discovery is unreliable — the
project's evidence shows small models do not reach for capabilities they
are not pointed at — so there is no skill- or rule-based auto-triggering of
the implementer.

**D3 — One user-facing command: `/implement`.** The orchestrator's front.
The orchestrator/implementer distinction may be invisible to users — they
say `/implement` and they are in the engine. Two flavors: ad-hoc prompt
(this phase, the existing bare form) and roadmap/structured packet (Phase
11's bridge).

**D4 — The rename is user-facing code and docs only.** The directory
rename, the digest-pinned closure, and the cell machinery stay pinned and
are deferred to packaging. The CLI module stays `tools/deliver_candidate.py`
(renaming it is churn for no gain); it is documented as the orchestrator.

**D5 — `/implement` is a thin shell-out.** It delegates to
`uv run python -m tools.deliver_candidate` from a checkout. Its value is
the user-facing name and session presence, not new machinery. No TypeScript
orchestration.

**D6 — The evidence run goes first.** The guards-baseline comparison runs
under the current names, so the rename is a pure vocabulary change.

**D7 — Phase 11 is shaped at the roadmap level.** The contract-authoring
bridge — the orchestrator pre-chewing real handoff packets — gets a roadmap
entry and a one-page shape, not a build.

## Section 1 — The evidence run (cycle 1)

Bare control versus `ENGINE_IMPROVEMENT` (guards-only) on
`agentclinic-phase-1-user-story` — the suite where the as-shipped arm
scored 0/16 — pilot n=6 per arm, n=16 if the direction holds. Updates
`docs/engine/shootout.md` with the discriminating comparison and closes the
ROADMAP Deferred-candidates entry. This is the run that tells us whether
the guards rescue failing runs or whether the effect lives in the
executor/stack.

## Section 2 — The rename/re-org (cycle 2)

The vocabulary lands across README, `docs/engine/*`, `docs/glossary.md`,
the evidence-index scope note, and the ROADMAP. "Bounded executor" retires
from user-facing text; the glossary gains engine / orchestrator /
implementer / handoff-packet. Historical phases keep their terms — history
is not rewritten into a cleaner story. Code: user-facing strings in
`tools/deliver_candidate.py` (help and docstrings) and comments in
`.pi/extensions/engine.ts` move to the vocabulary. No directory rename, no
closure changes, no behavioral change.

## Section 3 — The `/implement` command (cycle 3)

A Pi command registered by the engine package, registered via
`pi.registerCommand()`. It takes the user's prompt, maps it and the current
repo onto the existing CLI's flags, shells out to
`uv run python -m tools.deliver_candidate`, and returns the candidate ref
or the refusal. It is the vocabulary anchor — the command surface Phase
11's bridge will serve — not new orchestration.

## Section 4 — Phase 11 shape (cycle 4)

A ROADMAP entry for Phase 11 — the contract-authoring bridge: the
orchestrator pre-chews a real `HandoffContract` from a roadmap/manifest
(`tools/author_contract.py` → `HandoffContract` JSON, `inspectContract` as
the admission gate), driving `/implement`'s structured flavor. Spec-level
shape only; no build.

## Test strategy

- **Cycle 1 (the run):** research, not a unit test — the shootout update
  cites real checkpoints and states its non-claims.
- **Cycle 2 (the rename):** the drift tests (`tests/test_engine_doc.py`)
  updated to the new vocabulary and pinning the renamed terms; the engine
  bundle's pinned tests stay green (no code change to the bundle); Sphinx
  clean under `-W`.
- **Cycle 3 (the command):** a hermetic test that the engine package
  registers `/implement` and that the flag mapping is correct; a live test
  (skipped without a checkout/model) that it reaches a candidate ref or an
  actionable refusal.
- **Cycle 4 (the shape):** roadmap/spec only.

## Constraints and norms

- **No new dependencies.** Nothing added to `pyproject.toml`.
- **No directory rename, no closure/cell changes, no TypeScript
  orchestration.**
- **Historical phases keep their terms.** History is not rewritten.
- **Quality gates:** `uv run ruff check .`, `uv run ruff format --diff`,
  `uv run pyrefly check`, `uv run pytest`, `bun test`, Sphinx `-W` — all
  green before each commit.
- **Working style:** branch `phase10-name-the-engine` off `main`, worktree
  in `.worktrees/`. The phase opens with the ROADMAP entry and this spec;
  then one commit per cycle, test-first, messages in repo style
  (`feat(phase10): …`, `docs(phase10): …`).
- **Verify, don't assert.** Every claim is tested or recorded.

## Definition of done

- The evidence run is recorded: `docs/engine/shootout.md` carries the
  discriminating comparison with its non-claims, and the ROADMAP
  Deferred-candidates entry is closed.
- The vocabulary is consistent across README, `docs/engine/*`,
  `docs/glossary.md`, and the evidence-index scope note; "bounded executor"
  is retired from user-facing text; Sphinx clean under `-W`.
- `/implement` is registered by the engine package and works from a
  checkout — reaching a candidate ref or an actionable refusal.
- The ROADMAP carries the Phase 10 entry (complete) and the Phase 11 entry
  (planned, shaped).
- All quality gates green.
