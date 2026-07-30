# Design: Phase 1, feature cycle 1 — the accept/reject fixture pair

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine
**Feature cycle:** 1 of Phase 1 (this cycle only; later cycles get their own spec)

## Purpose

Establish ground truth for AgentClinic Phase 1: a solution known to be
correct, and a solution known to be broken, each confirmed by running
`pytest` directly. No grader, no harness, no model in the loop.

This is the smallest useful step toward Phase 1's evidence regime — *"A
grader's verdict isn't evidence until it has accepted a known-good solution
and rejected a known-broken one"* — proving the acceptance suite itself has
teeth before anything is built to depend on it.

## Background

AgentClinic Phase 1 is a FastAPI + Jinja2 + Bootstrap home page (no
database, no auth, in-memory). Its contract: `GET /` returns 200, contains
the exact tagline *"Come in. Sit down. Tell us about your human."*, extends
a shared base layout with a navbar (Home → `/`, Complaints → `/complaints`),
and declares HTML5 with `<html lang="en">`.

The grading contract is a separate artifact from the model's own tests: the
acceptance suite is harness-owned and is overlaid into a workspace *after*
a model finishes, so the model can never edit what judges it. This exists
because, on the prior attempt, a model rewrote its own test file with only
the current phase's assertions and went green while prior-phase behavior
went unverified. The acceptance suite must also be human-authored — not
model-drafted-then-human-reviewed — because reviewing plausible assertion
code is a different act from deciding what the contract is; a past attempt
at the latter was discarded outright.

## Fixtures

All new paths live under `examples/agentclinic/phase-1/`. This is a
deliberately simple, single-suite layout — not a general taxonomy for
suites that don't exist yet. Any code that reads these paths must take the
suite name/location as a parameter, never a literal, so the layout can
generalize later without a rewrite.

- **`reference/`** — a known-good Phase 1 solution (`app.py`,
  `templates/base.html`, `templates/home.html`), transplanted verbatim from
  the `user-story-batch` branch's `examples/reference/phase-1/`. No
  changes; it was already validated against this exact suite there.
- **`broken/`** — a known-broken solution, authored fresh for this cycle
  (not transplanted — the old branch's break catalog is orchestration
  machinery this reboot has rejected). Concretely: a bare `FastAPI()`
  instance with zero routes, so `GET /` 404s. Chosen because it fails via a
  clean assertion (`assert 404 == 200`), not an import or collection error
  — a suite that errors on everything would "reject" this fixture for the
  wrong reason, proving nothing about the suite's teeth.
- **`acceptance/`** — the acceptance test suite (the contract),
  transplanted verbatim from `examples/acceptance/phase-1/test_acceptance.py`
  on `user-story-batch`. Human-authored there; unmodified here; never
  edited by whatever it judges.

## Verification method

No isolation, no copy-to-workspace script. Isolation solves a problem this
cycle doesn't have — multiple runs interfering, or a model writing into a
shared directory — and building it now would be machinery ahead of the
contract it serves; it belongs to a later cycle that actually runs things
repeatedly or automatically.

Procedure, run one fixture at a time (never both fixtures' suite-copies
present at once — same-named test modules without `__init__.py` collide):

1. Confirm `fastapi`, `httpx`, `jinja2`, and `turbohtml` are importable via
   `uv run` in this repo. (If any is missing, the broken-fixture check
   below would "pass" via collection error instead of a real assertion
   failure — the exact failure mode this cycle exists to rule out.)
2. Place `acceptance/test_acceptance.py` alongside `reference/`. From
   *inside that directory*, run `uv run pytest -q`. Record the exit code
   and the number of tests passed.
3. Remove the copy. Place `acceptance/test_acceptance.py` alongside
   `broken/`. From inside that directory, run `uv run pytest -q`. Record
   the exit code and the specific assertion that failed.
4. Remove the copy.

Running from inside each fixture directory (rather than the repo root)
keeps `from app import app` resolving the fixture's own `app.py` — but the
repo's root `pyproject.toml`/`conftest.py` is still the effective rootdir
for `uv run pytest`, so any root-level `addopts`/`testpaths`/plugins could
silently affect collection. Worth a one-line sanity check if results look
surprising.

## Definition of Done

- `examples/agentclinic/phase-1/reference/` exists (transplanted verbatim).
  Running the procedure above against it: `pytest -q` exits 0, and the
  recorded output shows a nonzero count of tests passed (not a vacuous
  zero-collection green).
- `examples/agentclinic/phase-1/broken/` exists (freshly authored
  blank-app). Running the procedure against it: `pytest -q` exits
  non-zero, and the recorded failure is a genuine assertion failure (e.g.
  `assert 404 == 200`), not an import or collection error.
- `examples/agentclinic/phase-1/acceptance/` exists (transplanted verbatim,
  unmodified).
- Both results (exit code, test count or failing assertion) are written
  down in this repo — a short results note is sufficient — as the ground
  truth later cycles measure against.

## Out of scope for this cycle

The hermetic grader; any hook-written verdict file; workspace
provisioning/isolation; checkpointing; n=16 batch running; additional
broken fixtures beyond this one case; and the acceptance suite's other
rules from the old branch (cumulative, contract-vs-implementation,
non-vacuous, naming convention) — untouched, not re-argued here since this
cycle doesn't modify the suite.

Also out of scope: which AgentClinic roadmap variant (implementation-detail
vs. user-story phrasing) a model would build from. Moot here since fixtures
are transplanted, not built — becomes relevant when a later cycle has a
model construct a solution from a spec.

## Concept budget

Terms this cycle introduces or relies on, candidates for a Sphinx glossary
once docs exist:

`feature cycle`, `phase`, `roadmap`, `suite`, `fixture`, `workspace`,
`hermetic`, `oracle`.

"Direction" (the old branch's term for the two proof requirements) is
retired in favor of plainer language: **accept-check** (suite accepts the
reference solution) and **reject-check** (suite rejects the broken
solution).
