# Phase 5 cycle 1 — what one live delegation showed

**Date:** 2026-08-04
**Cycle:** phase 5 cycle 1 — the improvement mechanism
**Claims no number.** Two live invocations, n=1 each. Nothing here is a
measurement; the batches are cycle 2.

## Why a spike at all

Three facts about delegation reached this project by *reading* the prior
effort's spec, never by running anything under this harness's flags:

1. a delegation must pass `agentScope: "both"` or `.pi/agents/` is never read;
2. the project-local confirmation prompt only fires when a UI is present, so
   headless runs bypass it silently;
3. `--no-extensions` excludes project-local extensions, so the shipped
   subagent extension must arrive by explicit `--extension`.

Phase 3 cycle 1 retired a reading-justified claim when a run disagreed with
it. The same discipline applies here, and it earned its keep immediately.

## What happened

**Run 1** — `run_suite(AGENTCLINIC_PHASE_1, improvement=sdd_orchestrator(),
timeout=480)`, foreground, extension pointed at the `subagent/` *directory*.

| | |
|---|---|
| Grade | **accepted**, 4/4 tests executed |
| Pi return code | 0, not timed out |
| Captured stdout | 315,567 bytes |
| `subagent` tool calls | 1 |
| Result of that call | `"Tool subagent not found"`, `isError: true` |
| Other tools used by the parent | `bash` 11, `write` 8, `edit` 2 |

The model did everything right. It read the roadmap, built a well-formed
packet — Task, Allowed Files, Acceptance Strings, Validation — and passed
`agentScope: "both"` without being reminded. Pi answered that the tool does
not exist. The parent then wrote the whole solution itself, and the run
graded **accepted**.

**Run 2** — same seed and flags, extension pointed at
`subagent/index.ts`, prompt asking only for a trivial delegation.

| | |
|---|---|
| `subagent` tool calls | 1 |
| `isError` | **false** |

## The finding

**`--extension` needs the entry-point file, not the extension's directory.**
Pointing it at `subagent/` fails completely silently: exit code 0, empty
stderr, no warning, and our own `hello-world.ts` still loads and emits its
`entry_appended` evidence, so every observable signal says the run is
healthy. The only symptom arrives late, inside a tool result, after the
model has already spent turns building a packet for a tool that was never
registered.

Pi's own README for the example documents installation by symlinking
`index.ts` into `~/.pi/agent/extensions/subagent/` and never mentions
passing a directory. Our reading of "reference the shipped tree by path"
turned that into a directory path, and nothing contradicted it until a
model called the tool.

**The dangerous part is not the failure, it is the grade.** An orchestrated
arm whose orchestration never loaded still returns `accepted: True`, 4/4.
Had cycle 2 run first, it would have produced sixteen runs labelled
`improvement_name="sdd-orchestrator"` in which no delegation ever happened,
and the cost comparison would have measured a bare run against a bare run.
The numbers would have looked entirely reasonable. This is the same shape as
the model-server hazard `docs/setup.md` records — `pi` exits 0 with empty
stderr and the harness records a fabricated result that looks like data —
one layer over, and it is the argument for having split the mechanism cycle
from the batch cycle.

## The three read claims, now run

| Claim | Status |
|---|---|
| `agentScope: "both"` is required | **Not contradicted.** The model passed it unprompted in run 1, and run 2 succeeded with it. Whether omitting it fails was not tested. |
| The headless confirmation is bypassed | **Consistent.** Run 2's delegation completed with no UI and no prompt. |
| The extension must arrive by explicit `--extension` | **Refined.** True, but the path must be `index.ts`. |

## The observation that rides to cycle 2

The Backlog gates building our own ~150-line subagent tool on "a measured
run shows the shipped extension contaminating or losing a measurement",
because the shipped extension can put parallel children on a
single-threaded local server. **Neither run put more than one child on the
server** — run 1 made one call that failed, run 2 made one that succeeded.
The gate has not fired. Cycle 2's batch is the first real chance for it to.

## Residual gap, recorded not closed

`extension_digests` now covers `index.ts` only, while the extension is
really a tree: `index.ts` imports `agents.ts` beside it, and neither
`agents/` nor `prompts/` is hashed. The tree digesting built in this cycle
still earns its place — it covers the improvement's seed directory — but it
is not covering the shipped extension.

Left open deliberately rather than closed with a guess about which parent
directory to hash. The shipped tree changes when Pi changes, and
`EXPECTED_PI_VERSION` already refuses a batch on a different Pi. That is a
weaker guarantee than a digest and it is stated as such: it would miss a
contributor editing the installed package in place.

## Commands, for reproduction

```bash
curl -s -m 10 http://127.0.0.1:8001/v1/models
```

```bash
uv run python -c "
from harness.runner import AGENTCLINIC_PHASE_1, sdd_orchestrator, run_suite
result = run_suite(AGENTCLINIC_PHASE_1, improvement=sdd_orchestrator(), timeout=480)
print(result.grade.accepted, result.pi_returncode, len(result.pi_stdout))
"
```

Both runs were foreground. `timeout=480` rather than the default 600 so the
harness terminates its own process group rather than being killed from
outside — a run killed from outside leaves no trace in the harness's
records, which Phase 4 cycle 1 found the hard way.

Raw stdout for both runs was written to the session scratchpad and is **not**
committed; at 315 KB for one run it is diagnostic material, not evidence, and
this cycle claims no number that would need it.
