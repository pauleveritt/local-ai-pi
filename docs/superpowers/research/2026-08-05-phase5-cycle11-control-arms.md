# Phase 5 cycle 11 — the control arms

**Date:** 2026-08-05
**Cycle:** phase 5 cycle 11 — the control arms
**Status:** closed

Cycle 10 published 13/16 against 0/16 and called it the phase's headline.
Four things separated those arms, so the headline could not distinguish
*orchestration works* from *we told it the framework*. This cycle runs the
two controls that separate them, on the same hermetic configuration, at the
same n=16 and 600 s.

Every figure below recomputes with
`docs/superpowers/research/2026-08-04-phase5-cycle8-child-analysis.py`,
extended this cycle with the two control arms and with a parent-side refusal
counter. Run it with `PYTHONPATH=. uv run python <path>`.

> **Retraction, same day.** This record's first reported numbers — a "4.4×
> tool-call ratio" and refusal counts of 294 against 65 — were counted by
> matching substrings in the raw event stream. They are wrong, and wrong in
> a direction that flattered the conclusion being drawn. What replaced them
> is [below](#the-retracted-numbers-and-why-they-were-wrong). The corrected
> ratio is 1.33×.

## The arms

| arm | what it carries |
|---|---|
| **bare** | nothing appended |
| **facts-only** | `stack.md`: the empty-workspace fact and the `## Technology` section, both verbatim from the orchestrator's prompt. Loop breaker kept. No orchestration prose, no seeded specialist, nothing to delegate to. |
| **orchestrated** (cycle 10) | the same two blocks, plus orchestration prose, plus Pi's shipped subagent extension |

Against cycle 10, facts-only isolates orchestration. Against bare, it
isolates the two facts.

## Results

| arm | accepted | timeouts | turns med/max | context med/max | MB med/max | tok/s |
|---|---|---|---|---|---|---|
| bare | 0/16 | 0 | 1.0 / 30 | 1,744 / 1,867,139 | 0.11 / 4.40 | 11.11 |
| orchestrated | 13/16 | 1 | 14.0 / 42 | 39,760 / 674,945 | 0.50 / 5.66 | 11.55 |
| **facts-only** | **15/16** | **0** | 9.0 / 29 | 25,446 / 204,290 | 0.37 / 2.29 | **22.20** |

Run-accepted and grader-accepted agree in all three arms.

**The two facts take the suite from 0/16 to 15/16.** That is the cycle's
result, and it replicates cycle 7 at four times the sample.

**Orchestration's measured contribution is not distinguishable from zero,
and is possibly negative.** 15/16 against 13/16 is Fisher p ≈ 0.6 — nowhere
near a difference at this n, and it must not be reported as one. What is
not noise is the cost: ~1.6× the turns and context for the same outcome.

**The bare floor is a stopped-to-ask zero, and more extreme than cycle 4
recorded.** 15 of 16 bare runs made **zero tool calls** — the model replied
in prose and never invoked a tool. Only run 12 acted at all, and its 29
calls are essentially the whole arm's activity. The bare arm's 1,867,139
maximum context is that single run; its median of 1,744 is the real shape.

## What Phase 5 was for, and what this does not say

Phase 5's aim was to get an improvement to the point where it could be
weighed — a named, digested artifact the harness records, run once end to
end. **That aim is met.** The orchestrator is installable, hermetic,
recorded, and now measured against two controls on identical conditions.
Producing the sentence "it costs 1.6× and buys nothing detectable here" is
the phase working, not the phase failing.

The honest reading of *why* nothing is detectable is that **this suite is
too easy to show a benefit**. A workload where the facts alone reach 15/16
has almost no headroom for orchestration to occupy. That is a statement
about the workload, and the next cycle to schedule is a harder one, not a
verdict on delegation.

## Where the cost goes

Counted over all 48 runs, parsed from events.

| arm | parent calls | child calls | total executed |
|---|---|---|---|
| bare | 29 | 0 | 29 |
| facts-only | 181 | 0 | 181 |
| orchestrated | 50 | 190 | 240 |

**The real executed-call ratio is 240 : 181 ≈ 1.33×.**

The excess decomposes into four things, none of them the ones assumed:

1. **Environment re-derivation.** Children ran `pip install` variants **28
   times** across 16 runs; facts-only ran 2. Each child rebuilds its notion
   of the environment from nothing.
2. **More test cycles.** 63 pytest invocations against facts-only's 28.
3. **Parent verification.** 24 parent reads of files the child had just
   written — inspection, not redoing.
4. **Two churn runs.** Runs 1 and 3 rewrote one file up to 15 times and
   account for **36% of all child calls** and **all 12** child-side
   refusals. Excluding them, child totals fall to 122 and the arms are
   nearly even.

**Delegation itself is disciplined.** Exactly one delegation per run, 16 of
16, every one ending `stopReason: stop`. **Fan-out and retry are both
refuted** — neither occurs anywhere in the arm.

### The throughput gap is dead wall clock, not extra work

| arm | output tokens | wall seconds | s/turn | tokens/turn |
|---|---|---|---|---|
| orchestrated | 34,096 | 2,951 | 11.4 | 131.6 |
| facts-only | 34,080 | 1,535 | 7.8 | 173.0 |

**The two arms generated the same number of output tokens to within 16** —
and the orchestrated arm spent 1,416 extra seconds doing it. Both drive the
same single-threaded model server, so tokens per second is a property of the
server; a 1.9× difference means time spent producing nothing. Child process
startup and the 28 `pip install` invocations are the candidates, and the
arithmetic fits at typical install durations.

**Marked as inference, not measurement.** We have the install counts and the
wall clock; we do not have per-call timings, so the attribution to pip is
not established. Settling it costs one instrumented run.

## The retracted numbers, and why they were wrong

The first pass counted occurrences of `"toolCallId"` and of the refusal
marker as substrings of `pi_stdout`. Both over-count, and — the part that
made it dangerous — **they over-count each arm by a different factor**:

| arm | executed | substring | inflation |
|---|---|---|---|
| bare | 29 | 290 | 10.0× |
| facts-only | 181 | 1209 | 6.7× |
| orchestrated | 240 | 5265 | **21.9×** |

The mechanism is the subagent extension's update protocol. Each
`tool_execution_update` carries the child's **entire message list so far**,
so a child making n calls has its early calls re-serialized in every later
update — quadratic in per-run call count. Runs 1 and 3 each made 34 real
child calls and emitted 70 updates carrying **1,224** serialized toolCall
blocks: 36× per-run. It is also most of why the transcript is 15.2 MB
against 8.4 MB.

The refusal counts were the same artifact re-serialized. Parsed properly:
**orchestrated 12 child-side + 2 parent-side, facts-only 13 parent-side.**
Not 294 and 65. **The hypothesis that churn concentrates in children is
refuted**: refusal pressure is equal across the arms, and in each arm it is
concentrated in a single bad run.

A parent-side counter was added to the recompute script this cycle, because
the existing one only saw child-side refusals and therefore read zero for
every arm that does not delegate — silently, for the two arms this cycle
publishes. A raw substring count of one facts-only run reads 55 where the
true figure is 11: Pi emits the same refusal inside `tool_execution_end`,
`message_start`, `message_end`, `turn_end` and `agent_end`.

**Why this is recorded rather than quietly fixed.** The inflated figure was
reported before it was recomputed, and it happened to support the
conclusion then being drawn. That is the exact shape this project publishes
correction banners for. The rule it violated — a published figure needs a
recompute path — already existed; it was not followed because the number
looked decisive.

## The one failure

Run 4 wrote correct Jinja inheritance and a correct route, then plumbed the
template context through a helper with the wrong shape:

```python
def render_page(request, template_name, content):
    return templates.TemplateResponse(
        template_name, {"request": request, "content": content, ...})

# called as:
return render_page(request, "home.html", {"tagline": tagline, ...})
```

The dict lands under the key `content`, so `home.html`'s `{{ tagline }}`
resolves to nothing and the page renders `<h1></h1>`. Three of four
acceptance tests passed; the tagline assertion failed on the empty heading.

**It is neither a termination failure nor churn** — an ordinary wiring bug,
of the kind a run catches by executing its own tests, which this one did
not. Note the contrast with the withdrawn arm's single failure, which was a
failure to *start*.

## What this changes elsewhere

The enforcement-over-persuasion spec deferred its conclusion to this arm
and named the threshold: if facts-only landed near 13/16, the orchestrator
is scaffolding. It landed above. The bar for any new mechanism is therefore
**beat 15/16 on a suite with no headroom left**, which is not a sensible
target — so the next question is the workload, not the guard.

## What n=16 cannot settle

- Whether the 2-in-16 churn rate is stable. The whole churn tail is two runs.
- Whether the update protocol's re-serialization costs **tokens** or only
  bytes. Context per turn is roughly equal across arms (39,760/14 against
  25,446/9), which suggests the parent does *not* re-ingest the cumulative
  child transcript — but that is an inference from ratios, not a measurement.
  If it does cost tokens, making subagent updates incremental is a real fix.
- Why children pip-install 14× more often than the undelegated arm. A line
  in `stack.md` stating dependencies are pre-installed is a cheap A/B.
- Whether orchestration helps on any workload. Nothing here speaks to that;
  this suite has no room for it to show.
