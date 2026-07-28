# Writing an Eval Suite

You have a small local model building real software. Before you can teach it
anything, you need to know whether it actually succeeded — not whether it
*says* it succeeded, not whether *some* test it wrote came back green. This
chapter is about building the thing that actually knows: the eval suite.

Nothing here is specific to FastAPI, to Python, or to this course's example
app. The four properties below apply to any acceptance suite grading any
agent's output, in any language or framework. The worked example happens to
be a FastAPI complaints board because that's this course's app — treat it as
the illustration, not the scope.

## Why

**A passing smoke test is not a passing phase.** That's evidence policy
Rule 3, and it's the reason this chapter exists. "Acceptance" means the
phase's literal, stated requirements are met, checked explicitly — not that
the agent ran a command and it exited 0.

The gap between those two things is where false confidence lives. An agent
that writes its own tests is grading its own homework: it will write tests
for what it built, which is a different question from whether what it built
is what was asked for. If you only ever check "did the agent's own tests
pass," you have built a mirror, not a grader.

## What

A suite that actually grades has four properties. Skip any one and you get a
mirror that looks like a grader.

### 1. Harness-owned, human-authored, overlaid last

The suite is not something the agent can see, edit, or reason against while
it works. It lives outside the agent's workspace, gets written into place
*after* the agent finishes and *immediately before* grading runs, and it
accumulates — a suite for phase N checks phases 1 through N, not just N.

Each clause earns its keep:

- **Harness-owned**, because the alternative is exactly the mirror problem
  above. If the agent can see or edit the test file, "passing" measures
  whether the agent noticed the test file, not whether it built the thing.
- **Overlaid after the agent finishes**, so there's nothing to read, satisfy,
  or route around mid-task.
- **Cumulative**, so that damage to earlier work is *mechanically* visible.
  An agent that quietly breaks something it built two phases ago should fail
  loudly, not pass because nobody re-checked phase 1.

This one is worth a real story, because the failure mode it prevents is not
hypothetical. Early in this project, suite-authoring for two phases was
delegated to a model, with a human reviewing the result afterward. That
sounds reasonable — code review is normal — but it doesn't preserve the
property above. Reviewing a suite means re-deriving, line by line, whether
each assertion actually catches a real violation of the contract. That's the
entire authoring task, just done while staring at a plausible-looking answer
that's already anchoring your judgment. The work was discarded and
re-authored by hand.

### 2. Non-vacuous, gated in both directions

A suite that passes everything grades nothing. A suite that collects nothing
grades nothing either, and is easier to miss — it *looks* like a real suite
sitting there in the repo. So the property has two directions, and you need
to check both:

1. The suite **passes** a known-good, reference solution.
2. The suite **fails** a deliberately broken one.

Direction 2 is where naive suites go wrong, and it's worth being specific
about *how* they go wrong: a broken-app fixture that trips an *unrelated*
check (say, a phase-1 regression) will make your phase-2 suite look like it
caught the break, when actually a phase-2 suite made entirely of
`assert True` would have passed the same fixture. The fix is to isolate each
break — change exactly one thing the current phase is responsible for, leave
everything else correct — and confirm the suite fails *that specific,
isolated* breakage. Do this for every phase your suite covers, because a
suite that catches phase 3's breakage but is silently toothless on phase 1's
inherited assertions has the same vacuity bug, just hiding one layer down.

### 3. No model-controlled input reaches the grader

Grading happens somewhere the agent's output can't influence except through
the interface you intended (the code it wrote). No config files the agent
could have touched, no working directory the agent could have written into,
nothing.

This one gets defeated by anyone's first attempt, including this project's.
The instinct is to blacklist the obvious vectors — strip out the test file
the agent might have rewritten, reset the config file it might have edited —
and call it closed. It never is. This project's own hardened grader was
defeated twice by a different reviewer, both times by input types nobody had
thought to blacklist: an alternate config file format that outranks the one
being checked, and a process that exits before the grader's own accounting
code runs, so the grader sees "exit 0, nothing ran" and reports it as a pass.

Both defeats share a shape worth naming explicitly: exit code 0, but *zero
tests actually executed*. That's why "the command exited 0" is never
sufficient — you need a positive count of tests that actually ran, compared
against the number you expected. The general lesson underneath both
incidents: **blacklisting an open category never closes it.** You can
enumerate the vectors you know about; the input format space isn't
enumerable. The fix isn't a longer blacklist, it's an architecture where the
agent's output can't reach the grading process's configuration or control
flow at all — copy in an explicit allowlist of source artifacts, write your
own harness-authored config into a directory the agent never touched, run
from there.

### 4. Adversarially reviewed

The suite that grades everyone else doesn't get to grade itself. Have
someone — ideally someone other than whoever wrote it, ideally a different
model if a model helped write it — actively try to defeat it: find an input
that shouldn't pass but does, or a correct solution that gets rejected for
the wrong reason. Nearly every real gap this project found in its own suite
(including both defeats above) was found this way, by a reviewer looking for
a way to break it, not by the author re-reading their own work.

## How: deriving a suite from a loose spec

Suites are usually built against a detailed, implementation-heavy spec —
"the route is `/complaints`, the model is `models.py`, the field is
`created_at`." That's the easy case: the spec already tells you what to
assert. The harder, more realistic case — and the one that transfers to a
real open-source project, where contributors show up with wildly different
Python stacks and nobody hands them a file-level spec — is deriving a suite
from a **loose, business-level description** of what the software should do.

Here's the exercise. Don't open the existing detailed suite yet.

**Start from the story, not the implementation.** This project's example app
has a higher-level rewrite of its roadmap,
`examples/agentclinic/specs/roadmap-user-story.md`, that states each phase as
a user-facing outcome rather than an instruction list. Phase 1, for instance, doesn't say "create `templates/home.html`" — it
says an agent arriving at the home page "should feel invited in," names an
exact tagline the greeting must use, and describes a shared page identity
(valid HTML5, a brand name, two navigation links) that every page in the
app carries.

**Walk the story and pull out assertions, phase by phase:**

1. Read one phase's section only. Resist reading ahead — a suite for phase N
   should be derivable from phase N's story plus whatever phases 1..N-1
   already established, the same incremental discipline the harness itself
   uses when it seeds a workspace from prior-phase state.
2. For every concrete, checkable claim in the prose, write down what you'd
   assert and how you'd check it. "Feel invited in" isn't checkable; the
   exact tagline text is. "Consistent look and identity" isn't checkable on
   its own; "every page contains the brand name and both nav links" is.
   This translation step — vague experiential language in, literal
   assertions out — is the actual skill this chapter is teaching. It's also
   exactly where a suite quietly goes vacuous: if you can't state a concrete
   check for a sentence in the story, that requirement isn't tested yet, and
   pretending otherwise is how a suite ends up passing everything.
3. Ask, for each assertion: does this belong to *this* phase, or is it
   actually re-testing something an earlier phase already owns? Shared
   navigation described again in phase 2's story doesn't need a new
   assertion — it needs the phase-1 assertion to still be in the cumulative
   suite, still running.
4. Apply property 2 from above as you go: for each assertion, can you
   picture a broken implementation that would slip past it? If the answer is
   "sort of," tighten the assertion until it isn't.

**Now compare against the real thing.** Open
[`examples/acceptance/phase-1/test_acceptance.py`](../../examples/acceptance/phase-1/test_acceptance.py)
and its phase-2 and phase-3 siblings. You should find your derived
assertions line up closely with what's there — not because the answer was
hidden from you, but because both you and the original suite were deriving
from the same underlying contract, just entering through different doors
(the loose story vs. the detailed roadmap). That convergence is the actual
finding: **the loose, business-level spec and the detailed,
implementation-heavy spec describe the identical app**, and a suite built
correctly from either one grades the same thing. There is no second suite to
author here — the existing one already covers the contract this looser
roadmap states, which is precisely why this project didn't build a parallel
suite when the higher-level roadmap was written.

If your derived assertions *don't* line up — you asserted something the real
suite doesn't check, or missed something it does — that's not a failure of
the exercise. Go back to property 2 and property 3 above and ask which side
has the gap. Sometimes it's you; sometimes, in this project's own history,
it's been the suite.

## What this looks like on your own stack

None of the four properties above mention FastAPI, `pytest`, or Python. If
you're grading a different kind of agent output — a CLI tool, a data
pipeline, a different web framework, a non-Python language entirely — the
translation is:

- **Harness-owned, overlaid last, cumulative** → your grading step runs
  outside whatever the agent controls, after the agent is done, and checks
  everything built so far, not just the newest piece.
- **Non-vacuous, both directions** → you have at least one known-good
  reference the suite passes, and at least one deliberately-broken variant
  per requirement the suite fails, isolated one requirement at a time.
- **No agent-controlled input reaches the grader** → your grading process
  reads none of the agent's own configuration, and confirms a positive,
  expected count of checks actually ran — not just "the process exited
  cleanly."
- **Adversarially reviewed** → someone actively tries to break your suite
  before you trust its verdicts.

Start from a loose description of what "done" looks like, the way a real
issue or user story would read, and derive checkable assertions the same way
this chapter just walked through. The stack changes; the four properties and
the derivation discipline don't.
