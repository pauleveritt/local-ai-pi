# Cycle 3 predictions — Gemma 4 12B, brief-only

Written and committed **before** the run.

**Why.** The 12B's old 0/9 is retired as evidence: it predates the executor
environment, the probe budgets, grading rule 7, and validity checking, and it
ran under an envelope with `--tools read,write` that could not enumerate a
repository at all. The frontier needs an honest floor, and this is the only
remaining cell in the cohort whose outcome is genuinely uncertain — both larger
models are at or near ceiling on six of eight tasks.

**Arm.** Identical to Cycles 1 and 1b: brief-only, `--tools read,bash,edit,write`,
`probe-cap.ts` (60 turns / 150 tool calls), 1800s cap, workspace dev
environment, grading rule 7, validity assessed from the transcript.

**Context window matched deliberately.** The 12B had no oMLX per-model entry, so
it would have run at the 32,768 global default while Qwen ran at 80,000 — and
Qwen peaked at 33,861 tokens on `magicmock-factory`. That would have produced a
truncation indistinguishable from incapacity, on the one cell that still
matters. An entry was added and verified empirically: the server now rejects an
oversized prompt with "exceeds max context window of 80000 tokens".

One condition still differs and is recorded: `maxTokens` is 8,192 for this model
against Qwen's 32,768. That is a per-response cap, and the largest single
response observed in either sweep is far below it, so it should not bind.

## Per-task predictions

| Task | Gap | Qwen 27B | DS4F | Predicted 12B | Reasoning |
|---|---|---|---|---|---|
| `registry-iter` | 1 | closed | closed | **close** | Add `__iter__` to one class, adjacent to an existing `__contains__` to copy. The simplest thing in the cohort. |
| `flask-extensions` | 2 | closed | closed | **close** | Six mechanical lines relocating a value under the same key, in one small module. |
| `magicmock-factory` | 1 | closed | closed | **fail** | One line, but it needs the insight that a mock answers every attribute. Diagnosis, not transcription. |
| `local-pings` | 3 | closed | closed | **fail** | Three coupled behaviours including suppression. |
| `async-cm-enter` | 2 | closed | closed | **fail** | Async lifecycle across both factory paths — the known weak axis for small models. |
| `stringified-annotations` | 2 | closed | **0%** | **fail** | Reflection over annotation forms. DeepSeek failed it outright. |
| `fastapi-get-registry` | 15 | 27% | 87% | **fail** | Fifteen nodes across two integration modules. |
| `autowire` | 67 | 78% | void | **fail** | 251 lines of new production code. |

**Aggregate prediction: 2 of 8 gaps closed.**

## Calibration note, recorded because it should count against me

I have under-predicted both models today. DeepSeek: per-task 8 for 8 once the
tainted result was removed, but I called its ceiling task a certain reject.
Qwen: predicted 4 of 8, got 6, and was wrong in the same direction on
`local-pings` and `stringified-annotations` — both mid-difficulty tasks I judged
too hard.

So 2 of 8 may well be low again. I am not adjusting it upward, because moving a
number to protect a track record is worse than being wrong twice: the prediction
is only worth something if it is what I actually believe. What I do believe is
that the gap between a 12B general-instruct model and a coding-tuned 27B is
categorically larger than the gap between the 27B and DeepSeek.

## What each result means

- **1–3 closed** — the frontier is real and the 12B is on its lower slope. This
  becomes the model for the contract arm, because it is the only place where
  chewing has room to change an outcome.
- **0 closed** — a cliff, not a gradient. Capability rather than chewing is
  doing the work, and the pre-chewed-work pitch needs a mechanism it does not
  currently have. This is the most consequential possible result and the reason
  the cell is worth eight calls.
- **≥5 closed** — Fable's stop rule fires: the cohort is too easy across the
  whole model range available, and harder tasks must enter before anything else
  is measured.

## Non-prediction

Scope. Qwen touched nothing outside `src/svcs/**` on any task; DeepSeek wrote
changelogs or docs on four of seven. With one model at each extreme there is no
basis for a guess, and the third data point is the interesting part.
