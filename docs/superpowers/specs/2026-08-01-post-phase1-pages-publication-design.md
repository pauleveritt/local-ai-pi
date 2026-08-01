# Post-Phase 1 corrective cycle — Pages publication

**Status:** implemented

## Why this correction exists

The new `main` history has no GitHub Actions workflow, so pushes after the
restructure cannot publish the Sphinx site. GitHub Pages is still serving the
last old-project deployment from 2026-07-28, including the obsolete
`/section-3-sdd/` path. The new Satyrn docs also retain an old landing-page
status sentence that says Phase 1 is nearly complete.

## Contract

Add `.github/workflows/pages.yml` with the existing Pages deployment shape:

- run on pushes to `main` and on manual dispatch;
- install the project with `uv sync --frozen --group docs`;
- build `docs/` with `sphinx-build -W -b html`;
- upload the HTML artifact and deploy it with the GitHub Pages actions; and
- grant only the contents read, Pages write, and OIDC identity permissions the
  deployment needs.

Make the generated site truthful and link-safe:

- update `docs/index.md` to say Phase 1 is complete and Phase 2 is next; and
- add an orphan migration page at `docs/section-3-sdd/index.md` that tells
  readers the old Section III site moved to the new documentation home.

The old URL therefore stops serving stale old-project content and remains a
useful landing point after the next successful deployment.

## Evidence

The workflow YAML is parsed and inspected locally, and strict Sphinx builds
the new landing and migration pages with no warnings. The existing test suite
remains unaffected; a later push-run supplies the external proof that GitHub
Actions deploys the artifact.

## Non-goals

- Do not restore the old Section III content or old project workflow behavior.
- Do not change harness code, evaluation results, or Phase 2 scope.
- Do not add a new concept-budget term: this is publication wiring and a
  compatibility page, not an engine mechanism.
