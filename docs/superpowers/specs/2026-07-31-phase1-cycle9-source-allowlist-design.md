# Cycle 9 — Source allowlist

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine
**Status:** design, awaiting plan

## Why this cycle

`grade()` currently runs pytest with `cwd=workspace` — the model's actual
workspace, containing everything the model wrote. `python -m pytest` puts
that directory first on `sys.path`. A model-written module that shares a
name with something the grading process imports — a workspace-root
`harness/` package, or `pytest.py` — could shadow the real one, including
standing in for `harness/grading_plugin.py` itself and forging a passing
results file. No filename-based refusal (cycle 5) catches this, because
the threat isn't a config file at all; it's import-path manipulation.
Surfaced by cycle 5's final review, explicitly scoped out of that cycle
because refusal there is about files that *configure* the run, not files
that get imported instead of the real thing.

Cycle 8's live run gives this cycle its first real evidence of what a
model actually writes: exactly `app.py`, `templates/base.html`,
`templates/home.html`, and a self-written `tests/test_app.py` — nothing
unexpected, no scatter. That's useful negative evidence, but it doesn't
make the shadowing threat theoretical; it's a property of how `pytest` is
invoked, not of what any particular run happened to contain.

## What this cycle is not

- Not a general, multi-phase allowlist registry. The allowlist is scoped
  to Phase 1, the same way every other fixture set in this project is —
  a parameter with a Phase-1-specific default, not a hardcode, but not
  built to anticipate phases 2–3 either.
- Not the out-of-process fix (running the suite against a live app
  subprocess instead of in-process `TestClient(app)`). That closes the
  same-process forged-results-file gap for good, but it's materially
  larger than this cycle — explicitly named in the Backlog as a separate,
  bigger piece of work. This cycle closes the *sys.path* instance of the
  same underlying problem, not the in-process-secret-sharing instance.
- Not a replacement for cycle 5's config refusal or cycle 6's
  suite-scoping fix. Both stay, as defense-in-depth, even though this
  cycle makes both structurally redundant for Phase 1's specific
  allowlist (none of cycle 5's refused filenames, and no `tests/`
  directory, are on the Phase 1 allowlist, so neither could reach the
  grading directory even without those earlier fixes).

## Interface

```python
# harness/grading.py

def grade(
    workspace: Path,
    suite: Path,
    timeout: int = 30,
    source_allowlist: tuple[str, ...] = ("app.py", "templates"),
) -> GradeResult:
    ...
```

- `source_allowlist` is a new parameter with a Phase-1-specific default —
  a seam, not a hardcode. It names exactly what the task spec instructs
  the model to create, matching cycle 8's real diff.
- `GradeResult`'s shape is unchanged. This cycle changes *what pytest
  runs against*, not the verdict's fields.

## Behavior

`grade()`'s current order (test count, then refusal check, then copy the
suite in and run pytest with `cwd=workspace`) changes to:

1. `_test_count(suite)` — unchanged.
2. `_refused_config(workspace)` — unchanged, still checked against the
   original workspace, before anything else. Not because a refused
   filename could still reach the grading directory (it can't — none are
   on the allowlist) but because `refused_config` in `GradeResult` stays
   useful evidence of what the model attempted, independent of whether it
   could have mattered.
3. **New:** build a fresh, temporary grading directory. For each name in
   `source_allowlist`, if `workspace / name` exists, copy it into the
   grading directory (file or directory, recursively) under the same
   name. A missing allowlisted path is skipped, not an error — the
   `broken` fixture has no `templates/`, and that absence is exactly what
   its own existing test already depends on (a missing template producing
   a 404).
4. Copy the acceptance suite into the grading directory (as today, just
   a different destination directory).
5. Run pytest with `cwd=<grading directory>` instead of `cwd=workspace`.
   Nothing else about the invocation changes — same `-p
   harness.grading_plugin`, same `PYTHONPATH`, same results-file
   mechanism.
6. Read the verdict from the results file — unchanged.
7. Delete the temporary grading directory before returning, the same way
   `prepare_workspace` cleans up its own temp directory.

The original `workspace` is untouched by any of this — `grade()` reads
from it (to decide what to copy) but never writes to or grades it
directly.

## Testing

The existing `reference`/`broken` fixture tests need no changes: both
fixtures already contain only `app.py` (and `reference` additionally
`templates/`), so the new allowlist copy is transparent to them — proving
this cycle doesn't regress the trusted baseline it inherited.

The cycle's own proof is a genuine attack, matching cycle 4's pattern: a
workspace containing the `broken` solution (which should fail) plus a
workspace-root `harness/grading_plugin.py` that, if imported instead of
the real one, forges a passing results file — writing `__DONE__` and
`passed` outcomes for the suite regardless of what actually ran. Before
this cycle, that module would sit on `sys.path` (via `cwd=workspace`) and
could shadow the real plugin. After this cycle, it's never copied into
the grading directory at all, so it's never in a position to be imported.
The test asserts `accepted is False` — the forged file never gets
written, because the forging module is never on the import path pytest
actually runs against.

## Non-goals recap

Multi-phase allowlist generalization, the out-of-process fix for the
same-process forged-results-file gap, and removal of cycles 5/6's
now-redundant-for-Phase-1 checks are all explicitly deferred, per the
design discussion above.
