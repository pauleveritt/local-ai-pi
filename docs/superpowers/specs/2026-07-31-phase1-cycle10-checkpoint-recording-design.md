# Cycle 10 — Checkpoint recording

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine
**Status:** implemented — cycle marked Done in `ROADMAP.md`

> *Cycle numbers herein predate the 2026-07-31 harvest re-plan: the n=16
> batch this document calls "cycle 11" is now cycle 12. Left as-authored;
> `ROADMAP.md` is authoritative.*

## Why this cycle

`BRIEF.md` defines Phase 1's milestone as "One AgentClinic Phase 1 run,
hermetically graded, **recorded to a checkpoint**. Then n=16 reproducing
~15/16." Cycles 1–9 built and proved the run itself (a hermetic,
allowlist-graded `RunResult`); nothing yet persists one. Cycle 11's n=16
batch needs to know how many runs are already done and resume the
remainder — this cycle builds the artifact that makes that possible,
before the batch loop that consumes it exists, matching the pattern every
cycle since 3 has followed.

## What this cycle is not

- Not the batch loop itself. `append_checkpoint`/`load_checkpoint` are
  standalone functions; nothing in this cycle calls
  `run_agentclinic_phase1()` in a loop, or wires checkpoint recording into
  the runner at all. That's cycle 11's job — the same way cycle 7 built
  `check_model_server_alive` without wiring it into anything, and cycle 8
  did the wiring.
- Not telemetry (turn counts, tool calls, token usage, context window).
  Phase 1 is accept/reject only, per `BRIEF.md`'s own milestone
  definition — the old branch's `telemetry.py` is an explicitly rejected
  transplant candidate. `RunResult.pi_stdout` is still captured and
  persisted whole, so nothing here forecloses extracting such numbers
  post-hoc from a checkpoint later, but this cycle doesn't compute or
  store them.
- Not a general-purpose checkpoint/resume library. The record is exactly
  a serialized `RunResult`; the resume semantics are exactly "count valid
  lines." No configurability beyond that is being built ahead of a need.

## Interface

```python
# harness/checkpoint.py

def append_checkpoint(path: Path, result: RunResult) -> None:
    ...

def load_checkpoint(path: Path) -> list[RunResult]:
    ...
```

- New module, following this project's one-file-one-responsibility
  pattern (`liveness.py`, `workspace.py`, `grading.py`, `runner.py`).
- `path` is caller-supplied on every call, no default — there's no
  established per-project checkpoint location yet, and inventing one now
  would be a hardcode ahead of the need that names it (cycle 11).
- Format: JSONL — one JSON object per line, one line per completed run.
  `RunResult` and its nested `GradeResult` are both frozen dataclasses
  with only `str`/`int`/`bool`/`tuple` fields, so `dataclasses.asdict()`
  on write and keyword-unpacking on read round-trip cleanly. `tuple`
  fields (`GradeResult.refused_config`) come back from JSON as `list` and
  are cast back to `tuple` on load.

## Resume semantics

No explicit run-index field. The Nth valid line in the file *is* run N —
the file's append-only nature already guarantees order, so
`len(load_checkpoint(path))` tells a future caller how many runs are
done. This was a real design choice, not the only option: an explicit
`run_index` field would be more robust to manual edits or concatenated
files, but nothing has named that as a requirement yet.

## Truncation tolerance, precisely scoped

`load_checkpoint` parses each line as JSON:

- If the **last** line fails to parse, it's dropped silently. This is the
  specific, well-understood case `BRIEF.md` names — a process that died
  mid-write, leaving a partial JSON fragment as the final line.
- If any **other** line fails to parse, `load_checkpoint` raises instead.
  A corrupted line that isn't the last one is a different and more
  suspicious problem than an interrupted append, and silently dropping it
  would hide real corruption rather than surviving an expected failure
  mode.

Dropping a malformed final line means `len(load_checkpoint(path))` counts
*completed* runs only — the interrupted run is intentionally re-run, not
counted as done. That is the correct resume semantic ("the Nth valid line
is run N" only holds for valid lines), not a gap.

## Resuming after a truncated write

`load_checkpoint` tolerating a truncated final line is not enough on its
own — a caller who resumes after that (cycle 11: load, discover N runs
done, run N+1, append it) writes into a file whose last physical line is
still the dangling fragment `load_checkpoint` just skipped past, because
skipping it during a read does not remove it from disk. `append_checkpoint`
opening in append mode and writing straight to the end would then
concatenate the new record directly onto that fragment — producing one
merged malformed line, which either corrupts every future read (if a
later append makes it a non-final line, which now raises) or silently
discards the run that was just completed (if it stays final). This would
make the resume flow that motivates this cycle actively unsafe to use
more than once.

So `append_checkpoint` is responsible for leaving the file well-formed
before it writes, not just for writing correctly itself: before
appending, if the file exists and doesn't end in a newline, it truncates
the file back to the last complete line first, discarding the dangling
fragment, then appends the new record cleanly. This makes
`append_checkpoint` idempotent with respect to a prior interrupted write,
and keeps every file `load_checkpoint` is ever asked to read in the
"zero or more complete lines, optionally one incomplete final line" shape
its truncation tolerance already assumes.

## Testing

Fully hermetic — no model, no `pi`, no HTTP. Construct a `RunResult` (and
its nested `GradeResult`) by hand with representative field values,
round-trip it through `append_checkpoint` then `load_checkpoint`, and
assert equality with the original. Append a second record and confirm
both come back in order.

The truncation test writes one complete record, then appends a second
line that is a deliberately truncated JSON fragment (e.g. cut off
mid-object, not a full line) — simulating a process that died while
writing. `load_checkpoint` must return exactly the one complete record,
not raise.

A separate, non-vacuous control: corrupt a **non-final** line instead
(e.g. two complete records with the first one truncated) and assert
`load_checkpoint` raises. Without this control, the truncation test alone
couldn't distinguish "correctly tolerates only the last line" from "just
skips anything that fails to parse" — the same category of proof cycles 4
and 9 required for their own attack-resistance claims.

A third test proves the resume flow actually survives more than one
cycle: given a file left with a dangling truncated final line (the same
shape the truncation test produces), calling `append_checkpoint` again
must result in a file that reads back as the earlier complete record
followed by the newly-appended one — not a merged, corrupted line. This
is the test that would have caught this cycle's original gap: a naive
`append_checkpoint` that just opens in append mode and writes.

## Non-goals recap

The batch/resume loop, telemetry capture, and configurable checkpoint
formats or locations are all explicitly deferred, per the design
discussion above.
