# Phase 3 Spec Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the Phase 3 section of the model-facing spec
(`examples/agentclinic/specs/roadmap.md`) so it no longer states the answer
to its own known traps, re-validate the oracle per evidence policy Rule 6,
re-run the unsteered n=16 baseline against the rewritten spec, and record
the result's relationship to the standing Phase 3 report.

**Architecture:** One markdown edit (the spec), one new regression test
(guards against the hint reappearing), one oracle re-validation run, one
live n=16 batch via the existing `scripts/scout.py` harness, and one
provenance/decision step that interprets the result per Amendment 2's
pre-registered rule. No harness or acceptance-suite code changes — this
plan touches only the model-facing spec and adds a test on its content, so
per [`docs/superpowers/specs/2026-07-27-next-phase-decision-design.md`](../specs/2026-07-27-next-phase-decision-design.md)
Decision 1 rationale 2, **no Rule 8 review is required.**

**Tech Stack:** Python 3.14, pytest, the existing `harness/` package
(`harness.runner.run_baseline`, `harness.workspace`), `pi` CLI running
`omlx/gemma-4-12B-it-MLX-8bit` locally.

## Global Constraints

- **Model:** `omlx/gemma-4-12B-it-MLX-8bit` (fixed for all batches in this
  project; do not substitute).
- **Batch size:** n=16, unsteered (SP1 profile), per Amendment 2 — no
  sub-batch may decide alone.
- **Decision rule (Amendment 2, unchanged by this plan):** ≥15/16 → phase
  solved; ≤12/16 → candidate ditch; 13–14/16 → ambiguous, decide with the
  human. Do not auto-escalate or auto-invent a harder workload on any
  outcome — Amendment 1's own text: "the roadmap decision... returns to the
  human."
- **Start state (D1):** Phase 3 runs seed from `examples/reference/phase-2`
  (`harness.workspace.seed_for_phase(3)`), never from empty.
- **Rule 6:** any change to the workload (the model-facing spec counts)
  re-triggers oracle validation (`tests/test_oracle.py` green) before the
  next published batch.
- **The acceptance suite and reference solution are NOT modified by this
  plan.** `examples/acceptance/phase-3/test_acceptance.py` requires exactly
  `response.status_code == 303` on the POST — this plan's spec rewrite must
  preserve that numeric requirement even while removing the implementation
  hint that names it (`RedirectResponse`) and the test-technique hint
  (`follow_redirects=False`). Verified in the acceptance suite at
  `examples/acceptance/phase-3/test_acceptance.py:201-210` before writing
  this plan.
- **Report provenance:** the new report's filename and header must make its
  relationship to the standing
  [`docs/section-2-measurement/research/2026-07-27-post-repair-sp1-phase3.md`](../../section-2-measurement/research/2026-07-27-post-repair-sp1-phase3.md)
  (16/16) explicit — corroborates or supersedes, decided by the outcome, per
  the design doc's "What this design does not decide."

---

### Task 1: Regression test — the spec must not leak its own trap answers

**Files:**
- Create: `tests/test_spec_prescriptiveness.py`
- Test: same file (this task is the test)

**Interfaces:**
- Consumes: `examples/agentclinic/specs/roadmap.md` (read as plain text —
  no import from `scripts/scout.py`, which is a standalone script, not a
  package; the section-extraction logic is small enough to duplicate
  locally rather than refactor `scripts/scout.py` into an importable
  module for one caller).
- Produces: nothing consumed by later tasks — this is a standing regression
  gate, exercised again in Task 2.

- [ ] **Step 1: Write the failing tests**

```python
"""Regression: the phase-3 model-facing spec must state the behavioral
contract without leaking the answer to its own known traps.

Motivated by docs/superpowers/specs/2026-07-27-next-phase-decision-design.md
(Decision 1) and lessons.md #13 (the follow_redirects trap). The acceptance
suite (examples/acceptance/phase-3/test_acceptance.py) requires exactly
response.status_code == 303 on POST /complaints -- that numeric requirement
must stay in the spec. What must NOT stay: the FastAPI class name that
implements it, and the test-authoring instruction that tells the model
exactly how its own tests must observe the redirect.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROADMAP = REPO_ROOT / "examples" / "agentclinic" / "specs" / "roadmap.md"


def _phase_section(phase: int) -> str:
    text = ROADMAP.read_text()
    lines = text.splitlines()
    pattern_start = f"## Phase {phase} "
    pattern_next = f"## Phase {phase + 1} "
    start = None
    for i, line in enumerate(lines):
        if line.startswith(pattern_start) and start is None:
            start = i
        elif start is not None and line.startswith(pattern_next):
            return "\n".join(lines[start:i])
    if start is not None:
        return "\n".join(lines[start:])
    raise ValueError(f"Phase {phase} not found in roadmap")


def test_phase3_spec_does_not_name_the_redirect_implementation():
    section = _phase_section(3)
    assert "RedirectResponse" not in section, (
        "Phase 3 spec names the FastAPI redirect class directly -- this "
        "hands the model the implementation, not just the contract"
    )


def test_phase3_spec_does_not_leak_the_test_technique():
    section = _phase_section(3)
    assert "follow_redirects" not in section, (
        "Phase 3 spec tells the model exactly how its own tests must "
        "observe the redirect -- this is the follow_redirects trap "
        "(lessons.md #13) stated as an instruction instead of left for "
        "the model to discover"
    )


def test_phase3_spec_still_states_the_303_behavioral_contract():
    section = _phase_section(3)
    assert "303" in section, (
        "removing the implementation hint must not also remove the actual "
        "behavioral requirement the acceptance suite grades -- see design "
        "doc Decision 1 rationale 2"
    )
```

- [ ] **Step 2: Run tests to verify the first two pass and the third fails**

Run: `uv run pytest tests/test_spec_prescriptiveness.py -v`

Expected: `test_phase3_spec_does_not_name_the_redirect_implementation` FAILS
(current spec contains `RedirectResponse`); `test_phase3_spec_does_not_leak_the_test_technique`
FAILS (current spec contains `follow_redirects`);
`test_phase3_spec_still_states_the_303_behavioral_contract` PASSES (current
spec already contains `303`). This confirms the tests actually exercise the
current, unrewritten spec text before Task 2 changes it.

- [ ] **Step 3: Commit the test on its own**

```bash
git add tests/test_spec_prescriptiveness.py
git commit -m "test: regression guard — phase-3 spec must not leak its own trap answers"
```

---

### Task 2: Rewrite the Phase 3 spec section

**Files:**
- Modify: `examples/agentclinic/specs/roadmap.md` (Phase 3 section)

**Interfaces:**
- Consumes: nothing new.
- Produces: the rewritten spec text that `scripts/scout.py`'s
  `extract_phase_prompt(3)` will read at batch time (Task 4) — no code
  change needed there since it reads the file at runtime.

- [ ] **Step 1: Replace the Phase 3 section**

Current text (`examples/agentclinic/specs/roadmap.md`, the `## Phase 3 —
Add Complaint` section):

```markdown
## Phase 3 — Add Complaint

- Add a form at the bottom of `templates/complaints.html` with:
  - `POST` method to `/complaints`
  - Text input for agent name
  - Textarea for complaint text
  - Submit button
- Add `POST /complaints` route in `app.py`:
  - Import `Complaint` from `models`
  - Read `agent_name` and `text` from form data (`Form` from `fastapi`)
  - Create a new `Complaint` and append to the `complaints` list
  - Redirect to `GET /complaints` (use `RedirectResponse` with status 303)
- Write tests in `tests/test_app.py`:
  - `POST /complaints` with `agent_name` and `text`, using `follow_redirects=False`, returns 303 with `Location: /complaints`
  - After `POST /complaints`, `GET /complaints` response includes the newly added complaint
```

Replace with:

```markdown
## Phase 3 — Add Complaint

- Add a form at the bottom of `templates/complaints.html` with:
  - `POST` method to `/complaints`
  - Text input for agent name
  - Textarea for complaint text
  - Submit button
- Add `POST /complaints` route in `app.py`:
  - Read `agent_name` and `text` from the submitted form data
  - Create a new complaint from the submitted data and add it to the
    complaints list
  - Respond with a 303 redirect to `GET /complaints`
- Write tests in `tests/test_app.py` covering the new route's behavior
```

What changed and why, matching Task 1's assertions:
- Dropped `Import Complaint from models` / `Form from fastapi` — import
  mechanics, not the behavioral contract; Phases 1–2 don't spell these out
  either.
- Dropped `use RedirectResponse` — names the implementation class.
- Kept `303` — the acceptance suite's literal, non-negotiable requirement
  (design doc Decision 1 rationale 2).
- Dropped the two literal test assertions (`follow_redirects=False`, the
  exact `Location` header check, the exact GET-after-POST check) — these
  told the model precisely what its own tests should assert, which
  functions as a description of how the acceptance suite probes the route.
  Replaced with an unprescriptive instruction to write tests "covering the
  new route's behavior," matching Phase 1/2's own level of detail for their
  test-writing bullets.

- [ ] **Step 2: Run the regression tests to verify they now all pass**

Run: `uv run pytest tests/test_spec_prescriptiveness.py -v`

Expected: all three tests PASS.

- [ ] **Step 3: Commit**

```bash
git add examples/agentclinic/specs/roadmap.md
git commit -m "docs(spec): stop pre-defusing the phase-3 redirect trap in the model-facing spec"
```

---

### Task 3: Rule 6 oracle re-validation and full suite check

**Files:**
- None modified — this task only runs existing tests and records the
  result. No commit of its own; folded into Task 4's report if nothing
  fails (matching the writing-plans guidance to fold verification into the
  task whose deliverable needs it, when there is no independent artifact to
  commit).

**Interfaces:**
- Consumes: `tests/test_oracle.py` (unmodified), the unmodified
  `examples/reference/phase-3/` and `examples/acceptance/phase-3/`.
- Produces: a go/no-go signal for Task 4. If this task fails, STOP — do not
  run the batch. The spec rewrite touched only the model-facing prompt, not
  the reference solution or acceptance suite, so this is expected to pass
  unchanged; Rule 6 requires re-running it anyway because the workload
  changed.

- [ ] **Step 1: Re-validate the oracle**

Run: `uv run pytest tests/test_oracle.py -v`

Expected: all tests PASS, including
`test_acceptance_suite_accepts_reference[phase3]` (direction 1: the
unmodified phase-3 reference solution still satisfies the unmodified
acceptance suite — confirms the spec rewrite did not silently change what
"correct" means).

- [ ] **Step 2: Run the full test suite**

Run: `uv run pytest -q`

Expected: fully green, no new failures relative to the pre-rewrite baseline
(`154 passed` per the grading-path reboot plan's Task 8 gate — the count may
differ slightly with Task 1's three new tests added; the delta should be
exactly `+3 passed`, nothing else changed).

- [ ] **Step 3: If either check fails, stop and report**

Do not proceed to Task 4. A Rule 6 failure here means the spec rewrite
somehow changed what the acceptance suite or reference solution require —
re-read Task 2's diff against the acceptance suite's exact assertions
(`examples/acceptance/phase-3/test_acceptance.py:201-224`) before touching
anything else.

---

### Task 4: Run the n=16 unsteered batch against the rewritten spec

**Files:**
- Create (generated by the harness, not hand-written):
  `docs/section-2-measurement/research/<run-date>-post-repair-sp1-phase3.md`
- Create: `.pi-eval-checkpoints/scout-phase3-n16.jsonl` (checkpoint —
  already gitignored, matches the existing mechanism from Task 8 of the
  grading-path reboot plan)

**Interfaces:**
- Consumes: `scripts/scout.py`'s existing `run_scout(phase=3)` — no code
  change. It calls `extract_phase_prompt(3)`, which reads the just-rewritten
  spec section, and `harness.runner.run_baseline(...)` with
  `seed=seed_for_phase(3)` (= `examples/reference/phase-2`),
  `acceptance_suite=acceptance_suite_for_phase(3)` (unmodified).
- Produces: a `BaselineReport` written to the path above, consumed by
  Task 5.

**Preconditions:**
- Tasks 1–3 committed and green.
- The `pi` CLI is on `PATH` and can reach `omlx/gemma-4-12B-it-MLX-8bit`
  locally — same precondition every prior batch in this project has had; do
  not attempt this task in an environment where earlier batches (e.g. the
  standing Phase 1–3 reports) could not have been produced either.
- **Check for a filename collision before running:** if
  `docs/section-2-measurement/research/<today>-post-repair-sp1-phase3.md`
  already exists (only possible if this task and the standing 2026-07-27
  report were run on the identical calendar date), the harness's
  `write_report` will overwrite it silently. Verify with `ls
  docs/section-2-measurement/research/*post-repair-sp1-phase3*.md` first; if
  a same-date collision would occur, copy the existing file aside before
  running and diff after, rather than lose it.

- [ ] **Step 1: Check for filename collision**

```bash
ls docs/section-2-measurement/research/*post-repair-sp1-phase3*.md
```

Expected: only the standing `2026-07-27-post-repair-sp1-phase3.md`. If
today's date matches, see the precondition note above before continuing.

- [ ] **Step 2: Run the batch**

```bash
uv run python scripts/scout.py 3
```

Expected: runs to completion (n=16, ~60–200s per run per the standing
report's timing, so budget 20–40 minutes total). Prints a final line of the
form `→ <k>/16 — Phase 3 solved. Escalate to Phase 4.` or `→ <k>/16 —
candidate ditch at Phase 3.` or the 13–14 ambiguous message. **Run this in
the background** (or a terminal multiplexer) — do not let a shell timeout
or session teardown kill it; the grading-path reboot plan's Task 8
precondition documents three batches lost this way before checkpointing was
added. Checkpointing is already in place (`_append_checkpoint` in
`harness/runner.py`), so a kill is now resumable, but avoiding the kill is
still cheaper than resuming.

- [ ] **Step 3: Record the raw outcome before doing anything else**

Note the printed success count, the report path, and today's date. Do not
proceed to Task 5's interpretation until this raw result is written down
somewhere durable (even just the next commit message) — this guards against
motivated reasoning about the decision rule after the fact, which the
project's own evidence policy exists to prevent.

---

### Task 5: Provenance, decision rule, and disposition

**Files:**
- Modify: the report file generated in Task 4 (rename + header addition —
  prose, not measurement code; exempt from Rule 8 per evidence policy: "
  Chapter prose and reports are exempt; what grades models is not.")
- Possibly modify: `docs/superpowers/roadmap.md` (only if the ditch
  reopens — see Step 3)

**Interfaces:**
- Consumes: Task 4's report and raw success count.
- Produces: the final disposition this plan exists to produce.

- [ ] **Step 1: Rename the report to self-document as the rewritten-spec variant**

```bash
git mv docs/section-2-measurement/research/<run-date>-post-repair-sp1-phase3.md \
       docs/section-2-measurement/research/<run-date>-post-repair-sp1-phase3-less-prescriptive-spec.md
```

- [ ] **Step 2: Add the provenance header**

Insert directly under the report's H1 (`# Baseline: Phase 3 — Add
Complaint`):

```markdown
**Spec variant:** rewritten phase-3 spec, commit `<Task 2's commit sha>` —
no longer states the answer to the redirect-status and `follow_redirects`
traps (`lessons.md` #13). See
[`docs/superpowers/specs/2026-07-27-next-phase-decision-design.md`](../../superpowers/specs/2026-07-27-next-phase-decision-design.md)
Decision 1.
```

- [ ] **Step 3: Apply the pre-registered decision rule and write the disposition**

At the end of the report, add a `## Disposition` section. Choose the branch
matching Task 4's actual result — do not blend or hedge between them:

**If ≥15/16 (phase still solved):**

```markdown
## Disposition

**Corroborates, does not supersede,** the standing
[2026-07-27 report](2026-07-27-post-repair-sp1-phase3.md) (16/16). Removing
the implementation and test-technique hints did not reopen a ditch at
n=16 — spec prescriptiveness was not load-bearing for the original no-ditch
result. Amendment 1 decision 4's disposition (Section III proceeds,
cost-equivalence framing) stands unchanged.
```

**If ≤12/16 (candidate ditch):**

```markdown
## Disposition

**Supersedes** the standing
[2026-07-27 report](2026-07-27-post-repair-sp1-phase3.md). The prior 16/16
measured compliance with a spec that stated its own answer, not general
capability — with the hints removed, Phase 3 is a candidate ditch. This
reopens Amendment 1 decision 4 (the pre-registered no-ditch contingency):
per that amendment, the next workload decision returns to the project
owner, not to unilateral escalation. **Do not proceed with Section III's
cost-equivalence batches on the assumption that Phase 3 is solved** until
that decision is made.
```

**If 13–14/16 (ambiguous):**

```markdown
## Disposition

**Ambiguous** — within Amendment 2's undecided band. Report honestly;
per Amendment 2, pool with 4 more identical-config runs before deciding
rather than treating this sub-batch as final. Do not proceed to Section
III's cost-equivalence batches until pooled.
```

- [ ] **Step 4: If the ditch reopened or the result is ambiguous, update the roadmap banner**

Only for the ≤14/16 branches: edit `docs/superpowers/roadmap.md`'s "Next
action" banner to point at this report and state plainly that Section III's
premise (from the 2026-07-27 disposition) is now in question, per this
plan's Task 5 Step 3. Do not silently leave the old banner's "no ditch found
anywhere" claim standing next to a report that contradicts it.

For the ≥15/16 branch, no roadmap change is needed — the existing banner's
claim is corroborated, not altered.

- [ ] **Step 5: Commit**

```bash
git add docs/section-2-measurement/research/ docs/superpowers/roadmap.md
git commit -m "evidence: post-repair phase-3 baseline, rewritten spec (n=16)"
```

---

## Self-review notes

- **Spec coverage:** Decision 1's three rationale points are each covered —
  rationale 1 (Rule 6) by Task 3, rationale 2 (contract-vs-hint) by Task 2's
  exact wording plus Task 1's regression test, rationale 3/4 (Phase-3-only
  scope, evidence dependency) by this plan only touching Phase 3 and Task 5
  explicitly naming what the result does and doesn't imply for Section III.
  The design doc's "report provenance" requirement is covered by Task 5
  Steps 1–2. The design doc's "Task 9 prose waits on this result" note is
  not this plan's responsibility — it belongs to whichever plan executes
  Task 9, not this one.
- **Placeholder scan:** `<run-date>`, `<today>`, and `<Task 2's commit sha>`
  are the only bracketed placeholders, and each is a value only knowable at
  execution time (a date, a commit hash) — not missing design content. No
  TBD/TODO.
- **Type consistency:** N/A — no new functions or shared interfaces beyond
  the one helper (`_phase_section`) introduced and used entirely within
  Task 1's single test file.
