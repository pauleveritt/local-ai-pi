# Cycle 1 predictions — headroom probe, brief-only, full tools

Written and committed **before** the sweep runs.

**Purpose.** Separate "the brief or task is defective" from "the 12B is below
the floor", per task. A task a stronger executor solves brief-only has a sound
brief and real headroom; a task it fails is a suspect brief before it is
evidence about anything.

**Arm.** brief-only, `--tools read,bash,edit,write`, envelope budgets
(`extensions/envelope-cap.ts`: 16 turns, 30 tool calls), one attempt per task.
Cohort is 8 — `suppress-context-exit` was excluded by the ceiling replay.

**Executor.** `dsflash/deepseek-v4-flash`, a local server on port 8002,
60k context. Verified by throwaway probe: Pi drives it, it calls `read` then
`edit` with the correct input shape, and the edit lands.

## The caveat that limits what a null result means

This is a *different* local model, not a frontier one. If it also scores 0/8,
that is genuinely ambiguous — "the briefs are defective" and "both local models
are below this cohort's floor" both predict it, and this run cannot separate
them. A frontier control would. Only a **positive** result here is clean: any
task it solves is proven to have a sound brief and real headroom.

Recording this now so a null result is not narrated afterwards as though it had
settled something.

Two changes from the 12B screen also mean this is not a like-for-like
comparison, and no cross-model rate should be quoted from it: tools widen from
`read,write` to `read,bash,edit,write`, and grading moves from rule 4 to
rule 5. The 12B numbers would have to be re-run to compare.

## Per-task predictions

| Task | Gap (nodes) | Predicted | Reasoning |
|---|---|---|---|
| `registry-iter` | 1 | **accept** | Add `__iter__` to one class. The declared floor. |
| `magicmock-factory` | 1 | **accept** | Small, but needs the diagnosis that a `MagicMock` answers every attribute. A capable model should get it; the 12B did not. |
| `flask-extensions` | 2 | **accept** | Mechanical relocation in one small module. The only task the 12B has ever solved. |
| `async-cm-enter` | 2 | **accept** | Async lifecycle across both factory paths — real work, but well-bounded and fully described. |
| `stringified-annotations` | 2 | **reject** | Reflection over annotation forms; only 2 parametrised cases fail at base, so a partial fix scores zero. |
| `local-pings` | 3 | **accept** | Three coupled behaviours, but the fix sits in one resolution path. |
| `fastapi-get-registry` | 15 | **reject** | 15 nodes across two integration modules, with composed-lifespan and post-shutdown cases the brief lists but does not spell out. |
| `autowire` | 67 | **reject** | 251 lines of new production code. A one-call accept would be extraordinary. |

**Aggregate prediction: 5 of 8 accepted.**

## What each result means

- **5±1 of 8, split roughly as predicted** — the cohort is sound and has
  headroom. The 12B's 0/9 was a capability read, not a brief defect. Proceed to
  Cycle 2.
- **≤2 of 8** — Fable's stop rule fires. The phase halts on briefs and cohort,
  not on the 12B. Repair the failing briefs, bump `contract_version`, re-run
  only those. Spend nothing on the 12B until it clears.
- **0 of 8** — see the caveat above. Ambiguous, not informative. The next step
  is a frontier control on 2–3 tasks, not more local-model calls.
- **8 of 8, including `autowire`** — the briefs leak more than intended. Read
  the `autowire` candidate before believing any of it.

## Non-predictions

I am not predicting per-task runtime, and 60k context is a fifth of what the
12B had. If a task dies on context rather than on capability, that is an
envelope finding, not a capability one, and it must be reported as such.
