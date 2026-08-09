# Cycle 1 scoring rule — addendum to CYCLE1-PREDICTIONS.md

**Written after seeing task 1 of 8, with the run still in flight.** That timing
is the whole reason this file exists separately: it is pre-registration for the
remaining seven tasks and openly post-hoc for `registry-iter`. Folding it back
into the predictions file would have hidden that.

## The decision

**Cycle 1 is scored on gap closure, not on acceptance.** The scope-violation
rate is reported as a separate finding rather than as a failure.

## What forced it

`registry-iter` was solved. The production change is correct, the oracle went
34 -> 35, gap closed 100%, preservation green, no vanished nodes. The model
then also added `test_iter` to `tests/test_registry.py`, which is outside
`writable`, so it graded `out-of-scope` and `accepted = false`.

Cycle 1 exists to answer one question: does this task have headroom for any
executor? A candidate that closes the entire oracle gap has answered it. If
this executor keeps solving tasks and keeps writing a test alongside, the
acceptance rate approaches 0 while gap closure approaches 100%, and the
headline number states the opposite of the truth.

## Why this is not the harness going soft

The scope rule is doing real work and is not being weakened. Under rule 5 the
graded workspaces receive production paths only, so the model's test **was
never executed** -- it could not grade itself, which is the risk the rule
exists to remove. The violation is recorded, and it is harmless to the
measurement. What is in question is only whether it should additionally count
as an acceptance failure.

For the pilot's confirmatory arms it should, and it still will: `accepted`
keeps its current meaning and is reported alongside. For a positive control
whose only job is headroom detection, it converts a clean positive into a false
negative.

## The finding it becomes

No brief tells the model not to write tests, and writing one is ordinary good
practice. So the scope-violation rate is its own result: **does a competent
executor spontaneously write tests, and how often?**

That question has a cost attached. If contracts have to carry "do not write
tests" to keep candidates in scope, that instruction is a real cost of the
pre-chewed-work pitch, and Cycle 3 should know the number before authoring
anything.

## What gets reported

Three rates, always together, never one alone:

- **gap closed** -- the headroom signal, and Cycle 1's headline
- **accepted** -- unchanged meaning, reported for continuity with later cycles
- **scope violations** -- the new finding, with the paths touched

Fable's stop rule (`<= 2/8` halts the phase on briefs and cohort) is evaluated
against **gap closure**, per this rule.
