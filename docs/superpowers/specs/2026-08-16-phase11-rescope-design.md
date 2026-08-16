# Phase 11, re-scoped — the handoff packet, human-directed

**Date:** 2026-08-16
**Status:** design, approved in brainstorming; implementation plan to follow
**Supersedes:** the scope of
[`2026-08-14-phase11-contract-authoring-bridge-shape.md`](2026-08-14-phase11-contract-authoring-bridge-shape.md)
— that document is not withdrawn, and its other open questions still
stand. What changes is its **deliverable set**: open question 3
(authoring reliability), which it named its own binding risk, is answered
"not by a machine, and not in this phase," and the autonomous
authoring-and-gating deliverable moves to Phase 14.
**Evidence base:** the 2026-08-15/16 spike
([handoff](../research/2026-08-15-phase11-handoff-to-construction.md),
[overnight result](../research/2026-08-16-phase11-overnight-result.md))
and the gate build
(`phase11-inspect-contract`,
[what survives](../research/2026-08-16-phase11-what-survives-result.md))

---

## Direction, one sentence

> `/implement` takes a handoff contract written in-session by the main
> agent, lints it against the repository, and drives the bounded
> implementer with it — and refuses, before spending a model call, when
> it cannot.

## Why re-scope

Three claims travelled together through Phase 11 and must be separated.
Only the first two are established, and only they ship here.

| Claim | Status | Phase |
|---|---|---|
| Machine-made **bounds** confine a 12B implementer | **Proven.** Bare envelope 0/24 → high candidate-created; `autowire` created 1/8 → 8/8 | **11** |
| Packet **content** moves outcomes floor→ceiling | **Proven.** `async-cm-enter` contract 4/4 vs brief 0/4 within one batch, p = 0.029; the contract arm then held **8/8 at n=8** in a later batch that had no brief arm. Derive-vs-apply explains why — handed a verbatim change this model reproduces 2031 chars 40/40, made to derive one it emits byte-identical no-ops | **11** |
| The system **authors and gates** content autonomously | **Not established.** Authored 3/8 vs hand 8/8 (p = 0.0256); the remediated authoring prompt went 0/8 with 8/8 all-noop; three of four content criteria deleted under pre-registered rules | **14** |

### The authorship fact that shapes the whole design

The contracts that measure 8/8 and 4/4 were **not written by a human**.
`workloads/svcs/contracts/locating/async-cm-enter.provenance.json`
records the author: `omlx/Qwen3.6-27B-8bit`, read-only tools, 480
seconds, reading the tree, 6,045 characters, 8 solution statements.

So the working configuration was always *a capable model with repository
access writes the contract*. What failed in the 2026-08-15/16 batches was
a **substitute** author — a 26B model brought in after the original's
weights disappeared from the machine — which produced drafts that were
behaviourally complete and operationally vague.

That is what makes an in-session authoring affordance the right shape:
the main agent occupies the role that was already generating the good
contracts, better resourced, and with the repository already open. It is
not a workaround for an unrealistic ask.

## The blocker this fixes

Found by review, not by a build, and recorded in the Phase 13 shape doc
as its one blocking open question.

Today on `main`, `/implement <text>` writes the text to a temporary file
and calls `deliver_candidate.py --prompt-file`, which selects the
probe-cap child (`extensions/probe-cap.ts`) with stock tools and a
hardcoded `pytest -q`. The contract-requiring implementer child is
reachable **only** via `--contract-task <svcs task id>`, a smoke bridge
over four fixed tasks. Nothing in the product path ever builds a
contract.

And `extensions/implementer/implementer.ts:69-72` makes the failure
silent: with `SATYRN_HANDOFF_CONTRACT` unset, the child's entire system
prompt is *"The implementer handoff contract is missing or invalid. Do
not call tools; report this configuration failure."* So a
contract-flavoured invocation burns a full model call and a validation
timeout, then reports "candidate changed nothing" — unconditionally, by
construction, with no message saying why.

**AC-1 (acceptance criterion).** `/implement` invoked with no contract, a
missing file, an unparseable file, an invalid schema, or a blocking lint
finding produces a message naming the cause and exits non-zero, **having
made zero model calls**. The test asserts the model was never invoked —
not merely that the exit code was non-zero, which would pass even if the
call happened first.

## Deliverables

**1. An in-session authoring affordance.** The main agent reads the
repository and writes a contract file. Its instructions encode what the
measurements showed matters:

- Declare the bounds **explicitly** as structured fields. Nothing is
  inferred from prose — inference is what the deleted `tree_claims`
  nomination rule did, and it fired on the shape of a line rather than
  what the line asked for.
- Name **concrete operations** in the body: *"append `(name, svc)` to
  `self._on_close`, rebind `svc`"*, not *"register the resulting cleanup
  mechanism"*. This is the measured difference between the contract that
  scores 8/8 and the remediated draft that scores 0/8 with every run
  collapsing into no-op edits.

**Whether this is a skill, an extension, or something else is
deliberately left open** — see Open questions.

**2. `/implement <contract-file>`.** Loads, validates, lints, and either
refuses or drives the implementer. `--prompt-file` is removed, so the
product has exactly one path.

`--contract-task` — the four-task svcs smoke bridge — **stays for now**,
used only by the harness batch drivers, and is marked for removal. The
original intent was to fold it into the file path in this phase. Deferred
on simplicity grounds: folding means regenerating four fixtures and
proving them byte-identical, because 100+ recorded attempts depend on
that contract text and a drift would be invisible in a rate. That is the
largest and riskiest piece of work in the phase, and it buys internal
tidiness rather than user-visible value. A user still sees one way to
build a contract.

**3. The path lint — the rule, not the framework.** The gate branch's
`tree_claims` blocking logic is about **fifteen lines**: collect the paths
the body names, and refuse any that is neither a file in the base tree
nor listed in `writableFiles`. The surrounding ~365 lines
(`Packet`/`Finding`/`CheckerReport`/`Inspection`, severities, advisory
findings, per-criterion timing) exist to host a five-criterion gate that
no longer exists.

Port the rule as a small function. Carry across exactly two things from
the discipline, because both were earned by shipped bugs:

- **Refuse to run without `writableFiles`** rather than passing
  everything — this is the silent zero, and it is one guard, not a
  framework.
- **"Cannot judge" and "packet is bad" get different exits** — the gate
  shipped, and fixed, a bug conflating them.

The 380-line module stays on `phase11-inspect-contract` as the record of
what was measured and deleted.

## What is deliberately not in Phase 11

- Any authoring by a local model.
- Any machine judgement of packet **content** — the shipped lint judges
  *form*.
- Any executor change: F5 policy/loop-breaker ordering, and
  `MAX_PROPOSAL_BYTES` being size-blind. Each changes the arm and needs
  its own cell.
- Any live batch as a deliverable. The single live run in this phase is a
  smoke test, and the spec calls it one.

## Components and data flow

```
prompt
  └─ agent authors ──► contract file (front-matter + body)
                          │
        /implement <path> ─┤
                          ▼
              deliver_candidate.py --contract
                 1. parse front-matter + body
                 2. validate against HandoffContract
                 3. tree_claims lint vs repo
                 ├─ fault ──► refuse, name the cause, exit ≠ 0  (no model call)
                 └─ clean ──► SATYRN_HANDOFF_CONTRACT=<json>
                                  ▼
                        pi child: implementer.ts
                        (bounded edits; the parent owns validation)
                                  ▼
                        parent validation → candidate ref + receipt
```

| Piece | Where | New? |
|---|---|---|
| Authoring affordance | session | new |
| Contract file format + parser | `harness/` | new, small |
| `--contract <path>` | `tools/deliver_candidate.py` | replaces `--prompt-file` |
| Path lint (~15 lines + one guard) | `harness/` | ported from the gate branch |
| Implementer child | `extensions/implementer/` | unchanged |
| `--contract-task` | `tools/deliver_candidate.py` | unchanged, harness-only, marked for removal |

### Why the lint can live in the product path

The gate was designed as a key-holding admission gate, which meant it
could never run inside `/implement` — `/implement` has no answer key.
Every key-holding criterion was then deleted under pre-registered rules.
What survives needs **only the base tree and `writableFiles`**: no model,
no grader, no network, no key. That it can ship in the product path is an
accident of the deletions, and the one place that night's outcome came
out better than its design.

### The contract file

Front-matter carries the structural fields; the body is the `task` prose.
The exact field list follows `HandoffContract`
(`harness/typed_contract.py`, mirrored by `isContract()` in
`extensions/implementer/implementer.ts` — one wire format, two
declarations, kept in sync by hand).

```markdown
---
writableFiles: [src/svcs/_core.py]
readableFiles: [src/svcs/**, tests/**]
validation: pytest -q -p no:cacheprovider
knownFacts:
  - ...
acceptanceStrings:
  - ...
---
# Enter async context managers in aget()

...the recipe, naming concrete operations...
```

**Only `writableFiles` and `validation` are required.** Everything else
defaults to empty. A contract that declares its bounds and its check is a
valid contract; `knownFacts` earns its place when the task turns on a
fact the tree cannot reveal, and `preservedBehavior` stays optional
because the evidence on rendering it is mildly against. The author should
not have to fill in fields to satisfy a schema.

## Error handling

A zero must be loud. Five silent-zero incidents in the spike were caught
by a duration or an implausible zero, never by the value; and the gate's
own CLI shipped a bug leaking internal errors out as exit code 1, its
code for "bad packet." So the classes get distinct, documented exits, and
three of them happen before any model call.

`deliver_candidate.py` already defines 0/1/2/3, so the new class takes 4
rather than renumbering anything:

| Class | Example | Exit | Model called? |
|---|---|---|---|
| Success | candidate ref written | 0 | yes |
| Candidate not created | child ran, wrote nothing, or validation failed | 1 | yes |
| Refused — bad packet | missing file, invalid schema, path neither in tree nor `writableFiles` | 2 (existing refusal code) | **no** |
| Infrastructure | dead server, unusable setup | 3 (existing) | no |
| Instrument fault | the lint cannot judge | **4 (new)** | **no** |

"The tool cannot judge" (4) must never read as "your packet is bad" (2).

In practice the schema makes `writableFiles` required, so the lint's
own guard is unreachable from the CLI and exit 4 is defence in depth —
about five lines. It is kept because the conflation it prevents is a bug
the gate branch actually shipped.

## Testing

Deterministic and model-free, with one marked exception.

- **The corpus's lessons come across as fixtures, not as 16 files.** The
  gate branch measured 2 authored drafts blocked
  (`src/svcs/container.py`, where the tree has `_core.py`;
  `src/svcs/flask/app.py`, where it has `flask.py`) and 0/8 false
  positives on committed contracts — including `autowire`, whose contract
  correctly names a module that does not exist yet because that task's
  job is to add it. Those three cases become explicit unit tests. The
  full corpus stays on `phase11-inspect-contract`; copying it over would
  import a measurement apparatus to re-prove a fifteen-line function.
- **AC-1 tests assert the model was never invoked.**
- **One smoke test, marked as such.** `async-cm-enter`, contract authored
  through the new affordance, does a passing candidate come out. **n=1, a
  wiring check. It is not a rate.**

## Phase 14 — inherited work, with entry conditions

Written as conditions rather than a wish list, so this is not a place
claims go to be forgotten.

1. **Measure affordance-authored contracts.** Phase 11 ships this path
   unmeasured; Phase 14 measures a rate against hand contracts as
   concurrent controls. Highest-value unknown in the area. Inherits a
   permanent confound: `Qwen3.6-27B-8bit`, which authored the 8/8
   contracts, no longer exists on the machine.
2. **The runtime-signal meter.** Every good-content run was 3 turns, one
   edit, 23–43s; every bad one 200–420s of flailing. Wall time separated
   arms completely, needs no answer key, and nobody has built it.
3. **Automated content gating** — reopens only with: a target that is
   *not* a single reference patch; a pre-registered delete rule on
   labelled packets; and a deliberate stability-under-perturbation test.
   The third condition is what killed `missing_facts` — a known-good 4/4
   packet rejected in three of four prompt configurations, each time for
   a different pretext.
4. **Local-model authoring.** 3/8 complying, 0/8 with the prohibition
   relaxed. No reopen without a reason to think the author can produce
   concrete operations rather than merely be permitted them.
5. **Executor changes, each in its own cell:** F5 ordering;
   `MAX_PROPOSAL_BYTES` size-blindness (32 KiB flat against a 29 KB base
   file, which aborted Experiment B).
6. **Transfer:** `magicmock-factory` after the cap fix; another task;
   another model.

Carried forward verbatim: the spike's stop-list, its do-not-re-derive
list, and *"a live batch has an authored packet in at least one arm, or
it does not run."*

## Open questions

1. ~~Skill, extension, or another mechanism for the authoring
   affordance?~~ **Decided in planning: a Claude Code skill** at
   `.claude/skills/write-handoff-contract/SKILL.md`. Markdown
   instructions, no code, no runtime — the smallest thing that puts the
   guidance where the authoring already happens. An extension would add a
   build artifact and a load path for content that is entirely prose.
2. **Where do authored contract files live** — a conventional path in the
   repository, a temporary directory, or the user's choice? Affects
   whether contracts are reviewable artifacts in version control, which
   is one of the phase's stated benefits.
3. **When does `--contract-task` go?** Deferred out of this phase (see
   deliverable 2). Removing it needs the four fixtures regenerated as
   files and pinned byte-identical against `build_typed_handoff`, so it
   is its own small piece of work whenever it happens.

## What this design does not establish

- Anything about a different implementer model. Every rate cited is
  `gemma-4-12B-it-MLX-8bit`, Pi 0.84.1.
- Any rate for affordance-authored contracts. Phase 11 runs one smoke
  test and claims nothing from it.
- That the lint predicts success. It is a lint, not a predictor: 2-vs-0
  on 16 packets, and that split is partly a property of the authoring
  setup — the hand authors could read the tree and the drafting model
  could not.
- That packet content helps on tasks other than the two measured.
