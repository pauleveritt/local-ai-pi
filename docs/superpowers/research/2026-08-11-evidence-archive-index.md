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
| Cycle 7 confirmatory batch | `2026-08-11-phase7-cycle7-confirmatory/` | valid, confirmatory | `ab9b59e66b93e01f3661d92f63cf6f9b4d5992338516978ff28178c889713610` |
| `workloads/svcs/screen/` raw corpus | `screen-corpus/` | durability copy of a still-tracked path; per-batch validity labels mostly not yet assigned (see its own `MANIFEST.md`) | `1c319bbd9b45716663bff5a05dc838d515f1e299a6a8b93d9d1525ca84b79adb` |

Each bundle carries its own `MANIFEST.md` (provenance, contents, what is and
is not included, verification instructions) and `CHECKSUMS.sha256`. Verify any
bundle from its own directory with `shasum -a 256 -c CHECKSUMS.sha256`; verify
the manifest itself hasn't been tampered with by re-hashing `CHECKSUMS.sha256`
and comparing against the table above.

## What this index does not yet do

- Does not distinguish pre-registration / pilot / confirmatory / correction /
  superseded / raw-archive at the level of every individual research
  artifact — the distribution brief's step 5 item 5 asks for that across the
  whole `docs/superpowers/` tree, not just archived bundles. This index only
  covers the two bundles above.
- Does not yet carry per-batch status labels for the 24 unlabeled directories
  inside the `screen-corpus/` bundle.
- Does not include `workloads/svcs/overnight/` (7.9 MiB) — that path is still
  read directly by `tests/test_screen.py`, so it is a live test dependency,
  not yet a pure evidence artifact; decoupling it (distribution brief step 3)
  is separate, not-yet-done work.
