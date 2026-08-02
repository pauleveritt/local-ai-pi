# Phase 2, Cycle 1 — Telemetry reader

**Phase:** 2 — Measure the cost of orchestration
**Status:** design, awaiting plan

## Why this cycle

Phase 1 measured one thing: whether generated code can be *trusted*. It says
nothing about speed, cost, or effort. There is no claim to name in that
dimension yet because there is no instrument that could measure one.

The `ROADMAP.md` Backlog entry for telemetry sets a gate: build it "only
after a suite author has named a claim they need those measurements to
support." **This cycle satisfies that gate rather than waiving it.** The named
claim, from the owner and grounded in prior evidence:

> Getting an orchestrator to write handoff packets for an implementer is a
> delicate balance. It may consume more tokens than the orchestrator simply
> doing the work itself.

That is a measurable claim, and Phase 2's third step (incremental orchestrator
work) is where it gets tested. This cycle builds the instrument that makes the
test possible — the same instrument-before-experiment pattern cycles 3–7
followed, building the entire grading apparatus before any model ran once.

Two prior-effort documents motivate the metric choices and are cited
throughout:

- `dlai-local-ai-course/docs/lesson-metrics-report.md` — a ten-lesson chart
  comparing orchestration strategies.
- `local-ai-gemma/LESSONS.md` — qualitative findings on packet construction.

## What this cycle is not

- **Not wired into anything.** `read_telemetry` is a pure function over a
  string. `runner.py`, `checkpoint.py`, and the batch are untouched. Nothing
  consumes the result yet.
- **Not parent/child attribution.** The metrics report's central analytical
  device is a parent/children/total split, because "the clearest delegation
  effect is a change in *where* context accumulates." Today `pi` is invoked
  once, bare, with no delegation — there is no split to attribute. Building
  it now would be machinery ahead of its contract.
- **Not wall time, cost, or a report format.** See "Deliberate exclusions."

## Interface

```python
# harness/telemetry.py

@dataclass(frozen=True)
class ToolCall:
    name: str
    is_error: bool | None   # None = started but never finished

@dataclass(frozen=True)
class RunTelemetry:
    turns: int
    tool_calls: tuple[ToolCall, ...]
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    complete: bool          # the run finished normally; see "Incomplete runs"

    @property
    def context_processed(self) -> int:
        return self.input_tokens + self.cache_read_tokens + self.cache_write_tokens


def read_telemetry(pi_stdout: str) -> RunTelemetry: ...
```

## Behavior

Input is the raw `pi --mode json` JSONL text that `RunResult.pi_stdout`
already captures. No new invocation shape, no new flags.

- **`turns`** — the count of `turn_end` events. This definition is
  load-bearing and must not drift; see "Pinning the turn definition."
- **`tool_calls`** — `tool_execution_start` (carrying `toolName`) merged with
  `tool_execution_end` (carrying `isError`) by `toolCallId`, in start order.
- **Token fields** — summed across every `turn_end` event's
  `message.usage.{input,output,cacheRead,cacheWrite}`, with `usage.reasoning`
  folded into `output_tokens` (see "Deliberate exclusions"). Usage is
  **per-turn, not cumulative**; verified across all 16 runs of the real batch, where
  per-turn input is non-monotonic (run 1: 1751, 1778, 1115, 1344, 480, 600),
  which cumulative accounting cannot produce. Reading only the final event
  would undercount badly.
- **Malformed lines are skipped, not raised** — matching the truncation
  tolerance `harness/checkpoint.py` already established. A process killed
  mid-write leaves a partial final line.

### Incomplete runs

A run killed by cycle 12's timeout handling produces two kinds of truncation,
and reporting them as if they were normal would misrepresent exactly the case
that hardening exists for:

1. **A tool killed mid-execution** leaves `tool_execution_start` with no
   matching end. Its `is_error` is `None` — *unknown*, not `False`. Defaulting
   to `False` would report a hung tool as a successful call.
2. **A turn killed mid-flight** emits no `turn_end`, so its tokens are absent
   entirely. Nothing can recover them.

`complete` is `True` only when both hold: the stream contains an `agent_end`
event, and every `tool_execution_start` has a matching end. A killed process
emits neither signal. (Observed event order in a healthy run ends
`agent_end`, then `agent_settled`; `agent_end` is the semantic "agent
finished" marker and is what the reader checks.)

**When `complete` is `False`, every count in the result is a lower bound.**
This is stated in the module docstring, not left for a reader to infer.

## Metric choices

### `context_processed` is the headline, and cache reads are why

`lesson-metrics-report.md` defines its headline measure as
`input + cacheRead + cacheWrite`, called *context processed* — "a cumulative
workload measure, not a context window size." Every row of its ten-lesson
comparison rests on it.

The obvious objection is that cache reads might be a fixed system-prompt
prefix — constant across conditions, and therefore noise rather than signal.
**Checked against the real batch, and it is false:** turn-1 `cacheRead` is
**0 in all 16 runs**. There is no cross-run or system-prefix cache hit on this
server. Cache reads are purely within-run conversation-prefix reuse,
accumulating in 1024-token blocks and tracking turn count. Across runs under
*identical* conditions they varied 5,120–16,384 — **39.4% to 57.4% of context
processed.**

Excluding them would hide 40–57% of prefill mass and systematically flatter
many-turn strategies. That is precisely the bias that would corrupt a handoff
comparison, which is the only reason this instrument exists.

**Scope caveat, to be stated wherever the number is reported:**
`context_processed` is a *workload* measure. It is not latency and not cost.
On a local model metering $0.00, the handoff decision will ultimately also
care about wall-clock, where cached tokens are nearly free.

### Tool names measure packet quality

`LESSONS.md` §5 observes that without external orientation, small models
"grep, guess, and use trial and error for import paths, naming, registration
wiring." Counting exploratory tool calls therefore measures directly whether a
handoff packet oriented the implementer. Real run 1 shows `{bash: 1,
write: 4}` — no `grep`, no `find`: a well-oriented run.

`is_error` earns its place on evidence: **14 of 103 tool calls across the
all-accepted batch were errors**, all `bash`. Error churn is real signal even
when every run passes.

### Pinning the turn definition

`lesson-metrics-report.md` closes by warning that Lesson 12 counted assistant
messages while Lesson 11 used a session-level field, producing 45 turns versus
6 — uncomparable, and it poisoned a trend the report had to disclaim.

**A turn is one `turn_end` event.** This is recorded in the module docstring
as load-bearing. Any future change to it invalidates comparison against every
number this instrument has produced.

## Deliberate exclusions

Per the owner's Phase 2 guidance — *aim low, work in small steps, leave stuff
out until needed* — each of these is omitted with a reason and a known path
back.

| Excluded | Why |
|---|---|
| `totalTokens` | Verified pure arithmetic: exactly `input + output + cacheRead + cacheWrite + reasoning`, with zero violations across every `turn_end` in all 16 runs. Derivable, never stored. |
| `reasoning` (as its own field) | 0 in all 16 runs; gemma-4-12B cannot produce it, so a separate field would be dead weight today. **But it is not dropped:** reasoning tokens are generated output, so the reader folds them into `output_tokens`. A future reasoning-capable model's tokens therefore cannot vanish silently, and no assertion has to fire to prevent it. |
| Tool-call `args` / `result` | Real simplification, not false economy: the `toolCallId` correlation machinery is identical either way, so dropping them removes interface surface at zero cost. `args` can hold whole file contents. Raw stdout retains everything. |
| Wall time | Epoch-ms timestamps are already in the stream (`message_start`/`message_end`), so deferring the *field* loses no *data* — it is derivable later from the same stored text. Expect step 3 to want it, given `LESSONS.md`'s finding that throughput fell from ~60 tokens/sec at turn zero as context grew. |
| Cost | Every field is `0` on a local model. Meaningless here. |
| Parent/child attribution | Unmeasurable today; see "What this cycle is not." |

## A dependency worth naming

Telemetry is a **derived, recomputable view** — never load-bearing storage.
That is only true because checkpoints retain raw `pi_stdout`. If anyone later
proposes trimming stdout from checkpoint records to save space, every
telemetry number ever computed becomes unreproducible. This constraint is
recorded here because it is invisible from the checkpoint code itself.

## Testing

**Real fixture, already preserved.** `tests/fixtures/pi-run-0.82.0.jsonl` is
one genuine run's stdout, extracted from the n=16 batch checkpoint after
verifying its SHA-256 against the committed evidence record. Its known-good
values are recorded in `tests/fixtures/README.md`: 6 turns; 5 tool calls
(`bash` ×1, `write` ×4), all matched, none errored; input 7,068 / output 933 /
cacheRead 6,144 / cacheWrite 0; context processed 13,212.

Testing against real captured output rather than a synthetic stream is not
fussiness. The pre-restructure `telemetry.py` documented, for pi 0.81.1, that
`--mode json` carried no token usage and that `isError` was a string. **Both
are false in 0.82.0** — verified against this fixture: usage is present on
`turn_end`, and `isError` is a real `bool`. A synthetic fixture tests a parser
against its author's belief about the schema, and that belief is exactly what
went stale before.

**Synthetic fixtures, built inline, for what real data cannot reach.** All 123
lines of the real capture are valid JSON and all 5 tool calls matched, so it
cannot exercise:

- A malformed final line → skipped, not raised.
- A `tool_execution_start` with no matching end → `is_error is None` and
  `complete is False`.
- A truncated stream with no `turn_end` at all → zero counts, `complete`
  False, no exception.

**Non-vacuity check.** The incomplete-run tests must assert on `is_error is
None` and `complete is False` specifically — not merely that parsing didn't
raise. A parser that silently dropped unmatched starts would also "not raise,"
and would be wrong in exactly the way that matters.

## Concept budget

This cycle spends four terms, the largest single-cycle spend so far, which is
worth stating plainly rather than slipping through:

| Term | Status |
|---|---|
| `telemetry` | New. Structured measurements derived from a run's captured output. |
| `turn` | Borrowed from pi's own vocabulary, not coined. Pinned to `turn_end`. |
| `tool call` | Borrowed from pi's own vocabulary, not coined. |
| `context processed` | New, but adopted from `lesson-metrics-report.md` rather than invented — aligning vocabulary with the prior evidence base buys comparability with its chart. |

All four go in `ROADMAP.md`'s table at cycle close.

## Non-goals recap

Wiring into `RunResult`, parent/child attribution, wall time, cost, and any
report or aggregation format are all deferred. This cycle produces one pure
function and its proof.
