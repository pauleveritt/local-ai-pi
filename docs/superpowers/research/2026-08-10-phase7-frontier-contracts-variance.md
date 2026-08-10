# Phase 7, the two days after the reset — frontier table, noise floor, contracts, and the cap

**Date:** 2026-08-10
**Status:** research record. Everything here is pilot data under roadmap rule 8 —
it selects the cohort and the margins; none of it is confirmatory evidence.
**Code:** worktree `phase7-workload`, `fec4984..055aa2a`
**Plan:** [`../plans/2026-08-09-phase7-workload-first-roadmap.md`](../plans/2026-08-09-phase7-workload-first-roadmap.md)

---

## The one thing to read if you read nothing else

The best-looking result of the phase — "the contract fixes registry-iter,
5/6 accepted against a 0/8 brief-only baseline" — is real as a number and
wrong as recorded. The contract at
`workloads/svcs/overnight/drafts/registry-iter.md` contains the complete
solution verbatim: a fenced code block with the exact `__iter__` method,
docstring included, and the exact import edit, labeled "the only code
change required." All five accepted patches reproduce the **contract's**
docstring word for word — not the reference patch's, which differs — and
three of the five are byte-identical post-images. What Experiment A
measured is a pipeline: a read-only 27B planner derived the full fix from
the base tree and brief (firewall held — 7 attempts to use write/execute
tools, all refused, 0/8 authoring transcripts showing a detected escape), and the 12B
executor transcribed it correctly 5 times in 6. That is a legitimate and
possibly product-shaped result. It is not the result the commit message
claims ("collapses the model onto one consistent implementation" — the
implementation was printed in the prompt).

The sixth false reading of the phase was the aggregate hiding task-level
bimodality. This is the seventh: a confirmatory-looking arm whose
mechanism is transcription, recorded as if it were reasoning.

## The frontier table, as it now stands

Brief-only, `read,bash,edit,write`, dev env, 8 tasks, n=1 per cell except
where noted. Pilot numbers.

| model | accepted | note |
|---|---|---|
| dsflash (deepseek-v4-flash) | 2/8 | Cycle 1 |
| gemma-4-12B @8192 | 3/8 | Cycle 3; variance now known (below) |
| gemma-4-12B @32768 | 2/8 | cap repair; async-cm-enter gap 0→1.0 but out-of-scope; local-pings flipped accepted→no-changes |
| qwen3.6-27B @32768 | 6/8 | n=1, variance unmeasured |

Contract arms: qwen27b 5/8 (the contract *cost* it flask-extensions to a
scope violation), gemma12b 2/8 — but see the stub-draft confound below.

## The noise floor (24 replicates, gemma @8192, brief-only)

| task | accepted | failure shape |
|---|---|---|
| flask-extensions | 6/6 | stable solve |
| local-pings | 4/6 | 2 no-progress |
| magicmock-factory | 1/6 | 4 no-progress, 1 damaged; 5/6 runs ended on `stopReason: length` |
| registry-iter | 0/6 | 5 tests-vanished, 1 damaged — destructive |

Aggregate 11/24 = 46%. Cycle 3's 3/8 = 38% at n=1 was a dangerous
near-match: four different per-task distributions, two of them degenerate
(a stable solve and a stable destructive failure), averaging to a number
that looks like a capability midpoint and isn't. Task-level replicate
counts are the only usable currency for this model.

## Experiment A — registry-iter under the draft contract

5/6 accepted, prespecified bar ≥3/6 cleared. All five accepts:
reference_overlap 0.556 (the overlap metric is the share of added
production lines present in the reference — the accepts' docstrings came
from the contract, not the reference, hence <1.0). Accepts ran 40–49
seconds each. Brief-only baseline for this task: 0/8 across every cell in
the phase (0/6 variance, Cycle 3, 32k re-run) — verified per-record.

**The miss (r2) was misrecorded and is the load-bearing detail.** The
results commit describes it as "added the import, then stopped — not
timed out, not budget-exhausted, a milder failure." The transcript shows
53 edit calls of which one arg-set repeats **49 times byte-identically**,
each failing schema validation (`path` placed inside the edit entries
instead of at the top level), until the run died on a `length` stop at
1334.7s. The retried call contained the complete fix. The summary fields
(`budget_exhausted: none`, `model_timed_out: false`) are true and are
exactly what produced the false reading — the raw transcript was the only
honest witness. r2's overlap is 1.0, which also kills any temptation to
read overlap as progress: its single added line (the import) exists in
the reference.

**Prespecification gap:** Experiment B's bar is committed in its driver's
docstring before results. Experiment A's ≥3/6 appears nowhere in the repo
before its own results commit. It may have been agreed in conversation;
the repo cannot attest it, so this result must not be described as
having cleared a pre-registered bar.

## Experiment B — magicmock-factory at 32768

3/8 accepted — exactly on the prespecified ≤3/8 reject threshold, so
cap-runaway is **not** confirmed as the whole mechanism. But the
composition under the number moved, and that is the finding:

- Last-message `length` deaths: 5/6 at 8192 → 2/8 at 32768 (re-derived
  from raw transcripts, not summary fields).
- Oracle gap closed: 1/6 at 8192 → 5/8 at 32768.
- The difference was eaten by a new failure: close the gap, then keep
  writing throwaway diagnostic files (`check_mock.py`,
  `reproduce_issue.py`, `repro.py`, `test_mock_await.py` — recurring
  across three replicates) until scope rejection catches it (r4: five
  scratch files; r7: two).
- r5 is accepted **only** because the 1800s wall clock killed the process
  with the fix already on disk (`model_timed_out: true`, 1800.02s). Had
  it run longer it plausibly joins the scratch-file group.
- r2 burned its 60-turn budget on 54 edit calls — 51 of them a
  byte-identical anchor-mismatch retry.

Raising the cap fixed the failure it was aimed at and exposed the one
hiding behind it. The accept-rate barely moved; the mechanism moved a lot.

## Guards: one demonstrated failure is already covered

Both stuck runs (Exp A r2, Exp B r2) are identical-call retry loops —
the exact trigger of the already-shipped loop-breaker
(the tracked `.pi/extensions/loop-breaker.ts`: 5 identical calls in a
20-call window, hard block). Replaying the shipped artifact over the two
recorded call streams, no model involved:

| run | calls | blocked | first block |
|---|---|---|---|
| Exp A r2 | 57 | 44 | call 7 |
| Exp B r2 | 60 | 46 | call 14 |

So guard candidate 1 (fresh-read-after-failed-edits) needs no new
construction — the existing guard fires on both demonstrated failures.
The open question is behavioral, not mechanical: does the model recover
after the block message? That takes one small prespecified live run.
Candidate 2 (stop after the fix is written) has three transcripts of
evidence and no design yet — note rule 7 accepts written tests, and two
of Exp B's accepts wrote `tests/test_mock_factory.py`, so a naive
new-file block would false-reject accepted runs. Candidate 3 (prefer the
manifest's candidate paths) remains speculative: no failure fixture.

## The stub-draft confound

"Drafts for all 8 tasks" is true only as a file count. Three drafts —
async-cm-enter (80 bytes), fastapi-get-registry (55), magicmock-factory
(29) — are conversational preambles ("Now I'll write the contract:")
from authoring runs that produced nothing before ending. All three tasks
came out `no-changes` in the gemma draft-contract sweep, whose 2/8
therefore mixes real-contract cells with cells whose "contract" was a
dangling sentence appended to the brief. stringified-annotations
(no-progress → accepted under a real contract, n=1) is the one
unreplicated contract flip worth remembering.

## What these numbers do NOT show

- **Nothing about contracts improving reasoning.** The one replicated
  contract win is transcription of a solution the contract contained.
  Whether a requirements-only contract (no solution code) helps this
  executor is untested — and is a different authoring prompt.
- **Nothing confirmatory, anywhere.** Rule 8 applies to all of it.
  Experiment A additionally selected its task from the same pilot data
  that motivated it, and its bar is not repo-attested.
- **No frontier variance.** qwen27b's 6/8 and dsflash's 2/8 are n=1;
  gemma's variance measurement covers 4 of 8 tasks.
- **Nothing about guard rescue rates.** The replay shows the guard
  fires; it does not show the model then succeeds.
- **The r5 accept is an artifact of the wall clock**, and Experiment B's
  headline number sits exactly on its reject threshold — treat 3/8 as
  "not confirmed," never as "37.5% capability."

## Verification posture

Checked personally against raw records for this document: the 24-, 6-,
and 8-replicate outcome tables (re-derived from per-attempt `.json` and
cross-checked against driver logs); stopReason distributions from raw
`.jsonl` transcripts for all 14 magicmock runs and all 6 Experiment A
runs; the 49× and 51× identical-call loops (arg-set dedup on
`tool_execution_start` events); the contract-vs-reference docstring
provenance (all six patches read against the draft and the reference
patch); the authoring provenance and all 7 firewall refusals; taint
audits re-run on all 38 replicate directories, 3 sweeps, and 8 authoring
transcripts (0 detected escapes -- the audit matches literal
workspace-shaped names and four substrings, so this is not a hermeticity
claim); `models.json` restored and byte-identical to the
pre-experiment backup; the loop-breaker replay run against the shipped
TypeScript artifact. Two of the load-bearing claims above (the draft
containing the literal solution; the 49× identical-call loop ending in
`length`) were independently re-derived a second time before this
document was written, from the raw contract file and the raw transcript
respectively. Relayed without independent verification: the 41–47%
navigation-tax figure from earlier in the phase, and the destructive-
`__contains__` characterization of the brief-only registry-iter failures
(outcome labels verified; individual patches not re-read).
