# Pages publication implementation plan

**Goal:** Publish the new Satyrn Sphinx site from `main` and give the old
Section III URL a clear migration landing page.

**Architecture:** A GitHub Pages workflow builds the checked-in `docs/` tree
with the repository's frozen docs group and deploys the resulting artifact.
The old URL becomes an orphan page in that same tree, so no redirect service or
old content is needed.

**Tech stack:** GitHub Actions, `uv`, Sphinx, MyST.

## Constraints

- Trigger only on `main` pushes or manual dispatch.
- Use the existing `astral-sh/setup-uv`, Pages artifact, and deploy actions;
  do not add a new publishing service.
- Build with `sphinx-build -W` so a warning cannot publish a misleading site.
- Keep the migration page out of normal navigation while retaining its stable
  old URL.
- The spec and this plan are committed before workflow or docs changes.

## Tasks

### 1. Restore the Pages workflow

**File:** `.github/workflows/pages.yml`

- Adapt the archived workflow to the new repository.
- Keep least-privilege Pages permissions and serialized deployments.
- Run `uv sync --frozen --group docs` and strict Sphinx build before upload.

### 2. Repair published-document entry points

**Files:** `docs/index.md`, `docs/section-3-sdd/index.md`

- Update the landing-page status to Phase 1 complete / Phase 2 next.
- Add an orphan migration page linking to `../index.html` from the old path.

### 3. Verify and close

- Parse the workflow YAML and inspect its trigger, permissions, build, and
  deploy steps.
- Build Sphinx with warnings as errors and confirm both new pages are present.
- Run the existing non-live test suite as a regression check.
- Add Cycle 18 to `ROADMAP.md` and the development-record navigation, harvest
  no new jargon, commit, push `main`, and verify the resulting Actions run.
