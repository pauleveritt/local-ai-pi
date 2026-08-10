# Variance measurement — predictions

Written and committed **before** the run.

**Why now.** Every comparison in this phase is n=1 per cell, and last night
showed that is not enough. `local-pings` went accepted -> no-changes between
two runs of the same arm whose only difference was an output cap that bound in
neither. Until the noise floor is known, no arm effect can be claimed — and the
contract arm's +1, the frontier table, and every model comparison are all
resting on single attempts.

**Design.** Gemma 12B, brief-only, `maxTokens` 8192 — the exact cell every
comparison is made against. Four tasks, six replicates each, 24 calls.

| task | measured at 8192 | measured at 32768 | why included |
|---|---|---|---|
| `local-pings` | accepted | no-changes | **flipped**, cap bound in neither |
| `registry-iter` | tests-vanished | damaged (-100%) | **flipped**, both ended `stop` |
| `magicmock-factory` | accepted | accepted | apparently stable |
| `flask-extensions` | accepted | accepted | apparently stable |

Two known-unstable and two apparently-stable, because "these two are noisy and
those two are not" is itself a finding, and measuring only the noisy ones would
guarantee a high variance estimate.

## Predictions

- **`local-pings` and `registry-iter` will not be stable**: I expect each to
  produce at least two distinct outcomes across six runs. That is the
  straightforward reading of last night.
- **`magicmock-factory` and `flask-extensions` will be less variable but not
  clean**: I predict at least one of them shows a non-accepted result in six.
  Two identical results is weak evidence of stability, and I have now been
  wrong five times by treating small samples as settled.
- **Aggregate accept rate across all 24 will land between 40% and 60%**,
  against the 3/8 (38%) measured last night at n=1.
- **At least one replicate will produce an outcome not yet seen for its task** —
  a class that neither the 8192 nor the 32768 run produced.

## What this changes

If per-task outcomes are stable (5/6 or 6/6 identical), single attempts are
usable for screening and last night's flips were unlucky. If they are not, then
**every number this phase has produced is a sample of one from a wide
distribution**, the frontier table needs error bars or withdrawal, and the
contract arm has to be re-run with replicates before any of it means anything.

I expect the second, which makes this the cheapest way to find out how much of
the last two days needs redoing.

## Non-prediction

Wall-clock and token cost. Replicates vary in length by construction and
nothing here is designed to measure that.
