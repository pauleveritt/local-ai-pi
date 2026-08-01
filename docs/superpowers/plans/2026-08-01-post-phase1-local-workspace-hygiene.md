# Local workspace hygiene implementation plan

**Goal:** Keep the new `main` worktree clean without losing active worktrees,
local agent state, or generated evidence from the archived project.

**Architecture:** Track two general local-directory ignore rules in the new
repository. Move only the legacy generated session directory to the matching
ignored location in the archive; keep every other historical file in place.

**Tech stack:** Git, SHA-256, MyST/Sphinx.

## Constraints

- Preserve all nine session JSONLs byte-for-byte.
- Do not stage `.worktrees/`, `.superpowers/`, or generated sessions.
- Do not add a broad `docs/section-*` ignore rule to the new project.
- The spec and this plan are committed before `.gitignore` or session files
  change.

## Tasks

### 1. Measure the legacy session files

- Record a sorted path-and-SHA-256 manifest for the root session directory.
- Confirm the matching destination does not already exist in
  `.worktrees/pre-restructure`.

### 2. Separate local and archived artifacts

**Files:** `.gitignore`,
`docs/section-2-measurement/research/sessions/` (move only)

- Add `.worktrees/` and `.superpowers/` to the tracked ignore file.
- Move the exact session directory into the archive's matching path.
- Compare the destination's manifest with the pre-move manifest, then confirm
  the root source is absent.

### 3. Close the cycle

**Files:** `ROADMAP.md`, `docs/superpowers/index.md`, cycle spec

- Record Cycle 17 and the unchanged concept budget.
- Mark the spec implemented and add its spec/plan to the development record.
- Build Sphinx with warnings as errors.
- Confirm root `main` and the archive worktree are clean after commit, then
  push the normal `main` update.
