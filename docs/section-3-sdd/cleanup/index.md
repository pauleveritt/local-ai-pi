(cleanup-sp2)=

# Cleanup: SP2 Deep-Review Findings

A deep review of the SP2 implementation — conducted after the Section III
chapters shipped — found data-corrupting bugs, dishonest claims, and stale docs.
This chapter documents what was found, what was fixed, and what had to be
re-run. It establishes a **pattern for cleanup chapters**: whenever a review
finds issues in a section's work, add a `cleanup/` chapter to that section that
goes through Superpowers (spec → plan → build → evidence).

The full findings and fixes are in the [spec](spec.md) and [plan](plan.md). The
corrected baselines (after re-running) land in `research/`.

```{toctree}
:hidden:

spec
plan
```

## What held up

The part the reviewer was most suspicious of — the SP1 0/8 smoking gun — held
up. The earlier suspect report (0 turns, ~1s runs) was fixed and fully re-run;
the committed SP1 report rests on real sessions (6–9 turns, 38–64s, real
`turn_end` events in the JSONLs). SP1 vs SP2-pre differ only by the intended
delta (subagent extension + orchestrator prompt + timeout), with timeout ruled
out as a confound. Report tables match raw session artifacts. The deep-dive even
corrected one of its own chapter's conclusions from the artifacts. The doctrine
is being applied to itself.

SP2 also honored the earlier review's commitments: `agentScope: "both"` mandated
and taught with its failure mode, the orchestrator kept out of `.pi/agents/`,
the invocation profile matches spec, success decided by harness pytest+diff,
citations pinned to the installed package.

## What was broken

### The `no-delegation` veto (C1)

The harness reclassifies any exited run with zero subagent calls as
`no-delegation`, and `is_success` requires `outcome == "exited"`. So a plain
baseline profile scores 0/8 by definition — even if every run passed pytest.
This structurally rigs future SP3 guardrailed-vs-plain comparisons toward
"delegation wins." No existing data was affected (all 16 SP2 rows delegated),
but the hazard had to be gated before SP3 runs.

### The retry/timeout misrecord (C2) — worse than the review thought

`timed_out` is set on the first startup hang and never cleared. The audit found
that **all four "timeout" rows** show the misrecord signature: each artifact ends
with a graceful `agent_settled` event — a killed process can't write its
terminal event. The agent completed its work; the "timeout" label is wrong.

The unrecoverable part: whether those four runs passed pytest was computed at
run time and never persisted (workspaces were disposable). So 4 of 16 SP2 rows
carry an unreliable ❌. Pre could be 3–5/8; post could be 4–6/8. Since those two
numbers are the entire before-picture for SP3, both n=8 batches had to be
re-run.

### Spec-promised metrics that don't exist (C3)

The SP2 spec committed packet-fidelity, self-report-vs-verdict agreement, and
validation-drift as measurement deliverables. None was implemented. The chapter
stated the self-report "is recorded but never trusted" — it was not recorded at
all. Reframing broken promises as evidence-gated backlog isn't descoping
honestly.

### Statistical claims and hardcoded stamps (I1)

3/8 → 4/8 at n=8 is one run (Fisher p≈1.0). The GREEN/YELLOW stamps in the
reports were hardcoded template text, emitted unconditionally rather than
assessed. The defensible claim is the structural one (0/8 → 3–4/8); the tuning
delta needed a within-noise caveat everywhere it was cited.

## What was fixed

The [plan](plan.md) sequences the fixes into four phases:

1. **Stop the bleeding** — C1 (gate the veto), C2 (fix the misrecord + persist
   verdicts + define `exited-with-hang`), I2 (parameterize sessions path).
2. **Honest claims** — C3 (implement the metrics or descope), I1 (caveats +
   real evidence tiers), minor wording fixes.
3. **Re-run both SP2 batches** under the fixed harness (~16 runs).
4. **Stale docs** — KICKOFF and roadmap conventions.

## The pattern

This chapter is the template for future cleanup work. When a review finds
issues in a section's shipped work:

1. Add a `cleanup/` chapter to that section.
2. Write a spec capturing the findings and fixes.
3. Write a plan sequencing the work.
4. Build the fixes.
5. Re-run any affected measurements; record evidence in `research/`.

The cleanup chapter is a self-contained Superpowers unit — its own spec, plan,
and evidence — because cleanup is a distinct unit of work, not a continuation
of the original chapter's build.
