# The engine shootout — pilot

**Phase:** 9 — an engine you can install
**Status:** pilot — a light comparison behind the "why install the engine" pitch, not confirmatory
**Category:** [pilot](../evidence-index.md) — see "What this does not establish"
**Run:** 2026-08-13, model `omlx/gemma-4-12B-it-MLX-8bit` (the harness default), Pi 0.84.1
**Checkpoints:** `~/evidence/shootout-control-2026-08-13.jsonl`, `~/evidence/shootout-engine-2026-08-13.jsonl`

## Question

Does loading the engine — the two guards, `loop-breaker` and
`preserve-symbols`, shipped as one file — change accepted rates on an eval
suite, compared with the same suite, task, prompt, and model without them?

## Design

- **Suite:** `agentclinic-phase-1` — the model builds an application from a
  roadmap (`examples/agentclinic/specs/roadmap.md`) and is graded by the
  acceptance suite (`test_acceptance.py`, 4 tests). Chosen because it is
  the suite with the most room for both guard failure modes: the model
  iterates on `app.py` and templates, re-running the acceptance tests
  (loop-breaker territory) and editing code with functions and routes
  (preserve-symbols territory).
- **Arms:** control (no improvement) versus engine
  (`ENGINE_IMPROVEMENT` in `harness/runner.py` — an extension-only
  `Improvement` carrying `.pi/extensions/engine.ts`). Same task, same
  prompt, same model; the arms differ only in whether the guards are
  loaded. The engine arm's checkpoints record
  `improvement_name="engine"` and the artifact's extension digest, so the
  run is auditable: the guards were genuinely loaded.
- **n:** 6 attempts per arm, sequential, separate checkpoints. A pilot,
  not a pre-registered comparison — no hypothesis, no superiority margin,
  no interval math.

## Result

| Arm | n | accepted | refused | timed out |
|---|---|---|---|---|
| control | 6 | 6 | 0 | 0 |
| engine | 6 | 6 | 0 | 0 |

Both arms at **ceiling**. Loading the guards changed nothing measurable on
this suite at this task.

**The guards never fired.** No engine-arm run produced a single
`loop_broken` or `symbol_preserved` telemetry entry (checked in each run's
recorded Pi output). The model neither looped on a repeated call nor
attempted an edit deleting a public symbol. The engine was present and
inert.

## The honest headline

On a task the model already passes, the engine has no observable effect —
consistent with the loop breaker's own documented framing: it is
"insurance that mostly does nothing." This pilot is the null result that
framing predicts, not evidence against the guards. The guards' value was
established against recorded failures (the 261-turn loop run; the
`/about`-route-deleting edit), and those runs are a different population
from this one — a model that is not looping or deleting symbols cannot be
steered out of failures it is not having.

## What this does not establish

- **No with-versus-without difference.** Both arms at ceiling, so this
  pilot contributes no comparative information. It says nothing about
  whether the guards help on a suite where the control arm fails.
- **Nothing about the executor or orchestration.** This compared the
  guards alone, as everyday steering. The bounded executor
  (`deliver_candidate`), the mutation engine, and the typed-contract
  bridge are untouched by this comparison and unmeasured by it.
- **Nothing beyond one suite.** `agentclinic-phase-1` at this task and
  this model. No claim for `agentclinic-phase-1-user-story`, `duration`,
  another model, or a different task.
- **Not confirmatory.** Pilot, not pre-registered; no intervals, no
  superiority margin, and it is not pooled with the Phase 7 confirmatory
  result. A negative pilot is not a reason to distrust the guards' recorded
  evidence; a positive pilot would not have been a verdict.

## Reproduction

```bash
uv run python -c "
from pathlib import Path
from harness.runner import run_batch, AGENTCLINIC_PHASE_1, ENGINE_IMPROVEMENT
for arm, imp in [('control', None), ('engine', ENGINE_IMPROVEMENT)]:
    cp = Path.home() / 'evidence' / f'shootout-{arm}-2026-08-13.jsonl'
    results = run_batch(cp, suite=AGENTCLINIC_PHASE_1, target=6, improvement=imp)
    print(arm, sum(1 for r in results if r.grade.accepted), '/', len(results))
"
```

Requires the local model server (`docs/setup.md`, Part 2). The checkpoints
live outside version control, at the paths above.
