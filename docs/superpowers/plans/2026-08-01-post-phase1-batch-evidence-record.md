# Batch evidence record implementation plan

**Goal:** Preserve the completed n=16 batch's verifiable identity and result
in Git without committing its 4.5 MB raw checkpoint.

**Architecture:** One concise research page holds the verified summary and
retention boundary. `ROADMAP.md` and the development-record index link to it;
the raw JSONL remains outside the repository.

**Tech stack:** JSONL inspection tools, SHA-256, MyST/Sphinx.

## Constraints

- Record only values read from the existing checkpoint; do not infer a result
  from prose or rerun a model.
- State the local `/tmp` path as transient provenance, not durable storage.
- Do not commit raw model diffs/output, archive externally, or modify harness
  code or batch behavior.
- The spec and this plan are committed before the research page is created.

## Tasks

### 1. Verify the raw artifact

- Read the JSONL directly and count its records.
- Compute its byte size and SHA-256.
- Derive the unique run conditions and aggregate all outcome fields needed by
  the completed-batch claim.

### 2. Publish the compact record

**Files:** `docs/superpowers/research/2026-08-01-phase1-n16-batch-evidence.md`,
`ROADMAP.md`, `docs/superpowers/index.md`

- State the artifact identity, uniform conditions, and aggregate result.
- State exactly what was and was not retained.
- Link the page from the Roadmap and development record, including the Sphinx
  research navigation.

### 3. Verify and close

- Re-run the artifact inspection after writing the page and compare its
  recorded values with the raw checkpoint.
- Build Sphinx with warnings as errors.
- Rewrite the Roadmap as the cycle close and confirm the concept budget is
  unchanged.
- Commit the evidence page and navigation updates.
