# Section III — Spec-Driven Development on Pi

Installs Pi's shipped subagent extension, authors an implementer specialist
and an orchestrator parent prompt, then measures and tunes the
parent+implementer shape.

**Status:** SP1 and SP2 status is withdrawn (see the roadmap). The chapter
prose that narrated the SP1→SP2 structural-baseline arc is discarded — see
[`docs/superpowers/plans/2026-07-24-grading-path-reboot.md`](../superpowers/plans/2026-07-24-grading-path-reboot.md),
Task 9. Spec and plan are kept as historical record; the SP2 numbers below
predate the grading-path reboot and are superseded. The prose on this page is
written against the reframe, and it claims no steered measurement — no steered
batch has been run under the rebuilt grading path.

**Evidence (superseded, pre-reboot):**
[3/8 pre-tuning](research/2026-07-24-sp2-baseline-phase-1.md),
[5/8 post-tuning](research/2026-07-24-sp2-baseline-phase-1-post-tuning.md),
[deep-dive (5 telemetry gaps)](research/2026-07-24-sp2-deep-dive.md)

## About SDD

This course doesn't require spec-driven development. It uses it for two
reasons, both directly relevant to keeping a small local model on track:

**The handoff packet.** The whole point of a phase contract — a task
checklist, an allowed-files list, acceptance strings, and a single validation
command — is to give the SLM implementer a tight, focused unit of work. No
exploration, no context searching, just build what the packet says. This is
LESSONS #1 ("structure beats strings") expressed as a document format.

**Working in small units.** An SLM does best at routine, bounded work (
{doc}`/index`). A
well-sized packet is the difference between "build a FastAPI app" (too vague)
and "create app.py with a single route, one template, and one test that
checks for this exact string" (tight enough to succeed).

See {ref}`about-sdd` in the course overview for the broader rationale.

## Measuring the mechanism

A mechanism you cannot measure is a preference. This section owns the
measurement apparatus — the telemetry reader and the evidence ledger — and it
is introduced here the way it is used: attached to a specific claim, at the
point the claim is made. There is no "how the measurement works" chapter
before this one, deliberately. That mirrors **D2** in
[the evidence policy](../superpowers/policies/evidence.md): failure-mode
incidence is the primary metric, reported per named failure mode, not as an
aggregate scorecard.

Two claims are in scope. One has evidence and a correction attached to it. The
other has an apparatus, a pre-registration requirement, and no data at all —
and saying so is the point.

### Claim 1 — replace-vs-extend on inherited files

**The apparatus, first.** `harness/telemetry.py` parses the JSONL that
`pi --mode json` writes to stdout. Its schema was captured by hand against
pi 0.81.1 and the target model, and the docstring records what is *not* there
as carefully as what is: "No token usage data in `--mode json` mode," and
`isError` is a string `"True"`/`"False"`, not a boolean. On top of that reader
sits `inherited_file_activity()`, which classifies how a run touched the files
that were already in the workspace when it started — the seed from phases
1..N−1. It reads only `tool_execution_start` events, because the metric is an
*attempt*:

> `'replace'` if any inherited file was targeted by a whole-file `write`
> attempt (`lessons.md` #12) — blocked or failed attempts still count, since
> the attempt itself is the behavior this metric names, not whether it
> succeeded. `'extend'` if inherited files were touched only via `edit`.

That is a per-run, mechanically countable signal derived from the artifact, not
from anything the model says about itself. Which is exactly one of the three
things [Rule 7](../superpowers/policies/evidence.md) permits a mechanism to
claim: a *behavioral-incidence change*, evidenced at n=16 with counts.

**The finding.** The
[self-grade forensics report](../section-2-measurement/research/2026-07-24-selfgrade-forensics.md)
replayed the `write`/`edit` tool calls of eight seeded Phase 2 unsteered runs
onto the seeded phase-1 test file and reconstructed what each run did to
`tests/test_app.py`. Six runs edited it incrementally, keeping the phase-1
tagline assertion, and all six passed. Two runs (`aa7a0ac8980b`,
`c1acd1f2b533`) rewrote it from scratch, dropped the phase-1 assertion, and
both failed. The same two runs were also the false self-reporters in the
sample, and one of them — `aa7a0ac8980b` — is the run that rewrote
`templates/base.html`, a Phase 1 file, which is the preservation-breakage
failure the seeded workload exists to expose.

The
[grading-path reboot plan's](../superpowers/plans/2026-07-24-grading-path-reboot.md)
evidence-triage table rates this row "**Valid, and load-bearing.**
Oracle-independent, countable per run. This is the strongest finding in the
project."

**Now the corrections, which matter more than the finding.**

*Scope.* A Rule 8 review by a different model (Fable, 2026-07-26) found that
"8/8" names a narrower measurement than the standing metric computes. The
correction is pinned in the code, in `InheritedFileActivity.classification`'s
own docstring:

> the 2026-07-24 forensics report's 8/8 correlation (every run that
> incrementally edited an inherited file passed, every run that replaced one
> from scratch failed) was measured on the inherited TEST SUITE specifically
> (`tests/test_app.py`), not on any-inherited-file at the run level.
> Re-running this run-level classification against the same 8 forensics
> artifacts gives 6/8, not 8/8 — one old-oracle passer (`3ff54760771a`)
> whole-file-wrote `app.py` while incrementally editing the test suite. […]
> do not cite "8/8" for this run-level classification.

So: 8/8 on the test-suite-scoped classification, 6/8 on the run-level one that
`harness/telemetry.py` actually reports today. Two different measurements, one
number, and the docstring exists so nobody quotes the wrong one.

*Tier.* The forensics report itself grades its own numbers: "**Tier:** GREEN
for the replay facts; the correlation reading is YELLOW (n=8)." The replay is
deterministic. The correlation is eight runs.

*Provenance of the outcome column.* Those verdicts are labelled "Old-oracle
verdict" in the report — they were issued before the acceptance suite became
harness-owned (D3) and before the grading path was rebuilt (D4). The *behavior*
is replay-derived and survives; the pass/fail it correlates against was
produced by an oracle this project has since replaced.

**What the standing metric shows now.** Under the rebuilt grading path, every
unsteered n=16 report carries the counter:

| Batch | replace | extend | untouched | Success |
|---|---|---|---|---|
| [Phase 2, 2026-07-27](../section-2-measurement/research/2026-07-27-post-repair-sp1-phase2.md) | 5 | 11 | 0 | 15/16 |
| [Phase 3, 2026-07-27](../section-2-measurement/research/2026-07-27-post-repair-sp1-phase3.md) | 4 | 12 | 0 | 16/16 |
| [Phase 3, less-prescriptive spec, 2026-07-28](../section-2-measurement/research/2026-07-28-post-repair-sp1-phase3-less-prescriptive-spec.md) | 6 | 10 | 0 | 16/16 |

Read that honestly. In the 2026-07-27 Phase 3 batch all sixteen runs passed, so
all four replace-classified runs passed. In the 2026-07-28 batch all sixteen
passed with six replace-classified runs. The same gap reaches back a step
further, too: the 2026-07-27 Phase 2 batch's one failing run (run 7) is not
separable from its five replace-classified runs in the published aggregate
either — the table's replace=5/extend=11 split is not broken out by pass/fail,
so which bucket the failure landed in is not recoverable from the report as
published. Whatever the run-level counter is
measuring on this workload, it is **not** currently separating passing runs
from failing ones — there are almost no failing runs left to separate. The
signal is alive as a countable behavior and dead as a predictor here, and the
place it is expected to matter again is Section IV, where a mechanism tries to
make the whole-file rewrite structurally impossible rather than merely rarer.

**What Section III may claim from it: nothing yet.** No steered
orchestrator+implementer batch has been run under the rebuilt grading path.
The replace-vs-extend numbers above are all unsteered. Comparing them to
anything would require a steered arm that does not exist.

### Claim 2 — cost-equivalence, which has not been measured

**The apparatus.** For a delegating run, `subagent_stats_from()` walks the same
artifact for `tool_execution_start` events whose `toolName` is `subagent`,
counting invocations and summing the `task` argument's length in bytes. That is
what fills the "Subagent delegation metrics" section of every report: per-run
subagent calls and packet size, plus a mean over the runs that delegated. Turn
counts come from the same reader. Amendment 1 of the
[oracle-repair plan](../superpowers/plans/2026-07-24-oracle-repair.md) makes
the sourcing a rule, not a habit: "Delegation counts in any status or report
derive from `subagent_stats_from` only." The reason it had to be written down
is in the next section.

Timing is deliberately split into two differently-named numbers.
`task_duration_s` is the artifact's own first-to-terminal timestamp delta;
`mean_process_wall_time_s` is the harness's subprocess clock. The docstring
says why they are never merged: "Unlike `task_duration_s` this includes any
dead time from a killed-then-retried attempt, so it is reported separately and
labeled, never silently substituted."

**The claim this apparatus is for, and its ceiling.** Amendment 1's
pre-registered no-ditch contingency fired on 2026-07-27 — seeded Phase 2 scored
15/16 and Phase 3 scored 16/16 under Amendment 2's ≥15/16 rule — and its
disposition sets what Section III is allowed to say:

> Section III makes no improvement claim (there is nothing left to improve on
> this workload, per this contingency's own trigger): its only empirical claim
> is continuous-cost equivalence — does adopting the mechanism cost materially
> more (turns, packet/token size; wall time is context only […]) without
> degrading below Amendment 2's solved line.

The [roadmap](../superpowers/roadmap.md) attaches one precondition to that, in
its own words: "Before any Section III evidence batch: pre-register the
cost-equivalence metric set and degradation budget […] so the claim can't be
set after seeing the data."

**That batch has not been run.** There is no cost-equivalence number in this
course yet — not a favourable one, not an unfavourable one. The metric set and
degradation budget are not yet pre-registered either; that is the next step,
and it comes before the data, not after. Treating the orchestrator+implementer
shape as *better* than an unsteered run on this workload would be inventing a
result: on a workload that already scores 15/16, 15/16 and 16/16 unsteered,
there is nothing to improve, which is precisely why the surviving question is
what the mechanism *costs*.

Two apparatus gaps are worth naming before anyone runs that batch, both
standing items in the roadmap's backlog. **Child session JSONL is not
captured** — the parent artifact shows the subagent tool call and its summary
result, but not the child's own event stream, so a steered run is measured at
lower resolution than an unsteered one. And the **packet fidelity metric**
(mechanically checking that the packet's acceptance strings and allowed-files
list match the roadmap verbatim) is still open; the report writer prints that
it is deferred, and that line stays until it ships.

A second future measurement is named the same way, and is equally unrun:
`examples/agentclinic/specs/roadmap-user-story.md` — a higher-level
business/user-story rewrite of the same three phases, targeting the identical
app — is designated Section III's later packet source, so the mechanism can be
tested with less precise hand-holding. Whoever runs it owes Rule 6 first: the
oracle re-validated against that workload variant before any number out of it
is trusted.

### Why incidence, and not success rate

The clearest demonstration in this project of why D2 puts incidence first
happens to be a Section 2 batch, and it is worth borrowing. The phase-3
model-facing spec was rewritten to stop stating the answers to its own known
traps, then re-run at the same n=16, same model, same seed, same acceptance
suite. Only the spec's wording changed. From
[that report's](../section-2-measurement/research/2026-07-28-post-repair-sp1-phase3-less-prescriptive-spec.md)
own comparison table:

| Metric | Prescriptive spec (2026-07-27) | Less-prescriptive spec (2026-07-28) |
|---|---|---|
| Success rate | 16/16 | 16/16 |
| Hang incidence | 0/16 | 6/16 |
| Mean turns | 10.8 | 24.2 |
| Mean wall time | 91s | 205s |
| Inherited-file write attempts | 4/16 | 6/16 |
| Drift incidence (overreach) | 0/16 | 1/16 |

Success rate reports nothing. It cannot: it was saturated before the change and
saturated after. Everything the change actually did shows up in the incidence
columns — and a chapter written here would report *those*, never a
success-rate delta neither report can distinguish from noise at n=16
(Rule 7).

The report also states its own caveat, which belongs in any retelling: the six
`exited-with-hang` rows are all pinned at the 300s timeout ceiling, so 205s is
a censored statistic rather than a true mean, and hang incidence and turn count
are not independent signals — "a hang is largely a restatement of 'this run
needed more than 300s.'"

## When your metrics are fiction

Everything above depends on a report writer that tells the truth about what
ran. This project's did not, four times, and it is worth being specific about
each one, because none of them look like fraud from the inside. They look like
working code.

Read this next to Section 2's material on the *acceptance contract*. That was
about whether the grader can be trusted. This is about whether the thing
*watching the grader* can be trusted — the same apparatus this section owns.

**A duration metric that always returned zero, pinned by a passing test.**
Every report printed `**Mean task duration:** 0s`. The cause was a schema skew:
pi 0.82.0's `--mode json` stream carries a top-level `timestamp` on only the
initial `session` event, so `compute_task_duration_s` took first-to-last across
exactly one timestamped event and got zero, every time. Zero is not a null —
it is indistinguishable in any aggregate from a genuinely instantaneous run.
The part worth sitting with is that the test suite was green throughout,
because two unit tests had been written *around* the bug. One of them read, in
full:

```python
def test_compute_task_duration_s_single_event(tmp_path: Path):
    """A single timestamped event should yield duration 0."""
    from harness.telemetry import compute_task_duration_s
    f = tmp_path / "single.jsonl"
    f.write_text('{"type": "session", "timestamp": "2026-07-23T09:38:11.322Z"}\n')
    duration = compute_task_duration_s(f)
    assert duration == 0.0
```

The fix required at least two distinct timestamped events and returns `None`
otherwise; both tests were corrected to assert `None`. The current test's
docstring now carries the reasoning rather than the assumption: a single
timestamped event "cannot yield a real duration, so this must be `None`, not a
fabricated 0.0." A passing suite is evidence that the code does what the tests
say. It is not evidence that the tests say the right thing.

The fabricated number also outlived its own fix: the reboot plan's finding
**F6** records "Three live reports still carry the fabricated
`**Mean task duration:** 0s`, unbannered" — the metric was fixed on
2026-07-24 and the reports quoting it were not bannered until 2026-07-26.
They are bannered now, and kept:
[the phase-1](../section-2-measurement/research/2026-07-24-post-repair-sp1-phase1.md)
and
[phase-2 pooled](../section-2-measurement/research/2026-07-24-post-repair-sp1-phase2-pooled.md)
reports still show the `0s` line above a warning explaining it.

**Evidence tiers stamped GREEN unconditionally.** The evidence ledger's tiers —
GREEN artifact-backed, YELLOW real but noisy, RED estimated — are the
mechanism this project uses to keep weak numbers from being read as strong
ones. The report writer emitted them as template text. Finding **F5**: "Evidence
tier lines in `runner.py` are unconditional template text, not assessed from
run facts." Literally, the old code appended

```python
lines.append(
    f"- **Success rate:** artifact-backed — n={report.n} dated session files "
    f"(GREEN per [evidence policy](../../superpowers/policies/evidence.md))."
)
```

with no condition in front of it at all — a zero-run batch would have been
stamped GREEN and artifact-backed. The tier lines are now derived: the report
leads with an **Outcome mix** counted from the actual results so the tier
claims below it can be checked against something, the success-rate line is
guarded on there being runs at all, the timing line is guarded on timing data
existing, and n≤8 adds an explicit small-sample note. A tier that is printed
regardless of the run is not a tier; it is decoration that looks like rigor.

**A status narrating 70–74 subagent calls against an artifact recording 1.**
From the reboot plan's closing note, the fabrication verbatim: a status
narrating "70–74 subagent calls, spiraling as expected" when the artifact
recorded 1. Amendment 1 records the same event from the other end — "The first
Arm A status hand-derived ~70 calls/run; the artifact showed 1" — and turns it
into the standing rule quoted earlier in this section: delegation counts derive
from `subagent_stats_from` only, and "No interpretation ships without an
artifact-derived number behind it." Note the failure mode. The number was not
copied from a broken metric; it was *reasoned out* from what a delegating run
was expected to look like, and it came with a narrative ("spiraling as
expected") that made it feel confirmed. That is Rule 2's whole point: report
the literal result — the exact acceptance-command output, the changed file set,
the turn count — not a summary of it.

**An "Oracle validated" line that never ran the oracle.** Finding **F4**:
`runner.py` printed "**Oracle validated:** `tests/test_oracle.py` green at
commit `<sha>`" by running `git rev-parse` — "it never runs the test.
Fabricated attestation, in the artifact meant to end fabricated metrics." The
old code is worth seeing, because the exception handler is the tell:

```python
except Exception:
    lines.append("**Oracle validated:** `tests/test_oracle.py` green")
```

If even the `git rev-parse` failed, it still attested that the oracle was
green. The line is gone now, and the comment left where it stood states the
rule: `write_report` never runs `tests/test_oracle.py` itself, so it cannot
honestly claim the oracle is green — that claim is made separately, by whoever
runs the oracle, and cited in the commit or prose that publishes the report.
You can see the honest form in a live report header: "**Oracle re-validated
(Rule 6):** `tests/test_oracle.py` green, 71 passed, before this batch ran."

### Why this is Rule 8's job, not the author's

The four fictions above have one property in common: the automation that
produced them was written carefully, reviewed, and believed to be correct, and
none of them were caught by the pass that produced them. They surfaced later,
when something independent was checked: a number against the JSONL it was
supposed to summarize, or a fresh adversarial pass over the measurement code.
F4, F5 and F6 are recorded in the reboot plan's verified-findings table, and
the roadmap attributes the review round behind that plan to a different model —
"a deep review (Fable, 2026-07-24) found five further integrity failures, two
of which **defeat the hardened oracle**."

That is what
[Rule 8](../superpowers/policies/evidence.md) is built on, and its own record
states the pattern plainly: "Every adversarial review round in this project's
history was run by a different model than the one that produced the work, and
every round found a defect the author had missed and self-review had cleared."
So for any change to the grading path, the acceptance suites, or the harness's
measurement code, the gate is not passed until a model other than the one that
wrote it has reviewed it, with the findings recorded alongside the change. The
correction to this section's own "8/8" claim came from exactly that process.

The rule's justification is one sentence, and it applies to a person writing a
metric by hand every bit as much as to a model: **an author's confidence
carries no information about whether the work is correct.** Self-review cannot
be the last step, because the thing being reviewed is the reviewer.


```{toctree}
:hidden:

cleanup/index
spec
plan
research/2026-07-24-sp2-baseline-phase-1
research/2026-07-24-sp2-baseline-phase-1-post-tuning
research/2026-07-24-sp2-deep-dive
research/2026-07-23-sp2-baseline-phase-1
research/2026-07-23-sp2-baseline-phase-1-post-tuning
research/2026-07-24-sp2-session-deletion-record
```
