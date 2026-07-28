# Task 9 (Sections 2–3 Only) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute the Section 2 and Section 3 portions of the grading-path
reboot plan's Task 9 ("Write Sections 2–4 from scratch") — Section 4 is
explicitly OUT OF SCOPE for this plan (see below) and stays untouched.

**Architecture:** One new model-facing spec file (the higher-level roadmap
variant), then two chapter-prose rewrites (`docs/section-2-measurement/index.md`,
`docs/section-3-sdd/index.md`), each against the exact arc structure already
decided in two committed design docs — no new structural decisions, this
plan is prose execution against decisions already made.

**Tech Stack:** Markdown/MyST (Sphinx). No code changes.

## Global Constraints

- **Section 4 is explicitly out of scope.** Its chapter catalog is built on
  the pre-repair SP2 5/8 (62%) baseline and specific failure modes (child
  hang, overreach, drift, repeat spirals) that the grading-path reboot
  superseded — under the rebuilt oracle, unsteered goes 15–16/16 with no
  ditch. Re-scoping that chapter lineup is a real editorial decision, not a
  rewrite, and is deliberately left for the project owner. Do not touch
  `docs/section-4-keeping-on-track/`.
- **Evidence policy Rule 2: report literal results, not summaries.** Every
  number, artifact ID, and quoted finding in the new prose must trace to one
  of the source files each task lists — no invented numbers, no rounding
  that changes a citable figure, no paraphrasing a finding into something
  stronger or weaker than the source states.
- **No claims beyond what the sources support.** In particular: Rule 7 (no
  chapter may claim a success-rate delta) and D2 (failure-mode incidence is
  the primary metric) still bind this prose exactly as they bind any
  research report.
- **Rule 8 does not apply to this plan.** These are chapter prose files —
  evidence policy explicitly exempts "chapter prose and reports" from the
  different-model review requirement. (`examples/agentclinic/specs/roadmap-user-story.md`,
  Task 1 below, is the model-facing task spec, same category as the phase-3
  spec rewrite done earlier this session — also not measurement code.)
- **Do not run any batch.** Per
  [`docs/superpowers/specs/2026-07-28-eval-suite-chapter-design.md`](../specs/2026-07-28-eval-suite-chapter-design.md),
  Task 1's new roadmap file is not measured in this pass — that's future
  work for Section 3's mechanism measurement. No `pi` invocation, no omlx
  server needed for any task in this plan.
- **Sphinx build must stay clean.** Every task's gate includes
  `uv run --group docs sphinx-build -b html docs docs/_build/html` with no
  new warnings (broken toctree entries, unresolved refs).

---

### Task 1: Write the higher-level roadmap variant

**Files:**
- Create: `examples/agentclinic/specs/roadmap-user-story.md`

**Interfaces:**
- Consumes: `examples/agentclinic/specs/roadmap.md` (the existing detailed
  spec — read for the exact functional contract each phase must remain
  equivalent to; do not deviate from what it requires the app to do).
- Produces: the text Task 2's suite-authoring case-study chapter narrates
  deriving a suite from.

- [x] **Step 1: Read the source material**

Read, in this order:
1. `examples/agentclinic/specs/roadmap.md` — the existing detailed spec.
   This is the functional contract. `roadmap-user-story.md` must describe an
   app that satisfies the *exact same* observable behavior (same routes,
   same 303 redirect contract, same seed complaint text `Scope creep never
   ends.`, same tagline `Come in. Sit down. Tell us about your human.`) —
   business/user-story framing changes *how the requirement is stated*, not
   what is required.
2. `examples/acceptance/phase-3/test_acceptance.py` — the suite that will
   grade this variant unchanged (per the design doc's explicit decision:
   no new suite). Read it to confirm you are not accidentally describing an
   app that this suite would reject — every assertion in that file is a
   hard constraint on what `roadmap-user-story.md` may leave ambiguous.
3. `docs/superpowers/specs/2026-07-28-eval-suite-chapter-design.md` — the
   design this task implements.
4. `docs/superpowers/specs/2026-07-23-course-design.md` lines 30-41 — the
   master spec's own framing of what a "higher-level, business/user-story
   roadmap" means for this project (quoted quotes should not be copied
   verbatim beyond a short phrase; paraphrase the framing).

- [x] **Step 2: Write the file**

Structure: one heading per phase (three phases, matching the existing
spec's three phases — do not add a fourth; that was explicitly ruled out).
Each phase description states the user-facing outcome in business/user-story
language (e.g., "agents can see a welcoming home page when they arrive" not
"create `templates/home.html` extending `base.html` with a `{% block
content %}`") while still being unambiguous enough that the exact literal
strings and status codes the acceptance suite checks (the tagline, the seed
complaint text, the 303 status) are still derivable — do not omit or paraphrase
these three literal/numeric requirements away entirely; a business story can
still name an exact required phrase or status code when that IS the
business requirement (e.g., "the response must redirect the browser back to
the complaints board" is fine, but if a specific status code is contractually
required, state it — reference how the phase-3 spec rewrite from earlier
this session handled the identical tension for the 303 status, in
`examples/agentclinic/specs/roadmap.md`'s current Phase 3 section).

Do not describe implementation details (no file names, no class names, no
"use FastAPI's X"). Do describe outcomes precisely enough to be gradeable.

- [x] **Step 3: Verify against the acceptance suite by hand**

For each of the three phases, write one sentence (can be a code comment or
just verified mentally and noted in your report) tracing each acceptance
suite assertion for that phase back to something `roadmap-user-story.md`
states or clearly implies. If any assertion has NO textual basis in your
draft, revise the draft — this is the actual check this whole exercise
teaches, so do it for real, not just claim it.

- [x] **Step 4: Sphinx build check**

Run: `uv run --group docs sphinx-build -b html docs docs/_build/html`

Expected: no new warnings. (This file isn't referenced by any toctree yet —
Task 2 wires it in.)

- [x] **Step 5: Commit**

```bash
git add examples/agentclinic/specs/roadmap-user-story.md
git commit -m "docs(spec): higher-level business/user-story roadmap variant (Phases 1-3)"
```

---

### Task 2: Rewrite Section 2's chapter prose

**Files:**
- Modify: `docs/section-2-measurement/index.md` (full rewrite of the prose;
  keep the existing `{toctree}` directive's file list, updated only if a
  new file needs adding — it doesn't, for this task)

**Interfaces:**
- Consumes: Task 1's `roadmap-user-story.md` (for the suite-authoring case
  study), plus the source files listed below.
- Produces: nothing consumed by Task 3 — the two chapters are independent
  prose, cross-reference each other only where the existing content already
  does (e.g., links to the roadmap and to shared policy docs).

- [x] **Step 1: Read the source material**

Read, in this order:
1. `docs/section-2-measurement/index.md` (current file — the header/status
   banner and evidence links at the top are recent and correct; everything
   below the `{toctree}` needs full prose where there currently is none).
2. `docs/superpowers/specs/2026-07-27-next-phase-decision-design.md`
   Decision 2 — the exact arc structure for Section 2: **"what the workload
   actually is"** (D1/D2) then **suite-authoring** (Rule 3, D3, non-vacuity,
   D4, Rule 8).
3. `docs/superpowers/specs/2026-07-28-eval-suite-chapter-design.md` — the
   suite-authoring case study (Task 1's `roadmap-user-story.md`).
4. `docs/superpowers/policies/evidence.md` — D1, D2, D3, D4, Rule 3, Rule 8,
   quoted/cited accurately; this is the doctrine the chapter teaches.
5. `docs/superpowers/plans/2026-07-24-oracle-repair.md` — Amendment 1's
   empty-start incident ("Phase 2: 0/8" was actually phases 1+2 from empty)
   for the workload-definition arc's worked example.
6. `docs/superpowers/plans/2026-07-24-grading-path-reboot.md` — Task 1's
   incident (suite-authoring delegated to a model, discarded) and the F1/F2
   findings (`pytest.ini` + `--collect-only`, `os._exit(0)`) for the
   suite-authoring arc's worked examples.
7. `examples/acceptance/phase-3/test_acceptance.py` lines near the
   non-vacuity break matrix comments, for the break-matrix worked example.

- [x] **Step 2: Write the prose**

Required structure (as MyST headings under the existing H1 — do not change
the H1 or the status/evidence block above the `{toctree}`, only what comes
after it, and move the `{toctree}` to the end if it currently sits mid-file):

```
## What the workload actually is

[D1: incremental seeded start state, worked through the "Phase 2: 0/8" ->
"actually phases 1+2 from empty" incident. D2: pooled decision rule, why a
single sub-batch never decides alone (the two n=4 samples that returned 4/4
and 2/4 on identical config).]

## How to write an eval suite

[Rule 3: a passing smoke test is not a passing phase, as the opening claim.
D3: harness-owned, human-authored, overlaid after the model finishes --
narrated through the Task 1 incident (delegated to a model, discarded, and
why "a human reviews it after" isn't a substitute).
Non-vacuity gated both directions -- the break matrix as the worked example.
D4: the grader accepts no model-controlled input -- the pytest.ini and
os._exit(0) defeats, and why blacklisting an open category doesn't close it.
Rule 8: adversarial review by a different model as standing discipline.]

### Case study: deriving a suite from a higher-level story

[Walk through examples/agentclinic/specs/roadmap-user-story.md (Task 1):
what judgment calls a vaguer spec forces, then reveal that the existing
phase-3 suite already grades it correctly -- the pedagogical point that a
vaguer spec changes how much judgment deriving the grade takes, not what
is graded.]
```

Do not add a "validating the oracle" arc as a separate heading — that
content (oracle-invalid incident, `tests/test_oracle.py`) was reassigned in
Decision 2 to live inside the suite-authoring arc's D3/D4 material, not as
its own section. If you find yourself wanting a fourth top-level heading,
stop and fold it into one of the three above.

- [x] **Step 3: Self-check every number and quote**

Grep your draft for digits and quoted strings. For each, confirm it appears
in one of the seven source files from Step 1, verbatim or as an accurate
paraphrase of a non-numeric claim. List this check in your report (what you
checked, not just "I checked it").

- [x] **Step 4: Sphinx build check**

Run: `uv run --group docs sphinx-build -b html docs docs/_build/html`

Expected: no new warnings.

- [x] **Step 5: Commit**

```bash
git add docs/section-2-measurement/index.md
git commit -m "docs(section-2): chapter prose -- workload definition, suite authoring"
```

---

### Task 3: Rewrite Section 3's chapter prose

**Files:**
- Modify: `docs/section-3-sdd/index.md` (full rewrite of the prose below the
  existing status/evidence block; keep the `{toctree}` directive's file
  list as-is)

**Interfaces:**
- Consumes: source files listed below. Independent of Task 1/Task 2's
  output — do not block on them, though running after Task 2 is fine since
  this plan executes tasks in order.
- Produces: nothing consumed elsewhere in this plan.

- [x] **Step 1: Read the source material**

Read, in this order:
1. `docs/section-3-sdd/index.md` (current file — status/evidence block at
   top is current; "About SDD" section explaining the handoff-packet and
   small-units rationale is still accurate and should be KEPT, not
   rewritten — only the withdrawn/discarded chapter-prose gap needs filling).
2. `docs/superpowers/specs/2026-07-27-next-phase-decision-design.md`
   Decision 2 — Section 3's exact content: mechanism (orchestrator +
   implementer, packet/roadmap handoff — already covered by "About SDD",
   don't duplicate), the measurement apparatus interleaved per claim (not
   front-loaded), and the "when your metrics are fiction" catalog.
3. `docs/superpowers/plans/2026-07-24-oracle-repair.md` — the "Evidence
   triage" table's **replace-vs-extend 8/8 predictive** finding ("the
   strongest finding in the project") for the mechanism-claim worked
   example.
4. `docs/superpowers/plans/2026-07-24-grading-path-reboot.md` — the closing
   "honest note for Section 2's third chapter" (now Section 3's, per
   Decision 2's split) — the exact fabricated-metric catalog: duration
   always 0 with a passing unit test pinning that as correct; evidence
   tiers stamped GREEN unconditionally; a status narrating "70-74 subagent
   calls" when the artifact recorded 1; an "Oracle validated" line that
   never ran the oracle.
5. `docs/superpowers/roadmap.md` — Amendment 1 decision 4's disposition
   (Section III proceeds, cost-equivalence-only framing, no improvement
   claim) for how to frame what this section's evidence can and cannot
   claim.
6. `docs/section-2-measurement/research/2026-07-28-post-repair-sp1-phase3-less-prescriptive-spec.md` —
   the hang-incidence / turn-count delta finding (0/16->6/16 hangs,
   10.8->24.2 mean turns) as a concrete example of D2 failure-mode
   incidence in action, if a worked example of "incidence, not success
   rate" is needed beyond replace-vs-extend.

- [x] **Step 2: Write the prose**

Required structure (new headings after the existing "About SDD" section,
before the `{toctree}`):

```
## Measuring the mechanism

[Interleave, per claim, not front-loaded: for each mechanism claim
(replace-vs-extend 8/8 predictive; the cost-equivalence claim per Amendment
1 decision 4's disposition), introduce the apparatus that produced it
(telemetry reader, evidence ledger) right where the claim is made, not in a
separate up-front "how the measurement works" chapter.]

## When your metrics are fiction

[The fabricated-metric catalog from the grading-path reboot plan's closing
note, told plainly: this project's own automation produced these, and its
own agents cleared them on self-review -- the duration-always-0 bug pinned
by a passing test, the unconditional GREEN tier stamps, the "70-74 subagent
calls" status against an artifact showing 1, the "Oracle validated" line
that never ran anything. This is why Rule 8 (a different model reviews
anything that grades models) exists -- every one of these was found by a
different model, not by the author.]
```

Do not claim a success-rate improvement anywhere in this chapter (Rule 7).
Do not claim the orchestrator+implementer mechanism is *better* than
unsteered on this workload — per the roadmap's Amendment 1 decision 4
disposition, there is nothing left to improve on this workload; the only
claim available is cost-equivalence, and that measurement hasn't run yet
(it's future work, same as Section 3's use of `roadmap-user-story.md`) —
say so plainly rather than implying a result that doesn't exist yet.

- [x] **Step 3: Self-check every number and quote**

Same method as Task 2 Step 3, against this task's six source files.

- [x] **Step 4: Sphinx build check**

Run: `uv run --group docs sphinx-build -b html docs docs/_build/html`

Expected: no new warnings.

- [x] **Step 5: Commit**

```bash
git add docs/section-3-sdd/index.md
git commit -m "docs(section-3): chapter prose -- measurement apparatus, when metrics are fiction"
```

---

## Self-review notes

- **Spec coverage:** Task 9's Section 2 arc (three parts per the
  grading-path reboot plan: validating the oracle / what the workload
  actually is / when your metrics are fiction) is fully covered — "when
  your metrics are fiction" moved to Section 3 per Decision 2's explicit
  split, "validating the oracle" folded into suite-authoring's D3/D4
  material per Decision 2, both documented in Task 2 and Task 3's briefs
  respectively so the split isn't silently lost. Section 4 is explicitly
  excluded with reasoning, not silently dropped.
- **Placeholder scan:** the bracketed content inside the "Required
  structure" code blocks in Task 2/3 Step 2 are outlines, not placeholder
  prose to ship verbatim — each task's Step 1 reading list is what turns
  those outlines into real, sourced content. This is a deliberate
  adaptation of the plan template for a writing (not coding) task: the
  "complete code in every step" rule is replaced by "complete source list
  and required claims in every step," since course prose cannot be
  pre-written in the plan without simply writing the whole book here.
- **Type consistency:** N/A, no code.
