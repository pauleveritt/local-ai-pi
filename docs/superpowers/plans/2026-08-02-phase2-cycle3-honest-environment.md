# Phase 2, Cycle 3 — Honest environment, clean baseline: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tell the model what environment it is in, measure what that does to
a 32-run baseline, and correct the two records that taught otherwise.

**Architecture:** Four small changes, in a forced order. Two lines are
appended verbatim to the task spec the model receives as its prompt; a
derived `tool_errors` property is added to `RunTelemetry`; both are committed
*before* a live n=32 batch runs, because `run_batch()` reads `git rev-parse
HEAD` per run and a mid-batch commit aborts the batch. The batch's raw
checkpoint stays outside Git, exactly as cycles 2 and 16 did, and a committed
recompute script plus a research record are what survive it.

**Tech Stack:** Python 3.14, pytest 8.3.4, ruff, pyrefly, Sphinx (strict,
`-W`), `pi` 0.82.0 against a local `omlx` server.

## Global Constraints

- **No changes to `harness/runner.py`, `harness/workspace.py`,
  `harness/checkpoint.py`, or the batch mechanism.** Phase 2 has never
  touched the run machinery and does not start here.
- **No new concept-budget terms.** `tool_errors` aggregates *tool call* and
  its `is_error` field, both already budgeted. "Environment" is used in its
  ordinary sense.
- **The appended spec text is byte-exact.** Appending must leave
  `examples/agentclinic/specs/roadmap.md` at SHA-256
  `95f9303c749416fc84aeddea5ada10879dd86dd64713574a6d2655725457ce2d`
  (1313 bytes). The first bullet stays on one unwrapped line: the file is
  passed to `pi` as raw prompt text and re-wrapping changes the bytes, the
  recorded `task_spec_sha256`, and therefore what the baseline measures.
- **No git commits while `run_batch()` is in flight.** `_conditions()` reads
  `git rev-parse HEAD` live; a commit mid-batch raises `RuntimeError: run
  conditions changed during batch` and discards the batch. This happened
  once already (cycle 2's record, "Operational note").
- **Honesty gate.** If the error rate is not near zero, or any run is
  refused or rejected, the research record says the fix failed. It does not
  report a cheaper number, retry until a clean batch appears, or drop runs.
- **Raw checkpoints are never committed.** They live in
  `~/local-ai-pi-evidence/`. Only checksums, derived summaries, and the
  recompute script go into Git.
- **Gates, run before every commit:** `uv run pytest tests/ && uv run ruff
  check . && uv run pyrefly check`, plus `uv run --group docs sphinx-build -W
  -b html docs docs/_build/html`.

**Starting state:** `main` at `4d7b6ab`, clean tree, 25 commits unpushed. The
`omlx` server is up and verified.

**Task order is not optional.** Tasks 1 and 2 must be committed before Task 3
launches the live batch; Tasks 4–7 all happen after it finishes.

---

### Task 1: Append the `## Environment` section to the task spec

**Files:**
- Modify: `examples/agentclinic/specs/roadmap.md` (append at end; currently
  1152 bytes, ends with a newline)

**Interfaces:**
- Consumes: nothing.
- Produces: a task spec whose SHA-256 is
  `95f9303c749416fc84aeddea5ada10879dd86dd64713574a6d2655725457ce2d`. Task 3's
  batch records this value as `RunConditions.task_spec_sha256`; Task 5's
  research record quotes it.

Do not hand-type the text into an editor that may re-wrap or re-indent it.
Use the `printf` below, which was verified to produce the required checksum.

- [ ] **Step 1: Record the pre-change state**

Run:

```bash
shasum -a 256 examples/agentclinic/specs/roadmap.md && wc -c examples/agentclinic/specs/roadmap.md
```

Expected, exactly:

```
db17991e47b1b3dd5df18df08ff8939ed7924b81422a84cdb196dd0c51381c84  examples/agentclinic/specs/roadmap.md
    1152 examples/agentclinic/specs/roadmap.md
```

If either value differs, **stop**: the baseline this cycle compares against
was produced from `db17991e…`, and a different starting file means the append
cannot reach the target checksum.

- [ ] **Step 2: Append the two lines**

Run exactly this, as one command:

```bash
printf '\n## Environment\n\n- FastAPI, Jinja2, pytest, and httpx are already installed. Do not install anything.\n- Run tests with `python -m pytest` from the project root.\n' >> examples/agentclinic/specs/roadmap.md
```

- [ ] **Step 3: Verify the checksum — this is the test for this task**

Run:

```bash
shasum -a 256 examples/agentclinic/specs/roadmap.md && wc -c examples/agentclinic/specs/roadmap.md
```

Expected, exactly:

```
95f9303c749416fc84aeddea5ada10879dd86dd64713574a6d2655725457ce2d  examples/agentclinic/specs/roadmap.md
    1313 examples/agentclinic/specs/roadmap.md
```

If the checksum differs, run `git checkout examples/agentclinic/specs/roadmap.md`
and repeat Step 2 with the `printf` copied verbatim. Do not "fix" the file by
editing it toward the right length — the failure mode being guarded against is
an invisible whitespace or wrapping difference.

- [ ] **Step 4: Confirm the first bullet is one unwrapped line**

Run:

```bash
awk 'length > 79 {print FILENAME": "FNR": "length" chars"}' examples/agentclinic/specs/roadmap.md
```

Expected: one line reported —
`examples/agentclinic/specs/roadmap.md: <N>: 86 chars` (the FastAPI bullet).
That long line is intentional and must not be wrapped. Ruff does not lint
this path (`extend-exclude = ["examples/agentclinic"]`), and `E501` is
disabled project-wide regardless.

- [ ] **Step 5: Run the gates**

Run:

```bash
uv run pytest tests/ && uv run ruff check . && uv run pyrefly check
```

Expected: all pass. No test asserts the old spec checksum, so nothing should
break; if something does, report it rather than editing the test.

- [ ] **Step 6: Commit**

```bash
git add examples/agentclinic/specs/roadmap.md
git commit -m "feat(phase2-cycle3): state the environment in the task spec

The 48-run baseline's turn variance was ~95% explained by tool errors,
all of it environment friction: 43 failed dependency installs against
dependencies that were already importable, and 22 test-import failures
from a bare pytest. Two lines, byte-identical to the wording sixteen
exploratory runs went 16/16 clean against."
```

---

### Task 2: Add `RunTelemetry.tool_errors`

**Files:**
- Modify: `harness/telemetry.py` (add a property to `RunTelemetry`, after
  `context_processed`)
- Test: `tests/test_telemetry.py` (append two tests)

**Interfaces:**
- Consumes: `ToolCall.is_error: bool | None` and `RunTelemetry.tool_calls:
  tuple[ToolCall, ...]`, both already defined in `harness/telemetry.py`.
- Produces: `RunTelemetry.tool_errors -> int`, a read-only property. Task 4's
  recompute script calls it; Task 5's research record reports it.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_telemetry.py`:

```python
def test_tool_errors_counts_only_calls_that_reported_an_error():
    # Non-vacuity pin. `None` means *unknown*, not failure, and has two
    # distinct sources -- an unmatched start (c3) and a matched end
    # carrying no isError field (c4). Counting either would be the
    # plausible wrong implementation, so this asserts they are excluded
    # specifically rather than only asserting the total.
    stream = (
        '{"type": "tool_execution_start", "toolCallId": "c1", "toolName": "bash"}\n'
        '{"type": "tool_execution_end", "toolCallId": "c1", "isError": true}\n'
        '{"type": "tool_execution_start", "toolCallId": "c2", "toolName": "bash"}\n'
        '{"type": "tool_execution_end", "toolCallId": "c2", "isError": false}\n'
        '{"type": "tool_execution_start", "toolCallId": "c3", "toolName": "write"}\n'
        '{"type": "tool_execution_start", "toolCallId": "c4", "toolName": "write"}\n'
        '{"type": "tool_execution_end", "toolCallId": "c4"}\n'
        '{"type": "agent_end"}\n'
    )
    telemetry = read_telemetry(stream)
    assert [call.is_error for call in telemetry.tool_calls] == [
        True,
        False,
        None,
        None,
    ]
    assert telemetry.tool_errors == 1


def test_a_clean_real_run_reports_zero_tool_errors():
    # A weak pin on its own -- zero -- which is why the synthetic
    # mixed-outcome test above carries the non-vacuity weight. It is the
    # only real-data pin available: tests/fixtures/phase1-n48-telemetry-summary.json
    # holds only turns and context_processed, and extending it would
    # change a checksum already recorded in tests/fixtures/README.md.
    assert read_telemetry(_real_run()).tool_errors == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
uv run pytest tests/test_telemetry.py -k tool_errors -v
```

Expected: both FAIL with `AttributeError: 'RunTelemetry' object has no
attribute 'tool_errors'`.

- [ ] **Step 3: Write the implementation**

In `harness/telemetry.py`, inside `class RunTelemetry`, immediately after the
`context_processed` property:

```python
    @property
    def tool_errors(self) -> int:
        """Count of tool calls that finished and reported an error.

        Counts `is_error is True` only. `None` means *unknown*, not a
        failure, and has two sources (see `ToolCall.is_error`): a start
        with no matching end -- where `complete` already declares every
        count a lower bound -- and a matched end carrying no `isError`
        field, which `complete` deliberately still counts as a complete
        run. Neither is counted here.
        """
        return sum(1 for call in self.tool_calls if call.is_error)
```

Nothing else changes: no new field on `RunTelemetry`, no change to
`read_telemetry`, no schema change. `tool_errors` is derived from data the
dataclass already carries, the same shape as `context_processed`.

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
uv run pytest tests/test_telemetry.py -v
```

Expected: every test in the file passes, including the two new ones.

- [ ] **Step 5: Run the gates**

Run:

```bash
uv run pytest tests/ && uv run ruff check . && uv run pyrefly check
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add harness/telemetry.py tests/test_telemetry.py
git commit -m "feat(phase2-cycle3): add RunTelemetry.tool_errors

A derived property over existing data, the same shape as
context_processed. Counts is_error is True only; None means unknown,
not failure, and its two sources are pinned as excluded rather than
merely uncounted."
```

---

### Task 3: Run the clean n=32 baseline

**Files:**
- Create (outside Git): `~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-n32.jsonl`
- Create (scratch, not committed): a batch log file

**Interfaces:**
- Consumes: `harness.runner.run_batch(checkpoint_path, *, target, model)` and
  `harness.runner.preflight_model(model)`, both unmodified. The spec at
  `95f9303c…` from Task 1 and the committed `tool_errors` from Task 2 must
  both be in `HEAD` before this task starts.
- Produces: a 32-record JSONL checkpoint and its SHA-256, consumed by Tasks 4
  and 5.

**This task spends ~25 minutes of real model time and makes no code changes.**

- [ ] **Step 1: Confirm the working tree is clean and no commit is pending**

Run:

```bash
git status --short && git log --oneline -1
```

Expected: no output from `git status --short`, and the most recent commit is
Task 2's. **If the tree is dirty, stop and commit or stash first.** Once the
batch starts, no commit may land until it finishes.

- [ ] **Step 2: Verify the model server before spending batch time**

Run:

```bash
PYTHONPATH=. uv run python -c "
from harness.runner import preflight_model
preflight_model()
print('preflight OK')
"
```

Expected: `preflight OK`.

If it raises `ModelServerDown`, the local `omlx` server is not running —
start it and retry. If it raises `RuntimeError: model preflight produced no
usable assistant output`, check `~/.omlx/settings.json` for the API-key drift
cycle 2 hit (it wants `"skip_api_key_verification": true`) before changing
anything in `harness/`.

- [ ] **Step 3: Launch the batch in the background**

Run (in the background — this takes ~25 minutes, longer than a foreground
command may run):

```bash
mkdir -p ~/local-ai-pi-evidence && PYTHONPATH=. uv run python -c "
from pathlib import Path
from harness.runner import run_batch
path = Path.home() / 'local-ai-pi-evidence' / 'satyrn-phase2-cycle3-clean-n32.jsonl'
records = run_batch(path, target=32)
print('records:', len(records))
print('accepted:', sum(1 for r in records if r.accepted))
" 2>&1 | tee /tmp/cycle3-batch.log
```

`run_batch` calls `preflight_model` itself, and refuses to extend any
checkpoint whose conditions differ — which is why it cannot accidentally
append to cycle 2's checkpoints: `task_spec_sha256` changed in Task 1.

- [ ] **Step 4: Wait, without committing anything**

Poll progress with:

```bash
wc -l ~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-n32.jsonl
```

Do not run `git commit`, `git checkout`, `git rebase`, or anything else that
moves `HEAD` until Step 5 reports completion. Editing files is safe;
committing them is not.

Expected on completion: `records: 32` and `accepted: 32` in the log.

**If `RuntimeError: run conditions changed during batch` appears:** something
moved `HEAD`. Delete the partial checkpoint, restore `HEAD` to Task 2's
commit, and restart from Step 1. Do not salvage the partial records — they
are not comparable to runs under a different revision.

- [ ] **Step 5: Record the raw artifact's identity**

Run:

```bash
shasum -a 256 ~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-n32.jsonl
wc -c -l ~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-n32.jsonl
```

Expected: 32 lines. Copy the checksum and byte count somewhere safe — Task 5's
record needs both, and the checkpoint is not in Git.

- [ ] **Step 6: Read the conditions actually recorded**

Run:

```bash
PYTHONPATH=. uv run python -c "
import json
from pathlib import Path
path = Path.home() / 'local-ai-pi-evidence' / 'satyrn-phase2-cycle3-clean-n32.jsonl'
rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
conds = {json.dumps(r['conditions'], sort_keys=True) for r in rows}
print('distinct conditions:', len(conds))
print(json.dumps(json.loads(next(iter(conds))), indent=2))
# RunResult.accepted is the Pi-exit veto (cycle 15), not grade.accepted
# alone: not timed out, Pi exited zero, AND the grade accepted.
accepted = [
    r for r in rows
    if not r['pi_timed_out'] and r['pi_returncode'] == 0 and r['grade']['accepted']
]
print('accepted:', len(accepted))
print('grade-accepted only:', sum(1 for r in rows if r['grade']['accepted']))
print('refused:', sum(1 for r in rows if r['grade']['refused_config']))
print('refused paths:', sorted({p for r in rows for p in r['grade']['refused_config']}))
print('returncodes:', sorted({r['pi_returncode'] for r in rows}))
print('timed out:', sum(1 for r in rows if r['pi_timed_out']))
"
```

Expected: `distinct conditions: 1`, `task_spec_sha256` equal to
`95f9303c749416fc84aeddea5ada10879dd86dd64713574a6d2655725457ce2d`, 32
accepted, return codes `[0]`, 0 timed out.

**If any run was refused or rejected, do not stop the cycle and do not
re-run.** Record the actual numbers; Task 5's record reports them as a
failure of the fix. In particular, a refusal caused by a model-written
`conftest.py` (`_REFUSED_CONFIG` in `harness/grading.py`) is the specific
failure mode the spec predicted the *rejected* explanatory wording would
cause — if it appears against the tested wording, that is a finding worth
stating plainly.

- [ ] **Step 7: No commit**

This task commits nothing. The checkpoint is outside Git by design.

---

### Task 4: Commit the recompute script

**Files:**
- Create: `docs/superpowers/research/2026-08-02-phase2-cycle3-recompute-summary.py`

**Interfaces:**
- Consumes: `harness.telemetry.read_telemetry` and the `tool_errors` property
  from Task 2; the checkpoint from Task 3.
- Produces: the printed per-run table, aggregates, and support-coverage
  diagnostic that Task 5's record transcribes. Nothing imports this script.

It deliberately mirrors cycle 2's
`2026-08-02-phase2-cycle2-recompute-summary.py` — same `message_span` helper,
same output shape — so the two records can be read side by side. It adds one
thing cycle 2's did not have: the final-quarter support-coverage diagnostic.

- [ ] **Step 1: Write the script**

Create `docs/superpowers/research/2026-08-02-phase2-cycle3-recompute-summary.py`:

```python
"""Recompute this cycle's per-run table and aggregates from the clean
baseline checkpoint. Not a test -- a reproducibility aid the research
record cites, since its claims come from parsing pi_stdout via
read_telemetry, not from a trivial line count.

Usage (from the repo root, so `harness` is importable):
    PYTHONPATH=. uv run python \\
        docs/superpowers/research/2026-08-02-phase2-cycle3-recompute-summary.py \\
        ~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-n32.jsonl

The raw checkpoint is outside Git (see the research record alongside this
script for its checksum); this script cannot run without it.
"""

import json
import sys
from collections import Counter
from pathlib import Path

from harness.telemetry import read_telemetry


def message_span(pi_stdout: str) -> float | None:
    starts = []
    for line in pi_stdout.split("\n"):
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("type") == "message_start":
            ts = event.get("message", {}).get("timestamp")
            if ts is not None:
                starts.append(ts)
    if len(starts) < 2:
        return None
    return (max(starts) - min(starts)) / 1000.0


def load(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        tel = read_telemetry(data["pi_stdout"])
        rows.append(
            {
                "turns": tel.turns,
                "tool_calls": len(tel.tool_calls),
                "tool_names": Counter(tc.name for tc in tel.tool_calls),
                "errors": tel.tool_errors,
                "context_processed": tel.context_processed,
                "complete": tel.complete,
                "span": message_span(data["pi_stdout"]),
                # The Pi-exit veto (cycle 15), not grade.accepted alone.
                "accepted": (
                    not data["pi_timed_out"]
                    and data["pi_returncode"] == 0
                    and data["grade"]["accepted"]
                ),
                "refused": bool(data["grade"]["refused_config"]),
            }
        )
    return rows


def support_coverage(turns: list[int]) -> tuple[set[int], bool]:
    """Distinct turn values first seen in the final quarter of the batch.

    One-sided: a quiet final quarter is NOT evidence that the support is
    covered. The n=16 baseline is the proof -- its own runs 13-16
    introduced no new value, yet 10 and 12 were still unseen and
    surfaced at runs 17 and 20.
    """
    cut = len(turns) - len(turns) // 4
    earlier = set(turns[:cut])
    late_new = {t for t in turns[cut:] if t not in earlier}
    return late_new, bool(late_new)


def main(checkpoint_path: str) -> None:
    rows = load(Path(checkpoint_path))
    for i, r in enumerate(rows, 1):
        tools = ",".join(f"{k}x{v}" for k, v in sorted(r["tool_names"].items()))
        span = f"{r['span']:.1f}s" if r["span"] is not None else "n/a"
        print(
            f"{i:>2}: turns={r['turns']:>2} tools={r['tool_calls']:>2} ({tools:<14}) "
            f"errors={r['errors']} ctx={r['context_processed']:>6} "
            f"span={span} complete={r['complete']} accepted={r['accepted']}"
        )
    turns = [r["turns"] for r in rows]
    ctx = [r["context_processed"] for r in rows]
    tools = sum((r["tool_names"] for r in rows), Counter())
    late_new, uncovered = support_coverage(turns)
    print()
    print("runs:", len(rows))
    print("turn distribution:", dict(sorted(Counter(turns).items())))
    print("tool totals:", dict(tools))
    print("total errors:", sum(r["errors"] for r in rows))
    print("runs with >=1 error:", sum(1 for r in rows if r["errors"]))
    print("all complete:", all(r["complete"] for r in rows))
    print("accepted:", sum(1 for r in rows if r["accepted"]))
    print("refused:", sum(1 for r in rows if r["refused"]))
    print("context_processed min/max/mean:", min(ctx), max(ctx), sum(ctx) / len(ctx))
    print("new turn values in final quarter:", sorted(late_new) or "none")
    print(
        "support coverage:",
        "NOT covered -- a new value appeared late" if uncovered
        else "final quarter was quiet (this certifies nothing)",
    )


if __name__ == "__main__":
    main(sys.argv[1])
```

- [ ] **Step 2: Run it against the real checkpoint**

Run:

```bash
PYTHONPATH=. uv run python \
    docs/superpowers/research/2026-08-02-phase2-cycle3-recompute-summary.py \
    ~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-n32.jsonl | tee /tmp/cycle3-summary.txt
```

Expected: 32 numbered rows plus the aggregate block. Keep
`/tmp/cycle3-summary.txt` — Task 5 transcribes from it rather than retyping
numbers by hand.

- [ ] **Step 3: Run the precision figures the record needs**

Run:

```bash
PYTHONPATH=. uv run python -c "
import json
from pathlib import Path
from harness.telemetry import read_telemetry
from harness.precision import bootstrap_ci_halfwidth, minimum_n_for_precision, leave_one_out_spread
path = Path.home() / 'local-ai-pi-evidence' / 'satyrn-phase2-cycle3-clean-n32.jsonl'
tel = [read_telemetry(json.loads(l)['pi_stdout']) for l in path.read_text().splitlines() if l.strip()]
turns = [t.turns for t in tel]
ctx = [t.context_processed for t in tel]
print('distinct turn values:', sorted(set(turns)))
print('mean turns:', sum(turns) / len(turns))
print('loo spread (turns):', round(leave_one_out_spread(turns), 4))
for target in (1.0, 0.5, 0.25):
    print(f'min n for turns halfwidth {target}:', minimum_n_for_precision(turns, target, seed=0))
for target in (1500, 1000, 500):
    print(f'min n for ctx halfwidth {target}:', minimum_n_for_precision(ctx, target, seed=0))
print('halfwidth at n=32 (turns):', round(bootstrap_ci_halfwidth(turns, 32, seed=0), 4))
" | tee /tmp/cycle3-precision.txt
```

Expected: values printed without error. **If `distinct turn values` has one or
two entries, the bootstrap is being run over a near-degenerate sample** — the
numbers are still computed, but Task 5 must say so plainly and report a
binomial rate of longer-than-modal runs instead of publishing a precision
table as if it were meaningful. The spec requires exactly that fallback.

- [ ] **Step 4: Run the gates**

Run:

```bash
uv run pytest tests/ && uv run ruff check . && uv run pyrefly check
```

Expected: all pass. Ruff lints the new script (it is not under an excluded
path) and pyrefly does not (`project-includes = ["harness", "tests"]`).
Sphinx ignores `.py` files, so no docs build is needed for this task.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/research/2026-08-02-phase2-cycle3-recompute-summary.py
git commit -m "docs(phase2-cycle3): recompute script for the clean baseline

Mirrors cycle 2's script so the two records read side by side, and adds
the one-sided support-coverage diagnostic: a quiet final quarter is
reported as exactly that, never as evidence of coverage."
```

---

### Task 5: Write the research record

**Files:**
- Create: `docs/superpowers/research/2026-08-02-phase2-cycle3-clean-baseline.md`

**Interfaces:**
- Consumes: `/tmp/cycle3-summary.txt` and `/tmp/cycle3-precision.txt` from
  Task 4, and the checksum from Task 3 Step 5.
- Produces: the record Task 6's correction blocks point at, and Task 7 adds
  to the docs index and toctree.

**Every number in this file is transcribed from the two saved outputs, not
retyped from memory or recomputed by hand.** Cycle 2's record made the same
promise and it is why its table could be trusted.

- [ ] **Step 1: Write the record**

Create `docs/superpowers/research/2026-08-02-phase2-cycle3-clean-baseline.md`
with this structure, filling every `<…>` from the saved outputs:

````markdown
# Phase 2, Cycle 3 — Clean baseline

Verified 2026-08-02 against a 32-run batch executed after the task spec was
amended to state the environment (see the
[design spec](../specs/2026-08-02-phase2-cycle3-honest-environment-design.md)
for the friction finding that motivated it).

## Raw checkpoint

| Field | Value |
|---|---|
| Path | `~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-n32.jsonl` |
| Records | 32 |
| Size | <bytes> |
| SHA-256 | `<checksum>` |

Outside Git, per the same reasoning as cycles 2 and 16. This record and the
recompute script alongside it are what survive if the checkpoint is lost.

Recomputed by `2026-08-02-phase2-cycle3-recompute-summary.py`, alongside this
file.

## Conditions shared by all 32 records

| Field | Value |
|---|---|
| Model | `omlx/gemma-4-12B-it-MLX-8bit` |
| Pi version | `<pi_version>` |
| Task-spec SHA-256 | `95f9303c749416fc84aeddea5ada10879dd86dd64713574a6d2655725457ce2d` |
| Harness revision | `<harness_revision>` |
| Run timeout | 600 seconds |
| Grade timeout | 30 seconds |
| Accepted | <n> of 32 |
| Refused | <n> |
| Pi return codes | <values> |
| Timed out | <n> |
| `complete` (telemetry) | <value> for all 32 |

The task-spec hash differs from the 48-run baseline's
(`db17991e…`), which is why `run_batch()` refused to extend those checkpoints
and started a fresh one. That refusal is the conditions mechanism working, not
an obstacle worked around.

## Did the fix work?

| Metric | 48-run baseline | This batch |
|---|---|---|
| Total tool errors | 65 of 336 | <n> of <n> |
| Runs with at least one error | 28 of 48 | <n> of 32 |
| Zero-error rate | 20/48 | <n>/32 |

<One paragraph stating the verdict plainly. If the error count is not near
zero, this paragraph says the fix failed and the rest of the record is read
in that light. Do not soften it and do not re-run the batch.>

## Per-run table

`tools` is total tool calls; `err` is `tool_errors`; `ctx` is
`context_processed`; `span` is seconds between the first and last
`message_start` timestamp — a lower bound on wall-clock, not a true duration.

| run | turns | tools | err | ctx | span(s) |
|---|---|---|---|---|---|
| <32 rows transcribed from /tmp/cycle3-summary.txt> |

## Turn distribution and support coverage

| Metric | Value |
|---|---|
| Distinct turn values | <set> |
| Distribution | <counts> |
| Mean turns | <value> |
| `leave_one_out_spread` | <value> |
| New turn values in the final quarter (runs 25–32) | <values or "none"> |

**The support-coverage check is one-sided: it can fail, never certify.** The
n=16 baseline is the proof — its own final quarter introduced no new turn
value, yet 10 and 12 were still unseen and surfaced at runs 17 and 20. <State
what this batch's final quarter showed, and say explicitly that a quiet
quarter is being reported as a quiet quarter rather than as coverage.>

## How many runs would a claim need?

<If the distribution has enough distinct values for the bootstrap to be
meaningful, a precision table in cycle 2's format, from
/tmp/cycle3-precision.txt, carrying cycle 2's support-incompleteness caveat:
resampling cannot produce a value the sample never contained, so a reported
half-width is optimistic, not exact.

If it does not — a near-degenerate sample — say so plainly instead, and report
a binomial rate of longer-than-modal runs. Do not publish a precision table
built on two distinct values as if it meant the same thing as cycle 2's.>

## The three-question check, piloted

*Written in task 6 of this cycle's plan. Leave this sentence here until then.*

## Verification method

Every number above was produced by `harness.telemetry.read_telemetry` and
`harness.precision` via the recompute script and the precision command
recorded in this cycle's plan, then transcribed — not hand-aggregated and not
retyped from memory.
````

- [ ] **Step 2: Verify the transcription mechanically**

Run:

```bash
PYTHONPATH=. uv run python -c "
import re
from pathlib import Path
doc = Path('docs/superpowers/research/2026-08-02-phase2-cycle3-clean-baseline.md').read_text()
assert '<' not in re.sub(r'\`[^\`]*\`', '', doc), 'unfilled placeholder remains'
rows = [l for l in doc.splitlines() if re.match(r'^\| \d+ \|', l)]
print('per-run rows:', len(rows))
assert len(rows) == 32, 'per-run table must have 32 rows'
print('OK')
"
```

Expected: `per-run rows: 32` then `OK`.

- [ ] **Step 3: Build the docs**

Run:

```bash
uv run --group docs sphinx-build -W -b html docs docs/_build/html
```

Expected: a warning that this document is not in any toctree — **that is
expected here**; Task 7 wires it in. If the build fails for any *other*
reason (a broken cross-reference, malformed table), fix it now.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/research/2026-08-02-phase2-cycle3-clean-baseline.md
git commit -m "docs(phase2-cycle3): the clean baseline record"
```

---

### Task 6: Correct the records that taught otherwise

**Files:**
- Modify: `docs/superpowers/research/2026-08-02-phase2-cycle2-precision-baseline.md`
  (append a third dated correction block; leave the per-run table and
  checksums untouched)
- Modify: `docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md`
  (add an environment note; do not restate or re-litigate the result)
- Modify: `docs/superpowers/index.md` (a note under the Phase 1 section,
  where it describes what cycles 2 and 11 provisioned)
- Modify: `docs/superpowers/research/2026-08-02-phase2-cycle3-clean-baseline.md`
  (fill in the piloted-check section left open in Task 5)

**Interfaces:**
- Consumes: the finished record from Task 5.
- Produces: nothing later tasks depend on except Task 7's index wiring.

- [ ] **Step 1: Append the third correction block to cycle 2's record**

At the end of
`docs/superpowers/research/2026-08-02-phase2-cycle2-precision-baseline.md`,
append:

```markdown
## Corrected 2026-08-02 — what the turn variance was actually measuring

This record's central quantity, turn count, is almost entirely explained by
tool errors:

```
errors = -3.79 + 0.643 × turns     R² = 0.952
```

All 65 errored tool calls are environment friction, in two families: 43
dependency-install attempts against dependencies that were already
importable in a uv venv with no `pip`, and 22 test-import failures where a
bare `pytest` does not put the project root on `sys.path`.

**And the 20 zero-error runs all avoided that friction the same way.** Every
one has a byte-identical shape — `mkdir -p templates tests`, four `write`
calls, and no test run at all. The runs that looked cleanest were the runs
that skipped verification.

So "the one real random variable" was, to ~95%, a property of the
environment rather than of the model. Nothing in the per-run table or the
checksums above is withdrawn — they are the raw material the finding was
derived from, and they stay exactly as recorded. What is withdrawn is the
implicit reading that this variance measured task difficulty.

Cycle 3 amended the task spec to state the environment and re-measured:
[Phase 2, cycle 3 — clean baseline](2026-08-02-phase2-cycle3-clean-baseline.md).
```

- [ ] **Step 2: Add the environment note to the n=16 evidence record**

In `docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md`,
immediately before the `## Verification method` heading, insert:

```markdown
## Note added 2026-08-02 — the environment this was produced in

The result above stands and is not re-litigated here. What was not recorded
at the time is the environment the sixteen runs were given: the workspace was
a fresh git repository with no `pyproject.toml`, and the model was told
nothing about it. The dependencies it needed were already importable, but the
uv venv had no `pip`, and a bare `pytest` could not import `app`. Across the
wider 48-run baseline that grew from this batch, that friction accounts for
~95% of the variance in turn count, and the runs with no errors at all were
the runs that never ran a test.

The sixteen accepted runs were graded hermetically by the harness, so the
verdicts are unaffected. What the number cannot be read as is a measurement
taken under conditions that made verification easy. See
[Phase 2, cycle 3 — clean baseline](2026-08-02-phase2-cycle3-clean-baseline.md).
```

- [ ] **Step 3: Correct the teaching record**

In `docs/superpowers/index.md`, immediately after the paragraph beginning
"Fourteen cycles, building a grading engine…" in the Phase 1 section, insert:

```markdown
**One correction, added 2026-08-02.** Cycle 2 is titled *workspace
provisioning* and cycle 11 *corrective hardening*, and it is easy to read
those as having provisioned the model a working environment. They did not.
Cycle 2 provisioned a disposable **git repository**; cycle 11's controlled
environment covers the *pytest grading child* only, while `runner.py` passes
`env=None`, so Pi inherits whatever ambient environment it was launched in.
The model's own working conditions were never in any Phase 1 cycle's scope —
and Phase 2 cycle 3 found that this cost ~95% of the measured variance in
turn count, and that the cleanest-looking runs were the ones that skipped
testing. If you are copying this pattern, provision the environment too, or
state it in the task. See
[Phase 2, cycle 3 — clean baseline](research/2026-08-02-phase2-cycle3-clean-baseline.md).
```

- [ ] **Step 4: Fill in the piloted three-question check**

Replace the `## The three-question check, piloted` placeholder in
`docs/superpowers/research/2026-08-02-phase2-cycle3-clean-baseline.md` with a
section that applies these three questions to **every quantitative claim in
this record** and states, for each, whether it caught anything:

1. Am I extrapolating outside the observed range?
2. What exactly does this number measure — the same units as whatever I am
   comparing it to?
3. Could a new sample contain a value mine never showed?

Delete the "Written in task 6" holding sentence when you do. Then re-run Task
5 Step 2's transcription check, which now has to pass with no exemptions.

Write what the check actually found, including "it caught nothing" if that is
the truth. Cycle 4 designs the discipline; this cycle only supplies evidence
for whether it is worth having, and evidence that it found nothing is real
evidence. Candidate claims to run it against, at minimum: the error-count
comparison against the 48-run baseline (are 336 tool calls across 48 runs and
this batch's total the same unit?), any `minimum_n_for_precision` figure
(question 1 and question 3 both bite), and the support-coverage statement
(question 3 is the whole point of its being one-sided).

- [ ] **Step 5: Build the docs**

Run:

```bash
uv run --group docs sphinx-build -W -b html docs docs/_build/html
```

Expected: the only warning is the not-in-any-toctree one for the new research
record, resolved in Task 7. Cross-file links added in Steps 1–3 must resolve;
a broken relative path fails the build under `-W`.

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/research/2026-08-02-phase2-cycle2-precision-baseline.md \
        docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md \
        docs/superpowers/index.md \
        docs/superpowers/research/2026-08-02-phase2-cycle3-clean-baseline.md
git commit -m "docs(phase2-cycle3): correct the records that taught otherwise

Cycle 2's turn variance was ~95% environment friction and its 20
zero-error runs never ran a test. Phase 1 provisioned a git repository,
not a working environment -- a contributor copying that pattern inherits
the trap. Neither result is withdrawn; both are read correctly now."
```

---

### Task 7: Wire the cycle into the roadmap and docs index, and close

**Files:**
- Modify: `ROADMAP.md` (Phase 2 feature-cycle table; concept-budget check)
- Modify: `docs/superpowers/index.md` (Phase 2 table, Research list, two
  toctrees)

**Interfaces:**
- Consumes: everything above.
- Produces: a closed cycle. Nothing depends on it.

This task follows project convention rather than a numbered item in the design
spec — every prior cycle closes by adding its row and wiring its documents in,
and strict Sphinx fails on a document in no toctree.

- [ ] **Step 1: Add the roadmap row**

In `ROADMAP.md`, under `### Phase 2 feature cycles`, append a row after
cycle 2's:

```markdown
| 3 | Honest environment, clean baseline — the 48-run baseline's turn variance was ~95% tool errors, all environment friction, and all 20 zero-error runs skipped testing entirely. Two lines appended verbatim to the task spec state that dependencies are installed and that tests run with `python -m pytest`; `RunTelemetry.tool_errors` counts the friction; a fresh n=32 batch measures what changed. Cycle 2's record and Phase 1's teaching record are corrected: what Phase 1 provisioned was a git repository, not a working environment. | [spec](docs/superpowers/specs/2026-08-02-phase2-cycle3-honest-environment-design.md) | [plan](docs/superpowers/plans/2026-08-02-phase2-cycle3-honest-environment.md) | Done |
```

Adjust the summary if the batch's result contradicts it — the row states what
happened, not what was planned.

- [ ] **Step 2: Run the concept-budget check at close**

The spec budgets **no new terms**. Verify that against the prose actually
written, not against the plan — this is the exact check cycle 2 skipped, which
is how `orchestrator` and `handoff packet` entered and were retired a day
later. Read this cycle's research record and the four correction blocks and
confirm no word is doing the work of a defined mechanism without being in the
table. `tool_errors` aggregates *tool call* and its `is_error`, both already
budgeted; "environment" is ordinary English.

If the check finds a term, add it to the table with an honest note rather than
quietly keeping it.

- [ ] **Step 3: Wire the docs index**

In `docs/superpowers/index.md`:

Add to the Phase 2 table:

```markdown
| 3 | Honest environment, clean baseline | [spec](specs/2026-08-02-phase2-cycle3-honest-environment-design.md) | [plan](plans/2026-08-02-phase2-cycle3-honest-environment.md) |
```

Add to the Research bullet list:

```markdown
- [Phase 2 cycle 3 — clean baseline](research/2026-08-02-phase2-cycle3-clean-baseline.md)
```

Add to the Plans toctree, after `plans/2026-08-02-phase2-cycle2-precision-baseline`:

```
plans/2026-08-02-phase2-cycle3-honest-environment
```

Add to the Research toctree, after `research/2026-08-02-phase2-cycle2-precision-baseline`:

```
research/2026-08-02-phase2-cycle3-clean-baseline
```

The cycle 3 spec is already in the Specs toctree — do not add it twice.

- [ ] **Step 4: Run every gate**

Run:

```bash
uv run pytest tests/ && uv run ruff check . && uv run pyrefly check && \
uv run --group docs sphinx-build -W -b html docs docs/_build/html
```

Expected: all pass, **with no warnings at all** from Sphinx this time. The
not-in-any-toctree warning from Tasks 5 and 6 must be gone.

- [ ] **Step 5: Commit**

```bash
git add ROADMAP.md docs/superpowers/index.md
git commit -m "docs(phase2-cycle3): close the cycle

Roadmap row, docs index and toctree wiring, and the concept-budget
check run at close against the prose rather than the plan -- the check
cycle 2 skipped."
```

- [ ] **Step 6: Report the state, honestly**

State: the batch's accepted/refused/error counts as measured, whether the fix
worked by the spec's own gate (error rate near zero), what the
support-coverage diagnostic showed and that it certifies nothing, whether the
three-question check caught anything, and that the commits remain unpushed.

Do not describe the cycle as successful if the error rate was not near zero.
The spec's honesty gate is the deliverable, not the clean number.
