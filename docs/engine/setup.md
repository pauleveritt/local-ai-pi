# Engine setup

The in-depth setup for the engine. The terse version is
[quick start](../quickstart.md); the model it drives is
[model setup](../model-setup.md); the ways to use it are
[using the engine](usage.md); the front door is [what the engine is](index.md).

## Prerequisites

The engine is a Pi extension: it needs **Pi** running, and it steers a
model, so it needs **a model server and a resolvable model string**.
Both are in [model setup](../model-setup.md) — the short version is
`omlx start` and a `--model <provider>/<id>` that Pi can resolve.

The guards need nothing else: they inspect tool calls in your existing
sessions, and `/implement` needs a repository (it runs against `ctx.cwd`)
and a model — a working `pi --version` and a live server are the whole
dependency list.

## Install

**In this repository, nothing to install.** The engine is project-local
here — `.pi/extensions/engine.ts` and `orchestrator.ts` — and Pi loads
project-local extensions once you trust the project. `/implement` is
available in any session inside this repo, with no setup.

Install to user scope when you want the engine in *every* session,
everywhere — and in delegated children, where a small model's runaway
usually happens, because project-local files guard the parent only. The
install is two files, in user scope — the whole install, from a checkout:

```bash
mkdir -p ~/.pi/agent/extensions
cp packages/engine/engine.ts packages/engine/orchestrator.ts ~/.pi/agent/extensions/
```

If Pi is already running, `/reload` picks them up.

User scope is the point: Pi loads user-scope extensions unconditionally,
in every session, and — the reason it matters — in delegated children,
where a small model's runaway usually happens. A file in a project's
`.pi/extensions/` guards the parent and leaves the child unguarded.

Only want the guards, no orchestrator? `docs/engine/loop-breaker.md`
installs the loop breaker alone.

## Verify

In the repository you're working on, in a Pi session:

```
/implement add a hello() function to duration.py
```

The orchestrator chews the task into a handoff packet and drives the
bounded implementer against the current repo — a throwaway worktree,
`pytest -q` validation, your session's model. It leaves a ref. Review it,
then discard it:

```bash
git show refs/satyrn/candidates/<task-slug>
git update-ref -d refs/satyrn/candidates/<task-slug>
```

Your working tree is never written to; the only thing that lands in the
repo is the ref, and the second command removes that.

## What to expect

The guards are silent until they fire. The measured baseline: at the
ceiling (`agentclinic-phase-1`) and at the floor
(`agentclinic-phase-1-user-story`), both arms identical, guards loaded
but never fired — steering is invisible when the model never loops. When
a guard does fire, the model sees a refusal that says why and offers the
next concrete action. The evidence and the tuning are in
[using the engine](usage.md) and [the loop breaker](loop-breaker.md).

## Troubleshooting

- `/implement` finds no candidate ref — the implementer judged the
  attempt and discarded it; the receipt explains why. Exit codes: 0 a
  candidate exists, 1 judged and discarded, 2 refused before starting
  (dirty repo, dead server), 3 setup broken.
- The dead-server trap: a server that is down does not make Pi fail —
  Pi exits 0 having written nothing. Check `omlx diagnose` and
  `docs/evals/setup.md`'s liveness one-liner.
- The model doesn't resolve — the string must exist in the agent dir in
  use; see [model setup](../model-setup.md).
