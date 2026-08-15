# What is Agent Engine?

**Two halves, one instrument.** Agent Engine is a Pi extension plus an
eval harness, for keeping small local models on track during real Python
development. The engine steers; the evals measure; the loop between them
is the whole point.

## Why it exists

Small local models are not the "godbox" experience. A 12B model on your
own machine does not reason its way out of a vague prompt; the work is
small, routine, and much more like engineering. The field is full of
techniques offered on faith — does a prompt structure help? Does a
planner help? — and nobody can say without measuring. So the project
builds the measuring instrument first: a harness that answers *did the
technique help, on my machine, reproducibly?* — a question no benchmark
answers. See [why evals?](evals/why-evals.md) for the full argument.

## The two halves

**The engine — what you install.** A Pi extension, two files in user
scope, that steers every session. Its vocabulary:

- **Guards** — passive steering: they watch tool calls and refuse the
  failure modes that cost real runs. The loop breaker refuses a call the
  model has already made, unchanged, several times in a row; preserve-
  symbols refuses an edit that deletes a public symbol without replacing
  it. They know nothing about your task — that is what lets them ship in
  one file and guard any session, including delegated children.
- **The orchestrator** — the front you invoke: `/implement <task>` in a
  Pi session chews the task into a handoff packet and drives the bounded
  implementer against the current repository.
- **The implementer** — the bounded worker underneath: one attempt in a
  throwaway worktree, checked with a validation command, leaving a ref
  you can review or a receipt explaining why not.

**The evals — what measures.** The harness: `harness.cli` drives suites —
a task spec, a hermetic acceptance contract, an allowlist of what the
model may write — through real model runs, recording every condition
under which the run happened. Suites today: `duration`, `agentclinic-
phase-1`, and its comparison pair `user-story`; a `svcs` suite is
planned. The measured loop: evidence from the evals becomes engine
improvements — the 261-turn loop became the loop breaker, the deleted
route became preserve-symbols — and the improved engine is re-measured.

## How it works

You install the engine, use Pi normally, and type `/implement` when you
want a bounded attempt. You run evals when you want a number you can
trust. Everything in between — hermetic grading, recorded conditions,
hands-free batches, honest retractions — exists to make that number mean
something. Start at [quick start](quickstart.md).
