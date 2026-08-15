# Using the engine

Install it once, forget it's there, and use Pi normally — the guards act
in the background. When you want a bounded attempt against your own repo,
that is `/implement` in a session, or a CLI from a checkout. The
[front door](index.md) explains what the engine is; this page is how to
use it.

## Quick start

**In this repository you already have it** — `.pi/extensions/engine.ts`
and `orchestrator.ts` are project-local and load once you trust the
project. The user-scope install below is for every session, everywhere
(and for delegated children, which project-local files do not reach).

One line, as a pi package:

```bash
pi install git:github.com/pauleveritt/local-ai-pi@v0.1.0
```

(Or, from a checkout, copy the two files from the package:
`cp packages/engine/engine.ts packages/engine/orchestrator.ts
~/.pi/agent/extensions/`.) If Pi is already running, `/reload` picks it
up.

**Everyday use needs no typing.** The guards are passive: they watch tool
calls and refuse the two failure modes — repeating an identical call,
and deleting a public symbol — when they occur. Use Pi as you normally
would. When a guard fires, the model sees a refusal that says why and
offers the next concrete action; it is steering, not a bare "no".

## Ways to use it

**Everyday steering.** The two guards run in every session. The loop
breaker refuses the next identical call once it has seen 5 of them in a
20-call window, and a blocked call never enters the window — a model that
keeps retrying stays blocked. Preserve-symbols governs `edit` alone: an
edit that deletes a public symbol without replacing it is refused, while
`write` and shell heredocs are left alone, because the one run that
recovered did so by rewriting the file wholesale. Neither guard knows
anything about your task; that is what lets them ship self-contained.

**The loop breaker is part of the engine.** There is no standalone install;
[the engine](index.md) bundles both guards, and
[docs/engine/loop-breaker.md](loop-breaker.md) has the guard's behavior,
tuning, and the subagent gotcha.

## What to expect

- **Silence until it fires.** The guards do nothing visible until a
  guard blocks a call. The pilot shootout measured exactly this on both
  suites: at the ceiling (`agentclinic-phase-1` — 6/6 both arms, 7 turns
  and 6 tool calls in every run) and at the floor
  (`agentclinic-phase-1-user-story` — 0/6 both arms, one turn and zero
  tool calls per run, the model asking the human). In neither did a guard
  fire.
- **When the loop breaker fires:** the 6th identical call (after 5 in the
  window of 20) is refused with a reason; the blocked call does not enter
  the window, so the repeats stay blocked rather than sliding out of
  view.
- **When preserve-symbols fires:** an `edit` deleting a public symbol —
  a function, a class, a route — is refused unless the new text replaces
  it. It never touches `write`.
- **What it is not.** Not a planner, not a turn cap (Pi has none, and
  varied work is untouched), and not a godbox — it steers, it does not
  reason for you.

## The orchestrator: a bounded attempt, on demand

The engine package also registers **`/implement`**, the orchestrator's
in-session front: a task you type is chewed into a handoff packet, and
the implementer — the bounded worker — makes one reviewable attempt
against your repository in a throwaway worktree, checked with a command
you declare. It is an explicit command, not something that fires in the
background: it is for the deliberate moment when you want a validated,
reviewable artifact instead of just steering. The ad-hoc flavor validates
with `pytest -q`; the structured flavor (Phase 11) is the roadmap. The
CLI form is `tools/deliver_candidate` from a checkout; it lives at
[docs/engine/deliver-candidate.md](deliver-candidate.md), and the
one-liner is in the README.
