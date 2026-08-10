# Re-authoring sweep — predictions, registered before results

**Date:** 2026-08-10
**Written:** while the sweep was running, before any draft was read.
**Arm:** Qwen3.6-27B-8bit, `--tools read`, probe budgets, the rewritten
locating prompt (`workloads/svcs/authoring-prompt.md`).
**Out:** `workloads/svcs/contracts/locating/`

The previous sweep, under the superseded prompt, produced 3 empty stubs and
5 substantive drafts, 4 of which carry solution statements (autowire 11,
local-pings 12, registry-iter 12, stringified-annotations 6). All 8 are void.

## What is predicted

1. **4–6 of 8 pass the gate on the first sweep.** The prompt now forbids
   implementation code explicitly, which the old one never did, so most
   drafts should stop carrying bodies. But the gate is zero-tolerance and
   errs toward rejection, and `import` lines and example assignments are
   the shapes most likely to survive an instruction not to write the fix.
   Fewer than 4 means the prompt is not carrying the rule and the next
   move is the prompt, not the gate.

2. **Stubs recur, but fewer than 3.** The stub failure was a run ending
   before it produced anything, which the length and stop-reason checks
   now catch at authoring time rather than at grading time. Nothing in
   this sweep makes the underlying truncation less likely — the budgets
   are unchanged — so 1–2 is the expectation, not 0.

3. **`registry-iter` is the most likely gate failure.** Its entire fix is
   one statement, so any illustrative line at all trips a zero threshold.
   This is the task where the gate is most likely to reject a draft that
   a human would call locating.

4. **No draft reaches the oracle.** Zero authoring transcripts show a read
   outside the packet. The author has `read` and no shell, and the packet
   was leak-checked at staging.

## What would falsify the decision rather than the sweep

If the passing drafts turn out to be *vague* — naming the file but not the
extension point, or restating the brief — then "locating and bounding" is
not what this prompt produces, and the arm would measure an empty
intervention. That is a read of the drafts, not a count, and it is the
check that matters more than the pass rate.

## Verification posture

The pass/fail counts are mechanical. Any claim about draft *quality*
requires reading them, and is marked as such when made.
