# SP2/SP3 Cleanup Plan — from deep review (2026-07-24)

**Source:** Deep review from another agent, plus follow-up audit of whether
re-runs are needed.

## Sequencing

1. **Phase 1 — Stop the bleeding (data corruption)**: C1, C2-fix, I2
2. **Phase 2 — Honest claims (wording)**: C3-descope-or-implement, I1, Minor
3. **Phase 3 — Re-run both SP2 batches** under fixed harness (~16 runs, afternoon)
4. **Phase 4 — Stale docs**: KICKOFF, roadmap conventions

---

## Phase 1 — Data corruption (fix before any SP3 run)

### C1: `no-delegation` veto rigs SP3's comparison arm

**Where:** `harness/session.py:174` (`outcome = "no-delegation"`),
`harness/session.py:61` (`is_success` requires `outcome == "exited"`)

**Problem:** Any exited run with zero subagent calls is reclassified as
`no-delegation`, and `is_success` requires `outcome == "exited"`. So a plain
baseline profile (no subagent extension) scores 0/8 by definition — even if
every run passed pytest. This structurally rigs SP3's guardrailed-vs-plain
comparison toward "delegation wins."

**Audit result:** Zero recorded SP2 rows were affected (all 16 delegated at
least once). C1 is a forward hazard for SP3, not a corruption of existing data.

**Fix:** Gate the reclassification on whether the profile *expects* delegation.
Add `expects_delegation: bool` to `InvocationProfile` (true for SP2, false for
SP1). Only apply the `no-delegation` outcome when `profile.expects_delegation`
is true. When false, exited runs with zero subagent calls are normal successes
(or failures) — not vetoed.

**Test:** Add a unit test that constructs an SP1-profile `SessionResult` with
`outcome="exited"`, `tests_pass=True`, `changed_files=["app.py"]`, zero
subagent calls, and asserts `is_success is True`. (Currently fails by design.)

### C2: Retry/timeout misrecord — re-run required

**Where:** `harness/session.py` — `timed_out` is set on the first startup hang
and never cleared.

**Problem:** Attempt 1 hangs, attempt 2 succeeds cleanly → recorded as
`timeout`, `is_success=False`, wall time spanning both attempts.

**Audit result — worse than the review thought:** All four "timeout" rows (2
pre-tuning, 2 post-tuning) show the misrecord signature. Each artifact ends
with a graceful `agent_settled` event — a process killed mid-run can't write
its terminal event. So in all four, the agent completed its work and the
"timeout" label is wrong. Wall times corroborate (1426s, 1609s against a 900s
cap only add up as hung attempt + completed attempt).

**Unrecoverable:** Whether those four runs passed pytest was computed at run
time and never persisted — workspaces were disposable. So 4 of 16 SP2 rows
carry an unreliable ❌. Pre could be 3–5/8; post could be 4–6/8. **Both SP2
n=8 batches must be re-run under the fixed harness.**

**Fix (code):**
1. Reset `timed_out = False` at the top of each retry attempt (or track
   per-attempt outcome separately).
2. Persist `tests_pass` and the pytest stdout/stderr per row (this is telemetry
   gap #2 anyway — the reason we can't recompute is the verdict wasn't
   persisted).
3. Define semantics for "settled but hung" — these four runs may be pi/oMLX
   failing to exit after the agent finished. Record as a distinct outcome
   (e.g. `exited-with-hang`) judged on tests+diff like any exit, with the hang
   noted separately. Must apply identically to pre and post.

**Test:** Add a retry-semantics test — mock `communicate` to raise
`TimeoutExpired` on attempt 1, succeed on attempt 2 — assert outcome is
`exited` (not `timeout`) and `is_success` reflects attempt 2's result.

### I2: Sessions path hardcoded to pre-restructure location

**Where:** `harness/session.py:91` — `_REPO_ROOT / "docs" / "superpowers" /
"research" / "sessions"`.

**Problem:** Post-restructure, reports live in `docs/section-*/research/` with
relative `sessions/…` links. New session artifacts will land in an orphaned
directory on SP3's first run.

**Fix:** Make the sessions directory a parameter of `run_session` / `run_baseline`,
or resolve it from the profile (SP1 → section-2, SP2 → section-3, SP3 →
section-4). The report's `sessions/` relative links must resolve.

---

## Phase 2 — Honest claims (wording, before 4/8 is cited again)

### C3: Spec-promised metrics silently became backlog

**Where:** SP2 spec committed packet-fidelity, self-report-vs-verdict agreement,
and validation-drift as measurement deliverables. None is implemented.
`docs/section-3-sdd/implementer-orchestrator.md` states the self-report "is
recorded but never trusted" — it is not recorded at all.

**Fix — choose one:**
- **Implement** (preferred for SP3): packet-fidelity (mechanical literal
  match), self-report agreement (parse child's result for pass/fail claim),
  validation-drift detection (compare child's command to packet's). These are
  exactly what SP3's guardrail analysis wants.
- **Descope honestly:** add an explicit "deferred" note to the spec, and fix
  the chapter sentence to say "would be recorded but isn't yet" rather than
  implying it exists.

Reframing broken promises as evidence-gated backlog isn't descoping honestly.

### I1: Statistical claims violate evidence policy

**Where:** "38% → 50% improvement is real and verified." Roadmap's "4/8 is the
before-picture." GREEN/YELLOW stamps in reports.

**Problem:** 3/8 → 4/8 at n=8 is one run — statistically nothing (Fisher
p≈1.0). The GREEN/YELLOW stamps in `harness/runner.py:175` are hardcoded
template text, emitted unconditionally rather than assessed.

**Fix:**
1. Cite the structural claim (0/8 → 3–4/8) as the defensible result.
2. Add a within-noise caveat everywhere the tuning delta is cited: chapter,
   roadmap, section index.
3. Either compute the evidence tier from the data (GREEN for
   artifact-backed counts, YELLOW for noisy means with sample size) or remove
   the stamps and replace with prose noting the tier.

### Minor (one line each)

- **"Satyrn" leaked product name** — `docs/section-3-sdd/index.md` "About SDD"
  section. Replace with generic phrasing.
- **smoking-gun.md outdated** — shows old `run_baseline` signature, claims
  automatic phase escalation that's a manual snippet. Update to current
  signature; mark the escalation as a snippet.
- **Overreach stated as fact** — chapters state file-creation as fact where the
  deep-dive flags it as unverified inference (inferred from `changed_files`,
  not directly observed). Soften to "inferred from."
- **Wall-time means exclude timeouts silently** —
  `harness/runner.py:81` filters `outcome == "exited"`. Either include timeouts
  or note the filter in the report.
- **No tests for no-delegation / SP2 profile** — add tests pinning both.

---

## Phase 3 — Re-run both SP2 batches

After Phase 1 + Phase 2 code fixes land, re-run:

- Pre-tuning: n=8, SP2 profile, Phase 1
- Post-tuning: n=8, SP2 profile, Phase 1 (same prompts as the first post run)

~16 runs at 3–10 min each. Update the two research reports and the chapter
tables with the corrected numbers. The SP1 0/8 stands — no timeout rows, all
real 38–64s exits, neither bug touches it. The smoking gun survives.

---

## Phase 4 — Stale docs

### KICKOFF.md

- Says "Parts III, IV are unbuilt" — Section III is done.
- Describes `docs/chapters/` which no longer exists (restructured to
  `docs/section-*/`).
- Update "What is done" / "What is NOT done" / "How to start" to current state.

### roadmap.md conventions

- Promises `archive/{specs,plans}/` moves that never happened.
- Describes the pre-restructure `specs/` `plans/` layout.
- Update the conventions section to match reality (specs/plans now co-located
  in section directories; no archive moves yet).

---

## What the plan does NOT do

- Does not re-run SP1 (audited as sound — 0/8 stands).
- Does not change the SP2 spec's design (the reframing around the shipped
  subagent extension is correct).
- Does not start SP3 — the re-run in Phase 3 produces the corrected before-picture
  that SP3's guardrails will be measured against.

---

## Dispatch shape

Phases 1 and 2 are independent enough to dispatch in parallel (different files,
no shared state). Phase 3 depends on 1+2. Phase 4 is independent of all.
