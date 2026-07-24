(part3b-implementer-orchestrator)=

# The Implementer + Orchestrator

Last chapter you installed the subagent mechanism and ran a trivial delegation.
Now you'll build the real thing: an implementer specialist that builds code from
packets, and an orchestrator parent prompt that constructs those packets from the
AgentClinic roadmap.

## Authoring the implementer

The implementer specialist lives at `.pi/agents/implementer.md`. It has YAML
frontmatter that tells the subagent extension how to invoke it, and a system
prompt body that constrains its behavior.

### Frontmatter

```yaml
---
name: implementer
description: Builds exactly what the packet specifies. No exploration, no redesign.
tools: read, write, bash
model: omlx/gemma-4-12B-it-MLX-8bit
---
```

The `tools` field is load-bearing. It restricts the implementer to `read`,
`write`, and `bash` — no `edit` (too clever for an SLM), no `grep` or `find`
(the packet lists allowed files, no exploration needed), and no extensions (the
`--no-extensions` flag on the child prevents recursion into another subagent).

### System prompt

The body teaches the implementer to accept packets and build exactly what's
specified:

- **Follow the packet.** The packet is the complete specification. Do not deviate.
- **Do not explore.** Only read files listed in "Allowed Files."
- **Do not redesign.** Build what's asked, not what you think is better.
- **Acceptance strings must appear verbatim.** If the packet says `"Scope creep
  never ends."`, that exact text must be in the output.
- **Run validation before reporting.** `uv run pytest -q`. If tests fail, fix and re-run.
- **Report honestly.** Don't claim success if tests failed.

Each rule maps to a lesson from [`lessons.md`](../lessons.md). "Do not explore" is LESSONS #1
(structure beats strings — the packet IS the structure). "Acceptance strings" is
LESSONS #2 (treat validation as the source of truth). "Report honestly" is the
same — an agent's self-report is not evidence.

```{note}
The implementer's system prompt is **appended** to Pi's base coding prompt
(`--append-system-prompt`), not a replacement. The model still knows how to
write FastAPI code; the specialist prompt constrains what it chooses to do.
```

## Authoring the orchestrator

The orchestrator lives at `prompts/orchestrator.md` — a plain directory, not
`.pi/agents/`. This is deliberate: any `.md` file in `.pi/agents/` with
frontmatter is discovered as a callable specialist, and an SLM parent could
self-delegate to "orchestrator" with no depth cap. Keeping it in `prompts/` and
loading it via `--append-system-prompt` makes it a prompt, not a delegation
target.

### What the orchestrator teaches

1. **Read the roadmap.** Extract phases verbatim from the roadmap file.
2. **Construct a packet.** Copy the phase checklist into the task field. List
   allowed files for that phase. Extract acceptance strings.
3. **Dispatch.** Call `subagent({ agent: "implementer", task: "<packet>",
   agentScope: "both" })`. The `agentScope: "both"` is required — default
   `"user"` scope never reads `.pi/agents/`.
4. **Verify.** Check test results. If failure, construct a repair packet (at
   most twice).
5. **Proceed.** Only after the phase passes, move to the next.

The packet format:

```
## Task
<phase extracted verbatim from roadmap>

## Allowed Files
- app.py
- templates/base.html
- templates/home.html
- tests/test_app.py

## Acceptance Strings
- "Come in. Sit down. Tell us about your human."

## Validation
uv run pytest -q
```

```{warning}
The orchestrator prompt must teach the parent to extract phases *verbatim*, not
paraphrase. A paraphrased phase is a lossy handoff — the exact checklist items,
acceptance strings, and file names are the structure the implementer relies on.
Chapter 3 will measure this drift directly.
```

## Running the parent session

The parent loads the extension and the orchestrator prompt:

```bash
pi --extension <subagent-path> \
   --append-system-prompt prompts/orchestrator.md \
   --model omlx/gemma-4-12B-it-MLX-8bit \
   --no-extensions
```

Then in the chat:

```
Build Phase 1 of the AgentClinic app. Use the subagent tool to dispatch
to the implementer specialist with agentScope: both.
```

The orchestrator prompt teaches the parent to extract Phase 1 from the roadmap,
construct a packet, and call `subagent`. The implementer receives the packet in a
fresh child process, writes the code, runs the tests, and reports back.

## Measuring: the SP2 baseline

Run the SP1 harness against the parent+implementer setup with n=4:

```bash
uv run python -c "
from harness.runner import run_baseline, write_report
from harness.session import InvocationProfile
from pathlib import Path
from datetime import date

app_source = Path('examples/agentclinic')
roadmap = (app_source / 'specs' / 'roadmap.md').read_text()
subagent_path = Path('.pi/subagent-extension-path.txt').read_text().strip()
profile = InvocationProfile.sp2(subagent_path)

# Run per-phase measurement
for phase_num in (1, 2, 3):
    ...  # extract phase, run n=4, write report
"
```

The measurement compares directly to the SP1 0/8 baseline. Two key differences:

**Success is still harness-determined.** The harness runs `uv run pytest` itself
and diffs the workspace — same as SP1. The implementer's self-reported result is
recorded but never trusted.

**New outcome: `no-delegation`.** If the parent session produces zero `subagent`
tool calls, the outcome is `no-delegation` — indistinguishable from an SP1 rerun
and not averaged into delegation data as if the mechanism had been exercised.

## What the baseline shows

The single-run verification (Task 4) produced one success: tests passed, 5 files
changed, 247s wall time. The implementer was discovered, the packet was
dispatched, and the child built a working Phase 1. n=4 will show whether this
holds consistently.

```{eval-rst}
.. list-table:: SP2 Baseline vs SP1 Baseline
   :header-rows: 1
   :widths: 20 15 15 25 25

   * - Baseline
     - Success Rate
     - Mean Turns
     - Mean Wall Time
     - Notes
   * - SP1 (unsteered, per-phase)
     - 0/8 (0%)
     - 6.4
     - 45s
     - No delegation; raw SLM
   * - SP2 Ch2 (parent+implementer)
     - 3/8 (38%)
     - 7.8
     - 329s
     - 1-4 subagent calls per run; [dated report](research/2026-07-23-sp2-baseline-phase-1.md)
```

```{note}
The SP1 unsteered baseline went 0/8 on Phase 1. 3/8 from the parent+implementer
shape is a clear signal — delegation helps. The successful runs all used exactly
1 delegation with a clean packet (1,315 bytes); the failures either had tests
fail on the first attempt or spiraled into 3-4 repair attempts and timed out.
The dated evidence report lives at
[SP2 pre-tuning baseline](research/2026-07-23-sp2-baseline-phase-1.md).
```

## Results

### Metrics

| Metric | SP2 Ch2 | SP1 (for comparison) |
|--------|---------|----------------------|
| Success rate | 3/8 (38%) | 0/8 (0%) |
| Mean wall time | 329s | 45s |
| Mean parent turns | 7.8 | 6.4 |
| Mean subagent calls | 2.2 | N/A (no delegation) |
| Runs with delegation | 8/8 | 0/8 |
| Mean packet size | 2,837 bytes | N/A |

### What the telemetry revealed

**Delegation happened in every run.** No `no-delegation` outcomes — the parent
always called the subagent tool. The mechanism works.

**Successful runs (3/8) used exactly 1 delegation with a clean packet.** Each
successful run dispatched a single 1,315-byte packet. The implementer wrote
the correct files, tests passed, and the run completed in 145-243s.

**Two failure modes emerged:**

1. **Overreach (4/8 runs).** The implementer created `models.py` and
   `complaints.html` during Phase 1 — files not in the Allowed Files list. The
   specialist prompt said "do not redesign" but the implementer saw the full
   roadmap and built ahead.

2. **Repair spirals (2/8 runs).** Four subagent calls each — one initial
   delegation plus three repair attempts. Both runs hit the 900s timeout. The
   parent's repair policy ("at most twice") wasn't enforced strongly enough,
   and the implementer's overreach meant repairs never converged.

### Recommendations

- **Add a "build only this phase" rule to the implementer** (Chapter 3).
- **Tighten the parent's repair policy** from "at most twice" to "at most once"
  and add a pre-dispatch packet checklist (Chapter 3).
- **Mechanism-level overreach protection** (Part IV): a path guard on
  `tool_call` that rejects writes to files not in the Allowed Files list.
- **Mechanism-level repair cap** (Part IV): a turn cap or repeat breaker that
  stops runaway repair loops regardless of the prompt.
- **Instrument packet fidelity** in the harness: mechanically check whether the
  packet's acceptance strings and allowed-files list match the roadmap verbatim.
  This would distinguish "good packet, implementer failed" from "bad packet,
  implementer never had a chance."
