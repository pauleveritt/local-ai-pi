# Grading-Path Reboot — Plan

> **Supersedes** the remaining Tasks 6–8 of
> [`2026-07-24-oracle-repair.md`](2026-07-24-oracle-repair.md). That plan's
> Amendments 1–3 survive as **doctrine** and are not re-litigated here; they
> now live as **D1–D3** in
> [`policies/evidence.md`](../policies/evidence.md), alongside D4 (the grader
> accepts no model-controlled input) which this plan's Task 2 implements.
> **Read that policy first — it is the single authoritative statement of how a
> batch must be constructed.** The oracle-repair plan's Tasks 1–5 shipped and
> stand.

**Date:** 2026-07-24
**Status:** approved after deep review (Fable), pending execution
**Verdict:** targeted reboot of the **grading path** and full discard of
**Section 2–3 chapter prose**. NOT a harness rewrite. Confidence: high.

## Why a reboot, and why only this much

Five measurement-integrity failures were found and fixed in two days. A deep
review then found **five more**, two of which defeat the *hardened* oracle. The
pattern is not bad luck; it is one systemic error repeated:

**Every fix so far has been a blacklist against an open category.** The
conftest/pyproject hardening closed two config vectors; `pytest.ini`,
`tox.ini`, and `setup.cfg` remained. That is the same mistake `lessons.md` #8
records ("an allowlist is only as tight as the tools it can see") and the same
mistake the roadmap backlog had already flagged in writing — committed anyway,
hours later. Blacklisting cannot close this category. The grading path must be
rebuilt so that model-controlled input **cannot reach the grader at all**.

Two further structural errors, both confirmed:

- **The non-vacuity gate is vacuous where it matters.** `test_oracle.py`
  *skips* when an acceptance suite is a skeleton — so phases 2 and 3, the
  entire measurement site, are gated by nothing (verified: 6 passed, 4
  skipped). Authoring the suites is therefore the **unblocker**, not a late
  chore. The previously-proposed order (harden → review → author) could never
  have validated anything.
- **Success-rate before/after is not measurable** at this project's scale and
  must be abandoned as a claim structure (see Rule 7 below).

## Verified findings this plan closes

Reproduced by execution unless marked *(read)*.

| ID | Severity | Finding |
|----|----------|---------|
| F1 | **Critical** | `pytest.ini` outranks `[tool.pytest.ini_options]`. A model-written `pytest.ini` with `addopts = --collect-only` yields exit 0 on a deliberately broken app → `tests_pass=True`, `grading_env_tampered=[]`. `tox.ini`/`setup.cfg` are the same vector. |
| F2 | **Critical** | Import-time process exit forges green: `app.py` containing `os._exit(0)` produces empty pytest output and exit 0 → `tests_pass=True`. A stray top-level `sys.exit()` hits this accidentally. |
| F3 | High | `capture_diff` is blind to model-edited `.gitignore` (it is in `_HARNESS_FILES`, and `git status -uall` omits ignored files). A model can hide a created file *and the tampering*. Undermines preservation/overreach evidence, which is read off `changed_files`. |
| F4 | High | `runner.py:216-225` prints "**Oracle validated:** `tests/test_oracle.py` green at commit `<sha>`" by running `git rev-parse` — **it never runs the test**. Fabricated attestation, in the artifact meant to end fabricated metrics. |
| F5 | High *(read)* | Evidence tier lines in `runner.py` are unconditional template text, not assessed from run facts. |
| F6 | Medium | Three live reports still carry the fabricated `**Mean task duration:** 0s`, unbannered. |
| F7 | Medium *(read)* | `test_session.py:73-119` is a dead stub (body `pass`) counting toward the green suite. |

## Evidence triage — what survives

| Evidence | Status |
|---|---|
| SP1 0/8; SP2 3/8, 4/8, 5/8; Phase 2 pooled 0/8 (empty start) | **Never valid.** Correctly bannered. |
| Post-repair SP1 Phase 1 4/4; seeded Phase 2 2/4 and pooled 6/8 | **Superseded, currently UNBANNERED.** Self-graded oracle + fabricated duration. Task 5 fixes the marking. |
| Self-grade forensics (2/8 write-replace, 6/6 edit-extend) | **Valid** — replay-derived, oracle-independent. |
| **Replace-vs-extend 8/8 predictive** | **Valid, and load-bearing.** Oracle-independent, countable per run. This is the strongest finding in the project. |
| Guard experiment: fired 1/4, discriminated correctly, model recovered, task unbroken | **Valid, GREEN, mechanism-level.** |
| Preservation breakage 1/4 control (+2/8 forensic) | Valid, underpowered, honestly RED. |
| False self-report 2/2 | Existence proof; denominator is 2. |

## Discard

- **All Section 2 and Section 3 chapter prose.** It narrates the dead 0/8 arc;
  rewriting against final numbers costs more than writing from the reframe.
  Keep the section directories, specs, plans, and research.
- **Success-rate before/after as a claim structure**, everywhere (Rule 7).
- **The blacklist approach** in `session.py` grading-env hardening.

## Keep

`workspace.py` provisioning and seeding (the seed-in-pristine test genuinely
proves its invariant), `telemetry.py` (the `timestamped_events < 2` guard is
correct), the extensions, the reference fixtures, the forensics and
write-vs-edit reports, the evidence policy, Amendments 1–3 as doctrine.

---

## Tasks

Each task ends with a **gate**. Do not start the next task until the gate
passes. Run `uv run pytest -q` from the worktree root after each.

**Standing gate on Tasks 1–4 and 7** — the tasks that touch the grading path,
the acceptance suites, or measurement code. Per evidence policy **Rule 8**,
their gates are not passed until a **model other than the one that wrote the
change** has reviewed it adversarially, with findings recorded alongside the
commit. This is not ceremony: every prior review round by a different model
found a defect self-review had cleared, including two oracle defeats found
hours after the hardening commit meant to close them. Tasks 5, 6, 8, and 9 are
prose, batch execution, and bannering — exempt.

### Task 1 — Author the phase-2 and phase-3 acceptance suites (HUMAN)

The unblocker. `examples/acceptance/phase-{2,3}/test_acceptance.py` are
skeletons carrying the contract checklist extracted from the roadmap; the
preservation checks are already written. Author the contract assertions and
delete each `test_suite_is_authored` guard.

Per Amendment 3 rule 5 — doctrine **D3** — this is human work by design: the
acceptance suite is the one artifact that must not be model-written, because it
is what grades models. Read `examples/acceptance/WORKLOAD-FACTS.md` (in the
repo, outside the docs tree) first; it records mechanical properties of the
workload — escaping, import paths, mutable seed state — without pre-empting any
judgment call.

> **Incident, 2026-07-24.** A briefing handed this task to a model, which
> authored both suites. The work was discarded unmerged and the guards
> restored. It is recorded because the failure is instructive: the brief cited
> D3 and then instructed the agent to author anyway, and "a human reviews the
> model's suite afterwards" is not a substitute — it converts the judgment that
> *is* the deliverable into a rubber stamp on plausible code. The facts worth
> keeping were harvested into `WORKLOAD-FACTS.md`; the judgment calls were
> deliberately not.

**Three prerequisites the original gate missed**, all found 2026-07-24:

1. **`examples/reference/phase-3/` does not exist.** Both phase-3 oracle tests
   skip on `no reference solution for phase 3`, so the phase-3 suite cannot be
   validated in either direction. Author it before the phase-3 suite. A
   reference solution is spec-compliant *application* code, not a grader — D3
   does not apply and it may be delegated, provided the human-authored suite is
   what later judges it. Model it on `examples/reference/phase-2/`.

2. **The non-vacuity fixture is too weak to prove anything about phases 2–3.**
   `test_acceptance_suite_rejects_broken_solution` blanks `app.py` for every
   phase, removing all routes. For phase 2 that trips the *phase-1*
   preservation checks, so the test passes whether or not the phase-2
   assertions have teeth — a phase-2 suite whose contract assertions were all
   `assert True` would still clear the gate. Replace with a per-phase break
   that violates only that phase's own contract (phase 2: home route intact,
   `/complaints` removed; phase 3: GET intact, POST returning 200 instead of
   303). This is harness measurement code, so **Rule 8 applies** — it needs
   adversarial review by a different model.

3. **"Zero skips" is unreachable until (1) lands**, which is why the gate below
   now names both conditions explicitly.

**Gate:** with the per-phase broken fixtures from (2) in place,
`uv run pytest tests/test_oracle.py -q` reports **zero skips and zero
failures** — currently 6 passed, 4 skipped. Then the Rule 8 review of the
suites, findings recorded with the commit.

### Task 2 — Rebuild the grading path (closes F1, F2)

Do **not** extend the blacklist. Grade outside the workspace:

1. After the model finishes, create a fresh harness-controlled directory.
2. Copy in **only** the model's source artifacts by explicit allowlist —
   `app.py`, `models.py`, `templates/**`, and any other file types the phase
   contract names. Copy **no** configuration files of any kind: not
   `pyproject.toml`, `pytest.ini`, `tox.ini`, `setup.cfg`, `conftest.py`,
   `.pth`, `sitecustomize.py`.
3. Write the harness's own `pyproject.toml` and the acceptance suite into it.
4. Run pytest with `-p no:cacheprovider`, an explicit `-c <harness config>`,
   and an explicit `--rootdir`.
5. **Assert a positive executed-test count.** Parse pytest's summary for the
   number of tests that actually *ran*, and require it to equal the number of
   test functions in the acceptance suite. `returncode == 0` alone is not
   evidence; F1 and F2 both produce exit 0 with zero tests executed.

Record in `SessionResult`: `acceptance_tests_executed`, `acceptance_tests_expected`,
and the list of model config files that were refused entry (evidence, not a
silent repair).

**Gate:** two regression tests, one per defeat, each asserting the defeat now
FAILS to produce `tests_pass=True`:
- `app.py` broken + `pytest.ini` with `addopts = --collect-only`
- `app.py` containing `os._exit(0)`

Both are reproduced in this plan's findings table; copy them verbatim.

### Task 3 — Fix `capture_diff` (closes F3)

Remove `.gitignore` from `_HARNESS_FILES` (it is model-visible: the model can
edit it, and doing so is itself evidence). Add `--ignored` to the status query
so ignored-but-present files surface. Additionally hash-compare every seeded
file against its reference source, so preservation breakage is detected
independent of git.

**Gate:** a test where `.gitignore` is appended with `evil_module.py` and that
file created — `changed_files` must contain both.

### Task 4 — Make the report writer honest (closes F4, F5, F7)

- Either actually invoke `tests/test_oracle.py` and record its real result, or
  **delete the "Oracle validated" line**. A claim the harness did not verify
  must not appear.
- Derive tier lines from run facts (n, outcome mix, whether the delta is
  within noise), not from a template.
- Add `pi --version` to the report header (provenance; the 0.81.1 → 0.82.0
  skew already changed the event schema mid-project).
- Delete the dead stub at `test_session.py:73-119`.

**Gate:** a report generated from a run whose oracle test fails must not
contain the word "green".

### Task 5 — Banner the three unbannered superseded reports (closes F6)

`docs/section-2-measurement/research/2026-07-24-post-repair-sp1-phase1.md`,
`.../2026-07-24-post-repair-sp1-phase2-pooled.md`, and
`docs/section-3-sdd/research/2026-07-24-sp2-baseline-phase-1-post-tuning.md`.
Banner: superseded — self-graded oracle (Amendment 3) and a fabricated
`0s` duration; kept for the record.

**Gate:** no unbannered report contains `Mean task duration:** 0s`.

### Task 6 — Evidence policy Rule 7 ✅ DONE (2026-07-24)

Landed ahead of its gate, as prose with no code dependency, so that Task 2's
implementer reads it first. Rule 7 ("no chapter may claim a success-rate
delta") is now in
[`policies/evidence.md`](../policies/evidence.md).

The same pass consolidated the **measurement doctrine** into that one file:
D1 seeded start state, D2 failure-mode incidence and pooled decisions, D3
harness-owned acceptance suite, D4 the grader accepts no model-controlled
input. These were previously reachable only by reading plan headers. The
amendments keep the full argument and the incident that produced each; the
policy is now the single authoritative statement. **Read it before starting
any task below.**

### Task 7 — Standing behavioral instrumentation

Implement the metrics Rule 7 depends on, which Amendment 2 called for and
which were never built: per-run **inherited-file write attempts**,
**replace-vs-extend classification** (the 8/8 predictive signal), and
**self-report-vs-verdict disagreement**. All are derivable from the artifact.

**Gate:** a report from any batch shows all three counts.

### Task 8 — Run the evidence chain once

Unsteered n=16 per phase (seeded), locate the ditch by the Amendment 2 rule,
then the steered arms n=8. Only after Tasks 1–7 are gated green.

**Operational precondition — batch durability.** Three separate batches were
lost mid-run on 2026-07-24 (a 16-run scout killed at run 8, an experiment
killed between arms, another killed at run 1). Causes: agent-session teardown
reaping child processes, and `setsid` not existing on macOS. `nohup` alone was
not sufficient. Because `run_baseline` writes its report only after ALL n runs
complete, a kill at run 15 of 16 loses the entire batch.

Two requirements before spending an hour on a 16-run batch:
1. **Checkpoint per run.** Persist each `SessionResult` as it completes (the
   artifacts already survive; the aggregation does not), so a killed batch can
   be resumed or reported partially rather than lost.
2. **Use an execution mechanism verified to survive.** On this host only the
   agent harness's own backgrounding completed a long batch reliably. Record
   whichever mechanism is used in the report, and confirm it survives a
   session ending before relying on it.

This is also a reproducibility problem for readers, not just an annoyance
here — a course that asks someone to run n=16 batches must tell them how to
run them durably.

### Task 9 — Write Sections 2–4 from scratch

Against the reframe and the final numbers. The Section 2 second arc:
*validating the oracle* · *what the workload actually is* · *when your metrics
are fiction*. Section 4 leads with the write-vs-edit mechanism chapter.

### Task 10 — Consolidate the entry points

Doctrine was consolidated in Task 6. This closes the other half: what a fresh
session has to read before it can act.

The project now carries three plans, three amendments, twelve research
reports, and this reboot plan. `KICKOFF.md` and the roadmap header describe a
state two reboots old. That is a real cost — an implementer that reads the
wrong file first repeats a fixed mistake, which is how the blacklist commit
landed hours after the backlog warned against blacklists.

1. Rewrite `KICKOFF.md` against the shipped state, or delete it and point at
   the roadmap. One entry point, not two.
2. Give the roadmap header a **read-this-first** list, in order: evidence
   policy (rules + doctrine), current plan, then everything else as archive.
3. Fold the superseded plans under an explicit *Archive* heading so their
   status is visible without opening them.

Do this **last**, when the numbers are final — doing it earlier just means
doing it twice.

**Gate:** a reader following the roadmap header reaches every currently-live
constraint without opening a superseded plan.

---

## The honest note for Section 2's third chapter

Most of the fictions catalogued here were produced by this project's own
automation and reviewed by its own agents: a duration metric that always
returned zero with a unit test pinning that as correct; evidence tiers stamped
GREEN unconditionally; a status narrating "70–74 subagent calls, spiraling as
expected" when the artifact recorded 1; an "Oracle validated" line that never
ran the oracle; and a hardening commit that blacklisted two config files hours
after the same repository's backlog warned that blacklists do not close
categories. Recording that plainly is what makes the chapter worth reading.
