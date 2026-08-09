# Screen predictions — brief-only envelope, one attempt per task

Written and committed **before** the sweep runs. The point is calibration:
curator fingerprint predictions ran 7/10 in qualification, so predictions about
model behaviour deserve the same treatment — recorded in advance, scored
afterwards, wrong ones left visible.

**Arm:** brief-only. The executor sees `brief.md` and the base tree. No
contract. Envelope: one call, `read,write` only, 16 turns, 30 tool calls,
`omlx/gemma-4-12B-it-MLX-8bit`.

**This is not evidence.** One attempt per task, no repetition, no interleaving.
It answers one question: does the cohort spread outcomes?

## Per-task predictions

| Task | Role | Predicted | Reasoning |
|---|---|---|---|
| `registry-iter` | floor | **accept** | Add `__iter__` to one class. If this fails, the harness is broken, not the model. |
| `flask-extensions` | medium | **accept** | Mechanical: move a value from `app.config` to `app.extensions` under the same key, in one small module. |
| `magicmock-factory` | medium | **reject** | Requires knowing *why* a `MagicMock` breaks the existing check — a mock answers every attribute. Diagnosis, not transcription. |
| `local-pings` | medium | **reject** | Three coupled behaviours including a suppression case, and the fix sits in resolution code the brief does not point at. |
| `async-cm-enter` | medium | **reject** | Async lifecycle, and the known weak axis. Needs both sync- and async-factory paths handled in the async resolution route. |
| `stringified-annotations` | medium | **reject** | Reflection over annotation forms; only 2 of the parametrised cases fail at base, so a partial fix scores as failure. |
| `suppress-context-exit` | stretch | **reject** | New public option threaded through registry and both sync and async container exit paths. |
| `fastapi-get-registry` | stretch | **reject** | 15 hidden tests across two integration modules, with composed-lifespan and post-shutdown edge cases the brief lists but does not spell out. |
| `autowire` | ceiling | **reject** | 251 lines of new production code and 67 hidden tests. A one-call accept here would be genuinely surprising. |

**Aggregate prediction: 2 of 9 accepted** (`registry-iter`, `flask-extensions`).

## What each result would mean

- **2/9, and the seven rejections split across distinct failure modes** —
  cohort works. Middle tasks that fail *near* the oracle are the signal we
  need; the failure taxonomy tells us which.
- **0/9 or 1/9** — floor-heavy. Fable's predicted risk. The middle is empty and
  the instrument is two-point again. Fix the workload before building cycle 3.
- **2/9, but every rejection is the same shape** (nothing written, or scope
  violations everywhere) — not a capability read at all; a brief or harness
  defect, repairable.
- **5/9 or more** — the briefs leak more than intended, or the tasks are easier
  than judged. Re-examine the briefs before believing it.

The stop rule to honour: "universal floor or ceiling means the reset is
reconsidered" has a loophole at 1/9 or 2/9, which is not *universal* but is
still two-point. Treat fewer than ~3 middle tasks producing mixed or near-miss
outcomes as the stop rule firing.
