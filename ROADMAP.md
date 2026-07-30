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
