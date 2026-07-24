# Section III — Spec-Driven Development on Pi

Three chapters that install Pi's shipped subagent extension, author an
implementer specialist and an orchestrator parent prompt, then measure and
tune the parent+implementer shape. The structural baseline improved from SP1's
0/8 to 3–4/8 (SP2, n=4 per batch; the 3/8→4/8 tuning delta is one run at n=4
and not statistically significant).


**Status:** ✅ Complete ([spec](spec.md), [plan](plan.md))

**Evidence:** [3/8 pre-tuning](research/2026-07-23-sp2-baseline-phase-1.md),
[4/8 post-tuning](research/2026-07-23-sp2-baseline-phase-1-post-tuning.md),
[deep-dive (5 telemetry gaps)](research/2026-07-24-sp2-deep-dive.md)

## About SDD

This course doesn't require spec-driven development. It uses it for two
reasons, both directly relevant to keeping a small local model on track:

**The handoff packet.** The whole point of a phase contract — a task
checklist, an allowed-files list, acceptance strings, and a single validation
command — is to give the SLM implementer a tight, focused unit of work. No
exploration, no context searching, just build what the packet says. This is
LESSONS #1 ("structure beats strings") expressed as a document format.

**Working in small units.** An SLM does best at routine, bounded work (
{doc}`/index`). A
well-sized packet is the difference between "build a FastAPI app" (too vague)
and "create app.py with a single route, one template, and one test that
checks for this exact string" (tight enough to succeed).

See {ref}`about-sdd` in the course overview for the broader rationale.


```{toctree}
:hidden:

subagent-mechanism
implementer-orchestrator
lessons-from-handoff
cleanup/index
spec
plan
research/2026-07-23-sp2-baseline-phase-1
research/2026-07-23-sp2-baseline-phase-1-post-tuning
research/2026-07-24-sp2-deep-dive
```
