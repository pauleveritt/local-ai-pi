# Glossary

Terms this project uses in a particular way. If a word here also has an
ordinary meaning, the entry says what *we* mean by it.

Kept short on purpose — a term that no current document uses does not
belong here. If you meet jargon that isn't listed, that's a docs bug
worth reporting.

---

## Arm

One condition in a comparison. Two arms differ in exactly one thing —
say, whether the model gets a [brief](#brief) or a
[locating contract](#locating-contract) — so a difference in outcome can
be attributed to that one thing.

Changing anything else about an arm after it has produced results makes
those results incomparable, which is why a [cell](#cell) exists.

## Brief

A short, behaviour-only description of a task: what should change and
why, naming no file, no line, and no mechanism. Written before any
attempt, and frozen.

Contrast [locating contract](#locating-contract).

## Candidate

What one model attempt produces: a commit on a `refs/satyrn/candidates/`
ref. You read it with `git show`, cherry-pick it, or delete it. It is
never merged and never touches your working tree.

An attempt that fails [validation](#validation-command) produces no
candidate — just a [receipt](#receipt) saying why.

## Cell

A pinned, named set of conditions for a run: model, tool allowlist,
budgets, and a SHA-256 of the exact [extension](#extension) bytes.
Verified against live configuration before any model call, and the run
refuses to start on a mismatch.

The point is that two runs recorded under one cell name really were the
same experiment. A cell that could drift silently would make its own
name meaningless. See `workloads/svcs/cells/`.

## Cohort

The frozen set of tasks a [workload](#workload) offers. Frozen means
task definitions and their hashes don't change once results exist
against them.

## Confirmatory

Evidence gathered under a [pre-registration](#pre-registration) — the
design was fixed and committed *before* the data existed. Only
confirmatory evidence supports a claim.

Contrast [pilot](#pilot). See [rule 8](#rule-8).

## Engine

The package you install: a pi package at `packages/engine/`, whose two
files — `engine.ts` (bundling the two [guards](#guard): the
[loop breaker](#loop-breaker) and preserve-symbols) and `orchestrator.ts`
(the `/implement` command) — are the installable surface. `pi install
git:github.com/pauleveritt/local-ai-pi@v0.1.0` is the one-line install;
`.pi/extensions/` holds symlinks to the package, so a checkout loads the
engine with zero install.

Not to be confused with **Agent Engine**, the product name for the whole
project (the engine plus the [orchestrator](#orchestrator)).

## Extension

A TypeScript file Pi loads to change its behaviour — adding a tool,
inspecting a tool call, injecting a prompt. This project's
[implementer](#implementer) and [guards](#guard) are extensions.

Pi loads user-scope extensions unconditionally, which is why the
[loop breaker](#loop-breaker) installs by copying one file.

## Implementer

The bounded worker: a Pi child restricted to `read`/`write`/`edit` (no
shell), capped at 16 turns and 30 tool calls, with every write routed
through the [mutation engine](#mutation-engine). Driven by the
[orchestrator](#orchestrator), which pre-chews the task into a
[handoff packet](#handoff-packet).

"Bounded" is the whole idea — it cannot reach outside its declared
files, and code, not prose, enforces that.

## Guard

A small, self-contained rule that inspects a tool call and may refuse
it. Guards are deliberately *contract-blind*: they compare a call
against itself, never against the task, so they can ship standalone.

The [loop breaker](#loop-breaker) is the one with live evidence behind
it.

## Handoff packet

The pre-chewed task handed to the [implementer](#implementer): the task
text, the exact writable files, the
[validation command](#validation-command), and a SHA-256
[baseline](#baseline) per file. Its code type is `HandoffContract`.

Declared in two places that must agree — `harness/typed_contract.py`
(Python, builds it) and `extensions/orchestration/handoff-contract.ts`
(TypeScript, parses it).

## Baseline

A recorded claim about a file the model is about to see: its SHA-256,
mode, and line endings. The [mutation engine](#mutation-engine) refuses
a write whose baseline no longer matches, so a model editing a stale
read cannot silently clobber a change.

## Locating contract

A complete, human-authored description of a task: exact files, exact
locations, a verification checklist. Everything a [brief](#brief)
withholds.

A locating contract must *locate and bound*, never contain the fix —
a contract carrying the solution measures transcription, which happened
once and invalidated an experiment.

## Loop breaker

A [guard](#guard) that refuses a tool call the model has already made,
unchanged, several times in a row. Came out of a recorded run of 261
turns, 245 of them the identical `ls -R`.

Installable on its own, outside this project: see
[loop-breaker.md](engine/loop-breaker.md).

## Mutation engine

The only thing that writes files during an attempt. Checks the
[baseline](#baseline), bounds the proposal size, applies the edit
atomically, and refuses an edit that would delete a public symbol
without replacing it.

`extensions/orchestration/mutation-engine.ts`. It is the sole authority
on whether a write happens — deliberately, after a redundant second
check was found to contradict it.

## Oracle

The hidden test that decides whether a candidate is actually *correct*,
as opposed to merely safe. Never shown to the model, and run only
against a throwaway copy after the attempt finishes.

Distinct from the [validation command](#validation-command), which the
model *is* told about.

## Orchestrator

The explicit front you invoke: the `deliver_candidate` CLI
(`tools/deliver_candidate.py`). It pre-chews a task into a
[handoff packet](#handoff-packet), keeps the [implementer](#implementer)'s
context small, runs the model once in a throwaway worktree, and returns
either a reviewable [candidate](#candidate) ref or a
[receipt](#receipt) saying why not.

## Pilot

Exploratory data. It selects what to measure — which tasks, how many
repetitions — and never supports a claim. See [rule 8](#rule-8).

## Pre-registration

A dated, committed document fixing an experiment's design — tasks, arms,
sample size, what counts as success, what would abort the run — written
before any data exists. Makes [confirmatory](#confirmatory) evidence
possible.

## Receipt

The JSON record of one attempt: outcome, [cell](#cell), timings, the
[validation command](#validation-command) and its exit code, hashes of
the prompt and output. Written whether the attempt succeeded or not.

## Rule 8

"Pilot data selects, it does not confirm." The project's governing rule
about evidence: you may use exploratory results to *choose* what to
measure, never to support the claim you then make.

Most of the discipline in this repository exists to keep these two apart.

## Validation command

The command the parent runs against a candidate to decide whether to
keep it — typically the task's existing test suite. The model is told
exactly what it is, and the parent runs exactly that.

Not the [oracle](#oracle). This one checks *nothing broke*; the oracle
checks *the thing works*.

## Void

An attempt that never really happened — dead model server, a failed
worktree, a cell mismatch. Excluded from both numerator and denominator
of every rate, and replaced rather than dropped.

A void counted as a failure is a wrong number, which has happened here
once and is why the distinction is enforced.

## Workload

A body of real tasks the harness can replay — for this project, commits
from the open-source `svcs` library, each with a known-good target. See
`workloads/svcs/`.
