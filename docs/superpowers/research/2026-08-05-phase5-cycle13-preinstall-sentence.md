# Phase 5 cycle 13 — the pre-install sentence

**Date:** 2026-08-05
**Cycle:** phase 5 cycle 13
**Status:** closed — **all three predictions falsified**

Cycle 11 counted 28 child `pip install` invocations across the orchestrated
arm's 16 runs, against the undelegated arm's 2, and proposed the cheapest
possible fix: tell the model the packages are already there.

Both stack prompts now carry:

> **FastAPI, Jinja2, pytest and httpx are already installed and importable.**
> Do not install anything. `python` and `python -m pytest` are on the path and
> resolve to the environment that has them; `pip install` is unnecessary and
> will cost you turns for nothing.

It went into **both** `stack.md` and `orchestrator-with-stack.md`, because
the `## Technology` section is pinned verbatim across them by a drift test
and a one-sided edit would have reintroduced the second variable that
withdrew cycle 11's first attempt.

## The claim is true, and a test keeps it true

A run inherits the harness's own environment through `pi_env()` —
`VIRTUAL_ENV` and `PATH` included — so from a bare workspace
`import fastapi, jinja2, pytest, httpx` succeeds and `python` resolves to the
harness venv.

This was verified **before** the sentence was written, because a false claim
here is worse than no claim: a model told not to install a missing package
cannot recover, where one left alone would have installed it.
`test_the_preinstall_claim_is_true_of_the_environment_runs_actually_get`
asserts it from a temporary directory that is not the repository, and is
mutation-checked by stripping the venv from `pi_env`'s `PATH`.

## Predictions, and what happened

Registered before the arm ran: *child `pip install` calls fall to near zero,
wall clock drops materially, accepted count unchanged at 13/16 ± noise.*

| | cycle 10 (no sentence) | cycle 13 (sentence) |
|---|---|---|
| pip calls per run, sorted | 0,0,0,1,2,2,2,2,2,2,2,2,2,3,3,3 | 0,0,0,0,0,2,2,2,2,2,2,3,4,5,6,7 |
| **pip median** | **2** | **2** |
| pip total | 28 | **37** |
| turns, median | 14.0 | 14.0 |
| context, median | 39,760 | 41,010 |
| run-accepted | 13/16 | 11/16 |
| timeouts | 1 | 1 |

**1. Pip calls did not fall. The total rose, 28 to 37, and the median is
unchanged at 2.** Five runs did drop to zero against cycle 10's three, but
the upper tail grew further — 5, 6 and 7 installs in single runs, against a
cycle-10 maximum of 3. The distribution did not shift; it widened.

**2. Wall clock is not measurable and the prediction is void, not failed.**
Cycle 11's timing finding was withdrawn on the grounds that arms run as
contiguous blocks on a machine whose load varies. This cycle demonstrates
that directly: its *first* batch drifted 27.3 → ~15 tok/s under unrelated
load and is kept as `...-CONTAMINATED-...jsonl`; the rerun on a quiet
machine holds a 13.3–25.6 band. Cycle 10's own range is 3.7–25.0, so the
baseline was contaminated too. No wall-clock comparison between these arms
means anything.

**3. Accepted fell to 11/16 from 13/16**, which is noise at this n and is
reported as noise. Turns and context — both counts, both unaffected by
machine load — are flat.

## What the cycle actually found

**A single unambiguous sentence about a checkable fact does not change
behaviour.** This is cycle 8's persuasion ceiling reproduced under the
easiest possible conditions. Cycle 8's stop-repeating rule could at least be
argued away as asking the model to maintain state across turns. This asks
for nothing: the claim is verifiable in one command, the instruction is one
clause, and it is the second thing in the prompt.

The model installed packages anyway, at the same median rate, in an
environment where the packages were already importable.

That result is worth more than the cost saving it failed to deliver, because
it narrows what prompt text can be expected to do. The three prompt
interventions that worked — the call shape, the empty workspace, the
technology stack — all supplied a **fact the model did not have**. The two
that failed — cycle 8's stop rule, and this — supplied a **rule of conduct**.
Five cycles now separate cleanly along that line.

**It also removes the cheap answer to the cost question.** The Backlog holds
the owner's structural version: one agent owning the environment with
`pip`/`uv`/`venv` denied to every other agent. This cycle was the
instruction-shaped alternative to that, and it is refuted — which strengthens
the case for enforcement, without making it a scheduled cycle, since the
condition that a guard needs a workload whose failures it can fix is
unchanged.

## Hardening the counting

Cycle 11 published a "4.4× tool-call ratio" and refusal counts of 294
against 65, all substring matches over the raw event stream. Five tests over
synthetic streams now pin the parsed counters: a refusal echoed across five
event types counts once, cumulative subagent updates do not multiply a
child's call count, and every delegation is read rather than only the last.
Both historical bugs are mutation-checked as caught.

**The reflex survived the fix.** The first status check on this cycle's own
arm reported 690 pip "mentions" for one run; the parsed figure is 2. It was
caught before publication, three commits after writing the tests meant to
prevent it. The lesson recorded is that the guard has to sit in the tooling,
because the habit of reaching for a substring count at a terminal does not
go away.

## What this cycle cannot settle

- Whether *enforcement* removes the installs. Nothing here tests a `tool_call`
  denial; it tests instruction only.
- Whether the installs cost anything. Turns and context are flat between the
  arms, and the wall-clock question is unanswerable until runs are
  interleaved across arms — filed in the Backlog as a precondition for any
  future timing claim.
- Why the tail widened. Three runs at 5–7 installs is the only signal
  pointing the wrong way, and n=16 cannot say whether it is real.
