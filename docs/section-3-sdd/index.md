# Section III — Spec-Driven Development on Pi

Installs Pi's shipped subagent extension, authors an implementer specialist
and an orchestrator parent prompt, then measures and tunes the
parent+implementer shape.

**Status:** withdrawn pending rewrite. The chapter prose that narrated the
SP1→SP2 structural-baseline arc is discarded — see
[`docs/superpowers/plans/2026-07-24-grading-path-reboot.md`](../superpowers/plans/2026-07-24-grading-path-reboot.md),
Task 9. Spec and plan are kept as historical record; the numbers below
predate the grading-path reboot. New chapter prose is written against the
reframe and final numbers, not before.

**Evidence:** [3/8 pre-tuning](research/2026-07-24-sp2-baseline-phase-1.md),
[5/8 post-tuning](research/2026-07-24-sp2-baseline-phase-1-post-tuning.md),
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

cleanup/index
spec
plan
research/2026-07-24-sp2-baseline-phase-1
research/2026-07-24-sp2-baseline-phase-1-post-tuning
research/2026-07-24-sp2-deep-dive
research/2026-07-23-sp2-baseline-phase-1
research/2026-07-23-sp2-baseline-phase-1-post-tuning
research/2026-07-24-sp2-session-deletion-record
```
