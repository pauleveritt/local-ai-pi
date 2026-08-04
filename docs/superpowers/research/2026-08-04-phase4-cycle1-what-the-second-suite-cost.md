# Phase 4, cycle 1 — what the second suite cost

Three phases built this harness against exactly one workload. Every
parameter standing where a hardcode used to be had one caller and a
default shaped like AgentClinic Phase 1 — which `BRIEF.md` names as the
one thing that actually cost the previous project. This cycle added a
second, deliberately unlike workload (a stdlib-only duration parser) and
recorded what the harness had to change to accept it.

The bar was modest on purpose: *the harness runs two suites*. This
document is what that bar was chosen to produce — the list below, written
from the diff `0643e5b..95d3844`, not from the plan's predictions.

Every line number was opened and confirmed on 2026-08-04 at `95d3844`.

## What `harness/` had to change

Two files. Nothing else in `harness/` was touched.

**Seam extraction** means a constant became a parameter — the change the
design predicted. **Genuine gap** means something was not general and had
to be built.

| # | Change | Kind |
|---|--------|------|
| 1 | `PHASE_1` and `TASK_SPEC` deleted; `EXAMPLES = REPO_ROOT / "examples"` in their place (`harness/runner.py:13`) | seam extraction |
| 2 | `Suite` frozen dataclass — `name`, `task_spec`, `acceptance`, `source_allowlist` (`harness/runner.py:19-37`) | genuine gap: nothing named a workload before; the four values were four unrelated module constants and defaults |
| 3 | `AGENTCLINIC_PHASE_1` and `DURATION` instances (`harness/runner.py:40-51`) | seam extraction |
| 4 | `run_agentclinic_phase1` → `run_suite(suite, *, model, timeout)` (`harness/runner.py:96`) | seam extraction |
| 5 | The prompt read from `suite.task_spec` rather than `TASK_SPEC` (`harness/runner.py:113`) | seam extraction |
| 6 | `grade()` called with `suite.acceptance` and `source_allowlist=suite.source_allowlist` (`harness/runner.py:138-142`) | seam extraction |
| 7 | `_conditions` takes `suite` first and hashes `suite.task_spec` (`harness/runner.py:188`, `:215`) | genuine gap — see below |
| 8 | `run_batch` takes a required, undefaulted `suite` (`harness/runner.py:252-253`) and refuses a checkpoint recorded under another suite | genuine gap: nothing prevented cross-suite resumption |
| 9 | `grade()`'s `suite: Path` renamed `acceptance: Path`, and `source_allowlist` made keyword-only and **required**, deleting the `("app.py", "templates")` default (`harness/grading.py:75-80`) | seam extraction, and the removal of the one literal hardcode-in-parameter's-clothing |
| 10 | `_test_count(suite)` → `_test_count(acceptance)` and its internals (`harness/grading.py:166`, `:180`) | rename only |

Item 7 is the one worth reading twice. `_conditions` hashing a module
constant instead of the suite it was handed is not a cosmetic slip:
`pi_command` normalizes the prompt away to `"<task-spec>"`, and model, Pi
version, harness revision, both timeouts, and the extension digests are
identical across suites. `task_spec_sha256` is therefore the **only**
`RunConditions` field that distinguishes two suites. Get it wrong and two
suites' checkpoints become mutually resumable, and runs graded against
different contracts accumulate in one file looking like data. The
docstring at `harness/runner.py:195-205` says so, and a test now fails if
the behavior changes.

### The change outside `harness/` nobody planned for

Adding a suite required a `pyproject.toml` edit. `examples/duration` had
to join `norecursedirs` and ruff's `extend-exclude`, mirroring the
pre-existing `examples/agentclinic` entries, because an acceptance
suite's `from duration import parse_duration` only resolves inside a
grading workspace where `source_allowlist` has already copied
`duration.py` alongside it. Collected from the repo root it is an import
error, and linted as project source the reference solution and the
deliberately-broken fixture both raise diagnostics they are not meant to
answer for.

This matters directly to the eventual claim that *a suite author touches
only `examples/`*. Today they do not: they touch two lists in
`pyproject.toml` as well. That is small, but it is not zero, and it is
exactly the kind of cost that stays invisible until someone writes the
third suite.

## What was already general and needed nothing

Naming these is as much a finding as naming the gaps. Each accepted a
second, differently-shaped workload with **no diff at all**:

- `prepare_workspace` (`harness/workspace.py`) — a disposable
  git-initialized directory is workload-independent, and always was.
- The grading plugin (`harness/grading_plugin.py`) — it records one line
  per executed nodeid; it never knew what the tests were about.
- The checkpoint format (`harness/checkpoint.py`) — append-only JSONL of
  `RunResult`s, tolerant of a truncated last line. A second suite is just
  different bytes in `task_spec_sha256`.
- `_pi_command` — model, prompt, extensions. None of the three is
  workload-shaped.
- The process-group handling (`harness/processes.py`) — a timed-out child
  and its descendants die together regardless of which suite spawned it.

Five of the engine's seven modules were already right. The two that were
not are the two that had a workload's name written into them.

## The cycle's main finding: threading a parameter is not the hard part

The `Suite` refactor was mechanical. An independent statement-by-statement
review of it found **no semantic drift** — the refactor was correct as
written, on the first pass.

What nearly shipped broken was the *proof that the seam was used*. Two
tests required by the plan were reported as passing and did not exist
anywhere in the tree. A reviewer then mutation-tested the result:
replacing `suite.*` with the module-level `AGENTCLINIC_PHASE_1` constant
at **six sites** in `harness/runner.py` left the full 144-test suite green
on **every one**. The parameter had been threaded everywhere and proven
nowhere. A follow-up commit (`2dda27b`) added the missing tests and killed
mutations 2-6; Task 3 (`95d3844`) killed mutation 1 — `_conditions`
hashing a module constant instead of the suite it was handed — and added
the cross-suite checkpoint refusal test. An independent reviewer then
confirmed all six mutations die, each attributed to a specific assertion.

**Threading a parameter and proving it is threaded are different pieces of
work, and only the second one is hard.** A refactor that is correct is
indistinguishable, to a green test suite, from a refactor that is correct
*by accident* — and this project's entire premise is that a green suite
which proves nothing is the failure mode to design against. The verification
habit that caught this was not "run the tests"; it was "replace the
parameter with the old constant and see whether anything notices."

That is the practice worth keeping. A seam without a mutation that dies is
a seam on paper.

## Three plan defects, recorded because plans get reread

- The plan said six `run_batch` call sites needed `suite=`. There were
  eleven.
- The plan's model-server check was `omlx diagnose`, which is not a valid
  invocation — that subcommand requires a target argument. Corrected in the
  plan itself to `curl -s -m 10 http://127.0.0.1:8001/v1/models`.

  **This one is worse than it looks, and it is the more useful finding.**
  The same gotcha was already recorded two days earlier, in
  `docs/superpowers/plans/2026-08-02-phase3-cycle1-observable-extension.md`
  line 146: "`omlx diagnose` is not the check: the installed CLI requires a
  target argument". The knowledge existed, in this repository, in a document
  of the same kind. It simply did not reach the next plan, and the next plan
  was written without grepping for it. This is the fourth instance of the
  pattern the Backlog already tracks — a correction lands where the current
  task points and not everywhere the same fact is written — and it is the
  first instance where the earlier correction was one `grep` away from the
  person reintroducing the error. The three prior instances were caught by
  review; so was this one. Nothing structural has ever caught one.
- The plan told the implementer to "expect one to ten minutes" for the live
  run. That invited backgrounding the command, and the controlling process
  then tore it down mid-flight. A plan that predicts a duration invites that
  choice; it should say "run it in the foreground and wait" instead.

## `prepare_workspace`'s `finally` is load-bearing for diagnosis

`prepare_workspace` removes the workspace in a `finally` block
(`harness/workspace.py:76-77`). That was written for hygiene, but it has a
second property nobody designed for: because cleanup is guaranteed on every
non-fatal path, **a workspace that survives is unambiguous evidence of a
hard kill** — not a failed test, not a raised exception.

That inference is what made the killed live run diagnosable at all, since
the harness itself recorded nothing. Named here so it is not removed by
someone tidying up. The corresponding gap — that a dead run leaves no trace
in the harness's own records — is a Backlog entry.

## The `_test_count` / parametrize trap

`_test_count` (`harness/grading.py:166-185`) counts module-level
`def test_*` and `async def test_*` declarations from the AST. The grading
plugin records one line per *executed* nodeid. `grade()` accepts only when
`tests_executed == tests_expected`.

`@pytest.mark.parametrize` breaks that identity: one declaration, N
executions. The verdict then rejects a **correct** solution — the
engine-failure-that-looks-like-a-model-failure that Phase 1 exists to
prevent.

Two ways out were available. Extending `_test_count` to evaluate
parametrize arguments means the harness deciding what pytest *would*
collect, rather than reading what a file *declares* — reimplementing
collection, statically, against decorators that can hold arbitrary
expressions. The alternative is a documented constraint: one test function
per contract behavior, no parametrize in an acceptance suite. That is
cheap, it is what both suites already do naturally, and it fails loudly
rather than subtly if violated.

The constraint was chosen. It is recorded where a suite author will
actually meet it — in the acceptance file's own module docstring
(`examples/duration/acceptance/test_acceptance.py:5-11`), stating the
mechanism and that it binds acceptance suites only; the harness's own
tests under `tests/` parametrize freely.

## What is still not general

A list of what was *not* general enough is worth more to a future reader
than any claim that things are.

- **Seeding.** `prepare_workspace(source_dir=...)` still has zero real
  callers, and `Suite` has no seed field. The generality demonstrated here
  covers the spec and grading seams only. A workload that needs the model
  to start from existing code has not been tried.
- **The grading subprocess's dependencies.** `harness/grading.py:211` sets
  `PYTHONPATH` to the repo root, so an acceptance suite can only import
  what the harness's own venv provides. AgentClinic's imports `starlette`
  and `turbohtml`; the duration suite is stdlib-only, so this cycle never
  forced the question. `Suite` does not capture it. A third suite needing a
  dependency the harness does not already have will find this immediately.
- **Within-suite condition discrimination.** `RunConditions` records
  nothing about the acceptance file's contents or the `source_allowlist`,
  and `harness_revision` is `git rev-parse HEAD`
  (`harness/runner.py:206-207`) — so an *uncommitted* edit to an acceptance
  file leaves conditions byte-identical. Between suites, discrimination is
  now locked by tests. Within one, it is not. Deliberately left open;
  see the Backlog for why and for the gate.

## What this cycle does not claim

**Not that a third suite is free.** n=2 shows that a parameter is a
parameter — that `suite.task_spec` is genuinely read rather than
decorative. It does not show that a suite author never needs to touch the
engine. Two of the three items above are precisely the shapes a third suite
is likely to hit first, and the `pyproject.toml` edit is a cost every suite
pays today.

It also claims no number. No batch was run; the one live end-to-end
invocation of the duration suite passed in 88.68s against a real Pi and is
evidence that the seam works end to end, not a measurement of anything.
