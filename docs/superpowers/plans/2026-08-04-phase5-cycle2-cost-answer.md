# Phase 5 cycle 2 — the cost answer implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Two n=16 batches on `AGENTCLINIC_PHASE_1`, bare and orchestrated,
and an honest comparison of what the orchestration cost.

**Architecture:** No new harness code. `run_batch` already takes
`improvement=` and resumes from a checkpoint; a recompute script reads both
checkpoints and emits the research record's table.

**Tech Stack:** Python 3.14, `harness.runner`, `harness.telemetry`, uv.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-08-04-phase5-cycle2-cost-answer-design.md`
- **Commit freeze.** From the first run of Task 2 until Task 5's analysis is
  complete, no commit lands in `.worktrees/phase5-improvement-loop` from any
  session. `_conditions` re-reads `HEAD` per run; a commit aborts the batch
  *and* strands the checkpoint, because the records already written carry the
  old `harness_revision`.
- **Foreground only.** No backgrounded live runs.
- **No duration predictions in this document.** That expectation is what
  invited the Phase 4 teardown.
- Model server verified before each batch: `curl -s -m 10 http://127.0.0.1:8001/v1/models`.
  When it is down `pi` exits 0 with empty stderr and the harness records a
  fabricated result that looks like data.
- Checkpoints: `~/local-ai-pi-evidence/satyrn-phase5-cycle2-bare-n16.jsonl`
  and `~/local-ai-pi-evidence/satyrn-phase5-cycle2-sdd-orchestrator-n16.jsonl`.
  Outside version control.

---

### Task 1: Size the chunks from a measurement, not a guess

- [ ] **Step 1: Verify the server returns real output**

Run: `curl -s -m 10 http://127.0.0.1:8001/v1/models`
Expected: JSON naming `gemma-4-12B-it-MLX-8bit`.

- [ ] **Step 2: Run two bare runs and time them**

```bash
time uv run python -c "
from pathlib import Path
from harness.runner import AGENTCLINIC_PHASE_1, run_batch
records = run_batch(
    Path.home() / 'local-ai-pi-evidence' / 'satyrn-phase5-cycle2-bare-n16.jsonl',
    suite=AGENTCLINIC_PHASE_1, target=2,
)
print('records:', len(records), 'accepted:', sum(r.accepted for r in records))
"
```

This is the first two runs of the bare arm, not a throwaway — `run_batch`
appends to the checkpoint and later calls resume from it.

- [ ] **Step 3: Choose a chunk size**

Divide the elapsed time by two, and pick a `target` increment whose expected
duration leaves margin inside a single foreground invocation. Record the
per-run figure; Task 5's record needs it, and the Backlog's wall-clock entry
says a run's in-stream span understates true elapsed time by a median 7.6 s.

---

### Task 2: The bare arm to n=16

- [ ] **Step 1: Resume in chunks until the checkpoint holds 16**

Repeat, raising `target` by the chunk size chosen in Task 1:

```bash
uv run python -c "
from pathlib import Path
from harness.runner import AGENTCLINIC_PHASE_1, run_batch
records = run_batch(
    Path.home() / 'local-ai-pi-evidence' / 'satyrn-phase5-cycle2-bare-n16.jsonl',
    suite=AGENTCLINIC_PHASE_1, target=TARGET,
)
print('records:', len(records), 'accepted:', sum(r.accepted for r in records))
"
```

- [ ] **Step 2: Confirm the arm recorded no improvement**

```bash
uv run python -c "
import json
from pathlib import Path
p = Path.home() / 'local-ai-pi-evidence' / 'satyrn-phase5-cycle2-bare-n16.jsonl'
names = {json.loads(l)['conditions']['improvement_name'] for l in p.read_text().splitlines() if l.strip()}
print('improvement_name values:', names)
"
```

Expected: `{'none'}`. Anything else means the wrong arm was run.

---

### Task 3: The orchestrated arm to n=16

- [ ] **Step 1: Re-verify the server**

Run: `curl -s -m 10 http://127.0.0.1:8001/v1/models`

- [ ] **Step 2: Resume in chunks until the checkpoint holds 16**

```bash
uv run python -c "
from pathlib import Path
from harness.runner import AGENTCLINIC_PHASE_1, sdd_orchestrator, run_batch
records = run_batch(
    Path.home() / 'local-ai-pi-evidence' / 'satyrn-phase5-cycle2-sdd-orchestrator-n16.jsonl',
    suite=AGENTCLINIC_PHASE_1, target=TARGET, improvement=sdd_orchestrator(),
)
print('records:', len(records), 'accepted:', sum(r.accepted for r in records))
"
```

- [ ] **Step 3: Confirm the arm recorded the improvement**

Same command as Task 2 step 2 against the orchestrated checkpoint.
Expected: `{'sdd-orchestrator'}`.

---

### Task 4: The delegation check, and the recompute script

**Files:**
- Create: `docs/superpowers/research/2026-08-04-phase5-cycle2-recompute.py`

**Interfaces:**
- Consumes: both checkpoints; `harness.checkpoint.load_checkpoint`;
  `harness.telemetry.read_telemetry`.
- Produces: a markdown per-run table on stdout, and a summary block.

- [ ] **Step 1: Write the script**

For each record in each checkpoint it emits: index, accepted, turns, tool
calls, tool errors, `context_processed`, `subagent` call count, whether any
`subagent` call returned `isError: true`, and the maximum number of
`subagent` calls in flight at once (a start with no matching end before the
next start).

The concurrency figure is computed by walking `tool_execution_start` /
`tool_execution_end` pairs by `toolCallId` in stream order and tracking the
running count — not by counting calls per turn, which would not distinguish
sequential from concurrent.

- [ ] **Step 2: Run it and read the output before writing any prose**

```bash
uv run python docs/superpowers/research/2026-08-04-phase5-cycle2-recompute.py
```

- [ ] **Step 3: Apply the exclusion rule**

Any orchestrated run with zero successful `subagent` calls is a **failed
delegation**. Count them, exclude them from the cost comparison, and state
both. If more than a couple fail, the arm does not support a cost claim and
the record says so instead of reporting a median over the survivors.

---

### Task 5: The research record, and closing the cycle

- [ ] **Step 1: Write the record**

Create `docs/superpowers/research/2026-08-04-phase5-cycle2-cost-answer.md`
with the per-run table exactly as the script emitted it, both arms' accept
counts, the delegation check, medians and ranges for turns and
`context_processed`, each of the three predictions scored explicitly as
replicated or falsified, and the parallel-children observation with what it
means for the Backlog's own-tool gate.

State the per-run wall-clock measured in Task 1, and note that in-stream span
understates elapsed time by a median 7.6 s per the Backlog.

- [ ] **Step 2: Wire it into the docs**

Add a bullet under `## Research` in `docs/superpowers/index.md` and a line to
the research `toctree`.

- [ ] **Step 3: Close the cycle in `ROADMAP.md`**

Set the Phase 5 cycle 2 row to `Done` with `[spec]`, `[plan]`, `[research]`
links, add the concept-budget check, and record the result in one sentence in
the row itself. Then verify pipe-table contiguity:

```bash
python3 -c "
lines = open('ROADMAP.md').read().split(chr(10))
runs, cur = [], []
for i, l in enumerate(lines, 1):
    if l.startswith('|'): cur.append(i)
    else:
        if cur: runs.append((cur[0], cur[-1], len(cur)))
        cur = []
if cur: runs.append((cur[0], cur[-1], len(cur)))
[print(a, b, n, lines[a-1][:40]) for a, b, n in runs]
"
```

- [ ] **Step 4: Gates, then commit — the freeze ends here**

```bash
uv run pytest -q
uv run ruff check .
uv run pyrefly check
uv run sphinx-build -W -q -b html docs docs/_build/html
git add -A
git commit -m "docs(phase5): what the orchestration cost"
```

---

## Self-Review

**Spec coverage.** Two batches → Tasks 2 and 3. Delegation check → Task 4.
Parallel-children observation → Task 4 step 1, reported in Task 5 step 1.
Predictions scored → Task 5 step 1. Committed recompute script backing the
table → Task 4. Manual comparison only → no comparison code beyond the
recompute script, which reports rather than judges.

**Placeholder scan.** `TARGET` in Tasks 2 and 3 is deliberately symbolic: its
value comes from Task 1's measurement, and fixing a number here would be the
duration prediction the constraints forbid.

**Ordering risk.** Task 1 writes real records into the bare arm's checkpoint.
That is intended — it is the arm's first chunk — but it means the bare arm
must be run before any decision to change conditions, since a later change
would strand those two records.
