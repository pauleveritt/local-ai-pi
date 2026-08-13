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

**Superseded in part, 2026-08-12.** The paragraph above says "Nothing in this
archive has been removed from `local-ai-pi`'s tracked tree — every bundle
below is an *additional* copy, not a relocation," and that the curated export
is "the actual point at which repository size is reduced." Both stopped being
true that day for one bundle. `workloads/svcs/screen/` was untracked from the
working tree — 570 files, 104.7 MiB — after this index's own two-step
verification was re-run against `screen-corpus/` and the file sets compared
one-to-one (570 tracked, 570 archived, none missing either way). The corpus
remains in this repository's Git history; `screen-corpus/` is now the only
*working-tree* copy, which raises its stakes and is why the check was re-run
first rather than trusted. The Cycle 7 bundle is unaffected and remains a pure
additional copy. Reasoning and the surviving `overnight/` decision:
[`docs/contributing.md`](../../contributing.md). The original paragraph is left
as written.

**Location:** `local-ai-pi-evidence-archive/` (sibling directory to this
repository, outside Git entirely — no gitignore entry needed, no risk of
accidental commit).

## Bundles

| Bundle | Path | Status | Checksum-of-checksums |
|---|---|---|---|
| Cycle 7 confirmatory batch | `2026-08-11-phase7-cycle7-confirmatory/` | valid, confirmatory | `9a9efa711eb92b20302bbd709db0ca440e7c9efedda58a122b6672e8965194ff` |
| `workloads/svcs/screen/` raw corpus | `screen-corpus/` | **only working-tree copy** since 2026-08-12 (path untracked; still in Git history); all 25 batches labeled 2026-08-12 in its own `MANIFEST.md` | `589b19418c3b75c970daf0526f083c7a1c17055013fc5bb2d2648abfda2d1def` |

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

  *Corrected 2026-08-12. Step 3 was done, and this bullet went stale without
  being updated. `tests/test_screen.py` no longer reads that path — verified
  by moving the directory away and running the file: 38 passed, only comments
  reference it. The bullet's conclusion still holds for a different reason:
  `overnight/` stays tracked because, unlike the screen corpus, it has no
  out-of-tree copy, so untracking it would leave exactly one.*
