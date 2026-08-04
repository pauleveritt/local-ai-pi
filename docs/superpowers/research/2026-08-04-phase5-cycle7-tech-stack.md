# Phase 5 cycle 7 — one fact, and the suite stopped scoring zero

**Date:** 2026-08-04
**Cycle:** phase 5 cycle 7 — the tech-stack lever
**Model:** `omlx/gemma-4-12B-it-MLX-8bit` · **pi:** 0.83.0
**Suite:** `agentclinic-phase-1-user-story`

> **Publishes no number.** n=6 at `run_timeout=300`, not comparable with any
> n=16/600 s arm. Cycle 8 buys the comparable one.

## The result

| pilot | run-accepted | grader-accepted | Flask errors | timeouts |
|---|---|---|---|---|
| cycle 5 — corrected prompt | 0/6 | 0/6 | 5 | 3 |
| cycle 6 — + loop breaker | 0/6 | 0/6 | 5 | 4 |
| **cycle 7 — + tech stack** | **4/6** | **5/6** | **0** | 2 |

After four arms at zero — 0/16, 0/16, 0/6, 0/6 — the user-story suite
produced correct solutions. **Five of six runs passed all four acceptance
tests.** Four of those also exited cleanly and count as accepted runs.

## What the lever was

Two facts appended to the guarded orchestrator prompt as a `## Technology`
section: the application is **FastAPI** with Jinja2 templates, and the graded
module is **`app.py` at the project root** exposing `app`.

Nothing else changed. The task spec is untouched and still names no framework
— a test asserts that, because a lever that leaked into the spec would be a
different workload rather than a steered run of the same one.

## Why the credit belongs to the lever and not the quiet machine

The owner paused another workload partway through this cycle, so the pilots
did not all run under the same conditions. Measured, not assumed:

| pilot | aggregate throughput |
|---|---|
| cycle 5 | 12.38 tok/s |
| cycle 6 | 10.75 tok/s |
| **cycle 7** | **17.46 tok/s** |

Cycle 7's machine was ~40–60% faster. **So the timeout comparison across
pilots is confounded and no claim is made from it** — the drop from 3 and 4 to
2 may be contention, not the lever.

The correctness result is not confounded, for two independent reasons.
`GradeResult.accepted` depends only on whether the acceptance tests passed;
it never consults wall clock. And contention cannot turn a Flask application
into a FastAPI one. **Flask errors went 5 → 5 → 0, and grader-accepted went
0 → 0 → 5.** A faster machine does not write different code.

## What was actually wrong, corrected

Cycle 4's and cycle 5's records both blamed **file layout** — `index.html`
versus `home.html`, `test_app.py` placement. Both now carry corrections. The
acceptance file disclaims layout in its own docstring:

> *"Do not assert on internal function names or file layout — a
> correct-but-different solution must pass."*

Its only structural coupling is `from app import app`. Reading the grade
output of every run that wrote `app.py` — six in cycle 4, five in cycle 5's
pilot — gives one identical failure:

```
TypeError: Flask.__call__() missing 1 required positional argument: 'start_response'
```

The model wrote **Flask**, a WSGI framework, and the suite drives the
application through Starlette's ASGI `TestClient`. Every test errored during
setup, before asserting anything about the page. The applications were
otherwise plausible — right module, right templates directory, tagline
present.

That failure was one query away from the start. Cycle 4 read the *file list*
and inferred a cause; nobody read the grade output until cycle 7 needed to
scope a lever. The lesson is narrow and cheap: **when a graded run fails, read
what the grader said.**

This also replicates the prior project's dominant failure mode on its
comparable arm — recorded there as *wrong-framework (flask)* — which was a
prediction and is now an observation of our own.

## Predictions, scored

| # | Prediction | Outcome |
|---|---|---|
| 1 | `TypeError: Flask` disappears | **CONFIRMED.** 5 → 0. |
| 2 | Acceptance rises above zero | **CONFIRMED**, and by more than the phrasing anticipated: 5/6 grader-accepted, 4/6 run-accepted. |
| 3 | Timeouts do not improve | **NOT SCORED.** They fell 3–4 → 2, but the throughput difference makes the comparison uninterpretable. Recorded as unscored rather than claimed either way. |

The spec named a third outcome as the most informative — Flask gone but
acceptance still zero, implying an unnamed cause. That did not happen: the two
facts were sufficient.

## What is still open

**The hang.** Two runs timed out, and one produced no passing tests at all.
The unbounded child is untouched by everything in cycles 5–7, and it remains
the only known cause of a correct solution failing its run — the exit veto
refuses to certify a run whose Pi did not exit cleanly, which is right, and it
cost run 4 here and cycle 2's runs 12 and 13 before it.

**The loop breaker still has not fired** — zero `loop_broken` entries across
both pilots that carried it. Its case rests on replay, as cycle 6 recorded.

## Evidence

`~/local-ai-pi-evidence/satyrn-phase5-cycle7-stack-n6-t300.jsonl`, outside
version control, retaining full `pi_stdout`.

An earlier attempt at this pilot was killed after three records and the
checkpoint deleted, because those runs were contended. That was a deliberate
discard of three real runs to keep the pilot internally consistent, made on a
stale reading that the checkpoint was empty — recorded here rather than left
out.
