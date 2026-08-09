# Cycle 1b predictions — Qwen3.6 27B, brief-only

Written and committed **before** the run.

**Why.** Cycle 1 produced two far-apart points: a 12B that could not start, and
DeepSeek V4 Flash that closed 6 of 8 gaps outright including the declared
ceiling. Neither says where *pre-chewing* starts to matter, because a variable
only shows an effect where the outcome is uncertain. A 27B between them is the
most likely place to find that, which makes it the point every version of the
plan needs.

**Arm.** Identical to Cycle 1 in every respect that was recorded: brief-only,
`--tools read,bash,edit,write`, `probe-cap.ts` (60 turns / 150 tool calls),
1800s cap, workspace dev environment, grading rule 7. Scored on gap closure per
`CYCLE1-SCORING.md`.

**Two conditions differ and are recorded, not hidden.** Context window is 80,000
against DeepSeek's 60,000 — non-binding, since the largest per-call context
observed all day was around 30k. And sampling follows the Qwen card's
*precise-coding* profile (temperature 0.6, top_p 0.95, top_k 20) rather than
whatever DeepSeek's server defaults were, which were never inspected.
`defaultThinkingLevel` stays `high` for both, deliberately: it is a known cost —
about 60% of DeepSeek's output tokens were reasoning — but changing it here
would confound the model comparison this run exists to make.

## Per-task predictions

| Task | Gap | DS4F | Predicted 27B | Reasoning |
|---|---|---|---|---|
| `registry-iter` | 1 | closed | **close** | Add `__iter__` to one class. If this fails, something is wrong with the arm. |
| `magicmock-factory` | 1 | closed | **close** | Needs the insight that a mock answers every attribute, but the fix is one guard. |
| `flask-extensions` | 2 | closed | **close** | Mechanical relocation in one small module. |
| `async-cm-enter` | 2 | closed | **close** | Well-bounded, fully described, both factory paths. |
| `local-pings` | 3 | closed | **fail** | Three coupled behaviours including suppression; DS4F got it but I predicted otherwise and was wrong. Holding the harder call at the smaller model. |
| `stringified-annotations` | 2 | **0%** | **fail** | The only task DS4F failed on merit. A smaller model should not clear it. |
| `fastapi-get-registry` | 15 | 87% floor | **fail** | DS4F reached 87% and ran out of turns. 15 nodes across two integration modules. |
| `autowire` | 67 | closed | **fail** | 251 lines of new production code. DS4F solving this first-try was the biggest surprise of Cycle 1; I do not expect it to repeat two model sizes down. |

**Aggregate prediction: 4 of 8 gaps closed**, with partial progress on
`fastapi-get-registry` the most likely near-miss.

## What each result means

- **3–5 closed, spread across difficulty** — the frontier is real and the 27B
  sits on it. This becomes the model for the contract arm, because it is the
  only one where chewing has room to change an outcome.
- **7–8 closed** — the 27B is already above this cohort. The interesting cell
  is then the 12B, and the cohort needs harder tasks to say anything about
  anything larger.
- **0–2 closed** — the drop from DeepSeek is a cliff rather than a gradient.
  That would be the most interesting result of the phase: it would mean
  capability, not chewing, is doing the work, and the pre-chewed-work pitch
  needs a mechanism it currently lacks.

## Non-predictions

Scope violations. DeepSeek wrote changelog or docs on 4 of 8 and tests on 6 of
8; whether that is a property of capable models or of that model specifically is
exactly what a second model tells us, and guessing first would only make the
answer feel less surprising than it is.
