# Using the engine

Install it once, forget it's there, and use Pi normally — the guards act
in the background. When you want a bounded attempt against your own repo,
that is a shell command, not a Pi incantation. The
[front door](index.md) explains what the engine is; this page is how to
use it.

## Quick start

The whole install is one file, in user scope (so it loads in every
session, including delegated children):

```bash
mkdir -p ~/.pi/agent/extensions
cp .pi/extensions/engine.ts ~/.pi/agent/extensions/
```

If Pi is already running, `/reload` picks it up.

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
anything about your task; that is what lets them ship in one file.

**Only the loop breaker.** If you want guard #1 and nothing else,
[docs/engine/loop-breaker.md](loop-breaker.md) installs it alone, with
the same user-scope reasoning and the subagent gotcha.

## What to expect

- **Silence until it fires.** The guards do nothing visible until a
  guard blocks a call. The pilot shootout measured exactly this: guards
  loaded but never fired, both arms at ceiling — 7 turns and 6 tool
  calls with the same tool sequence in every one of the 12 runs.
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

## A companion tool: the orchestrator

The project also ships an **orchestrator** (`deliver_candidate`) — a
separate, non-interactive CLI that pre-chews a task into a handoff packet
and drives the implementer — the bounded worker — to make one reviewable
attempt against your repository in a throwaway worktree, checked with a
command you declare. It is not part of the engine and not something you
reach for mid-session: it is for the deliberate moment when you want a
validated, reviewable artifact instead of a session. It lives at
[docs/engine/deliver-candidate.md](deliver-candidate.md); the one-liner
is in the README.
