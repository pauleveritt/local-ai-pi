# Cycle 1, third attempt — stopped at 1 of 8, budget truncated the work

Kept as the evidence that sized the probe budget.

## What it showed working

The environment arm works. On `registry-iter` the model ran
`.venv/bin/python -m pytest tests/test_registry.py`, saw that its own new test
asserted the wrong thing (`n.split(".")[-1]` yields the module name, not the
class), fixed it, and re-ran green. That behaviour did not exist in any earlier
run.

Gap closed 100%, `executor_env_lock_sha256` recorded.

## Why it was stopped

The run used `envelope-cap.ts` — 16 turns, 30 tool calls. Those numbers mirror
`MAX_IMPLEMENTER_TURNS` and the implementer policy's `maxTools`, and exist to
answer a different question: whether constrained latency explains the engine's
tight wall-time distribution, in an arm with `--tools read,write` and no way to
execute anything.

Giving the executor an environment changed the arm and left the budget where it
was. On the declared **floor** task the result was:

- t16: ran `--doctest-modules src/svcs/_core.py`, saw the doctest it had just
  written into `__iter__` FAIL
- t17: turn budget exhausted, run aborted, repository left broken

Preservation failed on `src/svcs/_core.py::line:174` and `:176` — the model's
own doctest. A budget that truncates repair manufactures exactly the false
floor a headroom probe exists to rule out. On the eight-task cohort the harder
tasks (`fastapi-get-registry`, 15 nodes; `autowire`, 67) would have hit it
harder.

Three further turns went to a self-inflicted problem: the model twice tried to
`cd` to a truncated form of the workspace path (`satyrn-workload-76gm` for
`satyrn-workload-76gmctfl`), and only found the real name by running `pwd`. The
session record carries the full path, so this is the model failing to copy an
opaque random string, not a harness defect. It recurred across runs. Effective
budget was therefore about 13 turns, not 16.

## What changed as a result

- `extensions/probe-cap.ts` — 60 turns / 150 tool calls for headroom probes.
  `envelope-cap.ts` is untouched and byte-identical, so the historical arm stays
  reproducible by name.
- `Attempt.budget_exhausted`, lifted out of the transcript by the extension's
  own entries. A run that stopped at the ceiling is not a run that could not do
  the work, and nothing was carrying that distinction into the result.
  `report_screen` prints it per task and in the summary.
- Grading rule 6: damage outranks a scope violation. This run reported
  `out-of-scope` for a candidate whose own doctest had broken the suite —
  "wrote in the wrong place" standing in front of "left the repository
  broken".

## Status

Not poolable with anything. One task, superseded budgets, and rule 5.
