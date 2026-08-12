# Evidence archive index

**Purpose:** the durable, checksum-verified copy location for this repository's
large or raw research artifacts, per
[`2026-08-11-phase7-cleanup-and-distribution-brief.md`](2026-08-11-phase7-cleanup-and-distribution-brief.md)'s
step 1. Nothing in this archive has been removed from `local-ai-pi`'s tracked
tree — every bundle below is an *additional* copy, not a relocation. The brief
is explicit that this repository's own Git history remains the primary
research provenance; the archive exists for durability and for the future
curated/shareable export (the brief's step 2), which is the actual point at
which repository size is reduced.

**Location:** `local-ai-pi-evidence-archive/` (sibling directory to this
repository, outside Git entirely — no gitignore entry needed, no risk of
accidental commit).

## Bundles

| Bundle | Path | Status | Checksum-of-checksums |
|---|---|---|---|
| Cycle 7 confirmatory batch | `2026-08-11-phase7-cycle7-confirmatory/` | valid, confirmatory | `9a9efa711eb92b20302bbd709db0ca440e7c9efedda58a122b6672e8965194ff` |
| `workloads/svcs/screen/` raw corpus | `screen-corpus/` | durability copy of a still-tracked path; all 25 batches labeled 2026-08-12 in its own `MANIFEST.md` | `589b19418c3b75c970daf0526f083c7a1c17055013fc5bb2d2648abfda2d1def` |

Each bundle carries its own `MANIFEST.md` (provenance, contents, what is and
is not included, verification instructions) and `CHECKSUMS.sha256`. Verify any
bundle from its own directory with `shasum -a 256 -c CHECKSUMS.sha256`, then
re-hash `CHECKSUMS.sha256` itself and compare against the table above.

**Corrected 2026-08-12.** This section previously claimed the second step
proved `MANIFEST.md` was unaltered. It did not: neither bundle's
`CHECKSUMS.sha256` listed its own `MANIFEST.md`, so a manifest could be
edited — including the per-batch validity labels added that day — without
any check failing. Both bundles were regenerated to include `MANIFEST.md`,
and the hashes in the table above are the new ones. The two-step
verification above is now true as written.

## What this index does not yet do

- Does not distinguish pre-registration / pilot / confirmatory / correction /
  superseded / raw-archive at the level of every individual research
  artifact — the distribution brief's step 5 item 5 asks for that across the
  whole `docs/superpowers/` tree, not just archived bundles. This index only
  covers the two bundles above.
- ~~Per-batch status labels for the `screen-corpus/` bundle.~~ Done
  2026-08-12; all 25 are labeled in that bundle's own `MANIFEST.md`.
- Does not include `workloads/svcs/overnight/` (7.9 MiB) — that path is still
  read directly by `tests/test_screen.py`, so it is a live test dependency,
  not yet a pure evidence artifact; decoupling it (distribution brief step 3)
  is separate, not-yet-done work.
