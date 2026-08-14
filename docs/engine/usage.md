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

**A bounded attempt** — the executor — is a shell command from a checkout,
not something typed into Pi:

```bash
uv run python -m tools.deliver_candidate \
  --repo . --task add-iter \
  --prompt-file docs/engine/example-brief.md \
  --validation "pytest -q" --writable "src/**" \
  --model your-provider/your-model
```

It needs a model your Pi can resolve, a model server up, and a clean
repo. The details are below.

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

**A bounded executor attempt.** One model attempt against your repository
in a throwaway git worktree, checked with a command you declare, leaving
either a ref you can review or a receipt explaining why not. Your working
tree is never written to. The exit code is the answer: **0** a candidate
exists, **1** it was judged and discarded, **2** refused before starting
(dirty repo, dead server), **3** your setup is broken. Success prints a
ref; reviewing it is ordinary git:

```bash
git show refs/satyrn/candidates/add-iter
```

The full path, stage by stage, is
[docs/engine/deliver-candidate.md](deliver-candidate.md).

**The measured form.** Cells pin the arm — model, tools, budgets — and
verify the live configuration before spending a call. If you want a
reproducible arm rather than a one-off attempt, that is the cell
machinery; the model wiring is in
[docs/evals/model-setup.md](../evals/model-setup.md).

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
- **The dead-server trap.** A model server that is down does not make Pi
  fail — Pi exits 0 having written nothing. The executor checks liveness
  before spending a call and refuses with exit 2, so a dead server never
  reads as a bad model.
- **The model string.** `--model <provider>/<id>` must resolve in your
  Pi's `models.json`; how to register a provider or model, and the
  server-address limits, are in
  [docs/evals/model-setup.md](../evals/model-setup.md).
- **What it is not.** Not a planner (the typed-contract bridge under the
  executor is scoped to exactly four tasks and refuses the rest), not a
  turn cap (Pi has none, and varied work is untouched), and not a godbox
  — it steers, it does not reason for you.
