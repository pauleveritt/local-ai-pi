# Design: Phase 1, feature cycle 6 — the AgentClinic task spec

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine
**Feature cycle:** 6 of Phase 1 (this cycle only; later cycles get their own spec)

## Purpose

Put the document a model builds from onto this branch, and fix a grading
regression that document makes reachable.

`test_acceptance.py` has cited `examples/agentclinic/specs/roadmap.md`
since cycle 1. That file has never existed here. Cycle 8's first real run
needs it.

## Background

### This cycle does not choose a roadmap variant

`ROADMAP.md`'s cycle 6 row originally read "transplant **and choose** the
roadmap variant the model builds from" — implementation-detail prose
versus a user-story rewrite of the same three phases. That promotion, made
by the 2026-07-30 re-plan, is withdrawn, and the comparison is back in the
Backlog as a later experiment.

The reason is the phase's own definition. `BRIEF.md`: the engine's first
job is "to reproduce a number we already trust, not to discover one."
Whether a spec's abstraction level changes what a small model can build is
a discovery question — a good one, but not this phase's. Under a
reproduction framing there is no choice to make: you use the document the
trusted number was produced against, which is the detailed variant.

Evidence gathered while that question was (wrongly) live is recorded in
`ROADMAP.md`'s Backlog rather than repeated here. Its short form: the
detailed spec scored 16/16 on Phase 1 at n=16 under this reboot's own
model and Pi version, reproducing the published 15/16; the user-story
variant scored 1/16 bare, for the narrow reason that Phase 1's suite does
`from app import app` and only the detailed variant ever names `app.py`.

### Phase 1's section only

`roadmap.md` on the old branch carries all three AgentClinic phases. Only
Phase 1 is transplanted. Nothing on this branch cites the others, cycle
1's suite declares "Cumulative scope: Phase 1 only", and a model reading
Phase 2 and 3 sections could build ahead — scattering `models.py` and a
complaints template into a workspace whose suite never asked for them,
muddying the first real run and colliding with cycle 9's allowlist
question.

## Design

### The transplanted document

`examples/agentclinic/specs/roadmap.md`, containing the `# Roadmap` title
and the `## Phase 1 — Home Page` section, copied verbatim from
`user-story-batch`. That path and that heading are exactly what
`test_acceptance.py:5` cites, so the citation resolves with no change to
cycle 1's suite.

**Verbatim, with no added commentary.** No note explaining that phases 2–3
are omitted, no harness annotations, no "this document is under test"
banner. This file is read *by the model* at cycle 8; anything added to it
is input to the thing being measured. A reproduction run should differ
from the run that produced the trusted number in as few ways as possible,
and editorial additions are a difference we would be choosing. The
reasoning about scope lives in this spec, where humans read it.

**The smoke-test bullet stays.** Phase 1's section ends by instructing the
model to write `tests/test_app.py`. That instruction was present in the
runs that scored 16/16, so removing it would make our conditions diverge
from the trusted ones — see the next section, which is about making the
grader tolerate it rather than editing the spec to avoid it.

### The grading regression this makes reachable

`grade()` invokes pytest with `cwd=workspace` and **no path argument**, so
pytest collects every test file in the workspace — not just the acceptance
suite the harness copied in. Combined with the roadmap's smoke-test
instruction, a model that follows the spec *correctly* produces extra
tests and fails cycle 3's `tests_executed == tests_expected` condition.

Measured against cycle 1's `reference` solution plus a two-test
`tests/test_app.py`: `accepted=False, executed=6, expected=4,
returncode=0`. A correct solution is rejected.

This is a regression, not a new problem the roadmap introduces. The old
harness ran:

```
pytest -q -p no:cacheprovider -p _pi_grading_plugin -c <config> \
       --rootdir <grader> tests/test_acceptance.py
```

— an explicit path argument, plus a separate grader directory holding only
allowlisted files so model-written tests were never copied in. Cycle 3
carried over neither. The trusted number was produced under a grader that
collected the acceptance suite alone.

**The fix** restores the path argument:

```python
[sys.executable, "-m", "pytest", "-q", "-p", "harness.grading_plugin", suite.name]
```

The suite is already copied to the workspace root as `suite.name`, so this
collects that file and nothing else.

Deliberately *not* chosen: editing the smoke-test bullet out of the
transplanted spec. It would work, and it is the wrong direction — the
16/16 runs included that bullet, so removing it moves our conditions away
from the ones we are trying to reproduce. (An earlier revision of
`ROADMAP.md`'s note on this collision listed that option first; this cycle
corrects it.)

Also not chosen: deriving `tests_expected` from what pytest collected
rather than from the suite file. That discards the count check that
catches `--collect-only`, trading a proven defense for convenience.

## Verification method

Added to `tests/test_grading.py`, alongside the other `grade()` tests:

1. **A workspace carrying model-written tests still grades on the suite
   alone** — `prepare_workspace` over cycle 1's `reference` solution plus a
   `tests/test_app.py` containing two passing tests, then `grade()`,
   asserting `accepted is True` and
   `tests_executed == tests_expected == 4`.

This is a genuine red step, unlike cycle 4's: it fails before the fix with
`accepted=False, executed=6`, and passes after.

The existing suite carries the rest. Cycle 4's `--collect-only` attack must
still be rejected, which proves the fix narrows *what* pytest collects
without weakening the check on *how many* tests ran — the condition cycle
3 built and cycle 4 proved.

No test asserts on the transplanted document's contents. It is data for a
model to read, not code with behavior; the assertion that matters is
cycle 8's, when a model builds from it.

## Definition of Done

- `examples/agentclinic/specs/roadmap.md` exists, containing the
  `# Roadmap` title and `## Phase 1 — Home Page` section verbatim, and
  nothing else.
- `harness/grading.py`'s `grade()` passes `suite.name` to pytest.
- `tests/test_grading.py` has the model-written-tests case above.
- The full suite passes: 31 existing tests plus this cycle's one new test.

## Out of scope for this cycle

The roadmap-variant comparison (Backlog, as a later experiment). Phases 2
and 3 of the AgentClinic roadmap. The source allowlist (cycle 9), which
would independently close this collision by never copying model-written
tests into a graded directory — this cycle's fix is narrower and does not
pre-empt that design. Any actual model run (cycle 8). Any change to cycle
1's fixtures or acceptance suite, `harness/workspace.py`,
`harness/grading_plugin.py`, or cycle 5's refusal logic.

## Concept budget

**No new terms.** This cycle spends only what cycles 1–5 already bought:
`feature cycle`, `phase`, `roadmap`, `suite`, `fixture`, `workspace`,
`hermetic`, `harness`, `verdict`, `hook`, `accept-check`, `reject-check`,
`vacuous`, `refusal`.

Note that `roadmap` now names two distinct documents — this project's
`ROADMAP.md` and the transplanted `examples/agentclinic/specs/roadmap.md`
that the model builds from. That collision is inherited from the old
branch's filename, and it is load-bearing: `test_acceptance.py` cites that
exact path. Renaming it would be a gratuitous divergence from the
conditions the trusted number was produced under. Prose in this project
should say "the AgentClinic roadmap" or "the task spec" when it means the
model-facing one.
