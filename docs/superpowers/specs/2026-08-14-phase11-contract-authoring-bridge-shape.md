# Phase 11 — The contract-authoring bridge

**Date:** 2026-08-14
**Status:** shape — to be brainstormed into a full spec

## Direction, one sentence

> The orchestrator pre-chews a real `HandoffContract` from a
> roadmap/manifest — `tools/author_contract.py` → `HandoffContract` JSON,
> `inspectContract` as the admission gate — and the admitted packet drives
> `/implement`'s structured flavor.

## The goal

`/implement` ships in Phase 10 with one flavor: ad-hoc. The user's prompt
is mapped onto the CLI's flags and shelled out to the existing executor;
nothing is pre-chewed. The typed bridge already exists in pieces —
`tools/author_contract.py` authors a locating contract from a staged
packet, `harness/typed_contract.py` builds a `HandoffContract` for the
four-task smoke set, and `extensions/orchestration/implementer.ts` parses
one — but no path connects a roadmap/manifest to a real handoff packet
that `/implement` can serve.

Phase 11 closes that gap. It makes the orchestrator pre-chew real handoff
packets, so the one `/implement` command gains a second, structured flavor
fed by the contract-authoring machinery instead of an ad-hoc prompt.

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
  `extensions/orchestration/handoff-contract.ts` parses it. Its
  `writableFiles` are exact paths the manifest already declares, not the
  author's judgment; its `validation` is the manifest's command.
- **`inspectContract`** is the admission gate. A packet passes or it does
  not; the leak probe stays a screen behind it, not a second hard gate.

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

## Open questions

1. **Which product is the planned Cycle 6 buying?** A solution-bearing
   implementation plan for safe transcription, or a requirements-only
   contract intended to improve reasoning. The Phase 7 re-plan named the
   decision without settling it; the bridge cannot be fully specified
   until it is.
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
