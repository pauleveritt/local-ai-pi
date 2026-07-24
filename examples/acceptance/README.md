# Acceptance suites — the contract, owned by the harness

These files are **the grade**. They are overlaid into the eval workspace after
the model finishes and immediately before the oracle runs, so the model cannot
edit what judges it.

Why this exists: before Amendment 3, the oracle ran `uv run pytest -q` in the
workspace, which executed `tests/test_app.py` — a file the model writes. A model
that rewrote the suite with only the current phase's assertions passed green
while prior-phase behavior went unverified. That is `lessons.md` #7 exactly, and
it made preservation breakage nearly unmeasurable.

## Rules

1. **Human-authored.** This is the one artifact in the project that should not be
   written by a model, because it is what grades models. Do not delegate it.
2. **Cumulative.** `phase-<N>/test_acceptance.py` asserts the contract for
   phases 1 through N. Phase 2's suite must still check the Phase 1 tagline.
3. **Contract, not implementation.** Assert user-visible behavior and the exact
   literals the roadmap names. Do not assert on internal function names, file
   layout, or anything the roadmap leaves free — a correct-but-different
   solution must pass.
4. **Non-vacuous.** A suite that collects nothing, or that passes a deliberately
   broken solution, fails the oracle gate in `tests/test_oracle.py`. Both
   directions are checked.
5. **Named `test_acceptance.py`**, never `test_app.py` — the latter is the
   model's file and would collide.

## Status

| Phase | File | State |
|-------|------|-------|
| 1 | `phase-1/test_acceptance.py` | Authored — worked example |
| 2 | `phase-2/test_acceptance.py` | **Skeleton — needs authoring** |
| 3 | `phase-3/test_acceptance.py` | **Skeleton — needs authoring** |

Each skeleton carries the contract checklist extracted from
`examples/agentclinic/specs/roadmap.md`. Fill in the assertions; delete the
`test_suite_is_authored` guard when done (it fails on purpose so an unfinished
suite cannot silently grade a batch as all-pass).
