# Architecture: the bounded-implementer path

**One supported route, start to finish.** This page traces it in the order
execution actually happens, naming the real module and function at each
stage rather than describing the idea of one. If a claim here and the code
disagree, the code is right — file an issue or send a PR against this page.

This is the product path (distinguish it from the older, still-present
duration-suite harness `harness/runner.py` builds on — that machinery
answers a different, earlier question and is not part of this route; see
[history](#history) below).

## The path

```
task input                (a manifest + either a brief or a locating contract)
    |
    v
typed handoff              harness/typed_contract.py: build_typed_handoff()
    |                       -- HandoffContract + FileBaseline[], four tasks only
    v
bounded implementer         extensions/orchestration/implementer.ts
    |                       -- read/write/edit only, 16-turn / 30-tool caps,
    |                          runs as a Pi child under a pinned cell
    v
mutation engine              extensions/orchestration/mutation-engine.ts
    |                       -- MutationEngine.propose()/proposeEdits():
    |                          revision-checked, atomic, refuses undeclared
    |                          public-symbol loss
    v
preservation validation      the manifest's own command, run inside the
    |                          candidate worktree (tools/deliver_candidate.py)
    v
candidate ref               refs/satyrn/candidates/<task> -- reviewable,
    |                       cherry-pickable, discardable; never merged,
    |                       never promoted
    v
optional hidden-oracle grading   harness.workload.overlay_oracle(), run only
                             against a disposable grading copy the model
                             never sees (used by the Cycle 7 confirmatory
                             batch's primary metric, not by ordinary use)
```

## Stage by stage

**Task input.** A `workloads/svcs/tasks/<id>/manifest.toml` (writable scope,
preservation command, oracle command, attestations) paired with either the
task's own concise `brief.md` or a complete human-authored locating contract
under `workloads/svcs/contracts/locating/`. `harness/typed_contract.py`'s
`TaskSource` picks which one becomes `contract.task`; everything else the
executor is bound by comes from the manifest either way.

**Typed handoff.** `build_typed_handoff(task_id, worktree, task_source=...)`
assembles a `HandoffContract` (task text, exact writable files, validation
command, optionally `removableSymbols`) and a `FileBaseline[]` (SHA-256 +
line-ending + mode for every writable path, read from the worktree, not
guessed from the manifest). Deliberately narrow: only the four tasks in
`SUPPORTED_TASKS` are accepted — anything else is refused at this stage with
a clear error, not a silent pass-through (see
[`2026-08-11-phase7-cycle7-preregistration-design.md`](superpowers/specs/2026-08-11-phase7-cycle7-preregistration-design.md)
for why these four).

**Bounded implementer.** A Pi child, loaded with exactly
`extensions/orchestration/implementer.ts` and its same-repository import
closure (`IMPLEMENTER_EXTENSION_CLOSURE` in `tools/deliver_candidate.py`,
digest-verified against the pinned cell before every attempt). It registers
`read`, `write`, and `edit` — no `bash` — and enforces a 16-turn budget
(`MAX_IMPLEMENTER_TURNS`) and a 30-tool-call budget
(`ImplementerPolicy`'s default). It never sees the hidden oracle test
content or the target diff.

**Mutation engine.** Every `write` or `edit` the child calls routes through
`MutationEngine`, not Pi's own filesystem tools. `propose()` (whole-file) and
`proposeEdits()` (diff-shaped, `{oldText, newText}` pairs) share the same
checks: the file's SHA-256 baseline must match what the child last read
(refusing stale-revision writes), the proposal size is bounded, and an edit
that would delete a public symbol (`def`, `class`, a route decorator)
without a compensating add — anywhere in the invocation, not just the one
file — is refused unless the contract's `removableSymbols` declares it.
There is deliberately no separate pre-edit guard duplicating this check
ahead of the engine; a `preserve-symbols.ts` guard existed briefly and was
removed for exactly that reason (contract-blind, so it could refuse a
contract-authorized rename the engine would have admitted) — see
[`2026-08-11-phase7-cycle7-confirmatory-result.md`](superpowers/research/2026-08-11-phase7-cycle7-confirmatory-result.md).

**Preservation validation.** `tools/deliver_candidate.py` runs the
contract's own `validation` command (the manifest's preservation
command, with any manifest-declared deselects applied) inside the
candidate's disposable worktree. This is the same command string the
child's contract told it the parent would run — no separate, undisclosed
gate.

**Candidate ref.** A passing validation commits the candidate to
`refs/satyrn/candidates/<task>` and stops there. Nothing merges, nothing
promotes, the caller's own working tree is never touched. A failing
validation discards the worktree and produces a receipt explaining why, not
a ref.

**Optional hidden-oracle grading.** For research use (not part of ordinary
`deliver_candidate` calls), `overlay_oracle()` copies the real target test
file into a *separate*, disposable grading copy of the candidate commit's
tree, hash-verified against the manifest, and runs the manifest's
`oracle_command` there. This is how the Cycle 7 confirmatory batch's primary
metric (`oracle-passed`) was computed; the model itself never has access to
this file or this step.

## Guards still in the extension closure

Two guards ride along in every attempt's extension set, both contract-blind
by design (see `extensions/guards/`'s own module docstrings for why that
constraint exists):

- **`loop-breaker.ts`** — refuses an identical tool call repeated past a
  threshold within a window. General-purpose; also installable standalone
  outside this repository, see the README.
- **`preserve-symbols.ts`** — no longer wired into the implementer's
  `tool_call` handler (see "Mutation engine" above), but the module and its
  `symbolsIn()` helper remain, both because `mutation-engine.ts` imports
  `symbolsIn()` and because the guard itself may still have a standalone
  Pi-extension use case outside this bounded path.

## What is deliberately out of scope here

- **General contract authoring.** `harness/typed_contract.py` bridges a
  manifest to a `HandoffContract` for exactly four tasks; it is not a
  planner and does not decide what a fifth task's contract should say.
- **A planner arm.** The confirmatory comparison has two arms (brief,
  locating contract), not three — a planner-authored-contract arm is
  future work, not yet built.
- **Anything beyond `read`/`write`/`edit`.** No `bash` reaches the bounded
  implementer at any point in this path.

## History

`harness/runner.py`'s `Suite`/`Improvement`/`run_batch` machinery is the
Phase 1–5 duration-suite harness — a different, earlier measurement
question (does a technique change turn count / acceptance on a fixed
AgentClinic-style suite), not part of this path. It is still real,
still tested, and `harness/pi_invocation.py`'s `pi_command`/`pi_env` are
shared between both — but a change to the bounded-implementer path above
does not need to touch it, and vice versa. See
`BRIEF.md` and `ROADMAP.md` at the repository root (both marked
historical) for that earlier program's full record, and
[`docs/superpowers/index.md`](superpowers/index.md) for the cycle-by-cycle
design record spanning both.
