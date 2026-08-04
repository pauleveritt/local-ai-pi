# Phase 5 cycle 7 — the tech-stack lever

**Date:** 2026-08-04
**Status:** design
**Phase:** 5 — the improvement loop

## Purpose

The first lever proper, against a corrected and guarded baseline. Every arm on
the user-story suite has scored zero, and the cause is now known precisely
rather than assumed.

## What the evidence actually says

Cycle 4's record blamed file layout — `index.html` versus `home.html`,
`test_app.py` placement. **That was wrong, and both it and cycle 5's record
now carry corrections.** The acceptance file says so in its own docstring:

> *"Do not assert on internal function names or file layout — a
> correct-but-different solution must pass."*

Its only structural coupling is `from app import app`. Reading the grade
output of every run that wrote `app.py` — six in cycle 4, five in cycle 5's
pilot — gives one identical failure:

```
TypeError: Flask.__call__() missing 1 required positional argument: 'start_response'
```

**The model writes Flask.** Flask is WSGI; the suite drives the application
with Starlette's ASGI `TestClient`. Every test errors during setup, before
asserting anything about the page. The applications are otherwise plausible —
right module, right templates directory, tagline present.

This replicates the prior project's dominant failure mode on its comparable
arm (recorded there as *wrong-framework (flask)*, 14 of 16), which was a
prediction and is now our own observation.

There is a second, smaller cause: runs that wrote `app/main.py` or
`app/__init__.py` fail because `source_allowlist` copies `app.py` and
`templates` only, so no module reaches the grading directory. That is a real
coupling **the acceptance file's disclaimer does not cover** — the suite is
layout-agnostic, the *allowlist* is not.

## The lever

One fact: **the framework**. A `## Technology` section appended to the
orchestrator prompt, naming Python with **FastAPI** and Jinja2 templates, and
stating that the graded module is `app.py` at the project root exposing an
`app` object.

Naming the module is not scope creep past "the stack" — it is the one thing
the acceptance suite genuinely imports and the one thing the allowlist
requires. Withholding it would leave a known second cause in play and make the
result impossible to attribute.

**Still withheld**, so the lever stays one lever: template filenames, the
tests directory, route handler names, and anything about page structure beyond
what the user-story spec already says in prose.

## How it is built

A new improvement `sdd-orchestrator-guarded-stack`, identical to
`sdd-orchestrator-guarded` except for its `system_prompt`, which points at a
new file that is **the guarded prompt verbatim plus the Technology section**.

A test asserts the new file starts with the exact text of `orchestrator.md`,
so the two cannot drift apart silently — the alternative, a shared prompt with
conditional includes, is machinery for one caller.

The unguarded and guarded improvements both survive; cycle 8 needs them.

## Pre-registered predictions

1. **`TypeError: Flask` disappears.** No run writes a WSGI application once
   FastAPI is named.
2. **Acceptance rises above zero** — the first non-zero result on this suite.
   No threshold is predicted: n=6 cannot resolve one, and the prior project's
   comparable arms landed at 8/16 and 15/16 without a replication.
3. **Timeouts do not improve.** The unbounded child is a separate failure and
   nothing here addresses it.

A result where the Flask error vanishes and acceptance stays at zero would be
the most informative outcome of all: it would mean a *third* cause is in play
that no evidence so far has named.

## Verification

1. Static assertion: the new prompt contains the guarded prompt verbatim, and
   names FastAPI and `app.py`.
2. One smoke run: assert the produced `app.py` imports FastAPI, not Flask.
3. n=6 pilot at `run_timeout=300`, through `run_batch`'s new `timeout`
   parameter. Never published.

## Out of scope

- Any change to the suites. The user-story task spec stays framework-free;
  the lever lives in the improvement, which is what makes it a lever rather
  than a different workload.
- The unbounded child, turn caps, and watchdogs.
- The n=16 arm. Cycle 8.
