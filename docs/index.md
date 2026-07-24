# Keeping a Small Local Model On Track — with Pi

A course teaching how to keep a small local model on track while it does real Python development under
the [Pi agent harness](https://pi.dev), using only built-in Pi features.

The reader never adopts a technique on faith: each part shows the failure with recorded telemetry, applies one Pi
mechanism, then measures whether it helped.

[How This Was Built](how-this-was-built.md) traces the course's lineage, the spec-driven method behind it, and which
models did which work — the same accounting the course asks you to demand of any technique.

[Lessons](lessons.md) is the source catalog: seventeen lessons on keeping a small local model on track, ranked by
demonstrated impact and traceable to session telemetry rather than intuition. Every improvement chapter cites one of
these by number.

## Scope

Small-language models (SLMs) are quite different than the "godbox" experience we're used to. You don't just type in some
vague prompt and let a huge AI work its way to a conclusion, perhaps in a long conversation.

Agentic coding with SLMs is...small. Routine. It feels more like engineering. This repo tries to show a way of working
that keeps the human in the loop. It's your car: you want to drive your car, not be a passenger.

(about-sdd)=

## Spec-driven development

Yes, this repo use SDD both to build the system and as the first example application. This triggers some people. As a
note: Satyrn doesn't have to adopt SDD. That said, I think SDD is uniquely valuable for what we're doing:

1. It promotes the human-in-the-loop. The roadmap, specs, and plans plans let you put on your thinking cap and steer.
2. We are a distributed project with lots of folks. It's a useful artifact (even if ultimately unmaintained) for seeing
   why code emerged.
3. Most of all, I think SLMs need to eat their food in small bites. We can plan with a big brain, then develop with
   smaller brains which pre-chew the food for implementers that are even smaller brains.

```{toctree}
:maxdepth: 1
:caption: Sections

section-1-hello-agent/index
section-2-measurement/index
section-3-sdd/index
section-4-keeping-on-track/index
```

```{toctree}
:maxdepth: 1
:caption: About

how-this-was-built
lessons
```

## Development record

The course's own construction — the roadmap, the design specs, the evidence policy — is documented here. Evidence
reports live in their respective section research directories. Implementation plans (the task-by-task decomposition of
each spec) live alongside their specs in the section directories rather than listed here.

```{toctree}
:maxdepth: 1
:caption: Development record

superpowers/roadmap
superpowers/specs/2026-07-23-course-design
superpowers/policies/evidence
superpowers/policies/chapter-structure
superpowers/plans/2026-07-24-grading-path-reboot
superpowers/plans/2026-07-24-oracle-repair
```
