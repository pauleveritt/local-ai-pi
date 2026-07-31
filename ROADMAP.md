# Roadmap

*Phases group feature cycles. One direction at a time. Tangents go to the
Backlog, not into the current phase.*

## Now

**Phase 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine.** One
run, hermetically graded, recorded to a checkpoint; then n=16 reproducing
~15/16. The engine's first job is to reproduce a number we already trust, not
to discover one — see `BRIEF.md` for why. Everything else waits.

*(Superseded framing, kept for the record: an earlier pass named Phase 1 "the
restructure spec" — define the volunteer reader, then derive a section
structure for them. That's a real question, but it's downstream of having a
working engine and real suites to write about; it isn't Phase 1's job. See
`BRIEF.md`, "First decision for the new session.")*

## Phases

| # | Phase | Direction (one sentence) | Status |
|---|-------|--------------------------|--------|
| 1 | Reproduce AgentClinic Phase 1 | One trustworthy, hermetically-graded run; n=16 reproducing ~15/16 | active |

### Phase 1 feature cycles

| Cycle | Summary | Spec | Plan | State |
|-------|---------|------|------|-------|
| 1 | Accept/reject fixture pair — known-good and known-broken AgentClinic Phase 1 solutions, proven by plain pytest | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle1-fixture-pair-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle1-fixture-pair.md) | Done |
| 2 | Workspace provisioning — `prepare_workspace` context manager copies a fixture into a fresh, git-initialized, disposable workspace; proven by an automated pytest test re-running cycle 1's accept/reject procedure through it | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle2-workspace-provisioning-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle2-workspace-provisioning.md) | Done |
| 3 | Verdict from a hook-written results file — grade by reading a file a pytest hook wrote, not pytest's exit code. Names the verdict type. | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle3-verdict-file-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle3-verdict-file.md) | Done |
| 4 | Subversion fixtures — fixtures that attack grading (`addopts = --collect-only`; import-time `os._exit(0)`), confirmed to defeat a naive exit-code grader | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle4-subversion-fixtures-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle4-subversion-fixtures.md) | Done |
| 5 | Refusal of model-written config — the grader refuses to certify a run whose workspace carries model-written `pytest.ini`/`.pytest.ini`/`pyproject.toml`/`tox.ini`/`setup.cfg`/`conftest.py`/`sitecustomize.py`, before pytest ever runs. Split from the original combined row (below) — the allowlist half needed evidence this half didn't. | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle5-config-refusal-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle5-config-refusal.md) | Done |
| 6 | AgentClinic task spec — transplanted **Phase 1's section only** of the detailed roadmap to `examples/agentclinic/specs/roadmap.md`, the document the trusted number was produced against, resolving a citation cycle 1's suite had carried since. Deliberately *not* a variant choice: see the Backlog note. Also fixed the grading regression the transplant made reachable. | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle6-task-spec-design.md) | [plan](docs/superpowers/plans/2026-07-30-phase1-cycle6-task-spec.md) | Done |
| 7 | Model-server liveness check — server up passes; server stopped is caught, not recorded as data | | | Next |
| 8 | First real run — `pi` against a fresh workspace, graded hermetically. Exercises the workspace's initial commit as a diff base. | | | Planned |
| 9 | Source allowlist — which model-written *files* get graded at all, as distinct from cycle 5's config refusal. Split out of cycle 5's original row because it needs evidence of what a model actually scatters into a workspace, which doesn't exist until cycle 8 produces a real run to look at. | | | Planned |
| 10 | Checkpoint recording — append per completed run, tolerate a truncated final line | | | Planned |
| 11 | n=16 batch, sequential and resumable — target ~15/16 | | | Planned |

**Why this order.** Cycles 3–7 build and prove the entire judging apparatus
*before* a model runs once — every one of them is provable against fixtures
with no model in the loop. That is deliberate: it means the ~15/16 at cycle
11 measures the model rather than the engine, which is the whole reason
Phase 1 was chosen for being boring (see `BRIEF.md`). Building the grader
after the first run would produce output with no trusted way to judge it.
Cycle 9 (the allowlist) is the one deliberate exception — it is judging
apparatus built *after* a model has run, because it is the one piece that
needs a model's actual output to be anything more than a guess.

Cycles 4-before-5, 6-before-8, and 8-before-9 follow cycle 1's precedent:
the artifacts that make a proof possible get their own cycle, ahead of the
machinery that consumes them.

### Deferred candidates

*Things a cycle's brainstorming considered and passed over — usually the
"smallest choice" between two real options. Tracked here, updated at the
end of each cycle, so the next brainstorming session starts from this list
instead of re-deriving it from old specs.*

The 2026-07-30 re-plan absorbed this list into cycles 3–10 above (numbers
as they stood then): the hermetic grader split into cycles 3 and 5, the
typed verdict into cycle 3 (so the grader names the concept rather than
inheriting a name it never argued for), the git-diff exercise into cycle 8
(the first time a model writes changes worth diffing), checkpoint/resume
into cycle 9, and n=16 into cycle 10. That re-plan also found three things
the list had never named — a model actually being invoked, a liveness
check, and the AgentClinic spec the model builds from — which are now
cycles 8, 7, and 6. Cycle 5's own close then split its combined row and
inserted the allowlist as a new cycle 9, pushing checkpoint/resume and
n=16 to 10 and 11 — the numbers above reflect that; this paragraph is
historical record of the numbering as it stood before that split.

**Resolved by cycle 5, kept for the record.** The two notes above from
cycle 2's review (`core.hooksPath` breaking `prepare_workspace`'s commit;
`CalledProcessError` on an empty source directory) were about
`harness/workspace.py`, which cycle 5 correctly never touched — they carry
forward again below, still open. Cycle 3's git-isolation note and cycle
4's two notes (reusable attack helpers; the vacuity trap in "proven by
rejecting cycle 4's attacks") were all directly addressed by cycle 5: it
graded in the workspace with no second directory, consumed cycle 4's
helpers as planned, and its non-vacuous tests assert on `refused_config`
and `returncode is None` rather than `accepted is False` alone.

Carried forward as notes for cycle 9, the allowlist (both still open,
originally surfaced by cycle 2's review, both in the allowlist's problem
domain now that config refusal has shipped separately): a global
`core.hooksPath` pre-commit hook would make `prepare_workspace`'s commit
fail, and `prepare_workspace` raises `CalledProcessError` on an empty
source directory because `git commit` finds nothing staged.

Carried forward as notes for cycle 9, the allowlist (surfaced by cycle 5):

- **The `pyproject.toml` reservation.** Cycle 5 refuses a model-written
  `pyproject.toml` outright, on the grounds that AgentClinic Phase 1 never
  needs one and `[tool.pytest.ini_options]` inside it is a live attack
  path — but it's the one refused name a model might write for a
  legitimate reason (declaring dependencies). If cycle 8's first real run
  produces a legitimate `pyproject.toml`, this is the entry to revisit —
  not by loosening refusal, but as evidence for how the allowlist should
  treat it.
- **Module shadowing via `sys.path`** — see the Backlog entry below, next
  to the forged-results-file gap it shares a root cause with. Worth
  cycle 9's attention too: if the allowlist ends up copying only allowed
  files into an isolated directory (an open question per cycle 3's note
  above), that shape would also close this off as a side effect, without
  needing the out-of-process fix the Backlog entry names.

Carried forward as a note for cycle 10 or 11 (checkpoint recording / n=16
batch — surfaced by cycle 5's brainstorming, not a specific single cycle):
`grade()` never catches `subprocess.TimeoutExpired`; it propagates
uncaught. Immaterial for a single run, but a batch needs one hung run to
record a rejection and continue, not abort the whole batch.

**A collision surfaced by cycle 6's brainstorming, confirmed empirically,
and resolved by cycle 6.** `grade()` invoked `pytest -q` with
`cwd=workspace` and *no path argument*, so pytest collected every test
file in the workspace — not just the acceptance suite the harness copied
in. The AgentClinic roadmap's Phase 1 section ends by instructing the
model to "Write a smoke test in `tests/test_app.py`". So a model that
followed the spec **correctly** produced extra test files, and
`tests_executed == tests_expected` (cycle 3's condition, cycle 4's proof)
failed on a perfect solution.

Measured, not predicted: cycle 1's `reference` solution plus a two-test
`tests/test_app.py` graded as `accepted=False, executed=6, expected=4,
returncode=0`. Had it gone unresolved, cycle 8's first real run would have
rejected a correct solution and the failure would have looked like a model
problem rather than an engine problem — precisely the confusion Phase 1
was chosen to make impossible.

**Resolved by cycle 6.** `grade()` now passes the acceptance suite's
filename to pytest, so only the suite is collected — restoring what the
old harness got from `tests/test_acceptance.py` in its argv, and what the
trusted number was produced under. Pinned by
`tests/test_grading.py::test_grade_ignores_model_written_tests_and_grades_the_suite_alone`.

Two alternatives were considered and rejected. Editing the smoke-test
bullet out of the transplanted spec would work, and is the wrong
direction: the 16/16 runs included that bullet, so removing it moves our
conditions away from the ones being reproduced. Deriving `tests_expected`
from what pytest collected would discard the count check that catches
`--collect-only`.

Cycle 9's allowlist, if it takes the copy-only-allowlisted-files shape,
would close this a second way by never copying model-written tests into a
graded directory — independent of this fix, not superseded by it.

Carried forward as notes from cycle 6:

- **For cycle 8 (first real run).** The transplanted task spec is Phase 1
  only. If cycle 8's run shows the model needs surrounding context the
  omitted phases supplied — a sense of where Phase 1 sits in a larger
  build — that is evidence for how much of the document to transplant,
  not a reason to add commentary to it. The file is model-facing input;
  anything added is a difference from the conditions the trusted number
  was produced under.
- **The load-bearing-facts check, worth applying before any future
  cycle's first run.** From the old branch's research: grep a spec for the
  facts its acceptance suite imports. Anything the suite reaches for that
  the spec never states is a silent dependency on whatever prose happens
  to surround it. Phase 1's suite does `from app import app`; the
  transplanted spec states `app.py` and FastAPI explicitly, so this one
  checks out — but phases 2 and 3, whose suites import `models` and
  `Complaint` by name, are where it would bite.

Nothing else is currently deferred. Add to this list as later cycles pass
things over.

## Backlog

- Volunteer-reader / section-structure design (superseded Phase 1 framing;
  revisit once an engine and real suites exist to write about)
- Authoring scaffold for future acceptance suites (phase 2+): stub test
  functions named for the fact they prove, `raise NotImplementedError`
  bodies, a model fills in from owner-dictated bullets, owner reviews by
  tracing each assertion back to its bullet. Not needed for phase 1 (its
  suite already exists, human-authored).
- Which AgentClinic roadmap variant (implementation-detail vs. user-story)
  a model should build from — i.e. *does a spec's abstraction level change
  what a small model can build?* **Promoted to cycle 6 by the 2026-07-30
  re-plan; that promotion is withdrawn.** It is a discovery question, and
  Phase 1 is explicitly a reproduction milestone — `BRIEF.md`: "reproduce a
  number we already trust, not to discover one." With that framing there is
  no choice to make: reproduction uses the document the trusted number was
  produced against, which is the detailed variant. Cycle 6 transplants;
  it does not choose.

  Evidence gathered while the question was (wrongly) live, worth keeping so
  the experiment starts from it rather than re-deriving it — all from
  `user-story-batch`'s
  `docs/section-3-sdd/research/2026-07-29-user-story-workload-is-not-substitutable.md`,
  which carries a PENDING RULE 8 REVIEW banner and is not citable prose:
  - Phase 1, n=16, same model and Pi version this reboot uses: detailed
    spec 16/16 (reproducing the published 15/16); user-story spec 1/16
    bare.
  - The cause is narrow, not a general property of user-story framing. The
    Phase 1 suite's only structural coupling is `from app import app`; the
    detailed spec states it ("Create `app.py` with the FastAPI application
    instance"), the user-story variant never names `app.py`, FastAPI, or
    even that this is Python. Supplying that one fact separately recovered
    the arm to 15/16 — but that recovery is flagged post-hoc in the source,
    "a lead for a pre-registered replication, not a confirmed result," and
    the replication was never run.
  - The generalizable hazard, worth applying to any future suite: **grep a
    spec for the facts its acceptance suite imports.** Anything the suite
    reaches for that the spec never states is a silent dependency.

  Revisit as a deliberate experiment once a trusted number is in hand —
  not during Phase 1.
- Acceptance-suite rules beyond human-authorship (cumulative,
  contract-vs-implementation, non-vacuous, naming convention) — untouched,
  each needs its own argument when it becomes relevant.
- Acceptance grading still trusts a same-process signal a model can forge.
  A model-authored `app.py` can read the results-file path from the
  environment it shares with `harness/grading_plugin.py` and write forged
  `nodeid<TAB>outcome` lines and a completion marker straight into the
  results file. Cheap to do, and no in-process secret closes it — anything
  the plugin can read, model code sharing its process can read too. The
  real fix is running the suite out-of-process against a live app
  subprocess instead of in-process `TestClient(app)`, which is materially
  larger than the cycle that surfaced it. Scoped out of cycle 4 by
  explicit decision, not oversight — see that cycle's design doc, "Out of
  scope for this cycle".
- Same root cause, different shape: `python -m pytest` with
  `cwd=workspace` puts the workspace first on `sys.path`. A model-written
  module that shadows a real import name — a workspace-root `harness/`
  package, or `pytest.py`/`pytest/` — could be imported instead of the
  genuine one, including standing in for `harness/grading_plugin.py`
  itself and writing a forged results file exactly as above. No
  filename-based refusal catches this, since the threat isn't a config
  file at all. The out-of-process fix above closes both; a copy-only-
  allowlisted-files grading directory (cycle 9, if it takes that shape)
  would also close this one specifically. Surfaced by cycle 5's final
  review; scoped out of cycle 5 because refusal there is about files that
  *configure* the run, not import-path manipulation.

## Prior work

The pre-restructure project lives on the `user-story-batch` branch, untouched.
Nothing there is imported here except by an explicit phase decision.

## Workflow

`restructure` is this reboot's trunk — `main` stays untouched until the whole
reboot is ready to replace the old project. Starting with cycle 2, each
feature cycle branches from `restructure` and merges back to it, never to
`main`.
