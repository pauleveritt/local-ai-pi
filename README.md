# Satyrn Engine

**A Pi extension plus an eval harness, for keeping small local models on
track during real Python development.** Working name of the effort: "AI
Our Way."

Small local models are not the "godbox" experience. You don't type a vague
prompt and let a huge model reason its way to a conclusion. Agentic coding
with a 12B model is small, routine, and much more like engineering — which
means the interesting question is *how do you know whether a technique
actually helped?*

This project's answer is to measure. **North star: evidence first** — a
trustworthy, convenient, repeatable way to collect it. Explicitly not
over-designed, over-engineered, or too large to absorb.

## Status

**Phase 1 is nearly complete.** Eleven feature cycles have built and proven a
grading engine that can run a small local model against a real task and
decide, hermetically, whether it succeeded. The engine has survived
deliberate attacks on its own grading, and one real end-to-end run has
graded a live model's work as accepted.

Three cycles remain in Phase 1 (hang tolerance, the batch contract, and a
sequential n=16 batch). **Phase 2 is where new collaborators come in** — see
[the roadmap](ROADMAP.md) for what's planned and what's deliberately
parked.

## Start here

| If you want to… | Read |
|---|---|
| Understand why this project exists | [`BRIEF.md`](BRIEF.md) — the whole context, in one file |
| Get your machine set up | [`docs/setup.md`](docs/setup.md) |
| Understand how we work | [`docs/sdd.md`](docs/sdd.md) |
| See what's planned | [`ROADMAP.md`](ROADMAP.md) |
| Read the design record | [`docs/superpowers/index.md`](docs/superpowers/index.md) |

`BRIEF.md` is the single most valuable thing to read first. It is
deliberately short, it states the values this project is run by, and it
names the trap we are avoiding.

## Quick start

```bash
uv sync
uv run pytest
```

Most tests are hermetic and need nothing but Python. One live-model test is
explicitly opt-in, so a green run on a fresh machine is expected. Full setup,
including the model server, is in [`docs/setup.md`](docs/setup.md).

## How this project is built

Every feature goes through **spec-driven development**: brainstorm with the
owner, write a design spec, write an implementation plan, then implement it
test-first. The specs and plans are committed, not thrown away, so you can
read *why* code looks the way it does — see
[`docs/sdd.md`](docs/sdd.md).

Four disciplines are worth knowing before you contribute, because they
shape review:

**Concept budget.** Every piece of jargon is a cost against a volunteer's
ability to hold the design in mind. `ROADMAP.md` keeps a table of every term
the project spends, checked at the end of each cycle. If a doc needs a term
a 5-hour-a-week contributor can't absorb, the term goes — not the
contributor.

**No machinery ahead of the contract it serves.** Build the engine as needs
in the suites arise. Several genuinely good ideas sit in the Backlog
specifically because nothing needs them yet.

**Non-vacuity.** A test that passes without testing what it claims is this
project's recurring hazard, and most of the grading code exists to defeat
it. Ask of any new test: *what else could make this pass?*

**Verify, don't assert.** Claims get demonstrated, not argued. When a
review round claimed a security fix worked, we wrote the exploit and ran
it — it didn't, and the design changed. That norm has caught real bugs
more than once.

## Layout

```
BRIEF.md            the whole context — read this first
ROADMAP.md          phases, feature cycles, concept budget, backlog
harness/            the eval harness
tests/              its tests, mostly hermetic
examples/           AgentClinic fixtures and the task spec
docs/               setup, SDD explainer, and the design record
```
