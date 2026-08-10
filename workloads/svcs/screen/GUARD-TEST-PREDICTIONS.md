# Live guard test — thresholds, committed before the run

Experiment A cleared a bar that appears nowhere in this repository before its
own results commit. That is why nothing from it can graduate, and it is the
mistake this file exists to not repeat. **Nothing below may be edited after the
first attempt lands.**

## What is being tested

Replay over recorded call streams shows the shipped loop breaker
(`.pi/extensions/loop-breaker.ts`) firing on both of this phase's identical-call
retry loops — 44 blocks from call 7, and 46 from call 14 — and on neither of two
*accepted* runs drawn from the same cells, one of them 22 calls long.

Replay cannot answer the only question that matters for admission: **after the
block, does the model do something else?** A guard that refuses a call and
leaves the model repeating a near-identical variant has moved the failure, not
fixed it. Rule 7 admits a component when it catches a named failure *and*
survives false-rejection tests, and only a live run can supply the first half.

## Cells

Arm: `workloads/svcs/cells/gemma12b-probe-guarded.toml`, verified against the
live configuration before any call. It differs from `gemma12b-probe` in exactly
one respect — the extension set, hence a distinct `extensions_sha256`.

Two comparisons, both against measurements already banked:

| cell | n | banked comparison |
|---|---|---|
| guarded, `registry-iter`, draft contract | 6 | unguarded same arm: 5/6 accepted, 1 retry-loop death |
| guarded, `magicmock-factory`, brief-only at 8192 | 4 | unguarded same arm: 1/6 accepted, 5/6 `length` deaths |

`magicmock-factory` runs at **8192**, matching the noise-floor cell rather than
Experiment B's 32768, so the guard is the only variable against a 6-replicate
baseline instead of a 1-run one.

## Prespecified thresholds

**Primary — the failure the guard was replayed against must stop occurring.**
Across all 10 runs, **zero may die in an identical-call retry loop** (a run
whose transcript contains ≥5 byte-identical consecutive tool-call argument
sets). One such death means the guard fires and the model persists anyway, and
the loop breaker is not admitted on this evidence.

**Secondary — the guard must not cost accepted work.** `registry-iter` guarded
must reach **≥4/6 accepted**. The unguarded arm was 5/6; a drop to ≤3/6 is a
false-rejection signal and blocks admission regardless of the primary result.

**Exploratory, no threshold, reported either way.** Whether
`magicmock-factory` accepts more often. Its failures are mostly runaway
generation rather than retry loops, so the guard is not expected to convert
them; a rise would be interesting and unexplained, and is not being predicted.

## What each outcome means

- **Zero loop deaths, `registry-iter` ≥4/6** — the guard is admitted for this
  failure class on this cohort. Narrow, and the first component in the phase to
  clear rule 7's bar with live evidence rather than replay alone.
- **Zero loop deaths, `registry-iter` ≤3/6** — the guard works and costs
  accepted work. Not admitted; the block message likely needs to steer rather
  than merely refuse.
- **Any loop death** — refusing the call is insufficient. The finding is that
  blocking alone does not break this loop, which is more useful than an
  admission and should redirect the guard's design.

## Non-predictions

Wall clock and token cost. A blocked call is cheap and the runs are short; the
arm is not designed to measure either, and any difference would be confounded
by generation-length variance already known to be large in this cell.

---

## Correction, after the run — the test was aimed at the wrong half

**Do not read the 2/6 loop deaths as "the guard does not work."** The
`registry-iter` loop is structurally invisible to a `tool_call` guard, so this
half of the test could only ever have produced that result.

Pi validates tool arguments at `agent-loop.js:404` and invokes `beforeToolCall`
on the next line, inside the same `try`. A call that fails schema validation
throws one line above every `tool_call` hook. Of the 57 calls in the recorded
`registry-iter` loop, **52 are schema-validation failures and only 5 reach the
hook** — there is no window in which five identical calls are visible to it.

The replay that motivated this test said otherwise because its fixture was
extracted from `tool_execution_start`, which records attempts that never
reached the hook. That fixture is corrected in the main repo (`7ca49cb`).

**What was not tested:** the `magicmock-factory` half of this plan, which was
prespecified above and never run. Those anchor-mismatch retries are
schema-valid — all 60 reach the hook, and the guard fires on them 46 times from
call 14 in corrected replay. That is the half capable of answering the question
this test was written to ask, and it remains open.

**The thresholds above stand unchanged for that half.** They are not being
revised after seeing a result; the primary and secondary bars apply to the
`magicmock-factory` runs exactly as written.

**What this test did establish**, and it is worth more than the intended
result: a `tool_call` guard cannot address malformed-call retry loops at all.
That failure class needs a different mechanism — `tool_result`, or a
turn-level check — and no amount of tuning the loop breaker will reach it.

---

## The magicmock half, run — and four corrections to the correction above

External review caught three errors in the correction I appended, and a fourth
went stale while I wrote it. All four are verified against Pi 0.84.1's source
and the run records.

### Results (4 replicates, guarded cell, 8192)

| run | calls | reach hook | longest identical | guard blocks | outcome |
|---|---|---|---|---|---|
| r1 | 10 | 10 | 2 | 0 | no-progress |
| r2 | 13 | 13 | 2 | 0 | tests-vanished |
| r3 | 23 | 23 | 2 | 0 | **accepted** |
| r4 | 23 | 23 | 4 | **4** | tests-vanished, delta −30 |

**The guard fired live for the first time in this project** — r4, four blocks.
The mechanism works on schema-valid repeated calls, as corrected replay
predicted. And **r4 still failed, badly**: 101 preservation nodes missing, gap
−3000%. Blocking the repeat did not produce recovery; the model went on to
damage the repository. "The guard breaks the loop" and "the guard helps" are
different claims and only the first has any support.

Acceptance was 1/4 against an unguarded baseline of 1/6 at this cap. That
comparison was explicitly exploratory with no threshold, and 1/4 versus 1/6 is
not a difference.

### Correction 1 — the intervention path I named was wrong

I wrote that malformed-call loops "need `tool_result`, or a turn-level check."
The first half is false. A validation failure returns `kind: "immediate"`
(`agent-loop.js:445`), which skips `executePreparedToolCall` **and**
`finalizeExecutedToolCall` — and `afterToolCall`, which supplies the
`tool_result` event, lives inside the latter at line 487. So `tool_result`
cannot see these calls either.

What remains observable: `tool_execution_start`, `tool_execution_end`, and the
synthesized tool-result `message_end`. An extension-level response must cache
arguments at start, recognise validation failures at end, correlate repeats
itself, and intervene through an injected message, `turn_end`, or abort. **A
true pre-validation block requires a change to Pi core.**

### Correction 2 — "could only produce not admitted" was too strong

The model might by chance have avoided malformed loops entirely. What was
structurally impossible was *attributing any improvement to the guard*, which
had no causal access to those calls. The claim is about attribution, not about
the outcome being forced.

### Correction 3 — the thresholds do not transfer unchanged

Appending a correction preserved the text but implied the bars carry over
intact. They do not. The primary bar was "zero loop deaths across **all 10**
runs" and had already failed. The secondary was `registry-iter`-only and passed
at 4/6. Magicmock acceptance was explicitly exploratory with no threshold.

So **"not admitted" stands as the outcome of the flawed combined protocol.**
What is retracted is "the guard failed." These four runs can support a narrower
claim about schema-valid retry loops; they cannot retroactively make the
original combined experiment pass.

### Correction 4 — "was never run" was stale on arrival

It was already running when I wrote it.

### What the guard has and has not earned

Earned: it fires live on schema-valid repeated calls, and it does not fire on
runs that succeed (r1–r3, and the two accepted-run fixtures).

Not earned: any claim that it improves outcomes. One live activation, in a run
that then destroyed 101 test nodes, is not admission evidence. Under rule 7 the
loop breaker remains **unadmitted**, and the honest next question is not
"does it fire" but "does the model do anything better after it fires" — which
r4 is one datapoint against.
