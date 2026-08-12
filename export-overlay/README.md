# Agent Engine

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

**Usable now: a bounded implementer that turns a task into a reviewable
git ref, and a loop-breaker extension you can install standalone.** Neither
is a general coding agent — see "What remains experimental" below.

The current product path: a task manifest plus either a brief or a
locating contract becomes a typed handoff; a Pi child restricted to
`read`/`write`/`edit` implements it under a revision-checked mutation
engine that refuses undeclared destructive edits; the result is validated
against the task's own preservation command and either committed to a
`refs/satyrn/candidates/<task>` ref or discarded with a receipt. Full trace
of every stage: [`docs/architecture.md`](docs/architecture.md).

**Evidence.** A pre-registered, 64-attempt confirmatory comparison
(2026-08-11) found that a complete, human-authored locating contract beats
a concise behavior-only brief on one of four tasks (`stringified-
annotations`, 8/8 vs. 3/8 oracle-passed), with the other three tied between
arms — two at ceiling, one at floor. Full result, intervals, and what it
does and does not establish:
[`docs/evidence/2026-08-11-phase7-cycle7-confirmatory-result.md`](docs/evidence/2026-08-11-phase7-cycle7-confirmatory-result.md).
Every claim's evidence category (pre-registration, pilot, confirmatory,
correction, raw archive) is indexed at
[`docs/evidence-index.md`](docs/evidence-index.md).

**What remains experimental.** The typed-contract bridge
(`harness/typed_contract.py`) is scoped to exactly four svcs tasks on
purpose, and refuses anything else at the command line rather than
guessing — this is a smoke-tested bridge, not general contract authoring
or a planner. `autowire` sits at a genuine 0/8 capability ceiling in the
confirmatory batch regardless of arm; that's a real limitation, not a
harness defect (traced to the model's own import-structure and signature-
handling choices, not a validation-gate bug).

**Also installable standalone: the [loop breaker](docs/loop-breaker.md).**
A small Pi extension that refuses a tool call the model has already made,
unchanged, several times in a row. It came out of a recorded run of 261
turns, 245 of them the identical `ls -R` against an empty workspace. One
file, copied into place, useful outside this project entirely.

## Start here

| If you want to… | Read |
|---|---|
| See the supported path end to end | [`docs/architecture.md`](docs/architecture.md) |
| Get your machine set up | [`docs/setup.md`](docs/setup.md) |
| Contribute — test commands, starter tasks | [`docs/contributing.md`](docs/contributing.md) |
| Check what evidence backs a claim | [`docs/evidence-index.md`](docs/evidence-index.md) |
| Use the loop-breaker extension standalone | [below](#using-the-loop-breaker-extension-in-your-own-python-work) |
| Run one attempt against your own repository | [below](#running-one-attempt-against-your-own-repository) |
| See the full history, phase/cycle planning, and design record | the source research repository — this is a generated export, rebuilt by `tools/build_export.py`; ask whoever pointed you here for its location |

## Quick start

```bash
uv sync
uv run pytest
```

Most tests are hermetic and need nothing but Python. One live-model test is
explicitly opt-in, so a green run on a fresh machine is expected. Full
setup, including the model server, is in [`docs/setup.md`](docs/setup.md).

## Using the loop-breaker extension in your own Python work

**This half needs nothing from this repository except one file.** No harness,
no eval, no Python environment — the loop breaker is a Pi extension, and Pi
is what runs it.

Copy [`loop-breaker.ts`](.pi/extensions/loop-breaker.ts) into your user-scope
extensions directory:

```bash
mkdir -p ~/.pi/agent/extensions
cp .pi/extensions/loop-breaker.ts ~/.pi/agent/extensions/
```

That is the whole install. Pi loads user-scope extensions unconditionally,
so your next `pi` session in any project has it.

**This assumes Pi already has a model to talk to.** The extension is
provider-agnostic — it never names a model, an endpoint, or an API key — but
a genuinely unconfigured Pi fails before the extension ever gets a chance to
run, with `No API key found for the selected model`. That's Pi's own default
provider, nothing this project sets up. If `pi` isn't already working for you
outside this repository, get that working first — `/login` or
`~/.pi/agent/models.json`, per Pi's own docs — then the two commands above
are genuinely the whole install.

**Use the user-scope directory, not your project's `.pi/extensions/`, if you
delegate to subagents at all.** A delegated child does not load project
extensions — it loads user-scope ones — so a project-scope install guards the
parent and leaves the child unguarded, and on a small model the child is
usually where the runaway is. This project spent a whole cycle discovering
that.

What you get: when the model makes the same tool call, with the same
arguments, 5 times within a window of 20 calls, the next one is refused
before it executes and the model is told to do something else. It is not a
turn cap — a model doing varied work for a long time is untouched. Both
constants are at the top of the file.

Full page, including what to tune and the evidence behind it:
[`docs/loop-breaker.md`](docs/loop-breaker.md).

## Running one attempt against your own repository

The other installable piece. It runs a model once against your repo in a
throwaway git worktree, checks the result against a command *you* declare,
and leaves either a durable ref you can read or a receipt saying why not.
Your working tree is never written to, nothing is merged, and nothing is
promoted.

```bash
uv run python -m tools.deliver_candidate --repo . --task add-iter --prompt-file docs/example-brief.md --validation "pytest -q" --writable "src/**" --model your-provider/your-model
```

Three things must be true first, and only the third announces itself:

1. **Pi is installed** — `pi --version` answers (this repository pins
   0.84.1; a different version is not refused for your own repository, only
   for reproducing this project's own measured runs).
2. **`--model` names a model your Pi can resolve.** It reads *your*
   `~/.pi/agent`, not this repo's pinned one; pass `--agent-dir` to override.
3. **The server behind that model is up.** A dead server does not make Pi
   fail — it exits 0 having written nothing. The tool checks
   `--server` (default `http://127.0.0.1:8001`) before spending a call;
   `--skip-server-check` if your model is hosted elsewhere.

Exit codes are the answer, and three of them are distinct on purpose: **0**
a candidate exists, **1** a candidate was judged and discarded, **2** the
run was refused before it started (dirty repo, dead server), **3** nothing
was judged because the setup is broken. If you see 3, the problem is your
configuration, not the model.

Success prints the ref, and inspecting or discarding it is ordinary git:

```bash
git show refs/satyrn/candidates/add-iter
```

**This is the bare-envelope form** — your own prompt, your own validation
command, no typed contract. For the bounded-implementer path this project
actually has evidence for (`--contract-task`, `--cell`, the mutation engine,
the four-task typed bridge), see
[`docs/architecture.md`](docs/architecture.md).

## How this project is built

Every feature goes through **spec-driven development**: brainstorm with the
owner, write a design spec, write an implementation plan, then implement it
test-first. The specs and plans are committed, not thrown away, so you can
read *why* code looks the way it does — see
[`docs/sdd.md`](docs/sdd.md). More on repository conventions and starter
tasks: [`docs/contributing.md`](docs/contributing.md).

## Layout

```
harness/              the typed-contract bridge, mutation lifecycle, and cell verification
extensions/           the bounded implementer, mutation engine, and guards (Pi extensions)
tools/         deliver_candidate — the one entry point
tests/                Python tests, all hermetic
workloads/svcs/       the four supported tasks, their manifests and contracts, and the pinned cell
docs/                  architecture, setup, contributing, evidence index, and the evidence itself
```

**This is a generated export**, derived from the source research
repository by walking the product path's import graph
(`tools/build_export.py` there). It carries the evidenced
bounded-implementer path and the tests that protect it — not the
screening laboratory, the Phase 1–5 duration-suite harness, or the
research archive. Those stay in the source repository.
