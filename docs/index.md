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

## Spec-driven development

Yes, this repo use SDD both to build the system and as the first example application. This triggers some people. As a
note: Satyrn doesn't have to adopt SDD.

That said, I think SDD is uniquely valuable for what we're doing:

1. It promotes the human-in-the-loop. The roadmap, specs, and plans plans let you put on your thinking cap and steer.
2. We are a distributed project with lots of folks. It's a useful artifact (even if ultimately unmaintained) for seeing
   why code emerged.
3. Most of all, I think SLMs need to eat their food in small bites. We can plan with a big brain, then develop with
   smaller brains which pre-chew the food for implementers that are even smaller brains.

```{toctree}
:maxdepth: 2
:caption: Chapters

chapters/index
```

```{toctree}
:maxdepth: 1
:caption: About

how-this-was-built
lessons
```

## Development record

The course's own construction — the roadmap, the design specs, the evidence
policy, and the dated evidence reports each cycle produced — is part of the
site, not hidden in the repository. New specs and reports appear here
automatically as they land; nothing needs to be hand-added to this page.
Implementation plans (the task-by-task decomposition of each spec) are linked
from the roadmap table rather than listed here, to keep this page to the parts
meant to be read rather than executed.

```{toctree}
:maxdepth: 1
:caption: Development record

superpowers/roadmap
superpowers/policies/evidence
```

```{toctree}
:maxdepth: 1
:caption: Specs
:glob:

superpowers/specs/*
```

```{toctree}
:maxdepth: 1
:caption: Evidence reports
:glob:

superpowers/research/*
```
