# Agent Engine

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
current phase. Read [`BRIEF.md`](https://github.com/pauleveritt/local-ai-pi/blob/main/BRIEF.md)
for the full statement — it's short, and it's the whole context.

## What you can use today

Three things, independent of each other. You can take any without the
others, and none needs the rest of this project.

**The [engine](engine/index.md)** — why, how, and what: the two guards
bundled into one self-contained file.

**A [loop breaker](loop-breaker.md) for your own Pi sessions.** One file,
copied into place. It refuses a tool call the model has already made,
unchanged, several times in a row. It came out of a recorded run of 261
turns, 245 of them the identical `ls -R` against an empty directory.

**A [bounded executor](architecture.md) for your own repository.** It runs
a model once against your repo in a throwaway git worktree, checks the
result with a command *you* declare, and leaves either a git ref you can
review or a receipt explaining why not. Your working tree is never written
to. Nothing is merged, nothing is promoted.

New to the vocabulary? The [glossary](glossary.md) is short, and defines
only the words this project uses in a particular way.

## What the evidence says

One pre-registered comparison, 64 attempts, run 2026-08-11: does giving the
model a complete [locating contract](glossary.md#locating-contract) beat a
short [brief](glossary.md#brief)?

**On one task of four, clearly yes** — 8/8 against 3/8. On two, both arms
were already at ceiling. On the fourth, both were at the floor: the
contract got the model to a *safe* answer every time and a *correct* one
never.

That last one is the honest headline. Locating information solves locating
problems; it does not make a model capable of something it can't do.

Which claims here are [confirmatory](glossary.md#confirmatory) and which
are only [pilot](glossary.md#pilot) is written down, claim by claim, in the
[evidence index](evidence-index.md). Two published figures have been
retracted over this project's life, both recorded with banners rather than
edited away.

## What's still experimental

The bounded executor's bare form — your prompt, your validation command —
is general. The *evidenced* path underneath it is not: the typed-contract
bridge is scoped to exactly four tasks and refuses the rest at the command
line rather than guessing. It's a tested bridge, not a planner.

And the fourth task above sits at a genuine capability ceiling. That's a
real limit rather than a harness bug — we checked, because a
similar-looking result once turned out to be our own validation gate
rejecting correct answers.

## Where things stand

**Phases 1–5 built the measurement half** — a grading engine that runs a
small local model against a real task and decides hermetically whether it
succeeded, hardened by deliberate attacks on its own grading, then extended
to express *"this run had something applied to it"* and measure it.

**Phases 6–7 built the bounded-implementer half** — the guards, the
mutation engine, the typed handoff, and the pre-registered comparison
above. [architecture.md](architecture.md) traces that path end to end, in
the order execution happens, naming the real module at each stage.

The full phase-by-phase record, including the withdrawn framings and
retracted figures, is in [the development record](superpowers/index.md).

## For new collaborators

Start with [setup](setup.md) — most of this project's tests need nothing
but Python, so you can contribute before you ever start a model server.
Then [contributing](contributing.md) has the test commands, the
conventions, and three starter tasks sized for a first afternoon.

[How we work](sdd.md) is worth reading before your first review. This
project runs on spec-driven development, and the disciplines it names —
concept budget, non-vacuity, verify-don't-assert — are what review will
hold you to.

```{toctree}
:maxdepth: 1
:caption: Getting started

setup
contributing
glossary
loop-breaker
evals
```

```{toctree}
:maxdepth: 1
:caption: The engine

engine/index
engine/architecture
engine/shootout
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
