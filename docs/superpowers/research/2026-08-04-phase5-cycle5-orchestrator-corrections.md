# Phase 5 cycle 5 — what two prompt lines changed

**Date:** 2026-08-04
**Cycle:** phase 5 cycle 5 — correct the orchestrator's instructions
**Model:** `omlx/gemma-4-12B-it-MLX-8bit` · **pi:** 0.83.0
**Suite:** `agentclinic-phase-1-user-story`

> **This cycle publishes no number.** Its evidence is two smoke runs and an
> **n=6 pilot at `run_timeout=300`**, against cycle 4's n=16 at 600 s. A
> shorter cap truncates runs — 4 of 55 completed runs across earlier batches
> exceeded 300 s — and `run_timeout` is part of `RunConditions`, so these are
> **not comparable** with any published arm and are not offered as a result.
> Cycle 8 is where a comparable number gets bought.

> **Corrected 2026-08-04 by phase 5 cycle 9.** The delegated child in this
> arm was **not hermetic.** Pi's shipped subagent extension spawns the child
> without the parent's suppression flags, and user-scope resources load
> unconditionally, so the child loaded the operator's own
> `~/.pi/agent/extensions/` and packages -- including `rtk.ts`, which rewrites
> bash commands. Recorded child transcripts here show `ls -R` returning the
> output of `rtk ls -R`. The comparisons in this record stand, because the
> contamination was present in every arm compared; what it means is that the
> orchestrated arm measured **this orchestrator plus the operator's toolbelt**,
> not the orchestrator alone. Presence is verified from the transcripts;
> byte-identity across pilots is **not**, and cannot be — the operator's
> `~/.pi` contents were never recorded, which is precisely the gap cycle 9
> closed. `RunConditions` gained
> `agent_dir_digest` in cycle 9 so this can never again be silent.

## What changed

Two lines in `improvements/sdd-orchestrator/orchestrator.md`:

1. The literal call shape — `agent: "implementer"`, `task: <packet>`,
   `agentScope: "both"` — with a note that omitting `agent` invalidates the
   call.
2. A statement that the workspace is empty, nothing exists yet, everything
   must be created, and listing the directory will keep returning nothing.

No harness changes, no implementer changes, no packet changes.

## Result 1 — the parameter defect is closed

**8 subagent calls across 6 pilot runs, every one carrying `agent`. Zero
rejections.** Both smoke runs likewise.

The defect was worth its cycle. Pi's tool infers the mode from which
parameters arrive — `hasSingle = Boolean(agent && task)` — and every rejected
call in this project's history sent `{agentScope, task}` without `agent`,
producing `modeCount == 0` and `"Invalid parameters. Provide exactly one
mode."` Four such calls across cycles 2 and 4 ran no child at all, and one of
them was a run's *only* completed delegation. Because the rejection is
returned as a **non-error** with an empty `results[]`, no `isError` check
could ever have caught it; it took an adversarial audit to find, and a static
assertion now holds the line in milliseconds.

## Result 2 — the exploration spiral did not recur

| | cycle 4 (600 s, n=16) | cycle 5 pilot (300 s, n=6) |
|---|---|---|
| runs with a repeated identical tool call | **15/16** | **0/6** |
| worst single-command repetition | **245** | **1** |
| most tool calls in one run | **261** | **7** |

This is the cycle's most interesting signal and the one most in need of
caution.

**Why it is probably not the shorter timeout.** Truncation would reduce the
opportunity to repeat, but cycle 4's worst run made 261 tool calls in ~477 s —
roughly 150 within a 300 s window. The pilot's *most active* run made 7. A
drop from 261 to 7 is a change in behaviour, not a change in how long we
watched.

**Why it is still only a signal.** n=6, one configuration, one model, and
`ls -R` is not the only shape a spiral can take. A prompt line that asks the
model not to search is a weaker guarantee than a mechanism that refuses to let
it — which is cycle 6's argument, unchanged by this.

## Result 3 — acceptance is still zero, as predicted

0/6 accepted, and **5/6 wrote files** (cycle 4: 11/16). The runs are producing
plausible applications and failing on one fact the spec withholds.

**Corrected 2026-08-04 by cycle 7's investigation.** This section originally
blamed file layout — `index.html` versus `home.html`, `test_app.py` placement.
The acceptance file disclaims layout explicitly and its only structural
coupling is `from app import app`. Every pilot run that wrote `app.py` failed
with `TypeError: Flask.__call__() missing 1 required positional argument:
'start_response'`: the model chose **Flask**, a WSGI framework, and the suite
drives it with Starlette's ASGI `TestClient`. Five of six pilot runs failed
this way, identically. The withheld fact that matters is the *framework*, not
the filenames.

**Prediction 3 said acceptance would stay at or near zero, and that a pilot
showing rejections gone with acceptance unchanged is a success for this
cycle**: it isolates the remaining failure to the two facts cycle 7 supplies.
That is what happened.

## The orchestrator invents the fact it was not given

The smoke run's packet instructed the implementer to *"use a Python web
framework (like Flask or FastAPI)"*. Nobody told it either name.

This is worse for reproducibility than stalling would be. A model that stops
and asks produces a clean zero; a model that guesses produces runs that differ
from each other for reasons no condition records — and cycle 4 already showed
the resulting spread of layouts. It strengthens cycle 7's case: supplying the
stack is not only about raising the score, it is about removing a source of
variance the harness cannot see.

## Timeouts got worse, and that is expected

3/6 timed out at 300 s, against 6/16 at 600 s. Two smoke runs both timed out
with **zero completed parent turns** — one `subagent` call, 165 streaming
updates, 5.8 MB of stdout, no end event. The delegation now starts correctly
and the *child* runs unbounded.

The corrections moved the failure rather than removing it, which is the honest
summary of this cycle: parameters fixed, exploration apparently calmed, and
the dominant remaining failure is an unbounded child. That is cycle 6.

## A harness limitation this cycle exposed

`run_batch` computes the conditions it enforces with a **hardcoded 600 s** and
takes no `timeout` parameter, while `run_suite` records whatever it was given.
A pilot at a reduced cap therefore cannot be run through `run_batch` — the
first attempt aborted with `"run conditions changed during batch"`, correctly.

This matters because the phase's committed testing-economics plan names
"pilots at n=6, `run_timeout=300`" as its main cost control, and the harness
cannot express it. The pilot here ran as six direct `run_suite` calls
appended to one checkpoint, which works but gives up resume-on-interrupt.

Not fixed here: this cycle's spec says prompt-only, no `harness/` changes.
Recorded as a corrective owed before the plan relies on it again.

## Evidence

`~/local-ai-pi-evidence/satyrn-phase5-cycle5-pilot-n6-t300.jsonl`, outside
version control, retaining full `pi_stdout`. Every figure above recomputes
from it.
