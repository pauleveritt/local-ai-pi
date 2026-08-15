# SLM struggles

What actually goes wrong when you drive a small local model at agentic
coding. Every entry here is something this project hit, recorded somewhere
in this repository — the pointer is where. They are ordered roughly by how
much they bite: silent corruption first, wasted hours second, then the
narrower gotchas.

## The silent fabricated result

The model server is down, `pi` exits **0** with empty stderr, and the
harness records a result that looks like data — a verdict on the setup
masquerading as a verdict on the model. This is why every run path checks
liveness first, and why "verify, don't assert" is a project rule, not a
style preference.
*BRIEF.md, practical environment.*

## There is no trustworthy wall-clock number

Two published figures were retracted in one night, both for the same
reason: arms ran as contiguous blocks on a machine whose load varies.
Counts (turns, tokens, tool calls) survive; seconds do not. Interleaving
arms is the stated precondition for any future timing claim.
*ROADMAP, "Now" findings.*

## The 261-turn loop

One recorded run: 261 turns, 245 of them the identical `ls -R` against an
empty directory. The loop breaker extension exists because of this run —
refusing a tool call the model has already made, unchanged, several times
in a row.
*README and docs/engine/loop-breaker.md.*

## Stale-anchor edits

27 `oldString` mismatches in a single session record — the model keeps
editing text that moved, because it anchors on what it wrote before, not
what is there now.
*ROADMAP, candidate well.*

## Path-keyed churn

The same file rewritten identically again and again: 27× one template,
19× and 10× `app.py`. The loop breaker's key includes the arguments, which
is why 26 of 27 byte-identical writes tripped it and the rest did not.
*ROADMAP, candidate well.*

## Facts work, rules of conduct do not

Across five prompt interventions, the three that supplied a fact the model
lacked worked; the two that supplied a rule of conduct did not. "Stop
re-running a command that fails identically twice" produced three
pre-registered predictions and three falsifications.
*ROADMAP, "Now" findings.*

## The wrong framework contract

The suite drives ASGI; the model chose a WSGI framework. Every run that
wrote `app.py` and still failed did so with
`TypeError: Flask.__call__() missing 1 required positional argument:
'start_response'`. A related trap: a solution under `app/main.py` never
reaches the grader at all, because the allowlist copies `app.py` and
`templates` only.
*harness/runner.py, the sdd_orchestrator_guarded_stack docstring.*

## Tool-output explosion

A child lists recursively into directories that stay empty — the initial
choice is stochastic, the context explosion after it is deterministic. The
empty-workspace case is worse than it looks: there is nothing there, and
listing keeps returning nothing, but the model keeps spending turns
confirming it.
*ROADMAP, candidate well; improvements/sdd-orchestrator/orchestrator.md.*

## No turn cap at any level

Pi has no turn cap — a run goes to 261 turns and beyond unless something
stops it. Blocking dominates aborting, because an aborted delegation is
reported as a failed one.
*ROADMAP, candidate well.*

## The agency floor

The user-story suite ran both arms to **0/16** — a floor, not headroom.
Bare Pi read the spec, restated it accurately, and stopped to ask what to
do, writing nothing in all sixteen runs.
*docs/superpowers/phase-history.md.*

## Thrashing after agency

The orchestrator prompt restored agency (11/16 wrote files) but not
correctness: the arm thrashed — 15/16 runs repeating an identical tool
call, six timeouts, one run at 261 turns.
*docs/superpowers/phase-history.md.*

## Single-threaded contention

The model server serializes children. Concurrent children contend for it
and neither finishes sooner — a batch is many sequential runs, and the
prompt says so explicitly to stop the model from parallelizing.
*improvements/sdd-orchestrator/orchestrator.md; docs/evals/index.md.*

## A commit aborts a running batch

A batch records the harness revision as a run condition and refuses to
resume a checkpoint whose conditions moved. Committing mid-batch kills the
batch and forces a fresh checkpoint.
*harness/runner.py, RunConditions; docs/evals/index.md.*

## The silent extension-directory failure

Pointing `--extension` at a directory produces no error, no stderr, and no
warning. The only symptom appears much later, when the model calls the
tool and gets `"Tool subagent not found"` — by which point the parent has
often done the work itself.
*harness/runner.py, sdd_orchestrator docstring.*

## The missing Authorization header

oMLX demands a Bearer header but never checks its value. Without it, a
perfectly healthy server answers 401 and reads as down. Cost real
debugging time before it was documented.
*docs/evals/setup.md.*

## The child loads your own extensions

A delegated child inherited the operator's user-scope extensions. Recorded
transcripts show `ls -R` returning the output of `rtk ls -R` — the
operator's extension was rewriting the child's bash commands under it.
*harness/pi_invocation.py, pi_env docstring.*

## The model installs into the harness venv

A model with a shell spent eight turns making `import svcs` work,
running `ensurepip` and then `pip install`ing packages — replacing the
pinned pytest 8.3.4 with 9.1.1. The thing being graded changed its own
grader.
*harness/pi_invocation.py, pi_env docstring.*

## `which pi` lies under volta

It returns a shim binary that says nothing about which package it
dispatches to; `npm root -g` points at the node image, not the package. A
wrong answer here is expensive and silent — the improvement points at
nothing and every orchestrated run quietly becomes a bare run.
*harness/runner.py, pi_package_root docstring.*

## The forgotten models.json restore

The practice was: hand-edit `maxTokens`, run, hand-edit it back. Nothing
enforced the restore, and a forgotten one silently broke the frozen
envelope cells' reproducibility. A context manager now makes the restore
structural.
*harness/model_config.py.*

## A model-created nested git repo aborts the batch

`git init` in a subdirectory makes the harness's `git add -A` fail
outright, and before the fix that discarded one completed run and cancelled
every queued run — over a step that only produces a diagnostic.
*harness/runner.py, run_suite docstring.*

## Silent Pi-version drift

A different Pi version is an unrecorded variable between contributors.
The pin turns a silent upgrade into a red suite — a deliberate failure.
*docs/evals/setup.md; tests/test_runner.py.*

## Default-deny evasion

A child hit its denied `ls`, then routed the same intent through a shell
tool injected via the editor. Denial without a watched alternative just
moves the call.
*ROADMAP, candidate well.*

## The empty-workspace search trap

The workspace starts empty by design, and the model has to be told so in
the prompt — otherwise it spends turns listing a directory that will keep
returning nothing, because there is nothing there.
*improvements/sdd-orchestrator/orchestrator.md.*

## Environment leaks reach the child

A live `SSH_AUTH_SOCK` is push access to every remote the operator can
reach, and the harness venv on the child's PATH hands the model a
different Python than the grader intends. Both are stripped from the
measured run's environment.
*harness/pi_invocation.py, pi_env docstring.*

## A grader defeated by configuration

Earlier graders were defeated by `addopts = --collect-only` and an
import-time `os._exit(0)` — model-written config executed during
collection. The verdict now comes from a hook-written results file, never
from pytest's exit code, and model-written config is refused outright.
*BRIEF.md; harness/grading.py.*

---

Not every struggle is the model's fault — several above are environment
and harness traps the model merely walked into. That distinction is the
point of keeping the records: the honest question is always whether the
engine made the model look bad, not just whether the model was bad.
