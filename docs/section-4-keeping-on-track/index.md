# Section IV — Keeping the SLM on Track

Part II showed the ditch: an unsteered SLM goes 0/8 on Phase 1. Part III gave
it an implementer specialist and a parent taught to make packets — that took the
baseline to 4/8 (50%). The remaining failures are the target of this Section.

Every chapter in this Section picks one failure mode from the measured evidence,
applies a single built-in Pi guardrail, and measures whether it helped. No
technique is adopted on faith. Each guardrail maps to a numbered lesson from
[LESSONS.md](../lessons.md) and is measured against the Section III 4/8 (50%)
baseline.

```{note}
The four guardrails in this Section (output cap, path guard, repeat breaker,
turn cap) were previously designed and implemented in a reference repo
(`local-ai-gemma`, branch `slm-guardrails`, 75 passing tests). That work is
**read-only reference material** — each chapter rebuilds the guardrail live so
the reader constructs it. The design decisions, adversarial-review findings
(path-traversal bypass, bash false-positive), and live-verification evidence
are raw material, not a transplant.
```

## The method

Every chapter follows the pattern established in Part II and Part III:

1. **Show the failure** with recorded telemetry from the Section III baseline
2. **Apply one Pi mechanism** — a single guardrail hooking Pi's event lifecycle
3. **Measure** whether it improved the baseline
4. **Record evidence** in a dated research report

No guardrail ships without measured evidence that it helps.

## The guardrail catalog

Each guardrail is presented in the order its motivating failure appears in the
evidence, from most frequent to least:

| Guardrail | Lesson | What it prevents | Pi mechanism |
|-----------|--------|-----------------|--------------|
| **Path guard** | #8, #12 | Implementer writes to files not in the Allowed Files list | `tool_call` hook — reject writes outside declared paths |
| **Repeat breaker** | #1, #11 | Runaway repair loops, repeated identical failing calls | `tool_execution_start`/`tool_execution_end` — count failures, abort on threshold |
| **Turn cap** | #11 | Parent or child spirals beyond a reasonable turn budget | `turn_end` hook — abort session after N turns |
| **Output cap** | #8 | Tool output (bash, read) exceeds what the SLM can process | `tool_execution_end` — truncate output to context-scaled limit |
| **Structural orientation** | #5 | Model lacks structural context (symbols, imports, references) | `before_agent_start` — inject system-prompt context |
| **Tool-surface restriction** | #6, #8 | Too many tools available; model chooses wrong one | `setActiveTools` — restrict tool set per session or phase |
| **Model tuning** | #10 | Sampling entropy, context window, token budget mismatched to task | `models.json` selection + server-side sampling |
| **Context budgeting** | #9 | Growing context crushes generation throughput | `compaction` settings — reserveTokens, keepRecentTokens |

```{note}
The order of chapters is **not** fixed in advance. Each guardrail's motivating
failure must appear in the measured evidence before the chapter is written.
If the Section III baseline does not reproduce a particular failure mode
(e.g., the 48KB tool-output blowup), that guardrail is demoted to the backlog
with a note rather than taught as if the failure were live.
```

## The starting baseline

Every guardrail chapter measures against the same before-picture: the Section
III parent+implementer shape running Phase 1 of the AgentClinic app.

| Metric | Value |
|--------|-------|
| Success rate | 4/8 (50%) |
| Mean wall time | 213s |
| Mean turns | 7.6 |
| Mean subagent calls | 1.5 |
| Remaining failure modes | Overreach (1/8), validation command drift (2/4), child hang (1/4) |

The [post-tuning baseline](../section-3-sdd/research/2026-07-23-sp2-baseline-phase-1-post-tuning.md)
and the [deep-dive telemetry analysis](../section-3-sdd/research/2026-07-24-sp2-deep-dive.md)
are the evidence this Section's chapters cite.

## What the telemetry gaps mean for this Section

The [SP2 deep-dive](../section-3-sdd/research/2026-07-24-sp2-deep-dive.md)
identified five harness improvements that make guardrail measurement sharper.
Before building the first guardrail, consider fixing the highest-value ones:

1. **Capture child session JSONL** — without the child's detailed event stream,
   guardrail effect on the implementer is inferred from the parent's summary.
2. **Capture harness pytest output on failure** — shows why a run that "looks
   correct" actually failed.
3. **Packet fidelity metric** — distinguishes "good packet, implementer failed"
   from "bad packet, guardrail never had a chance."

These are not prerequisites — the guardrails can be built and measured without
them — but they make the before/after comparison sharper and the evidence
stronger.
