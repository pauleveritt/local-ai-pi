# Agent Engine

**Can a small local model do real Python work — and how would you know?**

A 12B model running on your own machine is not the "godbox" experience.
You don't hand it a vague prompt and let it reason its way out. The work
is small, routine, and much more like engineering — which makes the
interesting question not *is it magic* but *did that technique actually
help?*

This project's answer is to measure, carefully, and to write down what
the measurement does **not** show.

## What you can use today

Two things, and they're independent — you can take either without the other.

**A loop breaker for your own Pi sessions.** One file, copied into place.
It refuses a tool call the model has already made, unchanged, several
times in a row. It came out of a recorded run of 261 turns, 245 of them
the identical `ls -R` against an empty directory.
→ [Install it](#install-the-loop-breaker) (2 minutes, needs nothing else here)

**A bounded executor for your own repository.** It runs a model once
against your repo in a throwaway git worktree, checks the result with a
command *you* declare, and leaves either a git ref you can review or a
receipt explaining why not. Your working tree is never written to.
Nothing is merged. Nothing is promoted.
→ [Try it](#try-one-attempt-on-your-own-repository)

New to the vocabulary? The [glossary](docs/glossary.md) is short and
defines only words this project uses in a particular way.

## Install the loop breaker

Nothing from this repository is required except one file:

```bash
mkdir -p ~/.pi/agent/extensions
cp .pi/extensions/loop-breaker.ts ~/.pi/agent/extensions/
```

That's the whole install — Pi loads user-scope extensions
unconditionally, so your next session anywhere has it. When the model
makes the same call with the same arguments 5 times inside a 20-call
window, the next one is refused and the model is told to do something
else. It is not a turn cap; varied work is untouched. Both numbers are
constants at the top of the file.

**Use the user-scope directory, not a project's `.pi/extensions/`**, if
you delegate to subagents at all — a delegated child loads user-scope
extensions but not project ones, and on a small model the child is
usually where the runaway happens. We spent a whole cycle learning that.

This assumes `pi` already works for you. If it doesn't, fix that first
(`/login`, or `~/.pi/agent/models.json`) — an unconfigured Pi fails
before any extension loads.

More, including what to tune: [loop-breaker.md](docs/loop-breaker.md).

## Try one attempt on your own repository

```bash
uv sync
uv run python -m tools.deliver_candidate \
  --repo . --task add-iter \
  --prompt-file docs/example-brief.md \
  --validation "pytest -q" --writable "src/**" \
  --model your-provider/your-model
```

Three things must be true first, and only the third tells you when it
isn't: `pi --version` answers; `--model` names a model your Pi resolves;
and the server behind it is up. A dead server doesn't make Pi fail — it
exits 0 having written nothing — so the tool checks before spending a
call.

The exit code is the answer: **0** a candidate exists, **1** it was
judged and discarded, **2** refused before starting (dirty repo, dead
server), **3** your setup is broken. Success prints a ref, and reviewing
it is ordinary git:

```bash
git show refs/satyrn/candidates/add-iter
```

That's the bare form — your prompt, your validation command. The
evidenced path underneath it is more bounded than this; see
[architecture.md](docs/architecture.md) when you want it.

## What the evidence actually says

One pre-registered comparison, 64 attempts, run 2026-08-11: does giving
the model a complete [locating contract](docs/glossary.md#locating-contract)
beat a short [brief](docs/glossary.md#brief)?

**On one task of four, clearly yes** (8/8 versus 3/8). On two, both arms
were already at ceiling. On the fourth, both were at the floor — the
contract got the model to a *safe* answer every time and a *correct* one
never.

That last one is the honest headline: locating information solves
locating problems. It does not make a model capable of something it
can't do.

Full numbers, intervals, and what they don't establish:
[the result](docs/superpowers/research/2026-08-11-phase7-cycle7-confirmatory-result.md).
Every claim's evidence category — [pilot](docs/glossary.md#pilot) versus
[confirmatory](docs/glossary.md#confirmatory) — is indexed in
[evidence-index.md](docs/evidence-index.md).

## What's still experimental

The typed-contract path is scoped to exactly four tasks and refuses the
rest at the command line rather than guessing. It's a tested bridge, not
a planner.

And the fourth task above sits at a genuine capability ceiling. That's a
real limit, not a harness bug — we checked, because a similar-looking
result once turned out to be our own validation gate rejecting correct
answers.

## Where to go next

| You want to… | Read |
|---|---|
| Understand the one supported path, end to end | [architecture.md](docs/architecture.md) |
| Get set up properly | [setup.md](docs/setup.md) |
| Contribute — commands, conventions, starter tasks | [contributing.md](docs/contributing.md) |
| Look up a term | [glossary.md](docs/glossary.md) |
| Check what backs a claim | [evidence-index.md](docs/evidence-index.md) |
| Read the full research history | [ROADMAP.md](ROADMAP.md), [BRIEF.md](BRIEF.md), [the design record](docs/superpowers/index.md) — all historical |

## How this project works

Every feature gets a committed design spec and implementation plan
before the code, so you can read *why* something looks the way it does —
see [sdd.md](docs/sdd.md). Four habits shape review, and
[contributing.md](docs/contributing.md) covers them; the shortest
version is **verify, don't assert**: claims here get demonstrated, not
argued.

## Layout

```
harness/       the typed-contract bridge, candidate lifecycle, cell verification
extensions/    the bounded implementer, mutation engine, and guards (Pi extensions)
tools/         CLI entry points — deliver_candidate is the one to start with
tests/         Python tests, hermetic unless explicitly opted in
workloads/     the task cohort, manifests, cells, and recorded evidence
docs/          architecture, setup, contributing, glossary, evidence
```
