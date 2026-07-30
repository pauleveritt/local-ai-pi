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
| 2 | Workspace provisioning — `prepare_workspace` context manager copies a fixture into a fresh, git-initialized, disposable workspace; proven by an automated pytest test re-running cycle 1's accept/reject procedure through it | [spec](docs/superpowers/specs/2026-07-30-phase1-cycle2-workspace-provisioning-design.md) | | Spec approved |

### Deferred candidates

*Things a cycle's brainstorming considered and passed over — usually the
"smallest choice" between two real options. Tracked here, updated at the
end of each cycle, so the next brainstorming session starts from this list
instead of re-deriving it from old specs.*

- **Hermetic grader** (source allowlist, refusal of model-written config,
  verdict from a hook-written results file) — deferred at cycle 2 in favor
  of building its workspace-provisioning precursor first. Natural next
  cycle once provisioning is done.
- **Checkpoint/resume pair** (`_append_checkpoint` / `_load_checkpoint`) —
  the other "read-once-then-write-fresh" candidate from `BRIEF.md`, not
  taken at cycle 2. Relevant once something runs repeatedly or resumes.
- **Diff exercise** (using `prepare_workspace`'s initial git commit as a
  diff base) — deferred at cycle 2; the commit is created but not tested
  as a diff, since no model is yet in the loop to write changes against
  it.
- **n=16 batch running** — Phase 1's eventual target, not yet any single
  cycle's scope.
- **A typed verdict for a suite run** (e.g. a `SuiteRun` value with an
  `accepted` property, and a helper that provisions + overlays the suite +
  runs it, wrapping `prepare_workspace`) — considered at cycle 2 and
  deferred. It would replace raw `returncode` assertions in two tests, but
  that's three new names for two call sites, and "accepted" is a *verdict*
  concept: deciding what it means belongs to the grader's contract, not to
  provisioning's tests. Revisit with the hermetic grader, so the grader
  names it rather than inheriting a name it never argued for.

## Backlog

- Volunteer-reader / section-structure design (superseded Phase 1 framing;
  revisit once an engine and real suites exist to write about)
- Authoring scaffold for future acceptance suites (phase 2+): stub test
  functions named for the fact they prove, `raise NotImplementedError`
  bodies, a model fills in from owner-dictated bullets, owner reviews by
  tracing each assertion back to its bullet. Not needed for phase 1 (its
  suite already exists, human-authored).
- Which AgentClinic roadmap variant (implementation-detail vs. user-story)
  a future model-builds-from-spec cycle should use.
- Acceptance-suite rules beyond human-authorship (cumulative,
  contract-vs-implementation, non-vacuous, naming convention) — untouched,
  each needs its own argument when it becomes relevant.

## Prior work

The pre-restructure project lives on the `user-story-batch` branch, untouched.
Nothing there is imported here except by an explicit phase decision.

## Workflow

`restructure` is this reboot's trunk — `main` stays untouched until the whole
reboot is ready to replace the old project. Starting with cycle 2, each
feature cycle branches from `restructure` and merges back to it, never to
`main`.
