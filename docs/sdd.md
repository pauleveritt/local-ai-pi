# How we work: spec-driven development

Every feature in this project goes through the same loop, and the
artifacts it produces are committed rather than thrown away. This page
explains the loop, why we run it, and what it asks of you.

## Why SDD here

This project uses SDD both to *build* the engine and as its first *example
application*. That's deliberate, and there are three reasons for it.

**It keeps the human in the loop.** The roadmap, specs, and plans are where
you put on your thinking cap and steer. Most of the important decisions in
Phase 1 were made in brainstorming, not in code — including several where
the owner rejected a premise an agent had accepted too readily.

**It's a distributed project.** Committed specs and plans let someone who
wasn't there see *why* code emerged the way it did. Even unmaintained,
that's a useful artifact.

**Small models need small bites.** Plan with a big brain, then hand
pre-chewed work to smaller brains. A good implementation plan turns one
large ambiguous task into a sequence of small unambiguous ones — which is
exactly what a 12B model needs to succeed.

## The loop

```
brainstorm  →  spec  →  plan  →  implement  →  review  →  merge
```

**Brainstorm** with the owner, one question at a time. This is where scope
gets decided and bad premises get caught. It ends with an agreed design,
not code.

**Spec** — the design, written to
`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` and committed. A good
spec says what's being built, what's explicitly *not*, and why. The
"what this cycle is not" section earns its keep constantly.

**Plan** — the implementation, decomposed into bite-sized TDD steps in
`docs/superpowers/plans/`. Each step is one action: write the failing test,
run it, see it fail *for the stated reason*, implement, see it pass, commit.

**Implement** the plan test-first, in small commits.

**Review** — we send specs, plans, and finished work to a second model for
adversarial review. This has repeatedly caught real bugs before they
shipped, including an exploitable config-refusal bypass and a checkpoint
corruption bug that would have broken the first resume.

**Merge**, then update `ROADMAP.md`: mark the cycle done, advance the next,
record what got deferred and why.

## Feature cycles and phases

A **feature cycle** is the unit of work — one small, provable thing. A
**phase** groups cycles pursuing one direction. One direction at a time;
tangents go to the Backlog, never into the current phase.

`ROADMAP.md` holds three things:

- **Active phase** — its cycles, each with links to spec and plan.
- **Deferred candidates** — things a cycle's brainstorming considered and
  passed over, so the next session starts from that list instead of
  re-deriving it.
- **Backlog** — parked ideas, each with the reasoning that parked it.

That middle section matters more than it sounds. Phase 1 repeatedly found
that a note written three cycles earlier was exactly the evidence a later
cycle needed.

## The disciplines

These shape review, so they're worth internalizing before your first
contribution.

### Concept budget

Every term the project uses is a cost against a 5-to-10-hour-a-week
volunteer's ability to hold the design in mind. `ROADMAP.md` keeps a table
of every term spent, what it means, and which cycle introduced it. It's
checked at the end of every cycle.

If a doc needs a term a volunteer can't absorb, **the term goes, not the
contributor.** Two terms have already been retired for failing this test.

### No machinery ahead of the contract it serves

Build the engine as needs in the suites arise. Several genuinely good ideas
sit in the Backlog specifically because nothing needs them yet — and one
was promoted to a cycle, designed in full, and then withdrawn when the
owner correctly asked whether the threat it defended against was real.

The withdrawal is recorded, along with its research, in `ROADMAP.md`. That
kind of reversal is a normal outcome here, not a failure.

### Non-vacuity

A **vacuous** test passes without testing what it claims. It's green, so it
looks like evidence, but it would stay green if the thing it's supposedly
proving were broken.

This is the project's recurring hazard, because most of the grading code
tests a *rejection* mechanism — and rejection is the default outcome of
most failures, including uninteresting ones. A badly-written test of a
rejecter is almost guaranteed to pass.

The check: **ask what else could make this test pass.** If the answer
includes anything besides the behavior in the test's name, it's vacuous.
The fix is a genuine red step — break the thing deliberately and confirm
the test fails *for the stated reason*.

### Verify, don't assert

Claims get demonstrated, not argued. When a design claimed that running the
model's app in a separate process would close a forgery gap, we wrote the
exploit and ran it. It didn't — a broken solution graded as accepted — and
the design changed.

This norm has caught more real problems than any other single practice
here. If you find yourself writing "this should mean that…", stop and run
it instead.

## Tooling

We use the [Superpowers](https://github.com/anthropics/superpowers) skills
for the workflow: `brainstorming`, `writing-plans`, `executing-plans`,
`subagent-driven-development`, and `finishing-a-development-branch`. They
work with Pi, Claude, and Codex.

You don't have to use them — the loop matters more than the tooling — but
the artifacts they produce are the ones this repo expects.

## The design record

Every spec and plan from Phase 1 is browsable in
[the development record](superpowers/index.md). Reading two or three
before starting your first cycle is the fastest way to calibrate on what
"done" looks like here.
