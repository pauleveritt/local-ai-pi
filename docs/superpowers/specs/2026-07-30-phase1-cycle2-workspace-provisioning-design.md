# Design: Phase 1, feature cycle 2 — workspace provisioning

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine
**Feature cycle:** 2 of Phase 1 (this cycle only; later cycles get their own spec)

## Purpose

Introduce `harness/` — the first real code on this branch — with a single
function, `prepare_workspace`, that copies a fixture directory into a fresh,
disposable, git-initialized workspace. This is the smaller of the two
candidates named in `BRIEF.md`'s "read-once-then-write-fresh" entry (the
other being the checkpoint/resume pair, untouched here), and a deliberate
precursor to the hermetic grader: the grader's "fresh project dir" step
needs a workspace to exist before allowlist, config-refusal, and
verdict-file logic can be layered on top of it.

Proven by an automated pytest test that re-runs cycle 1's accept/reject
procedure through a provisioned workspace instead of in-place — unlike
cycle 1's fixtures, this cycle introduces actual code, and code needs a
re-checkable, automated proof rather than a one-time manual note. No
allowlist, no config refusal, no hook-written verdict, no checkpointing,
and no diff exercised — all deferred. This cycle provisions; it does not
judge.

## Background

Cycle 1 established `examples/agentclinic/phase-1/{reference,broken,acceptance}`
and proved, by running `pytest` directly inside each fixture directory,
that the acceptance suite accepts the known-good solution and rejects the
known-broken one. That procedure ran in place — no copying, no isolation.

This cycle doesn't change the fixtures or the suite. It adds the ability to
run that same procedure against a *copy* of a fixture, sitting in its own
temp directory with its own git history, rather than against the fixture
in place. That copy-and-isolate step is what every later cycle that runs
something repeatedly, or lets a model write into a workspace, will need —
but nothing here depends on those future needs yet.

## Design

`harness/workspace.py` exports one function:

```python
@contextmanager
def prepare_workspace(source_dir: Path) -> Iterator[Path]:
    """Copy source_dir into a fresh temp directory, git-init it, and
    yield the workspace path. The workspace is removed on exit."""
```

- Takes the fixture directory as a parameter — never a hardcoded path.
  Per `BRIEF.md`'s "seams, not hardcodes" principle, this must generalize
  to fixtures that don't exist yet without a rewrite.
- Copies all files from `source_dir` into a new temporary directory.
- Runs `git init` and commits the copied state as the initial commit. The
  commit exists so a later cycle can diff against it; this cycle does not
  exercise or test that diff — the initial commit is created and then left
  alone.
- Implemented as a context manager (`with prepare_workspace(...) as ws:`)
  so cleanup is guaranteed on exit, rather than left to the caller or the
  OS temp-dir reaper.

## Verification method

`tests/test_workspace.py` mirrors cycle 1's procedure, run through the new
context manager instead of in place:

1. A test that calls
   `with prepare_workspace(examples/agentclinic/phase-1/reference) as ws:`,
   copies `acceptance/test_acceptance.py` into `ws`, runs `uv run pytest -q`
   (or pytest's in-process runner) from inside `ws`, and asserts exit code
   0 and the same nonzero pass count cycle 1 recorded.
2. A test that does the same against `broken`, and asserts a nonzero exit
   code with the same failing assertion (`assert 404 == 200`) cycle 1
   recorded.
3. A test that asserts the workspace directory no longer exists once the
   `with` block exits — cleanup actually happens, not just claimed.

These tests are the proof; no separate manual procedure or results note
is required for this cycle (unlike cycle 1, where the fixtures being
proven were static files, not code).

## Definition of Done

- `harness/workspace.py` exists with `prepare_workspace` as a context
  manager, parameterized on `source_dir` (no hardcoded fixture path).
- `tests/test_workspace.py` exists and passes, covering the accept-check,
  reject-check, and cleanup-on-exit assertions above.

## Out of scope for this cycle

The hermetic grader (source allowlist, refusal of model-written config,
verdict from a hook-written results file); the checkpoint/resume pair;
exercising or testing the initial git commit as a diff base; n=16 batch
running; any change to the fixtures or acceptance suite from cycle 1.

## Concept budget

Terms this cycle introduces, added to the running list from cycle 1
(`feature cycle`, `phase`, `roadmap`, `suite`, `fixture`, `workspace`,
`hermetic`, `oracle`):

`harness`.
