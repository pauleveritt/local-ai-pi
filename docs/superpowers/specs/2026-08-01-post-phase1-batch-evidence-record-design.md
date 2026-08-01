# Post-Phase 1 corrective cycle — batch evidence record

**Status:** approved for implementation

## Why this correction exists

Phase 1's supervised n=16 batch produced the evidence for its completion, but
the raw JSONL checkpoint lives only in `/tmp`. It may disappear, while a
future reader still needs enough information to identify the artifact and
understand exactly what was verified from it.

Committing the raw file would put 4.5 MB of model diffs and process output in
Git. That is expensive to carry, and it is not necessary to state the result
or identify an independently retained copy.

## Contract

Add one committed research page that records:

- the raw checkpoint's local path at verification time, byte size, SHA-256,
  and record count;
- the uniform run conditions read from the checkpoint;
- the aggregate result: all sixteen runs accepted, with zero Pi timeouts,
  zero nonzero Pi exits, grade return code zero, and four of four acceptance
  tests executed per run; and
- the retention boundary: the raw checkpoint is not committed and `/tmp` is
  not durable storage. The path is a provenance reference, not a promise that
  the file will remain available.

Link the page from the development record and Roadmap. The checksum lets a
future retained copy be verified, but the page must not claim that the raw
artifact has been archived externally.

## Evidence

The implementation reads the existing JSONL at its recorded path and verifies
its line count, SHA-256, uniform conditions, and aggregate result before the
page is written. Sphinx with warnings as errors proves the new links and page
build.

## Non-goals

- Do not commit the raw checkpoint, copy it elsewhere, or create an external
  archive.
- Do not rerun the model, alter batch semantics, or change the completed
  Phase 1 result.
- Do not spend a new concept-budget term: this is a durable citation of the
  existing checkpoint and run evidence, not a new harness mechanism.
