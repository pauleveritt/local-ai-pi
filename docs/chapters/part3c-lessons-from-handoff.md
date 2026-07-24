(part3c-lessons-from-handoff)=

# Lessons from the Handoff

Chapter 2 gave you a parent+implementer shape and 3/8 (38%) on Phase 1. This
chapter examines what went wrong, tunes the prompts, and re-measures. The tuning
improves the result — but the deep-dive into the remaining failures reveals
what prompt tuning *can't* fix, setting up Part IV's mechanism-level guardrails
and five concrete telemetry improvements recorded for future work.

## What the first baseline revealed

The five failures fell into three patterns:

### Overreach

Runs 3, 5, 7, and 8 created `models.py` and `complaints.html` — Phase 2-3
files not in the Allowed Files list. The implementer specialist said "do not
redesign" but didn't explicitly forbid creating out-of-scope files. The
implementer saw the full roadmap in context and "helped" by building ahead.

### False pass claims — and what the deep-dive found

All five failures showed the implementer self-reporting "tests passed" while
the harness's `uv run pytest` showed failures. The initial read was "the
implementer is reporting dishonestly." The deep-dive
([research/2026-07-24-sp2-deep-dive.md](../superpowers/research/2026-07-24-sp2-deep-dive.md))
corrected this: **the implementer isn't dishonest — it ran a different command
than the packet specified.**

The packet says the validation command is `uv run pytest -q` (all tests). The
implementer ran `uv run pytest -q tests/test_app.py` (a specific file). The
narrower command passes; the broader command fails. This is **validation
command drift** — a packet/specification bug, not a dishonesty bug. The
implementer's tests pass in isolation but fail when collected with other tests
(import errors, conftest conflicts, fixture clashes).

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

This addresses the symptom (vague reporting) but the deep-dive showed the root
cause is command drift, not dishonesty. A prompt fix can insist on the exact
command; a mechanism fix (recorded below) would detect the drift directly.

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

### What the telemetry revealed

**Overreach dropped from 4/8 to 1/8.** The "build only this phase" rule worked
for most runs. The one remaining overreach run (run 5) still created `models.py`
and built all three phases — the rule needs mechanism-level enforcement.

**Repair spirals cut in half.** Mean subagent calls dropped from 2.2 to 1.5.
Mean wall time dropped from 329s to 213s. The parent's repair policy ("at most
once") and the pre-dispatch packet checklist reduced runaway repairs.

**Validation command drift persists.** Two runs (7, 8) wrote correct Phase 1
files and the implementer reported "1 passed" — but the harness's pytest failed.
The deep-dive confirmed: the implementer ran `uv run pytest -q tests/test_app.py`
while the harness ran `uv run pytest -q`. The narrower command passed; the
broader one didn't. Prompt tuning can insist on the exact command, but the
harness can't currently *detect* the drift — it only sees the child's summary
result, not the command it actually ran.

**One run hung on a routing edge case** (run 3). The implementer got stuck on a
`TemplateResponse` routing issue and the subprocess hung at 947s. Model-level
problem, not prompt-tunable.

## What prompt tuning couldn't fix — and what's recorded for future work

The deep-dive identified five telemetry gaps that limit failure analysis. Each
is recorded in the [roadmap backlog](../superpowers/roadmap.md) and the
[deep-dive note](../superpowers/research/2026-07-24-sp2-deep-dive.md):

1. **Child session JSONL is not captured.** The parent's JSONL shows the
   `subagent` tool call and its summary result, but the child's detailed event
   stream — every tool call, every message, the full pytest output at each step
   — is discarded by the shipped extension. We can only see what the implementer
   *reported* it did, not what it actually did. **Fix:** run the child with
   `--session <path>` so pi writes its own JSONL, parsed alongside the parent's.
   This is the single highest-value improvement.

2. **Harness pytest output is discarded on failure.** When the harness's pytest
   fails, we see only the return code — not the stdout/stderr that would show
   the exact failure. **Fix:** capture `test_proc.stdout`/`stderr` in
   `SessionResult` when `tests_pass is False`.

3. **Packet fidelity is not measured.** The spec calls for mechanically checking
   whether the packet's acceptance strings and allowed-files list match the
   roadmap verbatim. This would distinguish "good packet, implementer failed"
   from "bad packet, implementer never had a chance." **Fix:** implement
   `packet_fidelity(packet, roadmap_phase)` that checks each literal.

4. **Validation command drift is not detected.** The implementer runs a narrower
   pytest than the packet specifies. This is visible in the child's result text
   but not mechanically checked. **Fix:** parse the child's result for the exact
   command it ran, compare to the packet's validation command.

5. **Self-report vs harness verdict agreement is not measured.** The
   implementer's claimed pass/fail should be compared to the harness's verdict.
   **Fix:** parse the child's result for "passed"/"failed" and compare to
   `SessionResult.tests_pass`.

### Mechanism-level recommendations (Part IV and SP2c)

Beyond telemetry, the failures point to mechanism-level fixes:

- **Path guard** (Part IV): reject writes to files not in the Allowed Files
  list. Would have prevented the one remaining overreach run.
- **Turn cap or repeat breaker** (Part IV): a hard limit on subagent calls per
  parent turn, regardless of the prompt's repair policy.
- **Verifier specialist** (SP2c, evidence-gated): a separate specialist that
  runs the acceptance tests and mechanically checks for acceptance strings,
  removing trust from the implementer's self-report.

## The pattern

This is the method Part IV inherits:

1. **Measure** the failure (SP1 baseline)
2. **Apply the lightest fix** (SP2: delegation + packet structure)
3. **Tune** based on patterns (this chapter: prompt fixes)
4. **Deep-dive** to verify the conclusions and find what telemetry misses
5. **Escalate to mechanism** only when needed (Part IV: guardrails)

The post-tuning 4/8 (50%) is the before-picture for Part IV. Every guardrail in
Part IV will be measured against this baseline, not SP1's 0/8 — the implementer
delegation is the new floor. And the five telemetry gaps recorded here are the
harness improvements that make the next deep-dive sharper.
