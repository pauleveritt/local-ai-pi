# Phase 6 — Enforcement over persuasion: the extension earns its guards

**Date:** 2026-08-05
**Status:** design — the phase's opening document, approved before any cycle
**Supersedes nothing.** It schedules the thesis of
[the enforcement spec](2026-08-05-enforcement-over-persuasion-design.md),
which parked itself for want of a workload; this document accepts that
constraint rather than arguing with it, and changes what a feature is
measured *by* instead of waiting for a suite with headroom.

## Direction, one sentence

> One at a time, add a guard to the extension, each drawn from prior
> experience and each proven against a recorded failure before it ships.

## Why this phase, and why now

Phase 5 found the persuasion ceiling empirically. Five prompt interventions
separate cleanly: **the three that supplied a fact the model lacked worked;
the two that supplied a rule of conduct did not.** Cycle 8 is the sharpest
case — "stop re-running a command that fails identically twice" produced
three pre-registered predictions and three falsifications, with the worst
repeated command rising 93 → 178.

That is not a new finding so much as a re-derivation. `LESSONS.md` §1, from
the prior project, states it directly:

> A rule such as "repair at most twice" still relies on the SLM to count its
> own loop; a mechanical stop or fresh repair packet does not.

Tainie takes the same principle furthest — the model never decides scope;
deterministic discovery runs outside the model loop and the model executes
one bounded edit per site. Both wells say the same thing, and this project
pivoted to Pi *because* Pi offers machinery to control operations rather
than prose to persuade with. Phase 5 then spent four cycles writing prose.

**The pivot's premise is correct and we have been under-using it.**

## What this phase is not

It is **not** an attempt to show that a mechanism raises acceptance. It
cannot be, and saying so once here is cheaper than re-litigating it in every
cycle spec.

The user-story suite is at **15/16 facts-only** against an orchestrated
13/16 (Fisher p ≈ 0.6, recorded as noise). A guard measured against that
suite can only fail to show anything, and the honest reading — that **this
suite has no headroom left** — is a fact about the workload, not a verdict
on any mechanism. Building a harder workload is a real and probably
necessary phase; it is not this one, and a phase that opened by building a
suite would ship no guard.

The phase also publishes **no wall-clock number**. Phase 5 retracted two
figures in one night and filed interleaved arms as the precondition for any
future timing claim. That debt is real and it is not Phase 6's to pay.

## Section 1 — the shape a contributor installs

Satyrn becomes **one installable extension** rather than a growing pile of
one-file downloads: one entry point, one config block, and one file per
guard under `guards/`.

```
extensions/guards/
  index.ts           entry point: registers hooks, reads config, dispatches
  loop-breaker.ts    guard #1 (moved, unchanged)
  <next>.ts          one file per guard thereafter
```

**`--extension` is pointed at `index.ts`, never at the directory.** Phase 5
cycle 1's spike found that a directory argument fails *silently* and the run
still grades accepted — the most expensive shape a mistake can take here.

**It is installed into the agent dir.** The loop breaker currently exists in
two places, `.pi/extensions/` and `pi-agent-dir/extensions/`, and the
duplication is not incidental: cycle 9 proved `PI_CODING_AGENT_DIR` is the
**only seam that reaches a delegated child**, because the shipped subagent
extension passes no environment of its own. A guard that only lives in
`.pi/extensions/` cannot see the child — which is exactly why cycle 8
concluded the mechanism was undeliverable, wrongly. Cycle 1 collapses the two
copies into one installed location rather than carrying a copy-paste pair
forward into every future guard.

Each guard file keeps the loop breaker's proven shape: under ~150 lines,
constants at the top, and **the motivating number in the docstring** — the
loop breaker's says 245 identical `ls -R` calls in one recorded run, with
the upstream issues that declined to fix it.

Each guard is independently switchable. A contributor who wants one guard
gets one guard.

**On the directory name.** It is named for what it contains, not for the
project, because the project's own name is under revision — `README.md`
carries an uncommitted `Satyrn Engine` → `Agent Engine` change. A directory
named after a name in flux would need renaming twice.

## Section 2 — what has to be true for a guard to be kept

Two kinds of cycle. The first is the default; the second exists so a
hypothesis can be tried without pretending it is evidence.

### The recorded-failure cycle

A banked failure motivates the guard. It ships with two **replay
fixtures**: a recorded tool-call sequence on which it must fire, and a
healthy one on which it must stay silent.

This is the project's existing evidence regime, transposed. `BRIEF.md`
states it for graders —

> A grader's verdict isn't evidence until it has accepted a known-good
> solution and rejected a known-broken one.

— and the same sentence, for guards, reads: **a guard isn't evidence until
it has fired on a recorded failure and stayed silent on a healthy run.**
Cycle 6 already did this informally for the loop breaker (zero false
positives across 55 healthy runs; 239 of 261 calls prevented on cycle 4's
worst run). Phase 6 makes it the standing bar rather than one cycle's good
habit.

### The hypothesis cycle

Some guards will have no banked failure behind them — an idea from
`LESSONS.md`, from Tainie, or from a day's work. Those are allowed, on
three conditions:

1. **Pre-registered.** The prediction is written before any run, in the
   cycle's spec, in the shape cycles 7 and 8 used.
2. **Two exits only.** Either the predicted failure gets *recorded*, and the
   guard then earns its replay fixtures like any other; or the prediction is
   falsified, the guard is dropped, and the falsification is written into
   the roadmap the way cycle 8's 3/3 was.
3. **Nothing enters the shipped extension on a hypothesis alone.**

Condition 3 is the load-bearing one. `BRIEF.md` names the trap this phase is
most exposed to: a fourth attempt produced "two workloads, six arms, five
violation classes, three amendment chains" in a single day — correct output,
exploding surface area. A phase whose unit of work is "add a feature" walks
toward that trap by construction. The rule that keeps it away is that
speculation may cost a cycle but may not cost a permanent line of shipped
code.

## Section 3 — cycle 1, which ships no feature

`docs/superpowers/research/2026-08-04-phase5-cycle6-replay.py` already
replays banked batches against the loop-breaker policy. Its own docstring
names the flaw:

> **This is an analysis of the rule, not a test of the shipped code.** The
> extension implements the policy in TypeScript and this reimplements it in
> Python. They can diverge, and no test here would notice.

Cycle 1 closes that gap and builds the machinery the rest of the phase
needs:

- The `extensions/guards/` layout above, with the loop breaker moved in
  **unchanged** as guard #1 and its behavior pinned by the existing tests.
- A replay runner that exercises the **shipped TypeScript** against recorded
  tool-call sequences — so a fixture proves the artifact, not a paraphrase
  of it.
- Two replay fixtures for guard #1, drawn from batches already banked in
  `~/local-ai-pi-evidence/`: cycle 4's 261-turn run (must fire) and a clean
  accepted run (must stay silent).

It **claims no number and runs no batch.** This is deliberately the same
move as Phase 4 cycle 1, which added a second suite to prove a seam had more
than one caller before anything depended on it: prove the machinery on a
guard whose value is already established, so the first *new* guard is not
also the first test of the harness that judges it.

## Section 4 — the candidate well

Drawn from `LESSONS.md` and Tainie. **Not a commitment** — the phase
schedules one cycle at a time, and this list exists so a later brainstorming
session starts from it rather than re-deriving it. Roughly ordered by how
much recorded evidence sits behind each:

| candidate | source | evidence behind it |
|---|---|---|
| **Graceful turn budget** — past N turns, block every `tool_call` with a reason to summarize and stop | `LESSONS.md` §11/§16, "externally enforced repair budgets"; enforcement spec candidate #1 | Pi has no turn cap at any level and upstream closed #1898/#5248/#6158. `ctx.abort()` is **confirmed** to yield `stopReason: "aborted"`, which the shipped subagent classifies as a *failed* delegation — so blocking dominates aborting |
| **Tool-output limits / recursive-listing refusal** | `LESSONS.md` §8 | One `ls -R` traversed `.venv` and inflated every following request. "The model's initial choice was stochastic; the context explosion after that choice was deterministic" |
| **Path-keyed churn breaker** — N writes to one path in a window, regardless of content | enforcement spec candidate #2; `LESSONS.md` §12 | 27× one template, 19× and 10× `app.py`. The current key includes arguments, which is why 26 of 27 byte-identical writes tripped it and the rest did not. Churn appears in **both** arms at comparable amplitude |
| **Stale-anchor edit → demand a whole-file write** | `LESSONS.md` §12 | 27 `oldString` mismatches in one session record, across blind edits, stale content, whitespace, and empty anchors |
| **Resolved-model verification** | `LESSONS.md` §10 | "A configured name is not proof that it received the request" |
| **Default-deny tool policy** | `LESSONS.md` §8 | A child hit its denied `ls`, then routed the same intent through an editor-injected shell tool it had never been told to avoid, and burned its whole step budget |

Two candidates from the same wells are **deliberately excluded** as too
large for a guard: structural/LSP navigation and deterministic write-path
transforms. Those are Tainie's whole architecture, not a file under 150
lines. If they are wanted here, they are a phase.

The enforcement spec's **done-detector** stays demoted and unscheduled, on
its own evidence: it would never have fired in its own flagship run (that
run's single pytest collected 0), it has a premature-fire mode and a
bash-heredoc bypass, and both churning runs were graded accepted anyway — so
it would have changed **zero grades** in all observed data.

## Section 5 — the constraint that must survive the phase

A detector **must never touch the harness's acceptance file.** Its signal is
the model's own validation command. Running the harness's contract mid-run
would hand an arm a perfect done-signal that no earlier arm had — a
*capability*, not an information leak, which is why redacting failure text
does not fix it.

A structural guarantee already backs this: `grade()` copies allowlisted
paths out to a fresh temp directory, so the acceptance file is never in the
workspace during a run. The rule is restated here because it is the kind of
constraint a later cycle rediscovers expensively.

## Section 6 — concept budget

Two new terms:

| Term | Means | Introduced |
|---|---|---|
| guard | one enforcement rule in the extension, with its own replay fixtures | phase 6 cycle 1 |
| replay fixture | a recorded tool-call sequence a guard is run against offline, paired fire/silent | phase 6 cycle 1 |

`loop breaker` keeps its existing row: it names a specific guard the
published records cite, and generalizing that row into `guard` would make
those citations read as though they named a category.

Phase 5 let the budget fall twelve cycles behind and recorded it as a lapse.
This phase checks it at every cycle close.

## Open questions, carried rather than answered

- **Does revision churn cost anything measurable?** In every observed case
  it was survivable and every churning run was accepted. If it costs only
  wall clock, it may not deserve a guard at all — and the churn-breaker
  cycle should be willing to conclude that.
- **Is the `templates/` allowlist coupling worth fixing in the suite?** The
  allowlist copies `app.py` and `templates` only, so HTML under `views/`
  passes locally and fails grading, while the acceptance file's own
  docstring disclaims file layout. Inherited from the enforcement spec; not
  a guard, and it belongs to whoever next touches the suite.
