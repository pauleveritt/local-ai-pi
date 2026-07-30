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

- Command: `uv run pytest -q` from `examples/agentclinic/phase-1/broken/`
- Exit code: 1
- Result: 4 failed, all via genuine `AssertionError` — `assert 404 == 200`;
  the tagline and `"AgentClinic"` string absent from the `{"detail":"Not
  Found"}` JSON body; the HTML5-doctype/lang check false. Zero import or
  collection errors.
- Verdict: **PASS** — the suite rejects the known-broken solution, for the
  right reason.

## Definition of Done

Both directions confirmed. This feature cycle is complete.
