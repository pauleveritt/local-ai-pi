# Post-Phase 1 corrective cycle — local workspace hygiene

**Status:** approved for implementation

## Why this correction exists

Publishing the orphan `restructure` history as `main` left three kinds of
old-project material in the root worktree. They are not Satyrn source:
active linked worktrees, local agent state, and generated session JSONL from
the archived project. Until they are separated, `git status` is noisy and a
broad `git add` could accidentally treat local state as new project content.

## Contract

The published repository gains two durable ignore rules:

- `.worktrees/` for active linked worktrees; and
- `.superpowers/` for local agent task/review state.

The nine legacy JSONL files at
`docs/section-2-measurement/research/sessions/` move unchanged into the
matching directory of `.worktrees/pre-restructure`, the preserved old-project
worktree. That worktree already ignores generated `docs/section-*/research/sessions/`
artifacts. The new repository deliberately does **not** add a broad old-section
ignore rule: the data belongs in the archive rather than being hidden here.

## Evidence

Before moving the session files, record their paths and SHA-256 values. After
moving, compare the archive files against that manifest and confirm the source
directory is gone. Then verify that the root worktree reports only this
cycle's tracked changes before commit and is clean after commit; the archive
worktree stays clean because the copied session files are ignored there.

## Non-goals

- Do not delete linked worktrees, local agent state, or legacy session data.
- Do not commit generated sessions, modify harness code, or alter Phase 1's
  evidence.
- Do not add a concept-budget term: this is local file placement and ignore
  policy, not a new engine mechanism.
