# Phase 5 cycle 4 — the user-story suite, and two arms at zero

**Date:** 2026-08-04
**Cycle:** phase 5 cycle 4 — the user-story suite and its floor
**Model:** `omlx/gemma-4-12B-it-MLX-8bit` · **pi:** 0.83.0 · **n:** 16 per arm
**Suite:** `agentclinic-phase-1-user-story` — same acceptance contract as
`agentclinic-phase-1`, different task spec

> **CORRECTED 2026-08-04 by cycle 7's investigation.** This record attributes
> the failures to file layout — `index.html` versus `home.html`,
> `test_app.py` at the root. **That is wrong.** The acceptance file states in
> its own docstring: *"Do not assert on internal function names or file
> layout — a correct-but-different solution must pass."* Its only structural
> coupling is `from app import app`. The real cause, read from the grade
> output of every run that wrote `app.py`, is
> `TypeError: Flask.__call__() missing 1 required positional argument:
> 'start_response'` — the model wrote a **Flask** (WSGI) application and the
> suite drives it with Starlette's ASGI `TestClient`. Layout mattered only
> for runs that wrote `app/main.py`, which `source_allowlist` never copies,
> so the module was simply absent. The failure-mode table below is left as
> written; this note supersedes its interpretation.

> **Corrected 2026-08-04 by phase 5 cycle 9.** The delegated child in the
> orchestrated arm was **not hermetic.** Pi's shipped subagent extension spawns
> the child without the parent's suppression flags, and user-scope resources
> load unconditionally, so the child loaded the operator's own
> `~/.pi/agent/extensions/` and packages -- including `rtk.ts`, which rewrites
> bash commands. Recorded child transcripts show `ls -R` returning the output
> of `rtk ls -R`.
>
> **This record compares a bare arm against an orchestrated one, so the
> contamination is not constant across the comparison** -- the bare arm has no
> child and was clean. It lands specifically on the orchestrated arm, and rtk
> exists to *reduce* tokens, so any cost ratio here is if anything a
> **lower bound** on what the orchestration cost. The direction of the headline
> finding is unaffected; its magnitude is not defended.
>
> `RunConditions` gained `agent_dir_digest` in cycle 9 so this can never again
> be silent.

## The short version

**Both arms scored 0/16.** That is not the headroom this phase needed — it is
a *floor*, and a floor is exactly as useless for measuring an improvement as
the ceiling the detailed roadmap already had. The suite is built and its
contract is proven; whether it becomes a usable instrument is cycle 5's first
result, not this cycle's claim.

What the cycle did produce is three findings the saturated workload could not
have shown, and one harness bug it found the hard way.

## Aggregates

| | bare | sdd-orchestrator |
|---|---|---|
| accepted | 0/16 | 0/16 |
| wrote any file | **0/16** | **11/16** |
| turns — median (max) | **1 (1)** | 19.5 (**261**) |
| timed out | 0/16 | **6/16** |
| attempted a delegation | — | 9/16 |
| delegation succeeded | — | 6/16 |
| runs with a repeated identical tool call | 0/16 | **15/16** |
| total `context_processed` — median | 1,744 | 119,205 |

## Finding 1 — the bare arm did not fail at the task, it declined to start

All sixteen bare runs took **exactly one turn** and wrote **no files**. They
were not wrong; they were not even attempts. Every run read the spec,
restated it accurately, and stopped to ask what to do:

> "I am ready to begin implementing these requirements. Please let me know
> which file I should start with or if you would like me to explore the
> curr…"

There is nobody to answer: this is a headless single-shot invocation. The run
ends.

The model understood the requirements — it quoted the tagline, listed the
navigation links, restated the HTML5 and environment constraints. **The
missing ingredient was not knowledge, it was agency.** `agentclinic-phase-1`'s
spec is an imperative task list ("Create `app.py` with the FastAPI application
instance") and triggers building. The user-story document is a description of
outcomes and triggers a request for direction.

This is a *different* failure from the prior project's, which recorded
14/16 wrong-framework and 14/16 built-something-else on comparable arms. Ours
is 16/16 built-nothing. Their numbers are not citable, so this is not a
contradiction — but it is a third category, and worth carrying into any future
reading of that series.

## Finding 2 — orchestration restored agency and not correctness

The orchestrated arm wrote files in 11 of 16 runs against the bare arm's 0.
The orchestrator system prompt is itself imperative — *"You orchestrate… Read
the task specification… construct a handoff packet and delegate it"* — and
that appears to supply exactly the act-don't-ask framing the spec lacks.

**This was recorded as a prediction before the arm ran, and it is half
right.** The prediction was that the orchestrated arm would therefore score
"substantially better." It did not: both arms are at zero. Agency is
necessary and not sufficient.

What the runs wrote shows why, and it is the silent-dependency hazard landing
exactly where the spec's audit said it would:

| Layout chosen | Runs |
|---|---|
| `app.py` + `templates/` | 2, 3, 4, 6, 7, 12 |
| `app/main.py` or `app/__init__.py` or `app/app.py` | 5, 8, 9, 14 |
| nothing, or `TODO.md` only | 1, 10, 11, 13, 15, 16 |

and among the template names chosen: `index.html`, `home.html`,
`layout.html`, `base.html`. The acceptance suite imports `from app import
app` and the spec never says so. Four runs also wrote `requirements.txt`,
against an explicit instruction to install nothing.

**Run 6 came closest** — `app.py`, `templates/home.html` — and still failed.
Even the run that guessed the right names did not converge, which is worth
noting before anyone assumes a single missing fact explains everything.

## Finding 3 — this workload thrashes, and the thrash is trivially detectable

**15 of 16 orchestrated runs repeated an identical tool call.** Six timed out.
Run 1 is the extreme: **261 turns, of which 245 were the identical command**
`ls -R`, across only 7 distinct invocations in the whole run. Nothing was
written.

The bare arm's zero repeats is an artifact, not a virtue — a run that takes
one turn cannot repeat itself.

The Backlog's thrash-metrics entry was gated on "a workload where the bare arm
actually thrashes." That is not quite what happened: the *orchestrated* arm
thrashes here. The gate's intent is satisfied — there is now a batch in which
loops occur — and the metric derives from retained `pi_stdout`, so it
recomputes over these checkpoints without rerunning anything.

## Delegation degraded, in two distinct ways

Cycle 2's orchestrated arm delegated successfully on 16/16 runs of the
detailed roadmap. Here, with the *same* improvement and the same extension,
only the task spec differing:

- **7 of 16 never called `subagent` at all.**
- **3 of 16 called it and the child never returned** — a
  `tool_execution_start` with no matching end, which is why they show zero
  delegations and are among the six timeouts.
- 6 of 16 delegated successfully.

A single "delegation rate" collapses those, and they have different causes. A
mechanism worth testing for the first group, stated as a hypothesis and not a
finding: `orchestrator.md` requires every packet to carry an **Allowed Files**
section, and this spec names no files. An orchestrator unable to fill a
mandatory field may be falling back to doing the work itself.

## The harness bug this cycle found

Run 15 of the orchestrated arm **aborted the entire batch**. `git add -A`
exited 128 inside the workspace:

```
error: 'sub/' does not have a commit checked out
fatal: adding files failed
```

The model had run `git init` in a subdirectory — a reasonable thing to try
when the spec names no file layout. Git refuses to stage a nested repository
that has no commit, the exception propagated out of `run_suite`, and the
batch died: the completed run discarded, every queued run cancelled.

The step that killed it is **purely diagnostic**. `grade` copies allowlisted
files into a fresh directory and never reads the diff, so the verdict never
depended on it. Fixed this cycle: the diff is now best-effort and a failure is
recorded in the diff field rather than raised, with a regression test that
builds a nested repo and asserts grading still happens. Reproduced in five
seconds before fixing, rather than guessed at.

## Predictions, scored

| # | Prediction | Outcome |
|---|---|---|
| 1 | The bare user-story arm scores far below 16/16 | **CONFIRMED.** 0/16. |
| 2 | The dominant failure is structural, not partial | **CONFIRMED in direction, wrong in detail.** Predicted wrong-framework or built-something-else; actual bare failure was built-*nothing*, a category neither prior arm produced. |
| 3 | The orchestrated arm does not rescue it | **CONFIRMED.** 0/16. |

The in-flight prediction that orchestration would score "substantially
better" because it restores agency is recorded above as **half right**: the
mechanism appeared, the outcome did not.

## What this does not establish

- **Not that user-story specs are worse.** It establishes that *this* spec,
  against *this* acceptance contract, with two named facts withheld, scores
  zero on both arms. The prior project recovered a comparable arm to 15/16 by
  supplying the technology stack — flagged there as post-hoc and never
  replicated, so it remains a prediction for cycle 5.
- **Not a usable instrument yet.** Two arms at zero discriminate nothing.
  Cycle 5's first lever is what moves this suite off the floor, and until it
  does, no improvement can be measured here.

## Method

Two n=16 batches, sequential, same machine, model, and Pi version. No commit
landed in the batch's working directory between the first run and the last.
Checkpoints, outside version control:
`~/local-ai-pi-evidence/satyrn-phase5-cycle4-user-story-{bare,sdd}-n16.jsonl`,
retaining full `pi_stdout` so every figure here recomputes — including
metrics not yet written.

The orchestrated arm was resumed once after the `git add -A` abort. Resuming
was possible because the checkpoint appends per completed run; the fix was
deliberately **not** committed first, because committing would have moved
`harness_revision` and stranded the 14 records already banked.
