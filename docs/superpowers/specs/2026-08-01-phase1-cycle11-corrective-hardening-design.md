# Cycle 11 — Corrective hardening

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine  
**Status:** approved for implementation

## Why this cycle exists

The first complete review after the first live run found four proven faults in
the path to a resumable batch. They are prerequisites, not improvements to
defer until the batch is already depending on them:

- repairing a checkpoint rewrites valid records and can lose them if that
  rewrite is interrupted;
- grading inherits caller-controlled pytest and Python settings, contradicting
  its isolation claim;
- a global Git hook can prevent workspace setup, and an empty source cannot
  create its promised initial commit;
- two tests do not prove their stated contracts: async tests are unpinned and
  the liveness stub accepts every request path. The live runner test also
  derives its only assertion from the suite, rather than proving that Pi ran.

Cycle 11 repairs exactly those demonstrated faults. It introduces no batch
loop, timeout handling, retry policy, or measurement collection.

## Required behavior

### Checkpoint records

`append_checkpoint(path, result)` must preserve every complete JSON record
already on disk.

- A complete final JSON object without a trailing newline is a record, not a
  dangling fragment. Before appending, preserve it and add the missing newline.
- A malformed final fragment is the only recoverable corruption. Remove only
  that suffix by truncating the existing file at the preceding newline; never
  reconstruct the preceding contents with `write_text`.
- The new JSONL record is appended as one newline-terminated line and flushed
  to disk. An interrupted append therefore remains a recoverable final
  fragment.
- A malformed non-final line remains an error on load.

This is deliberately not a general journal or a promise to survive arbitrary
filesystem failure. It fixes the exact interruption window a batch would
otherwise enter while retaining Cycle 10's simple JSONL contract.

### Grading isolation

The pytest child process receives a constructed environment, rather than a
copy of `os.environ`. It must have only the values the grader deliberately
needs:

- the harness repository on `PYTHONPATH`, so the explicit grading plugin can
  load;
- a controlled `PATH`, locale, timezone, and fresh home/XDG locations;
- `PYTHONNOUSERSITE=1` and `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`;
- the grader's private results-file variable.

The command continues explicitly to load `harness.grading_plugin`. Settings
such as `PYTEST_ADDOPTS`, `PYTEST_PLUGINS`, user-site packages, and user config
must not alter the verdict. The regression proof sets an ambient pytest option
that would turn the reference fixture into collection-only mode under the old
implementation, and proves the fixture remains accepted.

“Hermetic” in this project means isolation from model-written files and
uncontrolled caller configuration for the graded process. It does not claim
that Python, pytest, or the host operating system cease to be dependencies.

### Workspace setup

`prepare_workspace(source_dir)` must support a literally empty source
directory and still yield a workspace whose `HEAD` is an initial commit. It
uses Git's `--allow-empty` option rather than adding a harness-owned placeholder
to the model's workspace.

Its initial commit must not run hooks or inherit a contributor's global/system
Git configuration. It uses a controlled Git environment and an explicit empty
`core.hooksPath` for the commit. This isolation applies only to harness-created
workspace setup; it does not alter the user's repository configuration.

### Proof repairs

- `_test_count()` has an explicit regression test for a module-level `async
  def test_*`, alongside existing synchronous coverage.
- The liveness stub returns success only for `/v1/models`; its existing success
  test therefore proves the checked path, not merely that some GET succeeded.
- `RunResult` records Pi's return code. The runner's non-live test replaces the
  circular `tests_expected == 4` assertion with controlled collaborators that
  prove liveness runs before Pi, Pi is invoked in the prepared workspace, and
  its stdout, stderr, and return code reach the result. It does not pretend a
  mocked Pi is evidence of real model output.

## Boundaries

Not in this cycle:

- timing out Pi or pytest, killing descendant processes, or converting a
  timeout into a recorded result — Cycle 12;
- choosing the final Pi invocation, checking a real model response, adding run
  identity fields, wiring checkpoints into a loop, or running sixteen attempts
  — Cycles 13–14;
- telemetry, retries, concurrent runs, or a new checkpoint format.

The one accepted live run remains historical evidence. A fresh real-output
check belongs at the start of the later batch contract, where it can use the
same final invocation the batch will use.

## Acceptance evidence

All new evidence is fixture-only and local:

1. checkpoint tests prove complete no-newline records survive a later append,
   malformed final fragments are discarded without rewriting valid prefixes,
   and malformed non-final records still raise;
2. the reference fixture remains accepted when the parent environment supplies
   `PYTEST_ADDOPTS=--collect-only`, while the ambient value remains observable
   outside the child;
3. workspace tests prove a global hook cannot block setup and an empty source
   has a real initial commit with no placeholder file;
4. focused tests prove async test counting, the exact liveness endpoint, and
   the runner's call/order/result contract.

No model server or Pi executable is required for this cycle's test suite.

## Deferred choices, with recommendations

Cycle 12 should use a separate process group for each timed subprocess and
terminate the whole group on timeout. Cycle 13 should restore the trusted
noninteractive, JSON, no-session invocation; perform a real-output preflight
with that exact invocation; and record the model, Pi version, task-spec digest,
and harness revision. Cycle 14 should then execute sixteen sequential,
checkpointed attempts. `ROADMAP.md` is rewritten at this cycle's close to make
that dependency order the active Phase 1 path.
