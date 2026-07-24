# Section IV — Keeping the SLM on Track

Part II showed the ditch: an unsteered SLM goes 0/8 on Phase 1. Part III gave
it an implementer specialist and a parent taught to make packets — that took
the baseline to 5/8 (62%). The remaining failures are the target of this
Section.

Every chapter in this Section picks one failure mode from the measured evidence,
applies one or more built-in Pi mechanisms, and measures whether they helped. No
technique is adopted on faith. Each chapter maps to a numbered lesson from
[LESSONS.md](../lessons.md) and is measured against the Section III 5/8 (62%)
baseline.

```{note}
Several mechanisms in this Section (output cap, path guard, repeat breaker,
turn cap) were previously designed and implemented in a reference repo
(`local-ai-gemma`, branch `slm-guardrails`, 75 passing tests). That work is
**read-only reference material** — each chapter rebuilds the mechanism live so
the reader constructs it. The design decisions, adversarial-review findings
(path-traversal bypass, bash false-positive), and live-verification evidence
are raw material, not a transplant.
```

## The method

Every chapter follows the pattern established in Part II and Part III:

1. **Show the failure** with recorded telemetry from the Section III baseline
2. **Apply one Pi mechanism** — a single hook into Pi's event lifecycle or
   configuration
3. **Measure** whether it improved the baseline
4. **Record evidence** in a dated research report

No mechanism ships without measured evidence that it helps.

```{note}
Chapter 1 is the exception to the "one mechanism" pattern: it teaches
escalation — a cheap prompt/packet fix first, then a mechanism-level fix if
residual drift remains. This is the course's thesis ("structure beats strings")
landing with the escalation visible rather than asserted.
```

## The chapter catalog

Chapters are ordered by the frequency of their motivating failure in the SP2
post-tuning baseline. Each is a single, focused lesson — one failure, one
mechanism, one before/after measurement.

### Evidence-backed chapters

These chapters address failure modes that actually appear in the SP2 deep-dive:

| # | Chapter | Failure (post-tuning) | Lesson | Pi mechanism |
|---|---------|----------------------|--------|--------------|
| 1 | Terminal validation | Validation command drift (2/8) | #16 | Escalating: first `./validate.sh` wrapper (prompt/packet fix), then a `validate` tool with empty parameter schema + drop bash from child `--tools` (mechanism-level fix). The wrapper is the cheap first line; the tool makes drift structurally impossible. |
| 2 | Path guard | Overreach (1/8) | #8, #12 | `tool_call` hook — reject writes outside the Allowed Files list |
| 3 | Turn cap | Child hang (1/8) | #11 | `turn_end` hook — abort session after N turns |
| 4 | Repeat breaker | Repair spirals (2/8 pre-tuning, reduced by tuning) | #1, #11 | `tool_execution_start`/`tool_execution_end` — count repeats, abort on threshold |

### Backlog

These chapters are queued only if their motivating failure appears in a future
measured run. A failure that never reproduces on this model is demoted to a
note rather than taught as if it were live.

| # | Chapter | Lesson | Pi mechanism |
|---|---------|--------|--------------|
| 5 | Output cap | #8 | `tool_execution_end` — truncate tool output to a context-scaled limit |
| 6 | Structural orientation (LSP) | #5 | `before_agent_start` — inject symbols via `@spences10/pi-lsp` |
| 7 | Per-phase tool sets | #6, #8 | `setActiveTools` — restrict the tool set per phase (Chapter 1 already restricts the child to `validate` + `read` + `write`; this chapter generalizes to phase-specific tool surfaces) |
| 8 | Context budgeting | #9 | `compaction` settings — reserveTokens, keepRecentTokens |

```{note}
**Model tuning** (Lesson #10) is not a Section IV chapter — SP2's post-tuning
run already covered sampling entropy, context window, and token budget
selection. The 3/8 → 4/8 delta from tuning is within noise, but the structural
direction (tuning helps) is the SP2 evidence Section IV builds on.
```

## The starting baseline

Every chapter measures against the same before-picture: the Section III
parent+implementer shape running Phase 1 of the AgentClinic app.

| Metric | Value |
|--------|-------|
| Success rate | 5/8 (62%) |
| Mean wall time | 261s |
| Mean turns | 6.6 |
| Mean subagent calls | 1.2 |
| Remaining failure modes | Child hang (1/8 exited-with-hang), test failures on well-scoped builds (2/8) |

The [post-tuning baseline](../section-3-sdd/research/2026-07-24-sp2-baseline-phase-1-post-tuning.md)
and the [deep-dive telemetry analysis](../section-3-sdd/research/2026-07-24-sp2-deep-dive.md)
are the evidence this Section's chapters cite.

```{note}
The before-picture (5/8 at 62%) was collected at n=8 by SP2. Going forward,
guardrail chapters default to n=4 — sufficient to surface the primary failure
modes while keeping measurement cycles practical. The shared re-run batch (the
one measurement every Section IV chapter compares against) overrides this
default and runs at n=8. The SP2 historical record stays at n=8.
```

## What the telemetry gaps mean for this Section

The [SP2 deep-dive](../section-3-sdd/research/2026-07-24-sp2-deep-dive.md)
identified five harness improvements that make guardrail measurement sharper.
Before building the first mechanism, consider fixing the highest-value ones:

1. **Capture child session JSONL** — without the child's detailed event stream,
   the mechanism's effect on the implementer is inferred from the parent's
   summary.
2. **Capture harness pytest output on failure** — shows why a run that "looks
   correct" actually failed.
3. **Packet fidelity metric** — distinguishes "good packet, implementer failed"
   from "bad packet, mechanism never had a chance."
4. **Validation command drift detection** — catches the specific bug found in
   the deep-dive (implementer narrows the pytest command).
5. **Self-report vs harness verdict agreement** — quantifies the
   dishonesty-vs-command-drift distinction.

These are not prerequisites — the mechanisms can be built and measured without
them — but they make the before/after comparison sharper and the evidence
stronger.

```{note}
**Exception:** Gap #4 (validation command drift detection) is a hard
prerequisite for the shared re-run batch. Child session JSONL is not captured,
so drift cannot be reliably recomputed after the fact — if the batch runs
before drift detection lands, Chapter 1's primary metric is lost.
```

```{toctree}
:hidden:
terminal-validation/spec
terminal-validation/plan

```
