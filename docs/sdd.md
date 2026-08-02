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

## Checking a quantitative claim

Research records carry numbers, and numbers are where this project has been
wrong most often. Six times in a single day, in prose that no test looked at:

| Error | What went wrong | Caught by |
|---|---|---|
| A regression intercept read as "23s of fixed overhead" | R² was 0.30; the fit was stated as unreliable and then used anyway. Measured, the floor is 1.6s — off by a factor of 14. | Measuring it, six minutes |
| A 46.1s median offered as a budgeting reference | It was *in-stream* span, next to an instruction to time an *end-to-end* call — about 16% apart, in the direction that under-budgets. | Adversarial review |
| "500 not reachable within 1000 runs" | A search bug published as a finding. | Adversarial review |
| A precision table built on 16 runs | The sample's support was missing two turn values that 32 more runs revealed. | Running the extra runs |
| Tool totals of `bash` 207 / `write` 129 | Never measured. 129 was another batch's figure copied across; 207 matched nothing at all. | Recomputing before commit |
| The paragraph confessing the previous row | It misreported the very numbers it was confessing, having been written from memory of the draft rather than from the draft. | Writing the next cycle's spec |

Before publishing a number, ask:

1. **Am I extrapolating outside the observed range?** Fitting a line to a
   narrow range and reading its intercept is the classic case. So is a
   bootstrap over a sample that is mostly one value.
2. **What exactly does this number measure — in the same units as whatever I
   am comparing it to?** Two counts over different denominators are not
   comparable. Neither are two durations that start and stop at different
   points. And a number can be *correct* while measuring the wrong thing: a
   zero error rate looked like success until it turned out the runs with no
   errors were the runs that never tested anything.
3. **Could a new sample contain a value mine never showed?** A quiet tail is
   not coverage. The 16-run sample's last quarter introduced nothing new, and
   two unseen values surfaced immediately afterwards.
4. **Did this number come from a command whose output I can point to, or did
   I write it down?** The last two rows of the table above are this question
   going unasked. Memory is not a source.

**What is enforced, and what is not.** Question 4 is mechanised for one thing
only: a record's per-run table is diffed against its script's committed output
by `tests/test_research_records.py`. Everything else on this page is a human
check. Neither fabricated number above was in a per-run table — one was a cell
in a comparison table, the other a paragraph — so the test would have caught
neither. A green suite means the per-run table was transcribed correctly. It
says nothing about the tables and paragraphs around it.

**And the test proves less than it looks like it proves.** It compares a record
against a committed text file. A hand-written text file passes identically.
What makes that file trustworthy is the checkpoint SHA-256s recorded in the
record beside it, and whoever ran the script — not the test.

**Why the output is committed and the data is not.** The raw checkpoints are
tens of millions of bytes of model output and stay outside the repository; a
script's output is a few dozen lines. Committing the small artifact is what
lets the check run on a fresh clone, where the data will never exist.

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
