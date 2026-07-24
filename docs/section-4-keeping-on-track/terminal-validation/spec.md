# Terminal Validation — Chapter Spec

**Date**: 2026-07-24
**Status**: approved in brainstorming, awaiting implementation
**Parent**: [Section IV index](../index.md)

## Purpose

The first evidence-backed chapter of Section IV. It addresses the most
frequent remaining failure in the SP2 post-tuning baseline: validation
command drift, which caused 2 of 4 post-tuning failures (2/8 overall).

The SP2 deep-dive found that the implementer narrows the packet's
`uv run pytest -q` to `uv run pytest -q tests/test_app.py`. The narrower command
passes in isolation but fails when collected with the full suite. The
implementer isn't lying — it ran a command that passed. The harness's
independent full-suite pytest correctly fails the run.

## The reframe

**The harness was never fooled.** Its independent full-suite pytest correctly
failed those two runs. What broke was the implementer's *stop condition*: the
narrowed command gave it false confidence, so it declared done and stopped.

This chapter is not defending the oracle (that is already independent). It is
making the child's stop-decision run against the true oracle. The chapter
states this explicitly, because it is the difference between "security" and
"steering."

This is LESSONS.md #1 ("remove decisions from the model, not add another
prompt rule") applied to the validation command specifically.

## Four levels, with evidence-based scope judgment

### Level 1 — prompt line (included, taught as insufficient)

Include the prompt line: "Run exactly the validation command in the packet."
But teach that it is insufficient, with receipts. LESSONS.md #16 records that
children re-ran pytest despite terminal-validation instructions, and concludes
bluntly: "terminal-validation wording alone is insufficient." A chapter that
landed on "add a prompt rule" would contradict the lesson catalog the course
cites.

The prompt line is the demonstrably-weak layer. It is included because a
honest chapter shows the reader what doesn't work before showing what does.

### Level 2 — the un-narrowable wrapper (the real fix)

Make the command un-narrowable. This is LESSONS.md #1 applied directly, and it
needs no extension — so it respects the chapter's own boundary clause (quoted
below from the SP2 spec):

> **Boundary with SP3:** This chapter is scoped to **prompt/packet tuning
> only**. Mechanism-level fixes (turn cap, output cap, path guard, repeat
> breaker) are Part IV territory and are not built here. If a failure needs a
> mechanism-level fix to progress, it becomes the motivating evidence for the
> corresponding SP3 chapter.

Concretely: the workspace ships a zero-argument wrapper — `./validate.sh` runs
`uv run pytest -q` and errors if given any arguments. The packet's Validation
section says exactly that one token: `./validate.sh`.

There is nothing to narrow. `uv run pytest -q tests/test_app.py` was a
plausible reading of an editable string; `./validate.sh tests/test_app.py` is
a visible error. The model can still choose not to run it, or run raw pytest on
the side — but any raw pytest invocation is now unambiguous drift rather than a
plausible reading of the packet.

### Level 3 — harness drift detection (measurement, not enforcement)

Implement validation-command drift detection in the harness, as measurement,
not enforcement. This is one of the three measurement deliverables the SP2
spec promised and the deep-dive deferred (cleanup review's C3).

Detection alone is not a fix — the child still stops confident and wrong if
drift occurs. But without it, the chapter can only assert the wrapper works,
which violates the evidence policy. Detection turns the fix into an
evidence-gated claim: drift incidence pre/post (the deep-dive gives the before
— it caused 2 of 4 post-tuning failures).

Mechanically: parse the child's result text for the exact command it ran,
compare to the packet's validation command. Flag disagreement as drift. Record
per-delegation in the report.

### Level 4 — tool-policy enforcement (NOT this chapter)

Explicitly deferred to Section IV. Pi has no per-command bash allowlist —
`--tools` restricts which tools, not command strings — so real enforcement
means a `tool_call` extension hook that blocks bash not matching the packet's
command. That is a mechanism-level guardrail, which the SP2 spec's boundary
clause routes to Part IV.

This chapter's measured drift is the motivating evidence for that future
chapter. The chapter closes with a pointer that mechanical enforcement is
coming, motivated by this exact recorded failure. Do not spend the motivation
here — a Section IV enforcement chapter teaching a solved problem is
pedagogically empty.

## Metrics

**Drift incidence is primary.** It is per-delegation and mechanically countable
(packet says `./validate.sh`; any raw pytest call is drift). The expected
effect is ~X-of-N → ~0 — a claim small n can support.

**Success rate is secondary** and must carry the within-noise caveat. At n=4
(or even n=8), per-run success-rate deltas of ±1 run are within noise (Fisher
p≈1.0). The chapter leans on drift incidence for its primary claim; success
rate is descriptive, supporting context.

## Binding sequencing

This sequencing is binding given the current cleanup state. The order matters
because child session JSONL is not captured, so drift cannot be reliably
recomputed after the fact.

1. **Land the drift-detection metric in `harness/` before the shared re-run
   batch.** It is not there yet (no drift/validation-command code in
   `harness/` as of the n=4 switch commit). If the batch runs first, the
   pre-arm loses the chapter's primary metric.

2. **Run ONE re-run batch under the fixed harness, with no wrapper.** That
   single batch is both the corrected SP2 before-picture and this chapter's
   pre-arm — they are the same measurement (fixed harness, current
   packet/prompts, no wrapper). Do not run a separate second pre-batch; two
   same-config batches at small n will disagree and create a "which pre is
   real" problem.

3. **Run this batch at n=8, overriding the new n=4 default.** The n=4 default
   is fine for iteration cycles, but this batch is the most-reused measurement
   in the project — every Section IV guardrail chapter compares against it. If
   it stays n=4, the chapter must lean entirely on drift incidence and treat
   success rate as descriptive only.

4. **Then land the wrapper and run the post-arm only.**

5. **Chapter authoring** (wrapper script, packet edit, prose) can proceed in
   parallel now — it touches nothing in `harness/`.

## Deliverables

- `examples/agentclinic/validate.sh` — zero-arg wrapper, errors if given args
- Packet format change: Validation section says `./validate.sh`
- `harness/` drift-detection code (parses child result, compares to packet)
- Dated research report with pre/post drift incidence + success rate
- Chapter narrative (`index.md`) following the chapter-structure policy

## Out of scope

- Tool-policy enforcement (`tool_call` hook) — Section IV, motivated by this
  chapter's measured drift
- Capturing child session JSONL (separate telemetry-gap work; would make drift
  detection direct rather than inferred from result text, but is not required
  for this chapter's claim)
- Re-running SP1 (audited as sound in the cleanup review)

## Source material

- SP2 deep-dive: `docs/section-3-sdd/research/2026-07-24-sp2-deep-dive.md`
  (the 2/8 drift finding, the implementer-vs-harness command discrepancy)
- SP2 spec boundary clause: `docs/section-3-sdd/spec.md` (prompt/packet tuning
  only; mechanism-level fixes are Part IV)
- Cleanup spec C3: `docs/section-3-sdd/cleanup/spec.md` (the deferred
  measurement deliverables this chapter pays back)
- LESSONS.md #1 ("remove decisions from the model"), #16 ("terminal-validation
  wording alone is insufficient")
