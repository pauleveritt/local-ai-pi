# Cycle 8 — First real run

**Phase:** 1 — Reproduce AgentClinic Phase 1 with a trustworthy engine
**Status:** design, awaiting plan

## Why this cycle

Cycles 1–7 built and proved the entire judging apparatus with no model in
the loop: workspace provisioning, hermetic grading, verdict-from-results-
file, subversion resistance, config refusal, the transplanted AgentClinic
task spec, and a model-server liveness check. Every one of them is provable
against fixtures alone. Cycle 8 is the first cycle that isn't — it invokes
`pi` for real, against a fresh workspace, and grades the result with the
same `grade()` cycles 3–6 already proved. This produces one number the
project can actually look at, plus the diff showing what the model wrote,
using no new judging machinery — all of it already exists.

## What this cycle is not

- Not the n=16 statistical batch (cycle 11). This produces one `RunResult`,
  once, and stops.
- Not checkpoint recording (cycle 10) or the source allowlist (cycle 9).
  Cycle 9 explicitly needs evidence from a real run to be more than a
  guess — this cycle is what produces that evidence, but does not build
  the allowlist itself.
- Not batch-friendly failure handling. A hung `pi` invocation raises
  `subprocess.TimeoutExpired` uncaught; making a batch tolerate one hung
  run without aborting the rest is cycle 10/11's job, already noted in
  `ROADMAP.md`.

## Interface

```python
# harness/runner.py

@dataclass(frozen=True)
class RunResult:
    diff: str
    grade: GradeResult

def run_agentclinic_phase1(
    model: str = "omlx/gemma-4-12B-it-MLX-8bit",
    timeout: int = 600,
) -> RunResult:
    ...
```

- `model` and `timeout` are parameters with defaults — seams, not
  hardcodes, per `BRIEF.md`'s stated principle. The default model matches
  `BRIEF.md`'s recorded setup; the default timeout (600 seconds) is
  generous enough to absorb a small local model's real latency without
  hanging indefinitely.
- Returns a `RunResult` on success. Two failure modes are allowed to
  propagate uncaught rather than being wrapped: `ModelServerDown` (cycle
  7 — an environment failure, not a graded run) and
  `subprocess.TimeoutExpired` (a hang is a fact about this run, not
  something this cycle tries to paper over).

## Behavior

1. Call `check_model_server_alive()` first. If the server is down, this
   raises and nothing else happens — no workspace is even prepared.
2. `prepare_workspace(EMPTY_DIR)`, where `EMPTY_DIR` is a new fixture,
   `examples/agentclinic/phase-1/empty/` — the fixture that stands in for
   "nothing," the same way `reference` and `broken` stand in for "a
   finished solution." It is not literally zero files: `prepare_workspace`
   does `git add -A` then `git commit` with no `--allow-empty`, so a
   directory with nothing in it would fail with `CalledProcessError` —
   this is the exact bug `ROADMAP.md` already carries forward as an open
   note for cycle 9. Fixing `prepare_workspace` to tolerate an empty source
   is cycle 9's job, not this one, so `EMPTY_DIR` instead contains a
   single inert placeholder (a `.gitkeep` file) — enough for `git add -A`
   to stage something, nothing an agent would mistake for seeded content
   or starter code.
3. Read `examples/agentclinic/specs/roadmap.md` and pass its contents as
   `pi`'s prompt text — not a file placed in the workspace. The workspace
   stays literally empty; the spec is never a second, undocumented channel
   the model could also discover on disk.
4. Invoke `pi` via `subprocess.run`, with:
   - `cwd=workspace`
   - the harness's own Python environment (so `fastapi`, `turbohtml`, and
     `pytest` are already importable — the model writes application code,
     not environment setup, matching the fact that the task spec never
     mentions installing dependencies)
   - the transplanted `.pi/extensions/hello-world.ts` (copied verbatim
     from `main`, read-once-then-write-fresh) and the old branch's known
     isolation flag set: `--no-extensions --extension
     .pi/extensions/hello-world.ts --no-skills --no-prompt-templates
     --no-themes --no-context-files --approve`
   - `timeout=timeout`
5. Capture `git diff` of the workspace against its initial commit (the one
   `prepare_workspace` made in step 2) — the only record of what the model
   wrote, since the workspace is deleted when the context manager exits.
   Plain `git diff <commit>` never shows untracked files, and every file
   the model creates starts out untracked, so this requires `git add -A`
   immediately before diffing (`git diff --cached <initial-commit>`), and
   the initial commit's hash must be captured right after step 2, before
   `pi` runs — in case the model itself commits during the run and moves
   `HEAD`.
6. Call `grade(workspace, PHASE_1 / "acceptance" / "test_acceptance.py")`.
7. Return `RunResult(diff=diff_text, grade=grade_result)`.

## Testing

This is the one cycle that cannot be fully hermetic — it needs a real
model server and a real `pi` invocation to prove anything at all. One
integration test:

- Skipped (`pytest.mark.skipif`) when `pi` isn't on `PATH` or the model
  server isn't alive, so the rest of the suite stays runnable without
  either.
- Runs `run_agentclinic_phase1()` once and asserts the *shape* of the
  result — a `RunResult` whose `grade` is a `GradeResult` with
  `tests_expected == 4` — not `grade.accepted is True`. A single run is
  not the n=16 statistical claim; asserting acceptance here would make
  this test flaky in exactly the way cycle 11's batch exists to measure
  honestly.

## Non-goals recap

Batch execution, checkpoint recording, and the source allowlist are
explicitly deferred to cycles 9–11, per the design discussion above.
