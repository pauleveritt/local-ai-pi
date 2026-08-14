# The engine shootout

**Phase:** 9 — an engine you can install
**Status:** pilot — a first pass behind the "why install the engine" pitch, not confirmatory
**Category:** [pilot](../evidence-index.md)
**Run:** 2026-08-13 (the pre-chewed ceiling) and 2026-08-14 (the user-story comparison), model `omlx/gemma-4-12B-it-MLX-8bit` (the harness default), Pi 0.84.1
**Checkpoints:** `~/evidence/shootout-control-2026-08-13.jsonl`, `~/evidence/shootout-engine-2026-08-13.jsonl`, `~/evidence/shootout-userstory-control-2026-08-14.jsonl`, `~/evidence/shootout-userstory-engine-2026-08-14.jsonl`

The question underneath the pitch is simple: does the engine — the two
guards, loop-breaker and preserve-symbols, shipped as one file — change
what happens? The answer depends entirely on the problem you hand it. Two
populations, two answers, and the one gap the record left open — the
guards' individual share of the composite number — is closed by this run.

## 1. The pre-chewed floor: no effect, and why that is the point

The easiest suite, `agentclinic-phase-1`, is easy on purpose. Its task
spec is the output of this project's own spec-driven process — 28 lines
naming every file, every route, and the exact tagline text. The model
transcribes a design a "big brain" already pre-chewed. There is nothing
left to get wrong.

| Arm | n | accepted | turns | tool calls | tokens |
|---|---|---|---|---|---|
| control | 6 | 6 | 7.0 — every run | 6 — same sequence every run | ~10,117 |
| engine | 6 | 6 | 7.0 — every run | 6 — same sequence every run | ~10,077 |

Every one of the twelve runs took exactly 7 turns and the identical six
tool calls (`bash`, `write` ×4, `bash`). The guards never fired — no
`loop_broken`, no `symbol_preserved` — because there was nothing to steer.

This is not evidence that the engine is useless. It is the floor we intend
to move: a task the model already passes cannot show steering, any more
than insurance pays out on a run with no accident. The shootout's real
question starts where this suite ends.

## 2. The harder suite: where the composed engine showed up

`agentclinic-phase-1-user-story` states the same application as outcomes
("what agents experience, not what files to create") — the model must
infer the implementation. Here the as-shipped pipeline came apart. The
full record is [phase 5 cycle 10](../superpowers/research/2026-08-04-phase5-cycle10-publishable-arm.md); the numbers:

| Arm | accepted | timeouts | median turns | max turns | median transcript |
|---|---|---|---|---|---|
| cycle 4 — as-shipped | 0/16 | 6/16 | 30.5 | 261 | 2.65 MB |
| cycle 10 — corrected, guarded, stacked, hermetic | 13/16 | 1/16 | 14 | 42 | 0.50 MB |

The baseline was not merely failing — it was deranged: 261-turn runs, a
71.88 MB transcript, 1.8M context tokens, an `ls -R` repeated 245 times,
and runs that stopped to ask a human what to do. The corrected arm cut
median turns in half, kept every run under 42, and — in the clearest
possible demonstration of what the guards are for — the loop breaker fired
12 times across two runs and **both still passed**; one had repeated a
single call 14 times and was steered out.

Two honesty clauses, from the record itself. First, that arm is
**composite**: four changes landed together (call shape, empty-workspace
statement, stack naming, hermetic child) with the guards as insurance on
top — the 0/16 → 13/16 is the composed pipeline's number, and the guards'
individual share is not isolated in it. Second, it is not a comparison
against bare Pi on this suite: the cycle-4 floor was partly "stopped to
ask a human", a different failure mode.

## 3. The missing measurement, run

Put the two sections together and the gap was exact. The guards alone had
been measured only on the pre-chewed suite, where nothing fires; the
composed engine had been measured on the harder suite, where the guards'
share could not be separated. The run that closes the gap — bare control
versus guards-only on `agentclinic-phase-1-user-story` — is the one this
section records (2026-08-14, pilot n=6 per arm, `run_timeout=600`).

| Arm | n | accepted | timeouts | turns | tool calls | guard firings |
|---|---|---|---|---|---|---|
| bare control | 6 | 0/6 | 0 | 1 — every run | 0 — every run | — |
| guards-only | 6 | 0/6 | 0 | 1 — every run | 0 — every run | 0 — no `loop_broken`, no `symbol_preserved` |

The two arms are floor-tied, and the guards never fired — not because they
slept through anything, but because there was nothing to fire on. Every one
of the twelve runs took exactly one turn and made **zero tool calls**: the
model read the spec, restated the requirements, and stopped to ask the human
how to proceed, then settled. The grader found `No module named 'app'` in
all twelve — the model wrote nothing. That is the cycle-4 bare failure mode
("stopped to ask a human what to do"), reproduced at n=6.

The engine arm's checkpoints record the engine bundle's extension digest
(`62dc3260…`, plus hello-world), so the guards were loaded; zero firings is
not a silent load failure.

The honest reading is the one the record's honesty clause predicted. The
guards do **not** rescue these failing runs, because the failure happens
before any tool call exists to steer — the loop breaker and
preserve-symbols act on tool calls, and a run that never makes one is out of
their reach. So the cycle-10 composite's 13/16 cannot credit the guards with
"rescuing failing runs" on this suite: whatever moved 0/16 to 13/16 lives in
the orchestrator/implementer stack and the facts (naming FastAPI and
`app.py`), not in the guards alone. That is a real finding, not a wash — it measures the guards'
individual share at zero and relocates the effect.

Two non-claims, stated so the zero is not overread. First, this is a pilot —
one suite, one model, n=6 per arm, not pooled, not confirmatory. Second, it
is not a verdict that the guards are worthless: the cycle-10 record already
shows the loop breaker firing 12 times across two runs that still passed.
The insurance pays out where there is an accident to steer; the user-story
suite's bare failure is upstream of any accident, so a tool-call guard is
the wrong instrument for it and shows exactly zero.

And there is no suite more complex than user-story to move to yet. The
three runnable suites are all ~30-line tasks; the genuinely harder
`workloads/svcs/` cohort lives on a different product path (the typed
handoff bridge, not `run_suite`). Making the floor move means authoring
harder tasks in the user-story style — which is the plan, not an accident.

## Reproduction

The pre-chewed ceiling (2026-08-13):

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

The discriminating user-story comparison (2026-08-14):

```bash
uv run python -c "
from pathlib import Path
from harness.runner import run_batch, AGENTCLINIC_PHASE_1_USER_STORY, ENGINE_IMPROVEMENT
for arm, imp in [('control', None), ('engine', ENGINE_IMPROVEMENT)]:
    cp = Path.home() / 'evidence' / f'shootout-userstory-{arm}-2026-08-14.jsonl'
    results = run_batch(cp, suite=AGENTCLINIC_PHASE_1_USER_STORY, target=6, improvement=imp)
    print(arm, sum(1 for r in results if r.grade.accepted), '/', len(results))
"
```

Requires the local model server (`docs/setup.md` Part 2). The checkpoints
live outside version control, at the paths above.
