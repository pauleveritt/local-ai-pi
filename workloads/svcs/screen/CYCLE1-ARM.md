# Cycle 1 arm change — the executor gets a dev environment

**Written before run 3, after two aborted runs.** Second addendum to
`CYCLE1-PREDICTIONS.md`, alongside `CYCLE1-SCORING.md`. Same reason both exist
separately: the arm changed mid-cycle and the record should say so in its own
file rather than have a "written before the run" document quietly grow.

## The change

The executor's workspace now carries a working dev environment: `uv sync
--locked --no-install-project` from `workloads/svcs/env/` into
`<workspace>/.venv`, with `PATH`, `VIRTUAL_ENV` and `PYTHONPATH=<workspace>/src`
set for the child. Same lock as the grading environment, dependencies only.
`--blind` reproduces the old bare-tree arm as an ablation.

## Why

The phase claims a small local model can do **routine, pre-chewed coding work**.
Routine work happens in a repository that has a working environment. An
executor that cannot run anything is being asked to write correct code blind,
which is a harder and more artificial task than the one being claimed, and it
is not what the eventual product does — that runs in a worktree of a user's own
repository, where an environment exists.

Cycle 1's specific job makes it worse. The probe exists to separate "the brief
is defective" from "the capability floor", and a bare workspace injects a third
cause that looks like neither. `magicmock-factory` is the measurement:
diagnosis correct at turn 6, then turns 9 through 16 spent trying to obtain a
runnable Python, turn budget exhausted, zero edits, graded `no-changes`. That
is an envelope artifact being recorded as a capability floor.

## What keeps the oracle hidden

Unchanged, and checked rather than assumed:

- Oracle files exist only inside the grading materialisations. `overlay_oracle`
  is called from `grade_candidate`, after the child has exited. The executor
  environment contains third-party dependencies only; nothing new is reachable.
- The base tests the executor can now run are the ones already in its
  workspace. They pass at base, contain no oracle nodes, and give regression
  signal — which is what a developer has.
- Editing tests to cheat was already defeated and still is:
  `apply_candidate(include=writable)` strips test edits before both graded
  runs, and preservation runs pristine base tests.
- Grading continues to use `.workloads/env` via `CohortEnv`, hash-verified. The
  executor venv dies with its workspace.
- The venv is excluded through `.git/info/exclude`, not a committed
  `.gitignore`, so the tree stays byte-identical to base and
  `capture_candidate` cannot sweep site-packages into a candidate patch.
  `test_the_executor_venv_never_reaches_the_candidate_patch` pins it.

One leak surface is unchanged and predates this: the clone cache at
`.workloads/svcs.git` holds full upstream history, including every target
commit. Nothing in the child's cwd or `PATH` points at it, and `materialize`'s
own docstring already says it is not confinement. Recorded, not fixed here.

## What is invalidated

Nothing. Cycle 0's ceiling replay and the frozen qualifications involve no
model and an unchanged grading environment. The freeze rule freezes the *task*
— oracle files, command, rejection fingerprint, SHAs, manifest env fields — and
gates brief and contract edits behind `contract_version`. The executor
environment is an arm parameter, not a manifest field, so no manifest changes,
no version bumps, and the three tasks with prior attempts (`registry-iter`,
`magicmock-factory`, `async-cm-enter`) are unconstrained.

`GRADING_RULE_VERSION` stays at 5: the acceptance rule is untouched. The
condition is recorded per attempt as `executor_env_lock_sha256`, and in the run
summary as `executor_env`.

## Predictions

The per-task predictions and the aggregate of **5 of 8** stand unchanged. They
were made assuming the executor could function at all, which is now closer to
true than it was when they were written.

## One consequence for the scoring rule

`CYCLE1-SCORING.md` reports the scope-violation rate as a finding of its own.
That rate is now **conditional on this arm**, and must be reported under the
arm name: an executor that can run the existing suite may verify against it
instead of authoring a test, or may write and run its own repro. Do not compare
the rate across environment conditions — the same discipline the predictions
file already applies to the 12B comparison.
