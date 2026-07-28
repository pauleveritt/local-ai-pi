# Writing an Eval Suite

Small models (12B, even 27B) can get off-track with agentic coding. They wind up in the ditch, for a number of common
reasons. We want to help Local AI succeed by keeping the model on the right path.

Part of this means post-training a model. But the bigger help *by far* is in the harness. Especially with an agent like
Pi, we have many leverage points to steer a small model. It's simple: you have a great idea for steering, you ask Claude
Code, it tells you that you're brilliant then implements it.

You then discover: it didn't work. It was a guess. A good guess, sure, but your hunch was "confounded" (to use a model's
favorite term) by other factors.

There is one true path: evidence. Agents have telemetry that will tell you the problem they had with tons of data. If
you can make a trusted, repeatable eval system, you'll find out what's needed. You can then have a hunch, implement it,
and prove it worked.

In this section we'll write the trusted eval system. But the system needs Python workflows that simulate a session. We
call these *suites* and they'll cover whatever Python technologies this project aims to make Local AI good at.

This, dear comrade, is where you come in. We're gonna write a boatload of quality suites and learn how to get good at it,
together. That's what this chapter is about.

Nothing here is specific to FastAPI, to Python, or to this course's example app. The four properties below apply to any
acceptance suite grading any agent's output, in any language or framework. The worked example happens to be a FastAPI
complaints board because that's this course's app — treat it as the illustration, not the scope.

## Why

**A passing smoke test is not a passing phase.** That's evidence policy Rule 3, and it's the reason this chapter exists.
"Acceptance" means the phase's literal, stated requirements are met, checked explicitly — not that the agent ran a
command and it exited 0.

That gap is where false confidence lives. An agent writing its own tests grades its own homework — it tests what it
built, a different question from whether it built what was asked. Check only "did the agent's tests pass" and you've
built a mirror, not a grader.

## What

An eval suite isn't one file — it's a handful of distinct parts, each with its own job. Before the four properties below, here's what's actually in the system:

- **The workspace** — a disposable, git-tracked directory the agent actually builds in. Fresh per run, torn down after. Nothing about grading lives here.
- **The reference solution** — a known-good, human-authored implementation of a phase. Used two ways: seeded into the workspace as the starting state for the next phase, and as the "must pass" side of the suite's own self-check.
- **The suite** — the literal test file(s) making the assertions (`examples/acceptance/phase-N/`). This is what most people mean when they say "the tests."
- **The oracle** — the suite acting as *verdict-giver*. Same file as "the suite," different word for a different concern: whether its verdicts can be trusted at all. An oracle has to be validated (shown to accept the reference solution and reject a broken one) before its pass/fail means anything.
- **The grader** — the isolated process that actually runs the suite against the agent's output, outside the workspace, with none of the agent's own configuration able to reach it.
- **Telemetry** — the harness's own instrumentation reading the agent's session: turns, tool calls, delegations. This tells you *what happened*; the grader tells you *whether it passed*. Don't confuse the two — a detailed telemetry trace of a failing run is not itself evidence of success.

A suite that actually grades has four properties. Skip any one and you get a mirror that looks like a grader.

### 1. Harness-owned, human-authored, overlaid last

The agent never sees, edits, or reasons against the suite. It lives outside the workspace, written in *after* the
agent finishes and *before* grading, and it accumulates — phase N's suite checks phases 1 through N.

Each clause earns its keep:

- **Harness-owned**, because the alternative is exactly the mirror problem above. If the agent can see or edit the test
  file, "passing" measures whether the agent noticed the test file, not whether it built the thing.
- **Overlaid after the agent finishes**, so there's nothing to read, satisfy, or route around mid-task.
- **Cumulative**, so that damage to earlier work is *mechanically* visible. An agent that quietly breaks something it
  built two phases ago should fail loudly, not pass because nobody re-checked phase 1.

This failure mode isn't hypothetical. Early in this project, suite-authoring for two phases was delegated to a model,
with a human reviewing afterward — reasonable-sounding, but it doesn't preserve the property. Reviewing a suite means
re-deriving, line by line, whether each assertion catches a real violation — the entire authoring task, done while a
plausible answer already anchors your judgment. The work was discarded and re-authored by hand.

**This applies to the suite. It does not apply to the reference solution.** The reference solution — the known-good
implementation you validate the suite against (property 2, below) — is application code, not a grader. It may be
written by anyone, including a model, delegated freely, with no review-afterward caveat needed. The reason the two
cases are different in kind, not just degree: a model-authored suite grading itself is a rubber stamp on its own
work, but a model-authored reference solution is just an input the human-authored suite has to correctly accept or
reject. **Don't hand-write reference solutions out of an overcautious reading of this property — save that effort
for the one artifact that actually needs it.**

### 2. Non-vacuous, gated in both directions

A suite that passes everything grades nothing. One that collects nothing grades nothing either, and is easier to
miss — it *looks* real, sitting there in the repo. So check both directions:

1. The suite **passes** a known-good, reference solution.
2. The suite **fails** a deliberately broken one.

Direction 2 is where naive suites go wrong: a broken-app fixture that trips an *unrelated* check (say, a phase-1
regression) makes your phase-2 suite look like it caught the break, when a phase-2 suite made entirely of `assert
True` would have passed the same fixture. Isolate each break — change exactly one thing the current phase owns, leave
everything else correct — and confirm the suite fails *that specific* breakage. Do this per phase: a suite that
catches phase 3's breakage but is toothless on phase 1's inherited assertions has the same vacuity bug, one layer
down.

### 3. No model-controlled input reaches the grader

Grading happens somewhere the agent's output can't influence except through the code it wrote — no config files it
touched, no working directory it wrote into, nothing.

This gets defeated by anyone's first attempt, including this project's. The instinct is to blacklist the obvious
vectors — strip the test file, reset the config — and call it closed. It never is. This project's hardened grader
was defeated twice by a different reviewer, both times by unblacklisted input: an alternate config format that
outranks the checked one, and a process that exits before the grader's accounting code runs, forging a pass.

Both defeats share a shape: exit code 0, *zero tests executed*. That's why "exited 0" is never sufficient — you need
a positive, expected count of tests that ran. The lesson: **blacklisting an open category never closes it.** You can
enumerate known vectors; the input-format space isn't enumerable. The fix is an architecture where the agent's output
can't reach the grading process's config or control flow — allowlist source artifacts, write your own config into a
directory the agent never touched, run from there.

### 4. Adversarially reviewed

The suite that grades everyone else doesn't get to grade itself. Have someone else — a different model, if one helped
write it — actively try to defeat it: an input that shouldn't pass but does, or a correct solution rejected for the
wrong reason. Nearly every gap this project found in its own suite (including both defeats above) was found this way.

## How: deriving a suite from a loose spec

Suites are usually built against a detailed spec — "the route is `/complaints`, the field is `created_at`." That's
the easy case: the spec already tells you what to assert. The harder, more realistic case — and the one that
transfers to open source, where contributors arrive with wildly different stacks and no file-level spec — is
deriving a suite from a **loose, business-level description** of what the software should do.

Here's the exercise. Don't open the existing detailed suite yet.

**Start from the story, not the implementation.** This app has a higher-level roadmap rewrite,
`examples/agentclinic/specs/roadmap-user-story.md`, stating each phase as a user-facing outcome. Phase 1 doesn't say
"create `templates/home.html`" — it says an agent arriving at the home page "should feel invited in," names an exact
tagline, and describes a shared identity (valid HTML5, a brand name, two nav links) every page carries.

**Walk the story and pull out assertions, phase by phase:**

1. Read one phase's section only. Resist reading ahead — a suite for phase N should be derivable from phase N's story
   plus whatever phases 1..N-1 already established, the same incremental discipline the harness itself uses when it
   seeds a workspace from prior-phase state.
2. For every checkable claim, write down what you'd assert and how. "Feel invited in" isn't checkable; the exact
   tagline is. "Consistent identity" isn't, on its own; "every page has the brand name and both nav links" is. This
   translation — vague language in, literal assertions out — is the skill this chapter teaches. It's also where a
   suite quietly goes vacuous: no concrete check means that requirement isn't tested, no matter what you tell
   yourself.
3. Ask, for each assertion: does this belong to *this* phase, or is it actually re-testing something an earlier phase
   already owns? Shared navigation described again in phase 2's story doesn't need a new assertion — it needs the
   phase-1 assertion to still be in the cumulative suite, still running.
4. Apply property 2 from above as you go: for each assertion, can you picture a broken implementation that would slip
   past it? If the answer is
   "sort of," tighten the assertion until it isn't.

**Prove it non-vacuous for real, not by eyeballing it.** Property 2 isn't satisfied by imagining a broken
implementation — run your derived suite against one. This project ships exactly the fixture for this:
`examples/reference/phase-1/`, `phase-2/`, and `phase-3/` are spec-compliant, no-workaround implementations of each
phase, built for precisely this check. `tests/test_oracle.py` is the worked example — it overlays each reference
solution into a fresh workspace and requires the suite to pass it (Direction 1). Do the same with your derived
assertions before trusting them: if your suite doesn't pass the reference solution, either your assertions are wrong
or your understanding of the story is. Either way, that's a finding, not a step to skip.

**Now compare against the real thing.** Open
[`examples/acceptance/phase-1/test_acceptance.py`](../../examples/acceptance/phase-1/test_acceptance.py)
and its siblings. Your derived assertions should line up closely — not because the answer was hidden, but because you
and the original suite derived from the same contract through different doors (loose story vs. detailed roadmap).
That convergence is the finding: **the loose and detailed specs describe the identical app**, and a suite built
correctly from either grades the same thing. There's no second suite to author — the existing one already covers
this looser roadmap's contract, which is why this project never built a parallel one.

If your derived assertions *don't* line up — you asserted something the real suite doesn't check, or missed something it
does — that's not a failure of the exercise. Go back to property 2 and property 3 above and ask which side has the gap.
Sometimes it's you; sometimes, in this project's own history, it's been the suite.

## How: running it, reading it, and using it

Writing the suite is half the job. The other half is running it enough times to trust what it tells you, reading
what comes back, and using that to form your next hypothesis rather than a guess.

### Running the eval

A single run provisions a fresh, disposable workspace, invokes the agent headlessly against a phase prompt, overlays
the suite after the agent finishes, grades, and reduces the result to outcome, turns, timing, changed files, and
pass/fail. A *batch* is N of these run sequentially — never concurrently, a shared local model has no isolation
between requests, and this project has the scars from finding that out by accident — reduced to a report written
into `research/`.

This project's own scripts are the concrete recipe, not a general-purpose runner — they're wired to one app and its
three phases, not "suite 1 of many":

```bash
uv run python scripts/scout.py 1
```

runs an unsteered batch against AgentClinic's phase 1; `scripts/steered_batch.py <phase>` runs a delegated one. A
different suite for a different app needs its own driver, but the same shape — provision, invoke, overlay, grade,
reduce, repeat.

### The purpose of n=

One run is an anecdote, not a rate. Agent behavior is stochastic — sampling temperature alone means the same prompt
against the same model can pass once and fail the next time — so a single pass or fail tells you almost nothing
about what will happen next time.

This project's discipline, worth borrowing directly: **scout, then pool.** Run a cheap n=4 first. If the result is
clearly one-sided, that's your signal; if it's ambiguous, escalate to a pooled n=16 rather than trusting the small
sample. Critically, the thresholds for "clearly one-sided" are fixed *before* looking at any batch — this project's
own rule is ≥15/16 solved, ≤12/16 a candidate problem, 13–14/16 genuinely ambiguous — so the bar can't drift to fit
whatever number shows up. Deciding "good enough" after seeing the data isn't a threshold, it's a rationalization.

Even a clean n=16 usually can't support a claim that one technique measurably beats another on success rate alone —
detecting a realistic effect size needs on the order of 100 runs per arm, which is rarely affordable. The workaround
this project uses throughout: report **incidence** (how often a specific, countable failure mode occurred) rather
than a success-rate delta, and always attach the sample size. "Hang incidence dropped from 6/16 to 1/16" is a claim
n=16 can support. "Success rate improved" usually isn't, even when the raw numbers moved.

### Reading results and telemetry

Every report this project produces has the same shape, and it's worth knowing what each part is for:

- **The per-run table** — outcome, success, turns, wall time, changed files, and a link to the raw artifact for that
  run. This is the ground truth; everything else is a summary of it.
- **Behavioral instrumentation** — countable signals beyond pass/fail: did the agent touch files it shouldn't have,
  did it destructively replace inherited work instead of extending it, did it report success while the suite
  disagreed. These are where the interesting failures usually live, because they can be true even in a run that
  technically passed.
- **Evidence tiers** — every number is labeled GREEN (artifact-backed, dated, reproducible), YELLOW (real but noisy —
  small n, one model, one provider), or RED (estimated, never presented as a result). A report that doesn't tier its
  own numbers is asking you to trust it on vibes.

Skim an actual one — [`2026-07-28-post-repair-sp2-phase1-tuned.md`](../section-3-sdd/research/2026-07-28-post-repair-sp2-phase1-tuned.md) — to see the shape rather than take it on description.

### From evidence to hypothesis

The point of all this isn't the report — it's what the report lets you do next. The method this whole course
follows: show a failure with recorded evidence *before* proposing a fix (never the reverse), change exactly one
thing, re-measure at the same n, model, seed, and suite, and let the incidence columns — not a vibe, not a single
anecdotal run — tell you whether the change did anything.

A real worked example: this project rewrote a phase's spec to remove an implementation hint it had been leaking,
re-ran the identical batch (same n=16, model, seed, suite), and changed nothing else. Success rate stayed saturated
at 16/16 both times — it had nothing left to say. But hang incidence moved from 0/16 to 6/16, and mean turns from
10.8 to 24.2. That's a hypothesis handed to you by the telemetry, not invented: *something about the less-prescriptive
wording makes the agent work harder to reach the same answer.* Whether that hypothesis holds up, and what (if
anything) is worth fixing about it, is the next batch's question — not this one's.

## What this looks like on your own stack

None of the four properties above mention FastAPI, `pytest`, or Python. If you're grading a different kind of agent
output — a CLI tool, a data pipeline, a different web framework, a non-Python language entirely — the translation is:

- **Harness-owned, overlaid last, cumulative** → your grading step runs outside whatever the agent controls, after the
  agent is done, and checks everything built so far, not just the newest piece.
- **Non-vacuous, both directions** → you have at least one known-good reference the suite passes, and at least one
  deliberately-broken variant per requirement the suite fails, isolated one requirement at a time.
- **No agent-controlled input reaches the grader** → your grading process reads none of the agent's own configuration,
  and confirms a positive, expected count of checks actually ran — not just "the process exited cleanly."
- **Adversarially reviewed** → someone actively tries to break your suite before you trust its verdicts.
- **Scout, then pool** → a cheap small batch first, a pre-registered threshold fixed before you look at it, escalate
  to a larger one only if the small batch is ambiguous.
- **Incidence over success rate** → a countable, specific failure mode with its sample size, not a pass-rate delta
  your batch size can't actually support.
- **Evidence before hypothesis** → change one thing, hold everything else fixed, re-measure at the same size — let
  the telemetry hand you the next question instead of guessing at it.

Start from a loose description of what "done" looks like, the way a real issue or user story would read, and derive
checkable assertions the same way this chapter just walked through. The stack changes; the four properties, the
n= discipline, and the derivation method don't.
