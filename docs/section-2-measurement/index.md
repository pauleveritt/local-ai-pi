# Section II — Measurement

The evaluation harness: it drives Pi headless via `subprocess`, provisions
disposable git-tracked workspaces, captures diffs, and runs pytest as the
acceptance oracle.

**Status:** evidence finalized 2026-07-27, chapter prose below is written
against it (Task 9). Every earlier number below (the n=4 0/8 baseline, the
pre-repair post-repair reports) was measured under an invalid or self-graded
oracle and is superseded — kept as historical record, bannered where
applicable. The grading path was rebuilt under the grading-path reboot (see
[`docs/superpowers/plans/2026-07-24-grading-path-reboot.md`](../superpowers/plans/2026-07-24-grading-path-reboot.md)),
and the 2026-07-27 unsteered n=16 reports below are the first trustworthy
numbers this project has produced.

**Evidence:** unsteered n=16 per phase, no ditch —
[Phase 1](research/2026-07-27-post-repair-sp1-phase1.md) 15/16 (Wilson 95%: 72–99%),
[Phase 2](research/2026-07-27-post-repair-sp1-phase2.md) 15/16 (Wilson 95%: 72–99%),
[Phase 3](research/2026-07-27-post-repair-sp1-phase3.md) 16/16 (Wilson 95%: 81–100%),
[Phase 3, less-prescriptive spec](research/2026-07-28-post-repair-sp1-phase3-less-prescriptive-spec.md) 16/16 (Wilson 95%: 81–100%).

## What the workload actually is

Before you can write a suite that grades a phase, you have to be able to say
what "a phase" is. That sounds like bookkeeping. It is the first thing this
project got wrong, and getting it wrong invalidated a whole batch.

### A phase-N run starts seeded, not empty

The rule, stated as **D1** in
[the evidence policy](../superpowers/policies/evidence.md): *a phase-N run
starts from the committed reference solution of phases 1..N−1, overlaid before
the pristine commit.* A run from an empty workspace measures phases 1..N
combined and must not be labelled phase N.

That rule exists because of a specific incident. An early batch was recorded as
**"Phase 2: 0/8"**. The workspace it ran in — `examples/agentclinic` — contains
no app code, so every one of those eight runs started from nothing. What was
actually measured was "build Phases 1+2 combined, from an empty directory," and
it was labelled as if it measured Phase 2 alone. The
[oracle-repair plan's Amendment 1](../superpowers/plans/2026-07-24-oracle-repair.md)
records the finding and the decisions that followed it.

The damage is not just a mislabelled row. Two things broke:

- **The escalation inference collapsed.** The reasoning the batch was run to
  support — Phase 1 passed, Phase 2 scored zero, therefore Phase 2 is the
  ditch — does not hold from an empty start. A run that fails may have failed
  on Phase 1 work. You cannot attribute the failure to the phase you named.
- **Preservation breakage became unmeasurable.** The failure this workload was
  built to expose is a model completing Phase 2 while erasing Phase 1 behavior.
  If Phase 1 behavior was never in the workspace to begin with, there is
  nothing to erase, and the failure mode simply cannot occur.

Amendment 1's fix has three mechanical parts worth copying:

1. **Seed from a fixed reference fixture** (`examples/reference/phase-<k>/`),
   identical across every run and every arm — never from a model's own prior
   output, which would make each run's starting point depend on how well the
   previous one did.
2. **Commit the seed into the workspace's pristine git baseline**, so the
   captured `changed_files` set reflects only the model's phase-N work.
3. **Every report header states its starting state** — `seeded: reference
   phase-1 @ <path or hash>`, or `empty`. Amendment 1 puts this bluntly: a
   report without it is not citable.

The superseded reports were not deleted. They carry a banner saying what start
state they actually used and are kept as the historical record — you can read
[the phase-2 pooled report](research/2026-07-24-post-repair-sp1-phase2-pooled.md)
and see the relabelling for yourself.

### One sub-batch never decides anything

The second half of defining the workload is defining when a result is allowed
to make a decision. **D2** in the evidence policy: failure-mode incidence is the
primary metric, batches are n=16 unsteered and n=8 steered, and *every
escalation decision operates on pooled results only*.

The number that forced this is small and unpleasant. Two independent n=4
samples of the *identical* seeded-Phase-2 unsteered configuration returned
**4/4 and 2/4** — pooled, 6/8. Same workload, same model, same prompt, same
start state — this is the D1-seeded measurement, a different quantity from
the empty-start "Phase 2: 0/8" incident above, and the two numbers are not
directly comparable. Under the decision rule in force at the time ("4/4 → escalate"),
the first sample would have declared the phase solved and the second would have
declared it a candidate ditch. The Wilson 95% interval on 6/8 is roughly
**41–93%**, which is another way of saying eight runs cannot tell you much of
anything.

So the thresholds moved to the pooled batch:

| Pooled unsteered result | Decision |
|---|---|
| ≥ 15/16 | phase solved — escalate to the next phase |
| 13–14/16 | ambiguous — report honestly, decide with the human |
| ≤ 12/16 | candidate ditch — stop escalating |

Sub-batches of an identical configuration may be pooled legitimately; the
report has to state that it pooled them. What a sub-batch may never do is
decide on its own.

Two practical notes from running these. Unsteered runs take about 60 seconds
each, so n=16 is roughly fifteen minutes; steered runs take 130–380 seconds,
which is what makes large arms unaffordable. And batches must be *durable*:
three separate batches were lost mid-run on a single day to session teardown
reaping child processes, because the runner wrote its report only after all n
runs completed. Per-run checkpointing landed before the real batches, and it
earned its keep — two live interruptions during the Phase 1 run were recovered
from checkpoint without losing completed runs
([grading-path reboot](../superpowers/plans/2026-07-24-grading-path-reboot.md),
Task 8 addendum).

Applied to the finished evidence chain: under the rebuilt grading path, the
pooled unsteered results were 15/16, 15/16, and 16/16 for Phases 1, 2 and 3
(linked at the top of this page). All three clear the ≥15/16 line, so by D2
the decision is "solved, escalate" — and, there being no fourth phase, "no
ditch on this workload for this model." That is a decision made by a
pre-registered rule, not a success-rate claim: the 15/16, 15/16, and 16/16
counts above feed Amendment 2's pooled escalation rule as decision-rule
inputs, not as reported effects. Per
[Rule 7](../superpowers/policies/evidence.md), no chapter in this course claims
a success-rate delta at all.

## How to write an eval suite

This section moved: [Writing an Eval Suite](writing-an-eval-suite.md) is now
its own chapter — why a passing smoke test isn't a passing phase, the four
properties a real suite needs, and a hands-on walkthrough deriving one from
a loose, business-level spec rather than the detailed roadmap. Start there.


```{toctree}
:hidden:

writing-an-eval-suite
spec
plan
research/2026-07-23-baseline-phase-1
research/2026-07-24-oracle-invalid-incident
research/2026-07-24-post-repair-sp1-phase1
research/2026-07-24-post-repair-sp1-phase2
research/2026-07-24-post-repair-sp1-phase2-pooled
research/2026-07-24-selfgrade-forensics
research/2026-07-24-write-vs-edit-experiment
research/2026-07-27-post-repair-sp1-phase1
research/2026-07-27-post-repair-sp1-phase2
research/2026-07-27-post-repair-sp1-phase3
research/2026-07-28-post-repair-sp1-phase3-less-prescriptive-spec
```
