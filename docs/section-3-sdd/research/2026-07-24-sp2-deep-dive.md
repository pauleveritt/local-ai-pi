# SP2 Deep-Dive: Metrics Verification and Telemetry Gaps

**Date**: 2026-07-24
**Status**: analysis note, not a baseline report
**Parent**: SP2 (Part III)

## Purpose

Verify the metrics and conclusions in the Part III chapters against the raw
session JSONLs, and record telemetry gaps that should inform the next roadmap
entry.

## Metrics verification

Re-derived from the session JSONLs (not the report tables):

### Pre-tuning (Chapter 2)

| Run | Success | Turns | Subagent calls |
|-----|---------|-------|----------------|
| 59a7953f | ✅ | 5 | 1 |
| 2f2cd629 | ❌ | 5 | 1 |
| fbb1228e | ❌ | 14 | 3 |
| c5c3aaef | ✅ | 5 | 1 |
| 27b6a8cb | ❌ | 7 | 3 |
| 03fbeae3 | ✅ | 5 | 1 |
| 2d6a552c | ❌ | 9 | 4 |
| b31afcf6 | ❌ | 12 | 4 |
| **Agg** | **3/8 (38%)** | μ=7.8 | μ=2.2 |

**Verified.** Matches the chapter table.

### Post-tuning (Chapter 3)

| Run | Success | Turns | Subagent calls |
|-----|---------|-------|----------------|
| 03b60d2e | ✅ | 8 | 2 |
| 1929617f | ✅ | 7 | 2 |
| 0c4cb9e5 | ❌ | 12 | 1 |
| 44a9f34c | ✅ | 9 | 1 |
| c2d816c5 | ❌ | 6 | 3 |
| 65a74c4b | ✅ | 9 | 1 |
| b017a8b1 | ❌ | 5 | 1 |
| 8527dc8c | ❌ | 5 | 1 |
| **Agg** | **4/8 (50%)** | μ=7.6 | μ=1.5 |

**Verified.** Matches the chapter table.

## Conclusion verification

### "Overreach dropped from 4/8 to 1/8"

**Partially verified, with a caveat.** I classified overreach by the presence of
`models.py` in `changed_files` (a Phase 2 file). Pre-tuning: runs 3, 5, 7, 8
had `models.py` (4/8). Post-tuning: only run 5 had `models.py` (1/8). The
count is correct.

**Caveat:** I inferred overreach from `changed_files`, not from inspecting the
implementer's actual writes. The child's detailed tool calls (what files it
wrote, in what order) are NOT in the parent's JSONL — only the child's final
summary text. This means I cannot distinguish "implementer wrote models.py" from
"some other process created models.py." The inference is strong but not
mechanically verified.

### "False pass claims (all 5 pre-tuning failures)"

**Verified, with an important refinement.** The implementer's result text
includes the pytest output. For runs 7 and 8 (post-tuning), the implementer
ran `uv run pytest -q tests/test_app.py` and got "1 passed." The harness runs
`uv run pytest -q` (all tests, no path). 

**The discrepancy is real but the cause is subtler than "dishonest reporting."**
The implementer's validation command differs from the harness's:

- Implementer: `uv run pytest -q tests/test_app.py` (specific file)
- Harness: `uv run pytest -q` (all tests)

When the implementer's test file passes in isolation but fails when collected
with other tests (import errors, conftest conflicts, fixture clashes), the two
commands give different results. The implementer isn't lying — it ran a narrower
command that passed. The harness runs the broader command that fails.

**This is a packet/validation-specification bug, not a dishonesty bug.** The
packet says `uv run pytest -q` as the validation command, but the implementer
narrows it to `tests/test_app.py`. The fix is either (a) make the implementer
run the exact command in the packet, or (b) make the harness run the same
narrow command the implementer ran. Option (a) is correct — the packet's
validation command should be authoritative.

### "Repair spirals (runs 7, 8 pre-tuning)"

**Verified.** Both had 4 subagent calls (1 initial + 3 repairs) and hit the
900s timeout. Post-tuning, no run exceeded 3 subagent calls, and only 2 runs
timed out (1 with 3 calls, 1 with 1 call that hung).

### "Child hang (run 3 post-tuning)"

**Verified.** Run 0c4cb9e5 had 1 subagent call, 12 turns, 947s wall time
(timeout). The child's result text mentions a Jinja2 `TemplateResponse`
routing issue — the model got stuck debugging an edge case and the subprocess
hung. Model-level problem, not prompt-tunable.

## Telemetry gaps

### Gap 1: Child session JSONL is not captured

**The biggest gap.** The parent's JSONL shows the `subagent` tool call and its
final result (a summary text), but the child's detailed event stream — every
tool call, every message, the full pytest output at each step — is NOT
captured anywhere. The shipped extension streams the child's JSONL internally
and aggregates it into a summary, then discards the stream.

**Impact:** We cannot answer "what did the implementer actually do?" We can
only see what it *reported* it did. For failure analysis, this is the
difference between "the implementer wrote the wrong test" and "the implementer
wrote the right test but ran it wrong" — and we can't tell which.

**Fix:** The harness should capture the child's session. Two options:
1. Run the child with `--session <path>` so pi writes its own JSONL, then
   parse that alongside the parent's.
2. Fork the shipped extension to tee the child's JSONL to a file. (Violates
   "built-in Pi only" — option 1 is preferred.)

### Gap 2: Validation command drift is not detected

**The implementer runs a different pytest command than the packet specifies.**
The packet says `uv run pytest -q`; the implementer runs
`uv run pytest -q tests/test_app.py`. This drift is visible in the child's
result text but is not mechanically checked.

**Fix:** Parse the child's result for the exact command it ran, compare to the
packet's validation command. Flag disagreement as a metric.

### Gap 3: Packet fidelity is not measured

**Deferred from the spec.** The spec calls for mechanically checking whether the
packet's acceptance strings and allowed-files list match the roadmap verbatim.
This would distinguish "good packet, implementer failed" from "bad packet,
implementer never had a chance."

**Fix:** Implement `packet_fidelity(packet_text, roadmap_phase) -> FidelityReport`
that checks each acceptance string appears in the packet verbatim, and each
allowed file matches the phase.

### Gap 4: Self-report vs harness verdict agreement is not measured

**The spec calls for this.** The implementer's self-reported pass/fail should be
compared to the harness's verdict, and disagreement recorded as a metric. This
requires parsing the child's result text for a pass/fail claim.

**Fix:** Parse the child's result for "passed"/"failed" and compare to
`SessionResult.tests_pass`. Record agreement/disagreement in the report.

### Gap 5: Harness pytest output is not captured for failed runs

**When the harness's pytest fails, we don't see why.** The harness runs
`uv run pytest -q` and only records `returncode`. The stdout/stderr (which
would show the exact test failure) is discarded.

**Fix:** Capture `test_proc.stdout` and `test_proc.stderr` in `SessionResult`
when `tests_pass is False`. Include in the report.

## What would help the telemetry more (for the next roadmap entry)

1. **Capture child session JSONL** (Gap 1) — the single highest-value
   improvement. Without the child's detailed event stream, failure analysis
   is guessing from summaries.
2. **Capture harness pytest output on failure** (Gap 5) — cheap to implement,
   immediately useful for diagnosing the false-pass pattern.
3. **Packet fidelity metric** (Gap 3) — distinguishes packet-quality failures
   from implementer failures. Directly measures the spec's "handoff drift"
   commitment.
4. **Validation command drift detection** (Gap 2) — catches the specific bug
   found in this deep-dive (implementer narrows the pytest command).
5. **Self-report agreement metric** (Gap 4) — quantifies the dishonesty-vs-
   command-drift distinction.

## Revised conclusions

The chapter conclusions are correct but under-specified:

- "False pass claims" is really "validation command drift" — the implementer
  runs a narrower pytest than the packet specifies. The fix is prompt-level
  (insist on the exact command) or mechanism-level (the harness reports the
  child's actual command).
- "Overreach" is inferred from `changed_files`, not directly observed. The
  child-session capture (Gap 1) would make this a direct measurement.
- The 38% → 50% delta from prompt tuning is one run at n=8 (Fisher p≈1.0) —
  not statistically significant. The defensible claim is the structural one:
  0/8 (SP1, unsteered) → 3–4/8 (SP2, parent+implementer). The tuning delta
  is a direction signal, not a confirmed improvement.
  remaining 50% failure rate breaks down into: command drift (fixable in
  prompt or harness), child hangs (model-level), and residual overreach
  (mechanism-level, Part IV).
