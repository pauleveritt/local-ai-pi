# Evidence index: the bounded-implementer path

What backs the claims in [`README.md`](../README.md) and
[`docs/architecture.md`](architecture.md), classified by what kind of
evidence each item is. **Scope:** the Phase 7 typed-contract / bounded-
implementer product line only (`harness/typed_contract.py`,
`extensions/orchestration/`, the `gemma12b-implementer-v1` cell). It does
not attempt to re-classify the wider Phase 1–6 record —
[`docs/superpowers/index.md`](superpowers/index.md) is the cycle-by-cycle
index for that, and it predates this page.

| Item | Category | What it establishes | What it does not |
|---|---|---|---|
| [`2026-08-11-phase7-cycle7-preregistration-design.md`](superpowers/specs/2026-08-11-phase7-cycle7-preregistration-design.md) | **Pre-registration** | The frozen 4-task × 2-arm × n=8 design, acceptance definition, and superiority margin, committed before any confirmatory attempt ran. | Not itself a result. |
| `gemma12b-implementer-v1.toml`'s own description field (`workloads/svcs/cells/`) | **Pilot** | Early per-task candidate-created / oracle-passed counts across two informal rounds, ahead of pre-registration — the data that selected the 4-task cohort and n=8. | Not confirmatory (governing rule 8); no dedicated write-up exists beyond the cell file's own description — a real gap, not a hidden one. |
| [`2026-08-11-phase7-cycle7-confirmatory-result.md`](superpowers/research/2026-08-11-phase7-cycle7-confirmatory-result.md) | **Confirmatory result** | The 64-attempt batch's per-task and pooled `oracle-passed` rates, Wilson/Newcombe intervals, floor/ceiling flags, void handling, abort-condition checks — the current evidence for "does a locating contract help." | One task discriminated (`stringified-annotations`); three did not. Not evidence for a fifth task or a general planner. |
| `harness/typed_contract.py`'s `_effective_preservation_command()` docstring | **Correction** | A validation-gate defect (the `flask-extensions` preservation suite rejecting a demonstrably correct fix, traced by reading the model's actual diff against the failing assertions) found and fixed before the confirmatory batch ran. | Recorded in code, not a separate research document — findable by reading the function, not by browsing `docs/superpowers/research/`. |
| `docs/superpowers/research/2026-08-11-phase7-cleanup-and-distribution-brief.md`'s "One correctness gate before distribution" section | **Correction** | The `preserveSymbols`/`removableSymbols` guard contradiction: a contract-blind pre-edit guard could refuse a contract-authorized rename before the mutation engine ever ran. Resolved by removing the redundant guard (`extensions/orchestration/implementer.ts`), not by making it contract-aware. | Confirmed inert for the Cycle 7 batch itself (no task in that cohort declares `removableSymbols`), so the confirmatory result above did not need re-running. |
| `local-ai-pi-evidence-archive/screen-corpus/` (external, sibling directory, not tracked in this repository) | **Raw archive** | A durability copy of `workloads/svcs/screen/`'s 570 files / 106 MiB of mechanism-screen output, checksum-verified, indexed in [`2026-08-11-evidence-archive-index.md`](superpowers/research/2026-08-11-evidence-archive-index.md). | Per-batch validity labels exist for only 1 of 25 subdirectories (`superseded-buggy-grading/`) — see [`docs/contributing.md`](contributing.md)'s starter tasks. |
| `local-ai-pi-evidence-archive/2026-08-11-phase7-cycle7-confirmatory/` (external, not tracked) | **Raw archive** | All 65 attempt receipts, `all_results.json`, and the batch's run log for the confirmatory result above, checksum-verified. | Does not include raw model transcripts or candidate diffs — neither was ever captured to disk for this batch (see that bundle's own `MANIFEST.md` for why). |
| `local-ai-pi-evidence-archive/screen-corpus/superseded-buggy-grading/` | **Superseded** | Self-labeled by its own directory name; not cited as current evidence anywhere in this index or the confirmatory result. | Not otherwise documented here — read the batch's own contents if you need to know what was superseded and why. |

## What this index does not cover

- The Phase 1–6 duration-suite record (`ROADMAP.md`, `BRIEF.md`,
  `docs/superpowers/index.md`) — a different, earlier measurement program,
  not re-classified here.
- 24 of the 25 `screen-corpus` batch directories' individual validity —
  flagged above as an open starter task, not silently assumed.
- The pilot round's full per-attempt detail — only the cell file's summary
  counts survive; the attempts themselves were not archived before this
  index existed.
