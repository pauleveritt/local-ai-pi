# SP2 Cleanup Spec

**Date**: 2026-07-24
**Status**: findings from deep review, awaiting execution
**Parent**: [Section III spec](../spec.md)

## Purpose

A deep review of the SP2 implementation found data-corrupting bugs, dishonest
claims, and stale docs. This spec captures the findings and the fixes. The
chapter (`index.md`) narrates what was found; the [plan](plan.md) sequences the
work; the corrected baselines land in `research/`.

This establishes the **cleanup chapter pattern**: whenever a review finds issues
in a section's work, add a `cleanup/` chapter to that section explaining what
was found, going through Superpowers (spec → plan → build → evidence).

## Findings

### Critical — data corruption

**C1: `no-delegation` veto rigs future comparisons.**
`session.py:174` reclassifies any exited run with zero subagent calls as
`no-delegation`, and `is_success` requires `outcome == "exited"`. A plain
baseline profile (no subagent extension) scores 0/8 by definition — even if
every run passed pytest. This structurally rigs SP3's guardrailed-vs-plain
comparison toward "delegation wins."

Audit: zero recorded SP2 rows were affected (all 16 delegated). Forward hazard
for SP3, not corruption of existing data.

**C2: Retry/timeout misrecord — 4 of 16 rows unreliable.**
`timed_out` is set on the first startup hang and never cleared. Attempt 1 hangs,
attempt 2 succeeds → recorded as `timeout`, `is_success=False`.

Audit — worse than the review: all four "timeout" rows show the misrecord
signature. Each artifact ends with a graceful `agent_settled` event — a killed
process can't write its terminal event. Wall times corroborate (1426s, 1609s
against a 900s cap). The `tests_pass` verdict was computed at run time and never
persisted — workspaces were disposable. Pre could be 3–5/8; post could be
4–6/8. **Both SP2 n=8 batches must be re-run.**

**C3: Spec-promised metrics silently descoped.**
The SP2 spec committed packet-fidelity, self-report-vs-verdict agreement, and
validation-drift as measurement deliverables. None is implemented. The chapter
states the self-report "is recorded but never trusted" — it is not recorded at
all. Either implement or descope honestly.

### Important — dishonest claims

**I1: Statistical claims violate evidence policy.**
3/8 → 4/8 at n=8 is one run (Fisher p≈1.0). GREEN/YELLOW stamps in reports are
hardcoded template text, emitted unconditionally. The defensible claim is the
structural one (0/8 → 3–4/8); the tuning delta needs a within-noise caveat.

**I2: Sessions path hardcoded to pre-restructure location.**
`session.py:91` writes to `docs/superpowers/research/sessions/`. Post-restructure
reports live in `docs/section-*/research/` with relative `sessions/` links. New
artifacts will be orphaned on SP3's first run.

### Minor

- **"Satyrn"** leaked product name in Section 3 index's About SDD section.
- **smoking-gun.md** shows outdated `run_baseline` signature, claims automatic
  phase escalation that's a manual snippet.
- **Overreach stated as fact** where the deep-dive flags it as unverified
  inference (inferred from `changed_files`, not directly observed).
- **Wall-time means** silently exclude timeout runs (`runner.py:81`).
- **No tests** pin no-delegation detection or the SP2 profile.

### Confirmed sound

SP2 honored the earlier review's commitments: `agentScope: "both"` mandated and
taught with its failure mode, orchestrator kept out of `.pi/agents/`, the SP2
invocation profile matches spec, success decided by harness pytest+diff,
citations pinned to the installed package. SP1's 0/8 stands — no timeout rows,
all real exits, neither bug touches it. The smoking gun survives.

## Fixes

### C1 fix

Add `expects_delegation: bool` to `InvocationProfile` (true for SP2, false for
SP1). Only apply the `no-delegation` outcome when `profile.expects_delegation`
is true.

### C2 fix

1. Reset `timed_out = False` per retry attempt.
2. Persist `tests_pass` and pytest stdout/stderr per row (telemetry gap #2).
3. Define `exited-with-hang` outcome for "settled but process didn't exit" —
   judged on tests+diff like any exit, hang noted separately.

### C3 decision

Implement packet-fidelity, self-report agreement, and validation-drift detection
— these are exactly what SP3's guardrail analysis wants. (Alternative: descope
honestly in the spec and fix the chapter sentence. The plan defaults to
implement.)

### I1 fix

Add within-noise caveats everywhere 3/8→4/8 is cited. Compute evidence tiers
from data or replace stamps with prose.

### I2 fix

Parameterize sessions directory — resolve from the profile or pass as a
parameter.

### Minor fixes

One line each — see [plan](plan.md).

## Out of scope

- Re-running SP1 (audited as sound).
- Changing the SP2 spec's design (the shipped-subagent reframe is correct).
- Starting SP3 — the re-run produces the corrected before-picture.
