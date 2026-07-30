# Design: Phase 1, feature cycle 5 — refusal of model-written config

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine
**Feature cycle:** 5 of Phase 1 (this cycle only; later cycles get their own spec)

## Purpose

Refuse to certify a run whose workspace contains model-written
configuration. A `pytest.ini`, `conftest.py`, or `sitecustomize.py` in the
workspace can change what pytest does before any test executes, so a
verdict computed from such a run is not evidence about the solution — it
is evidence about the configuration.

Cycle 4 built an attack that does exactly this. This cycle makes the
grader name it.

## Background

`ROADMAP.md`'s cycle 5 row bundled two mechanisms: a source allowlist and
refusal of model-written config. They have different jobs — an allowlist
decides *which model files get graded*, refusal decides *whether the run
is legitimate at all* — and only the second has a motivating fixture
today. Cycle 4's `--collect-only` attack is a config attack; nothing yet
exercises a model scattering stray source files, because no model has run
yet. Following cycle 1's precedent that artifacts precede the machinery
consuming them, the allowlist is split out of this cycle. Its motivating
evidence arrives at cycle 8, the first real run — its placement in the
roadmap is settled when this cycle closes.

**What the old branch actually did.** `harness/grading.py` on
`user-story-batch` collected `refused_config_files` onto its result and
then never consulted it: `passed` was `returncode == 0 and done and
executed == expected and executed > 0`. The field was reported and
ignored. Transplanting that shape unchanged would ship a field nobody
reads, so this cycle deliberately does not.

## Design

### What gets refused

```python
_REFUSED_CONFIG = (
    "pyproject.toml", "pytest.ini", ".pytest.ini", "tox.ini",
    "setup.cfg", "conftest.py", "sitecustomize.py",
)
```

All seven are live vectors for changing how pytest runs — `pytest.ini` and
its hidden-dotfile variant `.pytest.ini`, `tox.ini`'s `[pytest]`,
`setup.cfg`'s `[tool:pytest]`, and `pyproject.toml`'s
`[tool.pytest.ini_options]` all configure the runner; `conftest.py`
supplies hooks and fixtures; `sitecustomize.py` executes at interpreter
startup. Unlike most of the old branch's inventory this list is not
speculative padding, and a partial list would be a hole rather than a
smaller design. The list is derived from pytest's own config-source
order rather than hand-enumerated — see `_pytest/config/findpaths.py`'s
`locate_config()`, whose `config_names` is exactly this set of root-level
names — because a hand-enumerated list is exactly how `.pytest.ini` was
missed in this cycle's first pass.

Matching is root-level for all seven, plus a recursive sweep for
`conftest.py` **only**. The asymmetry is deliberate: a nested
`conftest.py` genuinely affects collection in its own subtree, while a
nested `pytest.ini`/`.pytest.ini` or `sitecustomize.py` is inert — pytest
reads ini files at the rootdir, and `sitecustomize` is imported from
`sys.path`. Sweeping all seven recursively would refuse files that cannot
do anything.

**`pyproject.toml` is the arguable entry**, and it is included with a
recorded reservation. It is the only one of the seven a model might write
for a legitimate reason — declaring dependencies for the app it was asked
to build. AgentClinic Phase 1's reference solution is `app.py` plus
`templates/`, so a packaging file is out-of-task regardless of intent, and
`[tool.pytest.ini_options]` inside it is a live attack path. But we have
no evidence yet about what a model actually writes. If cycle 8's first
real run produces a legitimate `pyproject.toml`, this entry is the one to
revisit. Recorded in `ROADMAP.md`'s Deferred candidates when this cycle
closes.

### What refusal does

Refusal rejects. `accepted` is false whenever any config file is found,
regardless of test outcomes, and the verdict carries which files caused
it. The model is not supposed to author configuration; if it did, that is
either an attempt to influence grading or a mistake, and in both cases the
honest answer is "this run cannot be certified" rather than silently
grading something other than what was submitted.

Notably this cycle does **not** neutralize the config (deleting it, or
overriding with `-c` and an explicit `--rootdir`) and then grade anyway.
That would make the harness mutate the submission and then certify the
mutated thing — the same species of quiet inference that got the old
branch's classifier layer rejected outright.

### When refusal happens

Before pytest runs, and before the suite is copied in.

This is a security property, not an optimization. Under this module's
actual invocation of pytest (`cwd=workspace`, `python -m pytest`),
`conftest.py` genuinely executes at collection time — Python's `site`
module processes `sitecustomize` during interpreter init, before `-m`
puts the workspace directory on `sys.path`, so a workspace-root
`sitecustomize.py` does not in fact execute under this invocation shape.
`sitecustomize.py` stays in the refused list as defense-in-depth against
how the invocation might change (e.g. if the workspace directory ever
ends up on `PYTHONPATH` or `sys.path` earlier), not because it currently
runs. Running the suite anyway would execute precisely the config that
triggered the refusal — including, potentially, the results-file attack
recorded in `ROADMAP.md`'s Backlog. Having decided a run cannot be
trusted, the grader does not then execute it.

### Consequences for the verdict type

`GradeResult` gains `refused_config: tuple[str, ...]`, and `returncode`
becomes `int | None`.

The `None` is load-bearing. With no subprocess there is no return code,
and the old branch's answer to this same situation on its timeout path was
`GradeResult(False, "", "", 0, ...)` — a `0` that means "no process ran"
but is indistinguishable from a genuine clean exit. `int | None` makes
"no process ran" representable instead of disguised, and it is the
observable the verification below leans on.

`_verdict` is unchanged apart from passing `refused_config=()`. It is only
ever reached when nothing was refused, so the empty tuple there is a fact,
not a default.

## Verification method

The trap this cycle must avoid: cycle 3's verdict **already** rejects
cycle 4's `--collect-only` attack, on the count mismatch. A test asserting
`accepted is False` would therefore pass whether or not refusal works at
all. Three of the four tests below exist to make the proof load-bearing.

`tests/test_config_refusal.py`:

1. **Pure `_refused_config`** — a workspace containing `pytest.ini`
   returns `("pytest.ini",)`; one containing a nested `sub/conftest.py`
   returns `("sub/conftest.py",)`; a clean one returns `()`.
2. **Refusal fires** — `grade()` against cycle 4's
   `_attack_with_collect_only` asserts `refused_config == ("pytest.ini",)`
   **and `returncode is None`**. The second assertion is the load-bearing
   one: it is the only observable proving pytest never ran, which is the
   entire point of refusing early. `accepted is False` is asserted too,
   but proves nothing on its own and is not relied upon.
3. **Control, clean fixture** — `grade()` against `reference` asserts
   `refused_config == ()` and `accepted is True`. Proves the list is not
   simply always populated.
4. **Control, attack carrying no config** — `grade()` against cycle 4's
   `_attack_with_exit_at_import` asserts `refused_config == ()` and
   `accepted is False`. Proves refusal is specific rather than blanket:
   that attack writes no config file, so it must still be caught by cycle
   3's completion-marker logic rather than by refusal.

Tests 2 and 4 import cycle 4's `_attack_with_collect_only` and
`_attack_with_exit_at_import` from `tests/test_subversion.py` — the reuse
cycle 4 shaped its helpers for. Test 1 builds its own directories by hand,
and test 3 uses cycle 1's `reference` fixture.

## Definition of Done

- `harness/grading.py` has `_REFUSED_CONFIG`, `_refused_config()`, the
  early-refusal branch in `grade()`, and `GradeResult` carrying
  `refused_config: tuple[str, ...]` with `returncode: int | None`.
- `tests/test_config_refusal.py` exists and passes, covering all four
  cases above.
- The full suite passes: 21 existing tests plus this cycle's, with **no
  existing test modified**. `GradeResult` has exactly one construction
  site (`_verdict`, in `harness/grading.py`); no test builds one directly,
  so adding a field breaks nothing. If an existing test does need editing,
  that is a signal the change is larger than this spec describes — stop
  and re-brainstorm rather than adjusting the test.

## Out of scope for this cycle

The source allowlist, split out as described above. Neutralizing config
rather than refusing it. The results-file attack in `ROADMAP.md`'s Backlog
— unchanged by this cycle, and explicitly not closed by it. Timeout
handling in `grade()` (`subprocess.TimeoutExpired` is still uncaught;
recorded as a Deferred candidate for cycle 9 or 10). Any change to cycle
1's fixtures, the acceptance suite, `harness/workspace.py`, or
`harness/grading_plugin.py`.

## Concept budget

This cycle introduces one term: `refusal` — the grader declining to
certify a run at all, as distinct from rejecting a solution. The
distinction earns its keep: a rejected solution failed the suite; a
refused run was never judged.

**Corrections to the running list**, from an audit of cycles 1–4:

- **`oracle` is dropped.** Outside the four concept-budget lists
  themselves, it appears exactly once on this branch: `BRIEF.md` line 119,
  "the old oracle suite is 71 tests, green" — a passing reference to prior
  work on the `user-story-batch` branch, not a term any spec, plan, test,
  or module here uses. Carrying a term across four cycles to support one
  backward-looking sentence is exactly the cost this budget exists to
  catch. `BRIEF.md`'s sentence stands as written; it just doesn't need the
  word kept in circulation for the current design.
- **`accept-check` and `reject-check` are restored.** Cycle 1 introduced
  them (retiring the old branch's "direction"), but cycles 2–4 dropped
  them from the carried list despite their being used in five files.
- **`conjunct` is retired in favour of `condition`.** Cycles 3 and 4 used
  it in prose without ever counting it. It is a logic term, not a project
  term, and "condition" costs a contributor nothing.
- **`vacuous` is counted, not retired.** Cycles 1 and 4 and `ROADMAP.md`
  all use it, and it names something with no short plain-English
  equivalent: a test that passes without testing what it claims. It is
  load-bearing in this cycle in particular.

The corrected running list, carried forward from here:

`feature cycle`, `phase`, `roadmap`, `suite`, `fixture`, `workspace`,
`hermetic`, `harness`, `verdict`, `hook`, `accept-check`, `reject-check`,
`vacuous`, `refusal`.
