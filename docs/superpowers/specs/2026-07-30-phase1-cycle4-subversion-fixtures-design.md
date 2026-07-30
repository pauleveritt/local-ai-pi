# Design: Phase 1, feature cycle 4 — subversion fixtures

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine
**Feature cycle:** 4 of Phase 1 (this cycle only; later cycles get their own spec)

## Purpose

Build the two attacks that defeat a naive exit-code grader — a
`pytest.ini` carrying `addopts = --collect-only`, and an import-time
`os._exit(0)` — as real fixtures, and prove two things about each: that it
does fool an exit-code check, and that cycle 3's verdict rejects it
anyway.

Cycle 3 built the verdict that these attacks motivate, but proved its
conjuncts against hand-crafted results-file text rather than against the
attacks themselves. This cycle closes that loop with the real thing, and
leaves behind fixtures cycle 5 consumes to prove config refusal.

## Background

`BRIEF.md` names these two attacks as the reason the hermetic grader reads
a hook-written results file instead of pytest's exit code: earlier grader
versions were defeated by both. Cycle 3 implemented that mechanism.

Confirmed empirically before this spec was written, against cycle 3's
shipped `grade()`:

| Attack | Return code | `grade()` verdict |
|---|---|---|
| `addopts = --collect-only` | `0` | rejected — 0 executed against a nonzero expected count |
| import-time `os._exit(0)` | `0` | rejected — no completion marker, 0 executed |

(That check ran against a minimal stub suite; against the real four-test
acceptance suite the expected count is 4, and both attacks still execute
0 tests.)

Both hand a naive grader a clean `0` while containing a test that would
have failed. That is the whole point of the cycle: the attacks are real,
and the verdict already survives them.

## Design

One new file, `tests/test_subversion.py`. Not appended to
`tests/test_grading.py`: that file holds cycle 3's mechanics (does the
grader compute the right verdict), this file holds a different question
(can the grader be defeated), and it is the file cycle 5 imports the
helpers from — so it is named for what it holds.

### The two attack helpers

Each returns a source directory ready to hand to `prepare_workspace`:

```python
def _attack_with_collect_only(tmp_path: Path) -> Path:
    """Cycle 1's broken solution, plus a pytest.ini that stops any test
    from running at all."""


def _attack_with_exit_at_import(tmp_path: Path) -> Path:
    """Cycle 1's broken solution, whose app.py kills the process at import
    time -- before the suite that imports it can assert anything."""
```

Both build on `examples/agentclinic/phase-1/broken` — a solution that
genuinely fails the acceptance suite — rather than on stub content. This
is deliberate: it makes each test demonstrate the attack *laundering a
real rejection into an apparent pass*, which is the threat, rather than
merely demonstrating that zero tests ran.

Built inline via `tmp_path`, not added as new directories under
`examples/agentclinic/phase-1/`. These attack the grading mechanism, not
the AgentClinic task; no model is ever meant to receive them. Keeping them
out of `examples/` preserves that directory's meaning as "case content a
model might plausibly produce."

### Why the helpers exist as named functions

Two callers in this cycle already need the same construction shape, and
`ROADMAP.md` frames cycle 4 as producing artifacts a later cycle consumes
("cycle 5 … proven by rejecting cycle 4's attacks"). The helpers are
justified by this cycle's own contents; cycle 5 reusing them is a
consequence, not the reason.

### A dependency this cycle must pin

**The `os._exit(0)` attack fires only because the acceptance suite does
`from app import app`.** If a suite does not import the model's code, the
attack silently does nothing — and a test asserting "the verdict rejects
this" would still pass, while proving nothing. This was hit accidentally
during the verification above, with a suite that didn't import `app`.

Stated here so a future change to the acceptance suite cannot quietly
neuter the fixture without someone noticing.

## Verification method

Two tests, each proving both halves from a single `grade()` call — cycle
3's `GradeResult` already carries `returncode`, so no separate naive-grader
run or naive-grader module is needed:

1. `test_collect_only_attack_defeats_the_exit_code_but_not_the_verdict` —
   grades `_attack_with_collect_only`'s workspace and asserts
   `returncode == 0` (a naive exit-code grader would accept),
   `accepted is False` (the verdict rejects), and `tests_executed == 0`.
2. `test_exit_at_import_attack_defeats_the_exit_code_but_not_the_verdict` —
   the same three assertions against `_attack_with_exit_at_import`.

The contrast proving the attacks actually *change* the outcome is already
on the record and is cited rather than duplicated: cycle 3's
`test_grade_rejects_the_broken_solution` grades the same unattacked broken
solution and observes a **nonzero** return code. Attacked, it is `0`.

## Definition of Done

- `tests/test_subversion.py` exists with the two helpers and the two tests
  above.
- The full suite passes: 21 tests (19 existing + 2 new).

## Out of scope for this cycle

The source allowlist and refusal of model-written config (cycle 5). Note
that the `--collect-only` attack will end up with two independent
defenses — cycle 3's count mismatch catches it today, and cycle 5's config
refusal will catch it again at a different layer. That is acceptable, not
redundancy to remove.

Any attack beyond the two `BRIEF.md` names. In particular, and by
explicit decision rather than oversight: **the results-file forge.** A
model-authored `app.py` can read the results-file path from the
environment it shares with the plugin and write forged
`nodeid<TAB>outcome` lines and a completion marker directly into the
results file. It is cheap, and cycle 3's design does not close it — no
in-process secret can, since anything the plugin can read, model code
sharing its process can read too. The real fix is running the suite
out-of-process against a live app subprocess instead of in-process
`TestClient`, which is materially larger than this cycle. Recorded in
`ROADMAP.md`'s Backlog at the end of this cycle.

Also out of scope: any change to cycle 1's fixtures or acceptance suite,
to `harness/workspace.py`, or to `harness/grading.py` and
`harness/grading_plugin.py` — all are read-only inputs here.

## Concept budget

**No new terms.** This cycle spends only what cycles 1–3 already bought:
`feature cycle`, `phase`, `roadmap`, `suite`, `fixture`, `workspace`,
`hermetic`, `oracle`, `harness`, `verdict`, `hook`.

"Subversion" stays `ROADMAP.md`'s existing label rather than gaining a
synonym ("adversarial", "attack fixture"). The helpers are named
`_attack_with_*` as plain description, not as a new concept.
