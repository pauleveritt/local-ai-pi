# Phase 11 — The contract-authoring bridge

**Date:** 2026-08-14
**Status:** shape — to be brainstormed into a full spec
**Context:** Phase 12 merged after this shape was first written — the
engine is now a packaged pi package (`packages/engine/`, `engine.ts` +
`orchestrator.ts`, a `pi` manifest), `extensions/orchestration/` is
`extensions/implementer/`, and the loop breaker is folded in. The paths
below are current; the mechanism and the open questions are unchanged.

## Direction, one sentence

> The orchestrator pre-chews a real `HandoffContract` from a
> roadmap/manifest — `tools/author_contract.py` → `HandoffContract` JSON,
> `inspectContract` as the admission gate — and the admitted packet drives
> `/implement`'s structured flavor.

## The goal

`/implement` shipped in Phase 10 with one flavor: ad-hoc. The user's
prompt is mapped onto the CLI's flags and shelled out to the existing
executor (`packages/engine/orchestrator.ts` writes the prompt to a temp
file, hardcodes `validation="pytest -q"`, `task=slugify(prompt)`,
`model=ctx.model`). Nothing is pre-chewed. The typed bridge already
exists in pieces — `tools/author_contract.py` authors a locating contract
from a staged packet, `harness/typed_contract.py` builds a
`HandoffContract` for the four-task smoke set, and
`extensions/implementer/handoff-contract.ts` parses one — but no path
connects a roadmap/manifest to a real handoff packet that `/implement`
can serve.

Phase 11 closes that gap. It makes the orchestrator pre-chew real handoff
packets, so the one `/implement` command gains a second, structured
flavor fed by the contract-authoring machinery instead of an ad-hoc
prompt.

## The mechanism

```
roadmap/manifest
  → tools/author_contract.py (author the locating contract, read-only)
  → HandoffContract JSON (writableFiles from the manifest, validation from its command)
  → inspectContract (the admission gate)
  → /implement's structured flavor (the existing bounded implementer)
```

Three pieces, two of which exist and one of which is the bridge:

- **`tools/author_contract.py`** authors the locating contract. It runs
  read-only against a staged packet (base tree plus brief) and refuses
  drafts that are stubs or solution-bearing. Today it writes a draft
  `.md`; the bridge extends it to emit `HandoffContract` JSON.
- **`HandoffContract`** is the wire format, declared twice and kept in
  sync by hand — `harness/typed_contract.py` builds it,
  `extensions/implementer/handoff-contract.ts` parses it. Its
  `writableFiles` are exact paths the manifest already declares, not the
  author's judgment; its `validation` is the manifest's command.
- **`inspectContract`** is the admission gate. A packet passes or it does
  not; the leak probe stays a screen behind it, not a second hard gate.
  **It is the one piece that does not yet exist as code** — named in the
  plans and this shape since Phase 7, still unimplemented.

The admitted packet then drives the existing bounded implementer exactly
as `harness/typed_contract.py` already does for the smoke set. The bridge
is about *who authors the packet*, not about a new executor.

## The two `/implement` flavors

| Flavor | Now (Phase 10) | Then (Phase 11) |
|---|---|---|
| Ad-hoc | Shipped: the user's prompt → CLI flags → executor | Unchanged |
| Structured | — | roadmap/manifest → authored contract → admitted packet → executor |

One command, two inputs. The structured flavor is what the roadmap's
"bridge contracts to the typed handoff" item has pointed at since the
Phase 7 re-plan; this shape is its roadmap-level home, not its build.

## Decisions from the 2026-08-14 review discussion

Three questions came up while this shape was being read; the answers
below are recorded here so the brainstorm starts from them.

**The two handoff lineages can be consolidated — deliberately.** The
eval's prompt packet (the orchestrator model chews a task into four
sections — Task, Allowed Files, Acceptance Strings, Validation, in
`improvements/sdd-orchestrator/orchestrator.md`) and the engine's typed
`HandoffContract` overlap field for field. The consolidation path is one
`HandoffContract` as the source of truth, with the prompt packet becoming
a *rendering* of it for the model. **But deliberately, not as a rename:**
they are not the same thing today — the eval packet is model-authored per
run (that authoring is the measured arm), the contract is manifest-authored
and machine-checked. Consolidating moves the eval's model-authored step
into machinery, which is exactly open question 1 — and the eval's
sdd-orchestrator arm is a comparison baseline, so changing the packet
format changes the instrument and the recorded arms must be re-measured,
not renamed.

**The executor stays a CLI; the extension is the front.** The extension
(`packages/engine/orchestrator.ts`) is the in-session surface
(`/implement`); the CLI (`tools/deliver_candidate.py`) is the engine room
— cell pins, `resolve_cell` verification, the Python test suite, the
worktree lifecycle, validation. `orchestrator.ts` shells out to the CLI
(`buildDeliverCandidateArgv`). Fully collapsing into the extension means
porting the bounded-implementer lifecycle to TypeScript and re-establishing
its cell/test machinery there — a large effort for little measured gain
right now. Recorded as a decision, not an open question.

> **Superseded, 2026-08-16.** A disposable spike (`ts-engine-core`, not
> merged) put a number on "large effort": the product-shaped half of the
> lifecycle ported in ~700 lines, one session, fully tested with no model
> calls. "Little measured gain" also doesn't hold — the packaged install
> (Phase 12) ships an `/implement` that only works from inside a checkout,
> which this decision didn't have in view. This is now shaped as Phase 13:
> [shape](2026-08-16-phase13-ts-orchestrator-shape.md). Left in
> place rather than deleted, per this file's own convention of recording a
> decision rather than erasing it. Phase 13's shape names a real
> dependency back onto this phase (which child `/implement` ships with),
> so the two are not independent — see that shape's open question 2.

**The `svcs` suite is wanted as a first-class eval suite — and that is
design work, not registration.** It discriminated where it should in the
Phase 7 confirmatory (stringified-annotations: brief 3/8 → locating-
contract 8/8, superiority, interval excludes 0). But it is a commit-replay
workload (base→target commits, hidden-oracle overlay, cell pins) — a
different shape from the three prompt→acceptance suites, so it does not
drop into the existing `Suite` (task_spec/acceptance/allowlist) shape
without design. Noted as wanted, not yet in any roadmap cycle.

## Open questions

1. **Which product is the planned Cycle 6 buying?** A solution-bearing
   implementation plan for safe transcription, or a requirements-only
   contract intended to improve reasoning. The Phase 7 re-plan named the
   decision without settling it; the bridge cannot be fully specified
   until it is. (This is the question the lineage consolidation hangs on:
   consolidating the eval's prompt packet onto the typed contract is a
   different change depending on which product wins.)
2. **The manifest-to-handoff boundary.** `harness/typed_contract.py`'s own
   guard refuses any task outside its four supported ones, and its
   docstring names this exact decision as what extending it requires.
   Which manifest fields are authoritative for `writableFiles`,
   `validation`, and the readable surface — and which stay human-authored?
3. **Reliable authoring under the gate.** Authoring is the open risk: the
   author's drafts have run stubby and solution-bearing in this phase, and
   the gate plus the leak probe have not been exercised together on a real
   re-authoring pass. If authoring is not reliable, the structured flavor
   is a demo, not a product.

## What this shape does not decide

- It does **not** pick the product Cycle 6 is buying — that stays open.
- It does **not** say authoring is reliable — it says the opposite and
  makes it the first thing the full spec must answer.
- It does **not** scope a manifest format; it names the boundary as a
  question.
- It does **not** consolidate the two handoff lineages in code — that
  consolidation is recorded above as a direction, gated on open question 1.
- It does **not** scope the `svcs` suite as a first-class eval — that is
  wanted but separately needs design work.
