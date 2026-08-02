# Phase 2, Cycle 3 — Clean baseline

Verified 2026-08-02 against a 32-run batch executed after the task spec was
amended to state the environment (see the
[design spec](../specs/2026-08-02-phase2-cycle3-honest-environment-design.md)
for the friction finding that motivated it).

## Raw checkpoints

| | Path | Records | SHA-256 |
|---|---|---|---|
| Part 1 | `~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-part1-n13.jsonl` | 13 | `cd116bd75b198c667eb6149d927b3b45f2d259604c62aa700c01cc37d8cb6a9e` |
| Part 2 | `~/local-ai-pi-evidence/satyrn-phase2-cycle3-clean-part2-n19.jsonl` | 19 | `150f274934d2908f4784bfe0489bee496d349c6fb2d97052c8d4c9630a5a8794` |

Outside Git, per the same reasoning as cycles 2 and 16. This record and the
recompute script alongside it are what survive if the checkpoints are lost.

Recomputed by `2026-08-02-phase2-cycle3-recompute-summary.py`, alongside this
file.

## Why two checkpoints, treated as one batch

The batch was launched as a single n=32 run and aborted after 13 records with
`RuntimeError: run conditions changed during batch`. A commit from a
*concurrent session* on the same repository moved `HEAD` while the batch was
in flight, and `_conditions()` reads `git rev-parse HEAD` per run. The
safeguard worked exactly as intended: it refused to append incomparable
records rather than producing a quietly mixed batch.

Verified before combining the two parts anyway — `harness_revision` is the
**only** field that differs across all 32 records:

| Field | Part 1 | Part 2 |
|---|---|---|
| `harness_revision` | `9a88ae7d73170c2c20eaadaf0a2f83bb568e0f0d` | `315db873d2cd4d3adcb9ee2cb9217f625b6247a1` |
| everything else | identical | identical |

And the diff between those two revisions is `ROADMAP.md`, 62 added lines,
nothing else — no `harness/`, no task spec, no change to the `pi` command
line. The task-spec SHA-256, `pi` version, model, both timeouts, and the
full normalized `pi_command` are byte-identical across all 32 records.

This is the same test cycle 2 applied before combining its n=16 and n=32
checkpoints, and it passes more cleanly here: cycle 2 had actual `harness/`
additions to reason about, while this diff cannot reach the run machinery at
all.

The operational rule cycle 2 stated — do not commit while a batch is in
flight — needs one amendment on this evidence: **it is a coordination
requirement across concurrent sessions, not self-discipline within one.** A
session obeying it perfectly still lost 13 runs to another session's commit.

## Conditions shared by all 32 records

| Field | Value |
|---|---|
| Model | `omlx/gemma-4-12B-it-MLX-8bit` |
| Pi version | `0.82.0` |
| Task-spec SHA-256 | `95f9303c749416fc84aeddea5ada10879dd86dd64713574a6d2655725457ce2d` |
| Run timeout | 600 seconds |
| Grade timeout | 30 seconds |
| Accepted (Pi-exit veto) | 32 of 32 |
| Refused | 0 |
| Pi return codes | all 0 |
| Timed out | none |
| Acceptance tests executed / expected | 4 / 4 in every run |
| `complete` (telemetry) | `True` for all 32 |

The task-spec hash differs from the 48-run baseline's (`db17991e…`), which is
why `run_batch()` would not extend those checkpoints and a fresh one was
started. That refusal is the conditions mechanism working, not an obstacle
worked around.

## Did the fix work?

| Metric | 48-run baseline | This batch |
|---|---|---|
| Total tool errors | 65 of 336 tool calls | **0 of 203** |
| Runs with at least one error | 28 of 48 | **0 of 32** |
| Zero-error rate | 20/48 | 32/32 |
| **Runs that actually ran a test** | **28 of 48** | **32 of 32** |
| Runs that were both zero-error and tested | **0 of 48** | **32 of 32** |

**Yes — and the last two rows are the ones that matter.** A zero error rate
on its own would not have been evidence of anything: the old baseline already
contained 20 zero-error runs, and *none* of them ran a test. Zero errors was
the signature of skipping verification. What is new here is that all 32 runs
ran `pytest` and all 32 encountered no friction doing it. The two families of
error the design spec identified — 43 dependency installs and 22 test-import
failures — are both absent entirely.

The `ran_a_test` diagnostic is validated against known ground truth rather
than trusted: run against the old 48-run checkpoints it reports 0 of the 20
zero-error runs as having tested and all 28 errored runs as having tried,
and it recomputes the design spec's 65-of-336 error figure from the raw
data.

## Per-run table

`tools` is total tool calls; `err` is `tool_errors`; `ctx` is
`context_processed`; `span` is seconds between the first and last
`message_start` timestamp — a lower bound on wall-clock, not a true duration
(see `ROADMAP.md`'s Backlog note on wall-clock timing). Runs 1–13 are part 1;
14–32 are part 2. Every run: `complete=True`, `accepted=True`, `tested=True`.

| run | turns | tools | err | ctx | span(s) |
|---|---|---|---|---|---|
| 1 | 7 | 6 | 0 | 16237 | 28.0 |
| 2 | 7 | 6 | 0 | 16302 | 30.8 |
| 3 | 7 | 6 | 0 | 16328 | 34.8 |
| 4 | 9 | 8 | 0 | 23184 | 41.8 |
| 5 | 7 | 6 | 0 | 16203 | 37.8 |
| 6 | 9 | 8 | 0 | 23109 | 55.1 |
| 7 | 7 | 6 | 0 | 16259 | 47.9 |
| 8 | 12 | 11 | 0 | 31993 | 71.9 |
| 9 | 7 | 6 | 0 | 16293 | 46.8 |
| 10 | 7 | 6 | 0 | 16322 | 45.0 |
| 11 | 7 | 6 | 0 | 16243 | 40.8 |
| 12 | 7 | 6 | 0 | 16281 | 41.3 |
| 13 | 7 | 6 | 0 | 16350 | 40.8 |
| 14 | 7 | 6 | 0 | 16388 | 28.9 |
| 15 | 7 | 6 | 0 | 16275 | 31.6 |
| 16 | 7 | 6 | 0 | 16295 | 34.9 |
| 17 | 7 | 6 | 0 | 16377 | 35.1 |
| 18 | 7 | 6 | 0 | 16277 | 35.4 |
| 19 | 7 | 6 | 0 | 16266 | 37.7 |
| 20 | 7 | 6 | 0 | 16317 | 42.7 |
| 21 | 7 | 6 | 0 | 16269 | 43.3 |
| 22 | 7 | 6 | 0 | 16235 | 42.4 |
| 23 | 9 | 8 | 0 | 23243 | 52.7 |
| 24 | 7 | 6 | 0 | 16300 | 43.1 |
| 25 | 7 | 6 | 0 | 16218 | 41.1 |
| 26 | 7 | 6 | 0 | 16222 | 39.5 |
| 27 | 7 | 6 | 0 | 16344 | 39.8 |
| 28 | 7 | 6 | 0 | 16334 | 41.1 |
| 29 | 7 | 6 | 0 | 16299 | 37.8 |
| 30 | 7 | 6 | 0 | 16246 | 36.8 |
| 31 | 7 | 6 | 0 | 16267 | 36.9 |
| 32 | 7 | 6 | 0 | 16344 | 37.7 |

This table is real data, not retyped by hand — it matches the recompute
script's output exactly.

## What the runs look like now

Totals across batches of different size are not comparable, so this table
gives per-run rates alongside them.

| | 48-run baseline | This batch |
|---|---|---|
| Tool totals | `bash` 137, `write` 199 (336) | `bash` 70, `write` 129, `edit` 4 (203) |
| `write` per run | 4.15 | 4.03 |
| `bash` per run | 2.85 | 2.19 |
| errored `bash` per run | 1.35 | **0** |
| `tool_calls == turns - 1` | held, all 48 | holds, all 32 |
| Modal shape | 6 turns, 4 writes, no test | 7 turns, 2 bash + 4 writes, tested |

**The `write` rate barely moves — 4.15 per run to 4.03.** The model was always
writing the same four files, and still is. What changed is the `bash` traffic
around them: 2.85 calls per run of which 1.35 failed, down to 2.19 of which
none did. The two error families the design spec identified — installing
dependencies that were already importable, and re-running a test command that
could not import `app` — accounted for essentially all of the difference.

`edit` appears for the first time (4 calls, confined to the 9- and 12-turn
runs): the model reading a real test failure and fixing its own code, which is
the behaviour the old environment priced out.

## Turn distribution and support coverage

| Metric | 48-run baseline | This batch |
|---|---|---|
| Distinct turn values | {6, 8, 9, 10, 11, 12} | {7, 9, 12} |
| Distribution | 6×20, 8×9, 9×7, 10×4, 11×7, 12×1 | 7×28, 9×3, 12×1 |
| Mean turns | 8.0 | 7.34375 |
| `leave_one_out_spread` | 0.128 | 0.161 |
| `context_processed` range | 12804–31710 | 16203–31993 |
| New turn values in the final quarter (runs 25–32) | — | none |

**The support-coverage check is one-sided: it can fail, never certify.** The
n=16 baseline is the proof — its own final quarter introduced no new turn
value, yet 10 and 12 were still unseen and surfaced at runs 17 and 20. This
batch's final quarter was quiet, and that is reported here as exactly that: a
quiet final quarter. It is **not** evidence that the support is covered. A
33rd run could show a value none of these 32 did.

Two honest observations against that caution. The distribution is far more
concentrated than the baseline's — 28 of 32 runs are the identical 7-turn
shape — so there is less tail to miss. But it is also *thinner*: three
distinct values, one of which occurs once.

## How many runs would a claim need?

**The bootstrap is reported here with a caveat heavy enough that it should
probably not be used.** `bootstrap_ci_halfwidth` resamples from the observed
values, and 87.5% of this sample is a single value. Resampling cannot produce
a value the sample never contained, and with support this thin the procedure
is close to reporting the precision of a near-constant. The numbers below are
what the module returns; they are optimistic in a way the n=48 numbers were
not, because that sample had six distinct values to draw from.

| Target half-width | Minimum n (turns) | | Target half-width | Minimum n (ctx) |
|---|---|---|---|---|
| 1.0 turn | 3 | | 1500 | 18 |
| 0.5 turns | 12 | | 1000 | 40 |
| 0.25 turns | 61 | | 500 | 162 |

(95% confidence, `seed=0`. Half-width at n=32 for turns: 0.344.)

**The more defensible claim from this sample is a binomial one.** Rather than
asking how precisely the mean turn count is known, ask how often a run
departs from the modal shape at all:

> **4 of 32 runs (12.5%) took more than the modal 7 turns.**
> 95% normal-approximation interval: 1.0% – 24.0%.

That interval is wide, and it is wide honestly: 4 events is not many. It is
the number this sample can actually support, and it answers the question a
contributor is likely to have — how often does this task need more than one
straight-through pass — without leaning on a bootstrap over a near-degenerate
distribution.

**Read in runs, not minutes, on purpose** — a contributor on any hardware
uses these tables by timing one `run_agentclinic_phase1()` call on their own
machine and multiplying, remembering that in-stream span (median 40.8s here)
excludes the ~7.6s per-run overhead cycle 2 measured outside the stream.

## The three-question check, piloted

The design spec asked that three questions be applied to every quantitative
claim in this record, and that the result be reported whether or not it caught
anything. It caught three things. All three corrections are already reflected
above; this section records what the check found rather than describing a
clean process.

**1. Am I extrapolating outside the observed range?**

*Caught the precision table.* The first draft of the section above presented
`minimum_n_for_precision` results in cycle 2's format, as a straightforward
recommendation. The question exposed that a bootstrap over a sample that is
87.5% one value is extrapolating in the most direct sense available:
resampling cannot generate a value the sample never held, so the reported
half-widths describe a near-constant. The section was rewritten to lead with
that caveat and to offer the binomial rate as the claim the data can carry.

**2. What exactly does this number measure — the same units as what I am
comparing it to?**

*Caught the error-rate comparison.* "65 errors" and "0 errors" are counts over
different denominators — 336 tool calls across 48 runs versus 203 across 32.
Comparing the bare counts would overstate the improvement by conflating fewer
errors with fewer runs. The comparison table now states both denominators, and
the per-run rate (28 of 48 runs versus 0 of 32) is given alongside the totals.

The same question also caught something the design spec had not anticipated:
error rate is **not the same measurement** as "the environment fix worked."
Zero errors was already achievable in the old environment by not testing, and
20 runs did exactly that. That is why `ran_a_test` exists and why the verdict
above rests on the both-zero-error-and-tested row rather than on the error
count.

**3. Could a new sample contain a value mine never showed?**

*Caught nothing new — the design spec had already required the guard.* The
support-coverage diagnostic was built one-sided from the start, precisely
because the n=16 sample had a quiet final quarter and an incomplete support
simultaneously. The question confirmed the guard was correctly stated rather
than revealing a missed case. Worth recording as a case where the check passed
cleanly: it is evidence about the check's hit rate, not only its usefulness.

**What the check did not catch, and something has to.** A draft of the "What
the runs look like now" section above reported the 48-run baseline's tool
totals as `bash` 207 / `write` 129. The real figures are `bash` 137 /
`write` 199. Both were wrong, in different ways: 129 is *this* batch's write
count, copied into the old batch's column, and 207 corresponds to nothing in
either dataset. On top of that error the draft built a striking claim — "the
`write` count is *identical*, 129 in both", which was only true because the
same number had been written in both cells — plus a derived "137 extra `bash`
calls" that was, by coincidence, the *entire* old bash total misread as a
difference. All three questions passed over it. They interrogate what a number
*means*; none of them asks whether the number was ever *measured*. It was
caught only by running the recompute script against the old checkpoints before
publishing.

**Corrected 2026-08-02, during cycle 4's design.** This paragraph itself
misreported the error it was confessing: it gave the bad draft's figures as
`bash` 207 / `write` 199 and called them "inverted". That is wrong twice over —
199 is the *correct* old write count, not the draft's, and nothing was
inverted. The confession was written from memory instead of from the draft,
which is the same failure it describes, one level up. Recording it rather than
quietly amending it, because an error-rate of two in one paragraph is the
strongest evidence this pilot produced that memory is not an acceptable source
for a number.

That is the most useful finding this pilot produced, and it points at a fourth
question, or better, a mechanical rule: **every number in a research record
must come from a command whose output is in the transcript.** The three
questions are a reasoning check; this failure was not a reasoning error but an
invented figure that reasoning then decorated. Cycle 4 should treat those as
distinct error classes.

**Assessment for cycle 4.** Two of three questions changed what this record
says, and question 2 changed the cycle's central verdict from "error rate is
near zero" to "error rate is near zero *and* verification actually happened."
A fourth error — fabricated tool totals — slipped all three and was caught by
verification instead. Nothing in this repository's test suite could have
caught any of the four. That is evidence the discipline is worth designing,
and evidence about what shape it needs.

## Verification method

Every number above was produced by `harness.telemetry.read_telemetry` and
`harness.precision` via `2026-08-02-phase2-cycle3-recompute-summary.py` and
the precision command recorded in this cycle's plan, then transcribed — not
hand-aggregated and not retyped from memory. The `ran_a_test` diagnostic was
additionally validated against the 48-run baseline, where its expected answer
was known in advance from the design spec.
