# Phase 7 cycle 2, built overnight — what was made, what broke, what it cost

**Date:** 2026-08-09
**Status:** research record and handover. Cycle 2 is implemented and reviewed;
the measurement in it is a **probe**, not evidence.
**Code:** branch `phase6-orchestrator-spike`, cycle 2 spans `604171a..HEAD`
**Spec:** [`../specs/2026-08-08-phase7-cycle2-bounded-executor-design.md`](../specs/2026-08-08-phase7-cycle2-bounded-executor-design.md)
**Plan:** [`../plans/2026-08-08-phase7-cycle2-bounded-executor.md`](../plans/2026-08-08-phase7-cycle2-bounded-executor.md)

---

## The one thing to read if you read nothing else

The bounded executor works, and the transactional boundary is nearly free — the
worktree, all five gates and the atomic promote together cost a median **385 ms
against a ~40 s model call, about 0.95%**, with an 11 ms spread across 8 runs.
That is the cycle's headline and it is a deterministic code path, so a small
sample carries it honestly. Safety, on an inference-bound workload, is close to
free.

The cycle also shipped with its central safety claim unenforced, and that has
since been fixed. **The child was not actually confined to the candidate
worktree**: `pi --tools read,write` restricts which tools exist, not where they
may write, and Pi's write tool resolves absolute paths by contract. A child
emitting an absolute path wrote into the live repository past all five gates,
the drift refusal, and the receipt. For the length of the cycle the isolation was
a property of model behaviour rather than of the system.

`extensions/orchestration/candidate-containment.ts` closes it — a `tool_call`
hook refusing any path that resolves outside the worktree, symlinks included.
**Verified against a live model instructed to escape**: the file was not created
and the refusal was recorded as `{tool: write, target: /tmp/…}`. Verified not to
false-positive: a full live run still promotes and grades 15/15 with gate timings
unchanged. The Pi tool is no longer categorically unsafe, though see the
remaining limits before trusting it with anything irreplaceable.

## What exists now

A contract renders to a prompt; one bounded `read`/`write` model call runs inside
a git worktree created at `HEAD`; five deterministic gates check the finished
candidate; the result is either promoted atomically into the live repository or
discarded with the live tree untouched. Two entry points — a CLI and a Pi tool —
are thin callers of one coordinator whose model call is injected, which is what
keeps all 156 tests free of live model calls.

The five gates, cheap to expensive, stopping at the first failure: scope →
acceptance-strings → symbol-loss → source-requirements → smoke-validation.

Promote is **all-or-nothing**. That was a correction, not the original design —
see "Decisions I made while you slept" below.

## Four bugs that only running it could find

None of these were caught by the unit suite. Three were caught by a live run and
one by an adversarial whole-cycle review.

**1. Cycle 1 had silently broken the engine.** Cycle 1's Task 9 added
`emitPromptTelemetry(pi)` as the first statement of `implementer.ts`'s extension
body — i.e. during extension loading, which Pi 0.84.1 forbids outright
("Action methods cannot be called during extension loading"). Every engine run
died at its child step: `implement` returned `isError`, nothing was written, and
the arm *looked like a fast rejection* rather than a broken harness. The tests
missed it because they call `emitPromptTelemetry` directly with a stub and never
exercise real extension loading. Fixed by emitting from `agent_start`, the
pattern `.pi/extensions/hello-world.ts` already documents. Verified live: the
engine went from 0/15 tests collected to accepted 15/15.

No banked evidence is affected — cycle 1 ran no batches — but had tonight's probe
run without checking, it would have reported the engine losing badly to a
comparator that was simply broken.

**2. A throwing gate leaked the worktree and its branch.** The coordinator
wrapped only the child call in `try`. The Phase 2 AST probes call
`spawnSync(python3)`, and Bun throws *synchronously* when that binary is missing,
so a gate could escape uncaught — leaking the worktree and its branch, after
which the next run with the same id failed on a branch collision for an entirely
unrelated reason. Everything after `createCandidate` now runs in `try/finally`.

**3. A half-applied promote reported `discarded`.** `promoteCandidate`'s apply
phase is not transactional; an I/O error partway leaves earlier files written.
Reporting that as "discarded" claims an untouched tree while it actually carries
the half-applied multi-file change this entire architecture exists to prevent.
New outcome: `promoted-partial`.

**4. Both entry points dropped the hermetic seam.** `harness/runner.py` sets
`PI_CODING_AGENT_DIR` on every `pi` process because child agents otherwise load
user-scope resources. Its absence cost twice: a live-session child would load the
operator's real agent directory, and the `envelope-coherent` arm being compared
against ran hermetic while the executor did not.

Bun-versus-Node divergence in `spawn` accounts for three separate bugs tonight
(#2 here, the missing smoke-validation executable during Task 4, and a
still-open one in `candidate-worktree.ts`'s `git()` helper). It is worth treating
as a known hazard in this codebase rather than a series of coincidences.

## Decisions I made while you slept

**Promote became all-or-nothing, against my own plan.** My plan's Task 6
specified a per-file partial promote — "promote the clean files and refuse only
the drifted one" — and a reviewer showed the consequence: a rename (delete
`a.py`, create `b.py`) lands the creation and drops the deletion, reconstructing
exactly the run-27 half-applied state. The spec said the opposite in two places
("there is no partial promote"; "a gate sequence that can leave a mixed
*promoted* state would reproduce the same failure shape one level up"). **I ruled
the spec governs** and changed the implementation, correcting the plan with a
visible note. This is the one design decision I made unilaterally and it is the
one to check first.

**I did not build a containment guard for the isolation hole.** Real enforcement
needs a `tool_call` hook in the child, and adding an extension to the child
changes the arm's extension set — which would have compromised the very
comparison the probe was about to make. Building an untested guard at 4am and
enabling it in the measured path risked more than it fixed. Disclosed instead,
loudly, in three places.

**I did not attempt cycles 4 or 5.** Curation is hours of judgment on real
repositories, and cycle 5's pre-registration margins are yours to set, not mine
to invent overnight. Producing either would have been the failure this project
keeps paying for.

## The probe

**This is a probe, not evidence.** Not pre-registered. Small n by construction.
It ran on `pi` 0.84.1 while `fourarm-v2` ran on 0.83.0, so **none of these numbers
may be compared with banked ones.** Its job was to answer three questions that do
not need statistics: does the executor work end-to-end against a real model, what
does the transactional boundary cost, and does promote/discard behave sanely on
real model output.

Design, following this project's rules even at probe scale: all three arms the
same night on the same machine, interleaved round-robin from a recorded seed;
`bounded-executor` and `envelope-coherent` information-matched by construction
(the executor renders `PHASE_2_SOURCE_CONTRACT`; the envelope arm's spec file is
a committed rendering of that same contract, verified byte-identical); a
discarded candidate delivered nothing and grades as a rejection.

I verified the two arms' `pi` invocations are argv-identical rather than trusting
the implementer's report, and matched the harness's base extension set so the
arms differ only by the transactional boundary and the gates.

### A flaw in the probe I caught mid-run, and what it means for these numbers

`wall_seconds` as recorded is **not comparable across arms** and is not used
below. For the reference arms it times `run_suite`, which does workspace
preparation and grading inside the timer; for the bounded executor it times only
the CLI subprocess, with preparation and grading outside. The bias runs in favour
of the thing I built, which is exactly the direction that needs catching before
publication rather than after. The run did not need redoing because the honest
fields were already being recorded: `pi_wall_seconds` for the reference arms and
`timings_ms.childMs` for the executor both isolate the model call.

### The model call, 8 runs per arm

| arm | accepted | model call, median | min | max |
|---|---|---:|---:|---:|
| bounded-executor | 8/8 | 40.6s | 33.8 | 48.5 |
| envelope-coherent | 8/8 | 41.0s | 33.5 | 51.5 |
| engine-oneshot | 6/8 | 75.5s | 64.9 | 78.7 |

The executor and the envelope arm sit on top of each other, which is what should
happen: same contract text, same budgets, same flags, same model. That agreement
is a sanity check on the harness, not a finding.

### The transactional boundary, which is the one number worth keeping

| stage | median | min | max |
|---|---:|---:|---:|
| create candidate worktree | 96.5 ms | 94 | 99 |
| all five gates | 287 ms | 276 | 289 |
| atomic promote | 1 ms | 1 | 2 |
| **total** | **385 ms** | 376 | 387 |

**About 0.95% of the model call.** The spread across 8 runs is 11 ms, because
none of this is model-dependent — it is worktree creation, five deterministic
checks and a rename. This is the quantity a small sample can carry honestly, and
it is the answer to "what does safety cost here": essentially nothing, against
an inference-bound workload.

All five gates passed on all 8 runs, all 8 promoted, and every run promoted the
same three files (`app.py`, `models.py`, `templates/complaints.html`).

### A second probe, with the containment guard active (6 cycles)

| arm | accepted | model call, median |
|---|---|---:|
| bounded-executor | 6/6 | 48.7s |
| envelope-coherent | 6/6 | 44.5s |
| engine-oneshot | 5/6 | 87.7s |

Boundary cost measured 507 ms here against 385 ms in the first probe — but that
is **not** the guard, and the reasoning matters more than the number:

- `gatesMs`, which accounts for most of the rise (287 → 393 ms), is **parent-side**.
  It runs after the child has exited. A guard living inside the child cannot
  touch it.
- Every arm slowed together: engine 75.5 → 87.7s, envelope 41.0 → 44.5s. That is
  this machine's documented throughput drift (23.0 → 5.6 tok/s within one
  evening has been measured before), not an effect of the change.

The bounded arm's model call sits 4.1s above the envelope's in this probe, where
the first probe had them identical (40.6 vs 41.0). **The mechanism does not
support reading that as guard cost.** The guard is one hook per tool call doing a
path resolution and a `realpath`; at the ~6 tool calls a median run makes, its
total cost is single-digit milliseconds. A 4-second gap is three orders of
magnitude too large for the mechanism, the min/max ranges overlap heavily
(33.0–70.2 vs 33.8–58.2), and n is 6. It is noise plus drift.

Pooling both probes, where envelope and engine ran identical code throughout:
bounded-executor 14/14, envelope-coherent 14/14, engine-oneshot 11/14. All six
guarded runs promoted, and every gate passed on every run.

### What these numbers do NOT show

- **Nothing about relative accuracy.** 8/8 versus 8/8 versus 6/8 at n=8 is not a
  difference; AgentClinic Phase 2 is at a documented accuracy ceiling and cannot
  discriminate. Reading anything into the engine's two rejections would be the
  error this project has withdrawn claims for before. Both engine rejections
  collected 15/15 tests — the workspace imported and the suite ran — so they are
  ordinary wrong-answer failures, not the collection-failure shape.
- **Nothing comparable to `fourarm-v2`.** Different `pi` version, not
  pre-registered, n=8 against 32.
- **The discard path was never exercised against real model output.** 8/8
  promoted, so the probe's third question — does promote/discard behave sanely on
  real output — is only half answered. The discard side is covered by the
  integration tests (the recorded `complaints_data` alias failure and a
  destructive edit dropping a route), but not by a live model tonight.
- **Nothing about the engine's true standing**, since the engine was broken until
  I fixed it a few minutes before this run and has had no other exercise since.

## What cycle 3 should start with

1. ~~A containment guard for the child~~ — **done**, see above.
2. **The remaining Bun/Node `spawn` divergence** in `candidate-worktree.ts`'s
   `git()` helper (a missing `cwd` throws instead of returning an error).
3. **The symbol-loss gate's cross-file blindness** — it refuses a moved symbol,
   and "a move/rename that changes imports and tests" is a named target work
   shape for the cycle-5 cohort.
4. Then the probes-and-slices work cycle 3 was originally scoped for.

## Verification posture

Every claim above that I could check myself, I checked myself rather than
accepting a subagent's report: the byte-identity of the extracted renderer, the
Python/TypeScript hash port across seven edge cases including vertical tabs and
astral-plane unicode, the path-traversal and binary-clobber fixes via my own
adversarial scripts, the worktree-leak fix, the argv equality of the two arms,
and Pi's absolute-path behaviour read from its own source. Where I could not
verify something, it is named as unverified.
