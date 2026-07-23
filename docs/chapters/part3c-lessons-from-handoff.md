(part3c-lessons-from-handoff)=

# Lessons from the Handoff

Chapter 2 gave you a parent+implementer shape and 3/8 (38%) on Phase 1. This
chapter examines what went wrong, tunes the prompts, and re-measures. The tuning
improves the result — but also reveals what prompt tuning *can't* fix, setting up
Part IV's mechanism-level guardrails.

## What the first baseline revealed

The five failures fell into three patterns:

### Overreach

Runs 3, 5, 7, and 8 created `models.py` and `complaints.html` — Phase 2-3 files
not in the Allowed Files list. The implementer specialist said "do not redesign"
but didn't explicitly forbid creating out-of-scope files. The implementer saw the
full roadmap in context and "helped" by building ahead.

### False pass claims

All five failures showed the implementer self-reporting "tests passed" while the
harness's `uv run pytest` showed failures. The implementer either ran tests and
reported dishonestly, or ran a different test command that passed vacuously.

### Repair spirals

Runs 7 and 8 had four subagent calls each — one initial delegation plus three
repair attempts. The parent kept dispatching repairs, the implementer kept
overreaching, and both runs hit the 900s timeout.

## Tuning

### Overreach fix

Added rule 4 to `implementer.md`:

```
4. Build ONLY the phase specified. If the packet says Phase 1, do NOT create
   files for Phase 2 or 3. The Allowed Files list is the complete set of files
   you may touch.
```

### False pass fix

Replaced the honest-reporting rule with stronger validation reporting:

```
7. Report the EXACT test output. Include the exact command you ran and the
   full validation output. Do not summarize or fabricate.
```

### Repair spiral fix

Tightened the orchestrator's repair policy from "at most twice" to "at most
once," added an overreach-specific check, and added a Packet Checklist section
for the parent to verify before dispatching.

## Post-tuning results

```{eval-rst}
.. list-table:: Handoff Tuning Results
   :header-rows: 1
   :widths: 20 15 15 15 15

   * - Baseline
     - Success Rate
     - Mean Turns
     - Mean Wall Time
     - Subagent Calls (mean)
   * - SP1 (unsteered)
     - 0/8 (0%)
     - 6.4
     - 45s
     - N/A
   * - SP2 Ch2 (pre-tuning)
     - 3/8 (38%)
     - 7.8
     - 329s
     - 2.2
   * - SP2 Ch3 (post-tuning)
     - 4/8 (50%)
     - 7.6
     - 213s
     - 1.5
```

4/8 (50%), up from 3/8 (38%). Key improvements:

- **Mean wall time dropped** from 329s to 213s — the repair-spiral fix cut the
  worst-case runs in half.
- **Overreach reduced** from 4/8 runs to 1/8.
- **Mean subagent calls dropped** from 2.2 to 1.5 — fewer repair attempts.

### What prompt tuning couldn't fix

Two runs still failed despite correct Phase 1 files being written. The tests
the implementer wrote simply didn't verify the spec — wrong assertions, missing
acceptance strings. This is a mechanism-level problem: prompt tuning tells the
implementer *to* run tests, but can't ensure the tests are *correct*.

The fix belongs in Part IV or an evidence-gated specialist: a verifier that
mechanically checks acceptance strings against the roadmap, or a test oracle
derived from the spec (the planner's oracle-derivation thread in SP2c).

## The pattern

This is the method Part IV inherits:

1. **Measure** the failure (SP1 baseline)
2. **Apply the lightest fix** (SP2: delegation + packet structure)
3. **Tune** based on patterns (this chapter: prompt fixes)
4. **Escalate to mechanism** only when needed (Part IV: guardrails)

The post-tuning 4/8 (50%) is the before-picture for Part IV. Every guardrail in
Part IV will be measured against this baseline, not SP1's 0/8 — the implementer
delegation is the new floor.
