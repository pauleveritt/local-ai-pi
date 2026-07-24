# Chapter Structure Policy

Every chapter in `docs/course/` ends with a **Results** section that makes the
chapter's measured claims auditable. This is the course's evidence-gated
constraint applied to the product the reader consumes, not just the development
record in `docs/superpowers/`.

## Required section: "Results"

Every chapter that runs a measurement or demonstrates a mechanism ends with a
`## Results` section containing these three subsections, scaled to the
chapter's content:

### Metrics

A table of the chapter's measured outcomes. Include every metric the harness
collects for that chapter's run type:

| Metric | Description | Source |
|--------|-------------|--------|
| Success rate | X/N (Y%) | `BaselineReport.success_rate` |
| Mean wall time | seconds | `BaselineReport.mean_wall_time_s` |
| Mean turns | count | `BaselineReport.mean_turns` |
| Subagent calls (mean) | count per run | `SubagentStats.invocations` |
| Packet size (mean) | bytes | `SubagentStats.packet_size_total` |
| Context in/out | tokens (when available) | deferred to RPC stats |
| Tool calls (mean) | count | `RunTelemetry.tool_calls` |

If a metric is deferred or unavailable, show the row with a note ("deferred",
"N/A") rather than omitting it — the reader should see what's measured and
what isn't.

### What the telemetry revealed

Plain-language findings from the session JSONLs. Name specific failure patterns
with run references (e.g., "Runs 3, 5, 7, 8 showed overreach"). Cite the
artifact in `docs/superpowers/research/` that backs each claim.

### Recommendations

Concrete next steps, categorized:

- **Prompt/packet tuning** (same Part): fixes that stay within prompt and packet
  format changes.
- **Mechanism-level** (later Part): fixes that need extension code — path guards,
  turn caps, output caps, repeat breakers. Each becomes the motivating evidence
  for the corresponding later chapter.
- **Harness improvements**: instrumentation gaps (packet fidelity, self-report
  agreement, captured pytest output for failed runs).

## When the section applies

- **Chapters with a live measurement** (baseline runs): full Results section
  with the dated report linked.
- **Chapters demonstrating a mechanism** (no measurement): abbreviated Results
  with key metrics (load time, spawn time) and recommendations.
- **Introductory chapters** (no code, no measurement): no Results section needed.

## Dating and linking

Every metric table cites the dated research report:

```markdown
The dated evidence report lives at `docs/superpowers/research/YYYY-MM-DD-*.md`.
```

The report is the artifact; the chapter table is the presentation. Claims in
the chapter that aren't in a dated report are estimates and must be marked as
such per the [evidence policy](evidence.md).
