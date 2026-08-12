# Satyrn Engine

**A Pi extension plus an eval harness, for keeping small local models on
track during real Python development.** Working name of the effort: "AI Our
Way."

## What we're trying to do

Small local models are not the "godbox" experience. You don't type a vague
prompt and let a huge model reason its way to a conclusion over a long
conversation. Agentic coding with a 12B model is small, routine, and much
more like engineering.

That's the opportunity and the problem. It's your car — you want to drive
it, not be a passenger. But driving well needs instruments, and the field
is full of techniques offered on faith. Does a particular prompt structure
help? Does a plan-first workflow help? Nobody can say without measuring.

So this project builds the measuring instrument first. **North star:
evidence first** — a trustworthy, convenient, repeatable way to collect it.
Explicitly not over-designed, over-engineered, or too large to absorb.

## The trap we're avoiding

Three prior attempts turned into engineering efforts *about orchestration*
— hangs, timeouts, gating decisions, graders, cardinal rules — until the
machinery outgrew anyone's ability to hold it in their head. A fourth
produced, in a single day, two workloads, six arms, five violation classes,
and three amendment chains: correct output, exploding surface area.

Everything about how this project is run follows from not repeating that.
One phase at a time. One small provable thing per cycle. A published
budget on its own jargon. Tangents go to the backlog, never into the
current phase. Read [`BRIEF.md`](https://github.com/pauleveritt/local-ai-pi/blob/restructure/BRIEF.md)
for the full statement — it's short, and it's the whole context.

## Where things stand

**Phase 1 is complete.** Fourteen feature cycles built and proved a grading
engine that runs a small local model against a real task — building an
AgentClinic home page from a spec — and decides hermetically whether it
succeeded. A supervised n=16 reproduction accepted all 16 attempts.

Phase 1 was chosen *because it is boring*: it starts from an empty
workspace, and its answer is already known and trusted. The engine's first
job is to **reproduce a number we already trust, not to discover one.**
~15/16 means the engine works; 3/16 means the engine is broken, not the
model. That inference isn't available on any phase whose answer is unknown.

Along the way the engine was attacked deliberately and repeatedly, by us, to
prove it can't be fooled — by test configs that skip execution, by processes
that exit before reporting, and by modules that impersonate the grader itself.
The live model run and supervised batch both have recorded evidence.

**Phase 2 is where new collaborators come in.**

## The extension half

`BRIEF.md` promises "a Pi extension (not a fork of Pi) plus an eval harness."
The first extension is the [loop breaker](loop-breaker.md): it refuses a tool
call the model has already made, unchanged, several times in a row.

It exists because of a recorded run of 261 turns, 245 of them the identical
command `ls -R` against an empty workspace. Live in a 16-run batch it refused
12 calls across two runs, and **both of those runs still passed**. (An earlier
replay-based false-positive figure is [withdrawn](loop-breaker.md); the live
result is what stands.)

It installs by copying one file, and it is useful outside this project. If
you delegate to subagents, read the section on where to put it — the child
does not load your project's extensions.

## For new collaborators

Start with [setup](setup.md) — most of this project's tests need nothing
but Python, so you can contribute before you ever start a model server.

Then read [how we work](sdd.md). This project runs on spec-driven
development, and the disciplines it names — concept budget, non-vacuity,
verify-don't-assert — are what review will hold you to.

```{toctree}
:maxdepth: 1
:caption: Getting started

setup
contributing
glossary
loop-breaker
```

```{toctree}
:maxdepth: 1
:caption: The bounded-implementer path

architecture
evidence-index
```

```{toctree}
:maxdepth: 1
:caption: How we work

sdd
```

```{toctree}
:maxdepth: 1
:caption: Development record

superpowers/index
superpowers/phase-history
```
