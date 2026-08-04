# Phase 5 cycle 3 — child telemetry implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `read_telemetry` reports what a delegated child cost, so a run's
total turns and context are readable from the instrument rather than from one
research script.

**Architecture:** A frozen `Delegation` per successful child parsed from the
parent's `tool_execution_end` payload, plus derived `child_*` and `total_*`
properties. Existing fields keep their meanings exactly.

**Tech Stack:** Python 3.14, pytest, uv, ruff, pyrefly. No new dependencies.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-08-04-phase5-cycle3-child-telemetry-design.md`
- **`turn` is a pinned term.** `RunTelemetry.turns` must keep counting the
  parent's `turn_end` events and nothing else. New numbers get new names.
- No change to `RunConditions`, `RunResult`, or any checkpoint. Telemetry is a
  derived view.
- Every seam ships a mutation check: apply the break, watch a **named** test
  fail, revert.
- Gates before each commit: `uv run pytest -q`, `uv run ruff check .`,
  `uv run pyrefly check`.
- Work in `.worktrees/phase5-improvement-loop`.

---

### Task 1: A real, trimmed fixture

**Files:**
- Create: `tests/fixtures/pi-run-0.83.0-delegation.jsonl`
- Modify: `tests/fixtures/README.md`

- [ ] **Step 1: Extract from a real cycle-2 orchestrated run**

Take run 1 of `~/local-ai-pi-evidence/satyrn-phase5-cycle2-sdd-orchestrator-n16.jsonl`.
Keep every `turn_end`, and the `subagent` `tool_execution_start` /
`tool_execution_end` pair. From the end payload, **drop `messages` and `task`**
(hundreds of KB of prose this cycle never parses) and keep `agent`,
`agentSource`, `exitCode`, `usage`, `model`, `stopReason`.

A trimmed *real* payload rather than a synthetic one: a hand-written fixture
would keep passing while Pi's actual shape drifted underneath it, which is the
failure this whole cycle exists to correct.

- [ ] **Step 2: Record its provenance**

Add an entry to `tests/fixtures/README.md` naming the source checkpoint, the
run index, the Pi version, and exactly which fields were dropped and why.

- [ ] **Step 3: Commit**

```bash
git add tests/fixtures/
git commit -m "test(phase5): a real trimmed delegation fixture"
```

---

### Task 2: `Delegation`, parsed and summed

**Files:**
- Modify: `harness/telemetry.py`
- Test: `tests/test_telemetry.py`

**Interfaces:**
- Produces: `Delegation(agent, turns, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, exit_code)`;
  `RunTelemetry.delegations: tuple[Delegation, ...]`; properties
  `child_turns`, `child_output_tokens`, `child_context_processed`,
  `total_turns`, `total_output_tokens`, `total_context_processed`.

- [ ] **Step 1: Write the failing tests**

```python
DELEGATION_FIXTURE = Path(__file__).parent / "fixtures" / "pi-run-0.83.0-delegation.jsonl"


def test_a_delegated_run_reports_the_childs_cost():
    """The regression this cycle exists for. Phase 5 cycle 2 published
    1.15x when the true figure was 8.11x, because telemetry counted the
    parent only. Asserted against a real trimmed payload."""
    telemetry = read_telemetry(DELEGATION_FIXTURE.read_text())

    assert len(telemetry.delegations) == 1
    assert telemetry.delegations[0].agent == "implementer"
    assert telemetry.child_turns > telemetry.turns
    assert telemetry.total_context_processed > 3 * telemetry.context_processed


def test_totals_are_parent_plus_child():
    telemetry = read_telemetry(DELEGATION_FIXTURE.read_text())

    assert telemetry.total_turns == telemetry.turns + telemetry.child_turns
    assert telemetry.total_context_processed == (
        telemetry.context_processed + telemetry.child_context_processed
    )
    assert telemetry.total_output_tokens == (
        telemetry.output_tokens + telemetry.child_output_tokens
    )


def test_a_run_with_no_delegation_totals_to_its_parent():
    """A bare run's totals must equal its parent figures exactly, or every
    number published before this cycle silently changes meaning."""
    telemetry = read_telemetry(FIXTURE.read_text())

    assert telemetry.delegations == ()
    assert telemetry.total_turns == telemetry.turns
    assert telemetry.total_context_processed == telemetry.context_processed
    assert telemetry.total_output_tokens == telemetry.output_tokens


def test_child_context_processed_includes_both_cache_fields():
    """Same definition as the parent's: input + cacheRead + cacheWrite.
    cacheRead dominates a delegated run -- cycle 2's first child read
    173,056 cached tokens against 23,955 fresh input -- so dropping it
    would understate the cost by most of it."""
    line = json.dumps({
        "type": "tool_execution_end", "toolCallId": "c1", "toolName": "subagent",
        "result": {"details": {"results": [{
            "agent": "implementer", "exitCode": 0,
            "usage": {"input": 100, "output": 10, "cacheRead": 1000,
                      "cacheWrite": 7, "turns": 3},
        }]}},
    })

    telemetry = read_telemetry(line)

    assert telemetry.child_context_processed == 1107
    assert telemetry.child_output_tokens == 10
    assert telemetry.child_turns == 3


def test_a_failed_delegation_is_not_counted_as_a_free_success():
    """Cycle 1 found a delegation whose result was the string 'Tool
    subagent not found'. It carries no usage, and counting it as a
    zero-cost delegation would make a broken arm look efficient."""
    line = json.dumps({
        "type": "tool_execution_end", "toolCallId": "c1", "toolName": "subagent",
        "isError": True,
        "result": {"content": [{"type": "text", "text": "Tool subagent not found"}],
                   "details": {}},
    })

    telemetry = read_telemetry(line)

    assert telemetry.delegations == ()
    assert telemetry.child_context_processed == 0


def test_two_delegations_in_one_run_are_both_counted():
    """Cycle 2's runs 4 and 10 made three delegations each; run 4's
    children totalled 128 turns."""
    def end(call_id, turns):
        return json.dumps({
            "type": "tool_execution_end", "toolCallId": call_id,
            "toolName": "subagent",
            "result": {"details": {"results": [{
                "agent": "implementer", "exitCode": 0,
                "usage": {"input": 5, "output": 1, "cacheRead": 0,
                          "cacheWrite": 0, "turns": turns},
            }]}},
        })

    telemetry = read_telemetry(end("c1", 4) + "\n" + end("c2", 6))

    assert len(telemetry.delegations) == 2
    assert telemetry.child_turns == 10


def test_a_delegation_with_no_usage_payload_is_skipped_not_crashed():
    """Pi's payload shape is not ours and may change. An end event with a
    results list but no usage must not raise."""
    line = json.dumps({
        "type": "tool_execution_end", "toolCallId": "c1", "toolName": "subagent",
        "result": {"details": {"results": [{"agent": "implementer"}]}},
    })

    telemetry = read_telemetry(line)

    assert telemetry.child_context_processed == 0
```

Add `import json` to the test module if absent.

- [ ] **Step 2: Run them to verify they fail**

Run: `uv run pytest tests/test_telemetry.py -q`
Expected: FAIL — `AttributeError: 'RunTelemetry' object has no attribute 'delegations'`.

- [ ] **Step 3: Add the `Delegation` dataclass**

```python
@dataclass(frozen=True)
class Delegation:
    """One completed child, as *the parent's stream* reports it.

    Pi's shipped subagent extension aggregates the child's `message_end`
    usage and surfaces it in the parent's `tool_execution_end` result. So
    this is the child's own accounting, read second-hand -- not this
    project's count.

    **`turns` is therefore not measured the same way as
    `RunTelemetry.turns`.** Ours is one per `turn_end` event in a stream we
    parsed; this is a number the extension computed from a stream we never
    saw. Both are called turns. If they ever need to be strictly
    comparable, the child's raw stream would have to be captured
    separately, which is the still-deferred parent/child attribution work.
    """

    agent: str
    turns: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    exit_code: int | None

    @property
    def context_processed(self) -> int:
        return self.input_tokens + self.cache_read_tokens + self.cache_write_tokens
```

- [ ] **Step 4: Parse it**

In `read_telemetry`, add `delegations: list[Delegation] = []` and a branch
inside the existing `tool_execution_end` case — after `ended[...]` is
recorded, so the `ToolCall` bookkeeping is unchanged:

```python
                if event.get("toolName") == "subagent" and not event.get("isError"):
                    details = event.get("result", {}).get("details") or {}
                    for result in details.get("results") or []:
                        usage = result.get("usage")
                        if not isinstance(usage, dict):
                            continue
                        delegations.append(
                            Delegation(
                                agent=result.get("agent", "<unknown>"),
                                turns=usage.get("turns", 0),
                                input_tokens=usage.get("input", 0),
                                output_tokens=usage.get("output", 0)
                                + usage.get("reasoning", 0),
                                cache_read_tokens=usage.get("cacheRead", 0),
                                cache_write_tokens=usage.get("cacheWrite", 0),
                                exit_code=result.get("exitCode"),
                            )
                        )
```

Pass `delegations=tuple(delegations)` in the `RunTelemetry(...)` construction.

- [ ] **Step 5: Add the field and derived properties**

On `RunTelemetry`, add `delegations: tuple[Delegation, ...]` and:

```python
    @property
    def child_turns(self) -> int:
        return sum(d.turns for d in self.delegations)

    @property
    def child_output_tokens(self) -> int:
        return sum(d.output_tokens for d in self.delegations)

    @property
    def child_context_processed(self) -> int:
        return sum(d.context_processed for d in self.delegations)

    @property
    def total_turns(self) -> int:
        return self.turns + self.child_turns

    @property
    def total_output_tokens(self) -> int:
        return self.output_tokens + self.child_output_tokens

    @property
    def total_context_processed(self) -> int:
        return self.context_processed + self.child_context_processed
```

Extend the module docstring: existing fields are parent-only and keep their
meanings; `total_*` is what a delegated run actually cost; and cycle 2
published a wrong headline because that distinction did not exist.

- [ ] **Step 6: Run the tests**

Run: `uv run pytest tests/test_telemetry.py -q`
Expected: PASS.

Run: `uv run pytest -q`
Expected: PASS, no regressions.

- [ ] **Step 7: Mutation checks**

1. Drop `+ usage.get("cacheRead", 0)` from `context_processed`.
   Expected: `test_child_context_processed_includes_both_cache_fields` FAILS.
2. Remove `and not event.get("isError")`.
   Expected: `test_a_failed_delegation_is_not_counted_as_a_free_success` FAILS.
3. Make `total_turns` return `self.turns`.
   Expected: `test_totals_are_parent_plus_child` FAILS.

Revert each. Re-run: `uv run pytest -q`. Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add harness/telemetry.py tests/test_telemetry.py
git commit -m "feat(phase5): telemetry counts the delegated child"
```

---

### Task 3: The recompute script uses the instrument

**Files:**
- Modify: `docs/superpowers/research/2026-08-04-phase5-cycle2-recompute.py`
- Modify: `docs/superpowers/research/2026-08-04-phase5-cycle2-cost-answer.md`

- [ ] **Step 1: Delete the local `child_usage` helper**

Replace its call sites with `read_telemetry`'s `child_*` and `total_*`
properties. The script keeps `delegation()`, which measures concurrency —
that is a different question and telemetry does not answer it.

- [ ] **Step 2: Re-run and diff the numbers against the published record**

```bash
PYTHONPATH=. uv run python \
    docs/superpowers/research/2026-08-04-phase5-cycle2-recompute.py
```

Every figure must match the corrected record exactly: total context median
132,218, ratio 8.11×, total turns median 22, total output median 2,399. **A
mismatch means the instrument and the workaround disagree, and that is a
finding to investigate, not a number to overwrite.**

- [ ] **Step 3: Note the provenance change in the record**

One line under the record's tables: the figures now come from
`harness.telemetry` rather than a helper local to the script, and are
unchanged.

- [ ] **Step 4: Gates and commit**

```bash
uv run pytest -q && uv run ruff check . && uv run pyrefly check
uv run sphinx-build -W -q -b html docs docs/_build/html
git add -A
git commit -m "refactor(phase5): cycle 2's recompute reads the instrument"
```

---

### Task 4: Close the cycle

- [ ] **Step 1: Set the Phase 5 cycle 3 row to `Done`** with `[spec]` and
  `[plan]` links and a concept-budget check (this cycle spends nothing:
  `Delegation` is a type name, not a concept a contributor must hold).

- [ ] **Step 2: Verify pipe-table contiguity**

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

- [ ] **Step 3: Gates, then commit**

---

## Self-Review

**Spec coverage.** `Delegation` → Task 2 steps 3–5. Successful-only → step 4's
`isError` guard, tested. `contextTokens`/`cost` ignored → not read anywhere.
Pinned `turns` preserved → `test_a_run_with_no_delegation_totals_to_its_parent`.
Real fixture → Task 1. Script refactor → Task 3. Definitional asymmetry →
`Delegation`'s docstring.

**Placeholder scan.** None; every test and code block is complete.

**Risk.** Task 3 step 2 is the one place this plan can surface a real problem:
if the instrument disagrees with the workaround the corrected record was built
from, the record is wrong a second time. Stated as a stop-and-investigate
rather than a formality.
