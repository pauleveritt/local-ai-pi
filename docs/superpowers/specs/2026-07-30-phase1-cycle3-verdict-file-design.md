# Design: Phase 1, feature cycle 3 — verdict from a hook-written results file

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine
**Feature cycle:** 3 of Phase 1 (this cycle only; later cycles get their own spec)

## Purpose

Grade a suite run by reading a file a pytest hook writes, not by trusting
pytest's exit code — because a naive exit-code grader is defeated by
`pytest.ini`'s `addopts = --collect-only` (no tests ever run, but the
process still exits 0) and an import-time `os._exit(0)` (the process exits
0 before pytest's runner does anything). Both are named in `BRIEF.md`'s
account of why this mechanism exists.

This cycle also names the concept the grader has been implicitly returning
since cycle 1's manual procedure: a typed **verdict**, not a bare pass/fail.
Naming it here, deliberately, rather than inheriting whatever name the old
branch happened to use, is the point of this cycle per `ROADMAP.md`.

## Background

Cycles 1–2 proved accept/reject by hand (cycle 1) and then through
`prepare_workspace` (cycle 2), in both cases by asserting on
`subprocess.run`'s return code and captured stdout text. That is exactly
the mechanism this cycle replaces. It doesn't change the fixtures, the
acceptance suite, or `prepare_workspace` — it adds a grading step that runs
*inside* the workspace cycle 2 already provisions.

The old branch's `harness/grading.py` (187 lines, named in `BRIEF.md` as
the strongest transplant candidate) bundled six things into one function:
a separate grader directory, a pinned `pyproject.toml`, a source allowlist,
refusal of model-written config, an AST-derived expected-test count, and
the results-file verdict. This cycle takes only the last two. The
separate directory and pinned dependencies existed solely to support the
allowlist and config refusal, which don't have an argument to stand on
until cycle 4 supplies the fixtures that attack them — building the room
before something needs keeping out of it buys no trust this cycle,
only cost. If isolation or variation is needed before then, the workspace
is already a git repo (per cycle 2) and can supply it without a second
directory.

## Design

### `harness/grading_plugin.py`

A pytest plugin, adapted from the old branch's version with its
now-irrelevant framing removed (the old file's docstring argued for this
mechanism over regex-scanning captured stdout; that argument doesn't need
repeating here, since this cycle starts from the hook-based design
directly). It hooks `pytest_runtest_logreport` and `pytest_sessionfinish`,
appending one line per test outcome plus a final marker line to a results
file, using real per-test hook events — which only fire when pytest's own
runner actually executes a test — rather than anything a model-imported
module could forge into captured output. The results file's path comes
from an environment variable the harness sets before invoking pytest.

### `harness/grading.py`

Exports:

```python
@dataclass(frozen=True)
class GradeResult:
    accepted: bool
    tests_executed: int
    tests_expected: int
    returncode: int
    stdout: str
    stderr: str
```

`accepted` replaces the old `passed` field name — the grader's own
vocabulary (BRIEF and ROADMAP already describe grading in terms of
accepting a known-good solution and rejecting a known-broken one) rather
than pytest's.

```python
def grade(workspace: Path, suite: Path, timeout: int = 30) -> GradeResult:
    """Copy suite into workspace, run pytest there, and return the verdict
    read from the hook-written results file."""
```

- Copies `suite` into `workspace` (mirrors the copy step cycle 2's own
  tests already perform manually before invoking pytest).
- Runs pytest with `cwd=workspace`, loading the plugin via
  `-p harness.grading_plugin` with `PYTHONPATH` set to the repo root (the
  interpreter reads `PYTHONPATH` at startup, ahead of pytest's own
  ini-based `pythonpath` setting — pytest's own plugin resolution happens
  too early for the ini form to help here).
- Allocates a fresh results-file path per call and sets it via the
  environment variable `grading_plugin` reads.
- Reads the results file's contents and hands them, along with the
  expected test count and the process's return code, to a pure verdict
  function that computes `GradeResult`. Splitting this out is what makes
  the conjuncts below testable with hand-crafted input, independent of any
  real pytest run — see Verification method.
- `timeout` defaults to `30`: these are fast, model-free runs (in-process
  `TestClient`, four tests), so every call site in this cycle would
  otherwise repeat the same value for no reason.

The expected test count is computed by AST-parsing `suite` for
top-level `def test_*` functions, unchanged from the old branch's
`_test_count`.

### Verdict logic

`accepted` is true only when all of:

1. The results file contains the `__DONE__` marker line — proves
   `pytest_sessionfinish` actually ran. This is what `os._exit(0)` defeats:
   a hard process exit unwinds nothing, so if it happens before the
   session finishes, the marker is never written. It does *not* catch
   `--collect-only` — pytest still completes its session lifecycle and
   fires `pytest_sessionfinish` normally when collection-only is set, so
   the marker gets written even though no test ever ran.
2. `tests_executed == tests_expected`, and `tests_expected > 0` — this is
   what catches `--collect-only`: the marker is present, but zero tests
   ever executed, so `tests_executed` is `0` against a nonzero
   `tests_expected`. It also rules out any other partial run (some tests
   deselected or never reached) and an empty suite. `tests_executed`
   counts unique nodeids in the results file, not lines — a test whose
   `call` phase passes but whose `teardown` phase then errors appends a
   second line for the same nodeid.
3. Every recorded outcome is `passed`.
4. The process's return code is `0`.

Conjunct 4 is a one-way veto, not a positive signal: a nonzero return code
rejects, but a zero return code alone never accepts on its own — that
judgment is entirely conjuncts 1–3's. This asymmetry is deliberate. A
model can force the return code to `0` (that is exactly what
`os._exit(0)` does), so trusting a `0` as proof of anything would repeat
the mistake this cycle exists to fix. But nothing in this design lets a
model force the return code to be *nonzero* when every real test outcome
was `passed` and the session finished normally — a nonzero code in that
situation reflects a genuine pytest-internal problem (a usage error, an
internal error, or no tests collected), not something forgeable in the
model's favor. Using the return code only as a veto uses it only in the
direction it can be trusted.

## Verification method

`tests/test_grading.py`, two tiers:

**Pure verdict logic** (hand-crafted results-file text, no pytest
subprocess involved) — proves all four conjuncts now, rather than leaving
two of them an argued-but-untested claim until cycle 4's adversarial
fixtures exist:

1. Marker present, `tests_executed == tests_expected == 4`, all outcomes
   `passed`, return code `0` → `accepted` is `True`.
2. Marker missing → `accepted` is `False`.
3. Marker present, `tests_executed == 2`, `tests_expected == 4` (a partial
   run) → `accepted` is `False`.
4. Marker present, counts match, one outcome is `failed` → `accepted` is
   `False`.
5. Marker present, counts match, all outcomes `passed`, but return code is
   nonzero → `accepted` is `False` (the veto).

**End-to-end**, through `grade()` against the real fixtures — mirrors
cycle 1 and 2's accept/reject procedure:

6. `grade(workspace, suite)` against the `reference` fixture (via
   `prepare_workspace`) → `accepted is True`,
   `tests_executed == tests_expected == 4`.
7. Same against the `broken` fixture → `accepted is False`.

## Definition of Done

- `harness/grading_plugin.py` exists, adapted from the old branch's
  version.
- `harness/grading.py` exists with `GradeResult`, `grade()`, and the pure
  verdict function.
- `tests/test_grading.py` exists and passes, covering all seven cases
  above.

## Out of scope for this cycle

Source allowlist and refusal of model-written config (cycle 5); a separate
grader directory and pinned dependencies (cycle 5, and only if the
allowlist still needs them once cycle 4's fixtures exist — the workspace's
own git history is the currently preferred source of isolation if any is
needed before then); adversarial/subversion fixtures themselves (cycle 4 —
this cycle's pure-function tests substitute hand-crafted input for what
cycle 4 will later prove end-to-end through real attacks); checkpointing;
n=16; any change to the fixtures or the acceptance suite from cycle 1.

## Concept budget

Terms this cycle introduces, added to the running list from cycles 1–2
(`feature cycle`, `phase`, `roadmap`, `suite`, `fixture`, `workspace`,
`hermetic`, `oracle`, `harness`):

`verdict`, `hook` (a pytest term of art — the same borrowed-vocabulary
status as `fixture`, already in the budget).
