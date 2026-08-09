# Cycle 1, second attempt — stopped at 2 of 8, environment not contained

Kept as evidence. These two attempts ran before `pi_env()` stripped the
harness virtualenv, and the transcripts are the record of what that allowed.

## What happened

`pi_env()` passed `os.environ` straight through, so the child's `PATH` began
with the harness's own `.venv/bin` and `VIRTUAL_ENV` pointed at it. An executor
with `bash` therefore had **the grader's interpreter as its `python3`**.

`magicmock-factory` used it. The transcript
(`magicmock-factory.jsonl`) shows the model diagnose the bug correctly at
turn 6 — it identified that `isinstance(svc, AbstractContextManager)` answers
true for a `MagicMock` because a mock answers every attribute — and then spend
turns 9 through 16 trying to make `import svcs` work:

- t9  `python -c "import svcs"` -> ModuleNotFoundError
- t10 retry with `sys.path.insert(0, 'src')` -> ModuleNotFoundError (needs attrs)
- t13 `import attrs` -> ModuleNotFoundError
- t14 `python3 -m pip install ...` -> no pip in that venv
- t15 **`python3 -m ensurepip`** -> installs pip 25.3 into the harness venv
- t16 **`pip install attrs pytest pytest-asyncio`** -> "Successfully uninstalled
  pytest-8.3.4", installs pytest 9.1.1, attrs 26.1.0, pytest-asyncio 1.4.0
- t17 stops with `stopReason=error`, having never edited a file

It replaced the harness's pinned pytest with a different major version. An
executor that can change the tooling that grades it is not being measured.

## Blast radius, checked rather than assumed

- **Harness venv: contaminated.** `pip`, `attrs`, `pytest-asyncio` added, and
  `pytest` swapped. Restored with `uv sync --all-groups`; verified absent after.
- **Frozen cohort env: untouched.** It lives at `.workloads/env`, is passed to
  `run_suite` explicitly rather than through `PATH`, and was never on the
  child's `PATH`. Verified package-by-package against `workloads/svcs/env/
  uv.lock`: no version mismatches, no extras beyond name-normalisation and
  platform-conditional entries. **Grading was not compromised.**
- **The repository: untouched.** `git status` clean apart from screen output.

## Why these results are not usable

`magicmock-factory` graded `no-changes`, but the cause was environmental
interference, not capability. The model had the right diagnosis and never got
to use it. Reporting that as a capability floor would have been wrong, and
before transcripts were saved it is exactly what would have happened.

`registry-iter` reproduced its earlier result (gap closed 100%, wrote a test,
out of scope, 147s vs 122s) and did not touch the venv — but it ran under an
environment no later run will use, so it is not comparable either.

## The question this leaves open

Even contained, the executor still has no way to run the suite: the workspace
has no installed dependencies. `magicmock-factory` shows a model spending half
its budget discovering that. Whether the arm should hand the workspace a
runnable environment is a real design decision with a real effect on power, and
it is recorded here rather than settled quietly.
