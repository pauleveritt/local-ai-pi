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
| 4 | Subversion fixtures — fixtures that attack grading (`addopts = --collect-only`; import-time `os._exit(0)`), confirmed to defeat a naive exit-code grader | | | Next |
| 5 | Source allowlist + refusal of model-written config — proven by rejecting cycle 4's attacks | | | Planned |
| 6 | AgentClinic task spec — transplant and choose the roadmap variant the model builds from | | | Planned |
| 7 | Model-server liveness check — server up passes; server stopped is caught, not recorded as data | | | Planned |
| 8 | First real run — `pi` against a fresh workspace, graded hermetically. Exercises the workspace's initial commit as a diff base. | | | Planned |
| 9 | Checkpoint recording — append per completed run, tolerate a truncated final line | | | Planned |
| 10 | n=16 batch, sequential and resumable — target ~15/16 | | | Planned |

**Why this order.** Cycles 3–7 build and prove the entire judging apparatus
*before* a model runs once — every one of them is provable against fixtures
with no model in the loop. That is deliberate: it means the ~15/16 at cycle
10 measures the model rather than the engine, which is the whole reason
Phase 1 was chosen for being boring (see `BRIEF.md`). Building the grader
after the first run would produce output with no trusted way to judge it.

Cycles 4-before-5 and 6-before-8 follow cycle 1's precedent: the artifacts
that make a proof possible get their own cycle, ahead of the machinery that
consumes them.

### Deferred candidates

*Things a cycle's brainstorming considered and passed over — usually the
"smallest choice" between two real options. Tracked here, updated at the
end of each cycle, so the next brainstorming session starts from this list
instead of re-deriving it from old specs.*

The 2026-07-30 re-plan absorbed this list into cycles 3–10 above: the
hermetic grader split into cycles 3 and 5, the typed verdict into cycle 3
(so the grader names the concept rather than inheriting a name it never
argued for), the git-diff exercise into cycle 8 (the first time a model
writes changes worth diffing), checkpoint/resume into cycle 9, and n=16
into cycle 10. That re-plan also found three things the list had never
named — a model actually being invoked, a liveness check, and the
AgentClinic spec the model builds from — which are now cycles 8, 7, and 6.

Carried forward as notes for cycle 5 (both surfaced by cycle 2's review,
both in config-refusal's problem domain): a global `core.hooksPath`
pre-commit hook would make `prepare_workspace`'s commit fail, and
`prepare_workspace` raises `CalledProcessError` on an empty source
directory because `git commit` finds nothing staged.

Carried forward as a note for cycle 5 (surfaced by cycle 3's brainstorming):
the workspace `prepare_workspace` provisions is already a git repository
with an initial commit (cycle 2). Isolation or variation should come from
git — a branch, a diff against that commit, a reset — rather than a second
directory. The old branch's separate grader directory existed only to
support the allowlist and pinned dependencies; cycle 3 graded directly in
the workspace instead, and cycle 5 should treat "does the allowlist still
need its own directory at all" as an open question, not inherit the old
answer.

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
- ~~Which AgentClinic roadmap variant (implementation-detail vs. user-story)
  a future model-builds-from-spec cycle should use.~~ **Promoted to cycle
  6** by the 2026-07-30 re-plan — no longer hypothetical, since cycle 8's
  run needs the document and `test_acceptance.py` already cites
  `examples/agentclinic/specs/roadmap.md`, which is not on this branch.
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

## Prior work

The pre-restructure project lives on the `user-story-batch` branch, untouched.
Nothing there is imported here except by an explicit phase decision.

## Workflow

`restructure` is this reboot's trunk — `main` stays untouched until the whole
reboot is ready to replace the old project. Starting with cycle 2, each
feature cycle branches from `restructure` and merges back to it, never to
`main`.
