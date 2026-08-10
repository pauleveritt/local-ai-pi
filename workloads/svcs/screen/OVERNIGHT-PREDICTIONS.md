# Overnight predictions — draft-contract arms and the gemma cap repair

Written and committed **before** the run.

Three sweeps, each a single variable against something already measured.

| stage | arm | changed vs measured cell |
|---|---|---|
| `qwen27b-draft-contract` | draft contract, 32768 | the contract |
| `gemma12b-draft-contract` | draft contract, **8192** | the contract |
| `gemma12b-brief-32k` | brief only, **32768** | the output cap |

Contracts are **drafts**, authored by Qwen from a read-only packet, uncorrected.
The design frames draft-versus-corrected as its own ablation, so the draft arm
is legitimate and correctly ordered before human correction. Manifests are
untouched: drafts are composed into the prompt at runtime and the composed
bytes are hashed into `prompt_sha256`, so today's brief-only cells stay valid
under their frozen `manifest_sha256`.

## The confound this is mostly about

Four of gemma's five brief-only failures ended `stopReason: length` at an 8192
output cap, against 32768 for Qwen and 16384 for DeepSeek. `async-cm-enter` was
recorded as "no changes written" while its final 31,620-character message
contains the correct fix, truncated at "I'll apply the change." Until the cap is
separated out, the 12B column is not a capability measurement.

## Predictions

### `gemma12b-brief-32k` — the repair

- **`async-cm-enter` flips to accepted.** The model had the fix in hand. If it
  does not flip, my reading of that transcript is wrong and the taxonomy
  withdrawal did not go far enough.
- `registry-iter` **unchanged** (still `tests-vanished`). It ended `stop` at 27
  seconds; the cap never bound. It is a destructive-anchoring failure and more
  output tokens do not address it.
- `autowire` — **no confident prediction.** Its final message was 2 characters:
  degenerate generation, not truncation of real work. Recorded, not predicted.
- `stringified-annotations`, `fastapi-get-registry` — likely still fail, but
  their failure *shape* should change from `length` to something else. If they
  also flip, "capability" was the wrong label for them too.
- Aggregate: **4–5 of 8** closed, against 3 measured.

### `gemma12b-draft-contract` at 8192 — the leak control

- `async-cm-enter` and `autowire` **unchanged**. Their deaths are mechanical. A
  contract cannot buy output tokens. **If a contract "fixes" either at 8192,
  something is leaking** — the draft is carrying answers, or the mechanism is
  misunderstood. This is the most important line in this file.
- `registry-iter` **still fails**. The brief already says "Registration,
  lookup, and lifecycle behaviour must not change," and the model deleted
  `__contains__` anyway. A contract restating a conduct rule is exactly what
  phase 5 cycles 8 and 13 found does not move small models. If this flips, that
  finding is challenged, which would be worth the night on its own.
- Aggregate: **3–4 of 8**, i.e. little movement.

### `qwen27b-draft-contract`

- The six accepted tasks **stay accepted**. A contract that breaks working tasks
  is a finding, and a regression check is why they are run rather than skipped.
- `fastapi-get-registry` improves **only if** the draft names the starlette and
  fastapi seams. Its bottleneck is navigation.
- `autowire` stays clock-bound near 0.78 ± 0.15. Contracts do not speed token
  generation.
- Aggregate: **6–7 of 8**.

## Non-predictions, recorded so they are not read as surprises

**Scope and test-writing.** The smoke run wrote no test where brief-only Qwen
wrote them on all eight. One attempt is not a rate.

**`reference_overlap` will rise across contract arms by construction** — the
smoke run went from 0.15 brief-only to 0.556. A contract names the approach, so
candidates converge on upstream's shape. The 90% flag will fire more often and
mean less; it is a prompt to read the candidate, never a verdict.

**Speed.** The smoke run took 98s against 299s brief-only. Interesting, n=1, and
not what any of these arms is designed to measure.

## What would make me distrust the whole night

Any authoring transcript reaching outside its packet. A draft written by a model
that saw an oracle is a contaminated contract, and every arm result built on it
is void. The transcripts are saved for exactly this and must be audited before
any number here is believed.
