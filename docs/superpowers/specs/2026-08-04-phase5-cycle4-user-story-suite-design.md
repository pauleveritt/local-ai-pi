# Phase 5 cycle 4 — the user-story suite and its floor

**Date:** 2026-08-04
**Status:** design
**Phase:** 5 — the improvement loop

## Purpose

Every measurement this phase has made is on a workload where bare Pi scores
16/16. Nothing about what an improvement *buys* is observable there. This
cycle adds a suite with headroom: the same application described as
user-facing outcomes instead of implementation steps.

Then it runs two arms on it — bare and `sdd-orchestrator` — giving the first
comparison in this project where the improvement has something to win.

## The design decision this cycle turns on

**The acceptance contract is shared with `agentclinic-phase-1`; only the task
spec differs.** The user-story document targets the identical application —
same route, same tagline, same layout — so the same acceptance file is not a
convenience, it is a requirement. Two arms graded against different contracts
would not be comparable, and the whole point is to vary *the description* and
nothing else.

Consequences, all deliberate:

- `acceptance_sha256` and `source_allowlist` are identical between the two
  suites. `task_spec_sha256` is what distinguishes them, which is exactly the
  property `test_every_suites_task_spec_digest_is_pairwise_distinct` enforces.
- **The evidence floor is already proven** for this acceptance file, by
  `agentclinic-phase-1`'s reference and broken fixtures. This cycle adds tests
  asserting the floor holds *for the user-story suite's own* `acceptance` and
  `source_allowlist`, rather than inventing a duplicate fixture pair whose only
  difference would be its directory. A second copy of a known-good solution
  would prove nothing the first does not, and would rot separately.

## The leak problem, and the decision

`agentclinic-phase-1`'s task spec ends with an Environment section naming
**FastAPI, Jinja2, pytest, and httpx**. Phase 2 cycle 3 added it because
environment friction was ~95% of turn-count variance, and removing it would
reintroduce that noise.

But naming FastAPI hands over the technology stack — and the prior project's
evidence says that is the single most powerful lever on this workload, taking
a user-story arm from 1/16 to 15/16. Copying the section verbatim would make
this suite a slightly wordier version of the detailed one and measure nothing.

**Decision: a framework-neutral environment note.** The user-story spec states
that dependencies are installed and how to run the tests, and names no library
and no module:

```markdown
## Environment

- Everything you need is already installed. Do not install anything.
- Run the tests with `python -m pytest` from the project root.
```

This still discloses Python and pytest. That is unavoidable while keeping the
environment honest, and it is recorded as a condition of the arm rather than
pretended away.

### The audit the Backlog asks for

*"Grep a spec for the facts its acceptance suite imports. Anything the suite
reaches for that the spec never states is a silent dependency."* Applied:

| The acceptance suite reaches for | The user-story spec states it? |
|---|---|
| `from app import app` — a module named `app` exposing `app` | **No.** Deliberate. |
| `starlette.testclient` — an ASGI application | **No.** Deliberate. |
| a well-formed HTML5 document, `lang` attribute | Yes, in prose |
| the tagline, verbatim | Yes, quoted exactly |
| a shared layout the home page extends | Yes, in prose |

Two silent dependencies remain, on purpose. **They are the experiment.** The
prior project found that supplying the first one alone recovered its arm from
1/16 to 15/16 — flagged there as post-hoc and never replicated, which is what
makes it a prediction worth testing rather than a result to cite.

## Pre-registered predictions

From the prior series, which carries a `PENDING RULE 8 REVIEW` banner and is
therefore a source of predictions only.

1. **The bare user-story arm scores far below 16/16** — the prior unsteered
   arm was 1/16.
2. **The dominant failure is structural, not partial**: solutions that build
   something else entirely, or in another framework, rather than solutions
   that nearly pass. Recorded as failure-mode counts, because a success rate
   alone collapses the distinction that matters.
3. **The orchestrated arm does not rescue it.** The prior as-shipped
   orchestrated arm also scored 1/16, failing for the *opposite* reason — 14
   of 16 wrong-framework against the unsteered arm's 14 of 16
   built-something-else.

A result where both arms score near zero is a real finding, not a failed
cycle: it would establish the headroom this phase needs and localise the
cause to the missing facts rather than to steering.

## Method

Two n=16 batches, sequential, bare and `sdd-orchestrator`, on the new suite.
Same commit-freeze discipline as cycle 2: no commit in the batch's working
directory from any session between the first run and the last.

Telemetry now counts delegated children (cycle 3), so the orchestrated arm's
cost is readable for the first time on a workload with headroom.

## Out of scope

- **Any tuning.** No tech-stack line, no mission or domain document, no packet
  changes. Those are the levers, they are inventoried in the Backlog, and they
  belong in cycle 5+ one at a time. This cycle establishes the baseline they
  will be measured against; tuning it here would leave nothing to improve on.
- AgentClinic phases 2 and 3.
- Thrash metrics, still gated in the Backlog — though this is the first
  workload likely to show thrash, so a later cycle may open that gate.
