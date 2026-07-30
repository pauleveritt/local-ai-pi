# Phase 1, Cycle 1 — fixture pair verification results

Manual verification per the [design spec](../specs/2026-07-30-phase1-cycle1-fixture-pair-design.md)
and [plan](../plans/2026-07-30-phase1-cycle1-fixture-pair.md). No grader, no
harness, no model — plain `pytest` run by hand against each fixture.

## Accept-check: `acceptance/` against `reference/`

- Command: `uv run pytest -q` from `examples/agentclinic/phase-1/reference/`
- Exit code: 0
- Result: 4 passed
- Verdict: **PASS** — the suite accepts the known-good solution.

## Reject-check: `acceptance/` against `broken/`

(filled in by Task 6)
