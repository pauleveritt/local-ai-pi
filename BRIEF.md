# Brief: bootstrapping Satyrn Engine

> **Historical record, not the current front door.** This is the bootstrap
> brief from before the bounded-implementer path
> (`extensions/orchestration/`, the typed-contract bridge, the Cycle 7
> comparison) existed. It is kept unedited for provenance — the values and
> the trap it names are still the ones this project runs by. For what's
> current, start at [`README.md`](README.md),
> [`docs/architecture.md`](docs/architecture.md), and
> [`docs/evidence-index.md`](docs/evidence-index.md) instead.

*Read this first if you want the original bootstrap context. Nothing else
from that period needs importing.*

## What we're building

**Satyrn Engine** — a Pi *extension* (not a fork of Pi) plus an eval harness,
for keeping small local models on track during real Python development. Working
name of the effort: "AI Our Way."

**North star: Evidence first.** A trustworthy, convenient, repeatable way to
collect evidence. Explicitly *not* over-designed, over-engineered, or too large
to absorb.

## Who it's for

Two volunteer groups of strong Python developers. All have used coding agents;
some have built skills; a handful have real eval/harness experience.

| Group | Owns | Capacity |
|---|---|---|
| **Engine** | the Pi extension, the eval harness, docs on writing suites | 15–20 h/wk, first month bootstrapping |
| **Suites** | eval suites for particular Python workflows | 5–10 h/wk |

Motivated by: making the world better, helping others succeed at local AI for
Python, and career upskilling. **Contributors are the priority audience.** A
loosely-linear set of how-tos is a subordinate output, written later from what
the suites prove — not a linear course.

## The trap we are deliberately avoiding

Three prior attempts turned into engineering efforts about orchestration —
hangs, timeouts, gating decisions, graders, cardinal rules — until the machinery
outgrew anyone's ability to hold it in their head. A fourth attempt produced,
in a single day: two workloads, six arms, five violation classes, three
amendment chains. Correct output, exploding surface area.

Consequences for how we work:

- **One phase at a time.** Phases group feature cycles; tangents go to the
  backlog, never into the current phase.
- **Owner-in-the-loop, one small thing at a time, strict SDD.** Speed is not
  the scarce resource; the owner's ability to hold the design in mind is.
- **Concept budget.** If a doc needs a term a 5-h/wk contributor can't absorb,
  the term goes — not the contributor. (Count the jargon: ladder, rung, grader,
  batch, checkpoint, run, arm, tier… that count is a design metric.)
- **Build the engine as needs in the suites arise.** No machinery ahead of the
  contract it serves.

## Phase 1 — the first milestone

> One AgentClinic Phase 1 run, hermetically graded, recorded to a checkpoint.
> Then n=16 reproducing ~15/16.

Phase 1 is chosen **because it is boring**: it starts from an empty workspace
(no seeding), and its answer is already known and trusted. The engine's first
job is to *reproduce a number we trust*, not to discover one. ~15/16 means the
engine works; 3/16 means the engine is broken, not the model. That inference is
unavailable on any phase whose answer is unknown.

## Candidates for transplant — nothing has crossed over yet

**This branch starts empty and stays empty except by deliberate decision.**
Nothing below has been imported. Each item is a candidate to be argued when
the need for it actually arises, on its merits at that moment — and may be
rejected, or rewritten from scratch instead. What follows is the *reasoning*
about each, so the decision is informed rather than re-derived.


**Strongest candidate (187 lines):**
`harness/grading.py` + `harness/grading_plugin.py` from the old branch. A
hermetic grader: fresh project dir with pinned deps, an allowlist of source
files, refusal of model-written config (`pyproject.toml`, `pytest.ini`,
`conftest.py`, `sitecustomize.py`), and a verdict read from a hook-written
results file rather than pytest's exit code. It exists because earlier versions
were defeated by `addopts = --collect-only` and an import-time `os._exit(0)`.
Two independent adversarial reviews probed it and found nothing.

**Candidate, read-once-then-write-fresh (don't keep the original open):** `prepare_workspace` (disposable temp
workspace, git-init for clean diffs) and the checkpoint/resume pair
(`_append_checkpoint` / `_load_checkpoint` — append per completed run, tolerate
a truncated final line, resume the remainder). Both sound; both tangled with
old specifics.

**Not a candidate — rewrite from scratch:** the orchestration layer (old `session.py` +
`runner.py`, 856 lines of accumulated fixes). Every hang and timeout lived here.

**Rejected outright:** the classifier/interpretation layer (4 of 8 recent defects
lived in it — it infers meaning from pytest text formatting), `telemetry.py`,
`packet_context.py`, both workloads, all six arms, the section/chapter docs
structure, and the eight numbered evidence rules.

**Seams, not hardcodes.** The one thing that actually cost the old project: the
case was hardcoded (`_SOURCE_FILES = ("app.py", "models.py")`, and
`examples/{acceptance,reference}/phase-N` baked into two functions) rather than
parameterised with a single caller. One case is right; naming it in a literal
is not.

## The evidence regime, for now: one sentence

> **A grader's verdict isn't evidence until it has accepted a known-good
> solution and rejected a known-broken one.**

That is the whole regime at bootstrap. Tiers, claim shapes, and degradation
budgets arrive when a suite author first needs to make a claim — not before.

A drafted (**not adopted**) four-rung replacement for the old Rule 7 exists at
`docs/superpowers/specs/2026-07-30-evidence-tier-ladder-proposal.md` on the
`user-story-batch` branch. Treat it as an input to a later phase, not a
decision.

## Practical environment

- Model: `omlx/gemma-4-12B-it-MLX-8bit` via `pi` 0.83.0.
- Local model server: `/Users/pauleveritt/.omlx/bin/omlx {start,stop,restart,diagnose}`,
  serves `127.0.0.1:8001`. **Verify it returns real model output before any
  batch** — when it is down, `pi` exits 0 with empty stderr and the harness
  records a fabricated result that looks like data.
- Known-good reference: the old oracle suite is 71 tests, green.
- Runs are sequential, never concurrent — one shared local model has no
  isolation.
- Prior work: branch `user-story-batch` (untouched). This branch (`restructure`)
  is an orphan — air-gapped, nothing imported except by explicit decision.

## What kind of effort this is

**A clean slate that gets gardened — not a clean-room rewrite.**

The branch begins with nothing in it. Things move over one at a time, each by
deliberate decision, and nothing gets in that hasn't been thought about. That
is different from clean-room (reimplementing without looking at the original),
and the difference is intentional: the grader exists *because* two specific
attacks defeated its predecessors. Rewriting it blind would mean re-earning
those defeats through incidents. So we read the old work, argue about each
piece, and transplant what earns its place.

The gardening metaphor is the operative one. The candidate list above is what
we've already thought about, with the reasoning attached — not a manifest of
things scheduled to arrive.

## First decision for the new session

**`ROADMAP.md` currently names Phase 1 "the restructure spec." That wording is
probably wrong and should be challenged first.**

The spec is the *output*; the milestone is the *direction*. Phase 1's direction
is closer to *"reproduce AgentClinic Phase 1 with a trustworthy engine"* — and
its first deliverable is the spec for how. Getting this right matters because
the phase name is what everyone reads to know what they're working on, and a
phase named after a document invites producing a document rather than a
working engine.

Decide the wording before anything else. Do not inherit it by default.

## Starting point for the new session

Begin with brainstorming, owner-driven, on Phase 1. Produce a **spec** — do not
build anything yet. Keep answers brief; go slow; one small thing at a time.
