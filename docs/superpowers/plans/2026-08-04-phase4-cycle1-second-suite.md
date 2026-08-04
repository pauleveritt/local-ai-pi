# Second Eval Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the harness a second workload, so the parameters that stand
where hardcodes used to be are demonstrated by a real second caller rather
than asserted.

**Architecture:** A frozen `Suite` dataclass collects the three constants
currently at `harness/runner.py:13-14` — the prompt, the acceptance
contract, and the source allowlist. `harness/runner.py` declares two
instances and `run_agentclinic_phase1` becomes `run_suite(suite, ...)`. A
new stdlib-only duration-parser suite lands under `examples/duration/`,
with its own known-good and known-broken solutions.

**Tech Stack:** Python 3.14, pytest, uv, Sphinx (MyST), Ruff, pyrefly.

## Global Constraints

- **Design spec:** `docs/superpowers/specs/2026-08-04-phase4-cycle1-second-suite-design.md`. Read it before Task 1.
- **Branch:** `second-suite`, in the worktree `.worktrees/second-suite`. Never work on `main`.
- **Never run `git stash`.** The stash stack is shared across worktrees and concurrent sessions.
- **Never `git commit` while a `run_batch()` is in flight** — `_conditions` reads `git rev-parse HEAD` on every run and aborts the batch when HEAD moves.
- **Runs are sequential, never concurrent.** One shared local model has no isolation. Never leave an abandoned `pi` process queued against it.
- **The four gates**, all of which must pass before a task is done:
  - `uv run pytest`
  - `uv run ruff check .`
  - `uv run pyrefly check`
  - `uv run sphinx-build -W -b html docs docs/_build/html`
- **Sphinx toctrees are explicit.** Any new document under `docs/superpowers/` must be added to the matching toctree in `docs/superpowers/index.md`, or the strict build fails.
- **Pi is pinned** to `EXPECTED_PI_VERSION = "0.83.0"` (`harness/runner.py:17`). Do not change it.
- **No `@pytest.mark.parametrize` in any acceptance suite under `examples/`.** `_test_count` counts declarations; the grading plugin records executions. Parametrize splits them and a *correct* solution gets rejected. This rule does **not** apply to `tests/` — the harness's own tests may parametrize freely.
- **Live model runs** require `SATYRN_LIVE=1` and a verified-alive model server. When the server is down, `pi` exits 0 with empty stderr and the harness records a fabricated result that looks like data.
- **This cycle runs no batch.** It claims no number.

---

### Task 1: The duration suite fixtures

Creates the workload's four files and proves the grader accepts the
known-good solution and rejects the known-broken one. Touches no harness
code — `grade()` is called directly, so this task stands alone and its
tests keep passing unchanged through Task 2.

**Files:**
- Create: `examples/duration/spec.md`
- Create: `examples/duration/acceptance/test_acceptance.py`
- Create: `examples/duration/reference/duration.py`
- Create: `examples/duration/broken/duration.py`
- Create: `tests/test_duration_suite.py`

**Interfaces:**
- Consumes: `harness.grading.grade(workspace, suite, timeout=30, source_allowlist=("app.py", "templates"))` and `harness.workspace.prepare_workspace(source_dir)` as they exist today.
- Produces: the four `examples/duration/` paths, which Task 2's `DURATION` instance points at. The graded module is named `duration.py` and exports `parse_duration(text: str) -> int`.

- [ ] **Step 1: Write the acceptance contract**

Create `examples/duration/acceptance/test_acceptance.py`:

```python
"""Acceptance contract -- duration parser. Harness-owned; the model cannot edit this.

Contract source: examples/duration/spec.md.

**No `@pytest.mark.parametrize` here, or in any acceptance suite.**
`harness.grading._test_count` counts module-level `def test_*` declarations,
while the grading plugin records one line per *executed* nodeid. Parametrize
splits them -- 1 declared, N executed -- so `tests_executed == tests_expected`
fails and a *correct* solution is rejected. One test function per contract
behavior. This constraint is on acceptance suites only; the harness's own
tests under `tests/` may parametrize freely.

Assert only the contract in spec.md. Do not assert on internal helper names,
module layout, or the exception message -- a correct-but-different solution
must pass.
"""
import pytest

from duration import parse_duration


def test_seconds_alone():
    assert parse_duration("30s") == 30


def test_minutes_alone():
    assert parse_duration("5m") == 300


def test_hours_alone():
    assert parse_duration("1h") == 3600


def test_hours_and_minutes_combine():
    """The defining case: a parser that stops at the first unit returns 3600."""
    assert parse_duration("1h30m") == 5400


def test_all_three_units_combine():
    assert parse_duration("2h15m30s") == 8130


def test_unparseable_input_raises_value_error():
    with pytest.raises(ValueError):
        parse_duration("banana")
```

- [ ] **Step 2: Write the known-good solution**

Create `examples/duration/reference/duration.py`:

```python
"""Known-good solution for the duration suite. Harness-owned fixture."""
import re

_PATTERN = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?")


def parse_duration(text: str) -> int:
    """Return the number of seconds in a duration string like "1h30m"."""
    match = _PATTERN.fullmatch(text)
    if match is None or not any(match.groups()):
        raise ValueError(f"cannot parse duration: {text!r}")
    hours, minutes, seconds = (int(group or 0) for group in match.groups())
    return hours * 3600 + minutes * 60 + seconds
```

The `not any(match.groups())` guard matters: the pattern is entirely
optional groups, so it matches the empty string. Without the guard,
`parse_duration("")` returns 0 instead of raising.

- [ ] **Step 3: Write the known-broken solution**

Create `examples/duration/broken/duration.py`:

```python
"""Known-broken solution for the duration suite. Harness-owned fixture.

One defect: it stops at the first unit, so every multi-unit input is
wrong. `"1h30m"` returns 3600 and `"2h15m30s"` returns 7200. Single-unit
inputs and the unparseable case are handled correctly, so this fixture
proves the grader discriminates on behavior rather than rejecting anything
that merely looks different.
"""
import re

_UNITS = {"h": 3600, "m": 60, "s": 1}
_PATTERN = re.compile(r"(\d+)([hms])")


def parse_duration(text: str) -> int:
    """Return the number of seconds in a duration string like "1h30m"."""
    match = _PATTERN.match(text)
    if match is None:
        raise ValueError(f"cannot parse duration: {text!r}")
    return int(match.group(1)) * _UNITS[match.group(2)]
```

- [ ] **Step 4: Write the task spec the model receives**

Create `examples/duration/spec.md`:

````markdown
# Duration parser

Write a module `duration.py` in the project root containing one public
function:

```python
def parse_duration(text: str) -> int:
    ...
```

It returns the total number of seconds a duration string represents.

## Contract

| input | result |
|---|---|
| `"30s"` | `30` |
| `"5m"` | `300` |
| `"1h"` | `3600` |
| `"1h30m"` | `5400` |
| `"2h15m30s"` | `8130` |
| anything it cannot parse | raises `ValueError` |

Units are hours (`h`), minutes (`m`), and seconds (`s`). When several
appear they are written largest-first and their values add together.

## Environment

- The Python standard library only. Do not import third-party packages
  and do not install anything.
- The file must be named `duration.py` and must sit in the project root.
- Run tests with `python -m pytest` from the project root.
````

The filename is stated in the spec because `DURATION.source_allowlist` is
`("duration.py",)` and the two must agree — a solution written anywhere
else is copied nowhere and fails grading for a reason that looks like a
model error.

- [ ] **Step 5: Write the failing evidence-floor test**

Create `tests/test_duration_suite.py`:

```python
"""The evidence floor for the duration suite.

From `BRIEF.md`: "A grader's verdict isn't evidence until it has accepted a
known-good solution and rejected a known-broken one." These are that proof
for this suite. They need no model and no Pi.
"""
from pathlib import Path

from harness.grading import grade
from harness.workspace import prepare_workspace

REPO_ROOT = Path(__file__).resolve().parents[1]
DURATION = REPO_ROOT / "examples" / "duration"
ACCEPTANCE = DURATION / "acceptance" / "test_acceptance.py"
ALLOWLIST = ("duration.py",)


def test_grade_accepts_the_duration_reference_solution():
    with prepare_workspace(DURATION / "reference") as workspace:
        result = grade(workspace, ACCEPTANCE, source_allowlist=ALLOWLIST)

    assert result.accepted is True
    assert result.tests_executed == result.tests_expected == 6


def test_grade_rejects_the_duration_broken_solution():
    with prepare_workspace(DURATION / "broken") as workspace:
        result = grade(workspace, ACCEPTANCE, source_allowlist=ALLOWLIST)

    assert result.accepted is False
    # Non-vacuity: the broken solution is rejected for failing tests, not
    # for a collection error or an empty run. Four of six behaviors are
    # correct, so a grader that rejected everything would pass this test
    # for the wrong reason.
    assert result.tests_executed == result.tests_expected == 6
    assert result.refused_config == ()
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_duration_suite.py -v`

Expected: 2 passed. `grade()` already accepts `source_allowlist` as a
keyword with an AgentClinic-shaped default; passing `("duration.py",)`
overrides it.

If `test_grade_accepts_the_duration_reference_solution` fails with
`tests_executed` of 0, the acceptance file was not collected — check the
allowlist copied `duration.py` into the grading directory.

- [ ] **Step 7: Verify the broken fixture is broken for the stated reason**

Run:

```bash
uv run python -c "
import sys; sys.path.insert(0, 'examples/duration/broken')
from duration import parse_duration
print(parse_duration('1h30m'), parse_duration('2h15m30s'), parse_duration('5m'))
"
```

Expected output: `3600 7200 300`

This confirms the fixture fails exactly the two multi-unit rows and gets
the single-unit row right — the discrimination the non-vacuity assertion
depends on.

- [ ] **Step 8: Run the four gates**

```bash
uv run pytest && uv run ruff check . && uv run pyrefly check && uv run sphinx-build -W -b html docs docs/_build/html
```

Expected: all pass. `examples/duration/**` is not part of the docs build.

- [ ] **Step 9: Commit**

```bash
git add examples/duration tests/test_duration_suite.py
git commit -m "feat(second-suite): the duration workload and its evidence floor"
```

---

### Task 2: The `Suite` descriptor and the re-plumbing

Dissolves the three constants into a dataclass, gives the runner a suite
parameter, and makes `grade()`'s allowlist a required argument so no
workload-shaped default survives. Behavior for the existing suite is
unchanged; this is a refactor with its own test updates.

**Files:**
- Modify: `harness/runner.py` (constants at `:12-17`, `run_agentclinic_phase1` at `:61-111`, `_conditions` at `:147-165`, `run_batch` at `:199-237`)
- Modify: `harness/grading.py` (`grade` signature at `:75-80`, body use of `suite` at `:92` and `:122` and `:139`, `_test_count` at `:159-178`)
- Modify: `tests/test_runner.py`
- Modify: `tests/test_grading.py`
- Modify: `tests/test_config_refusal.py`
- Modify: `tests/test_subversion.py`

**Interfaces:**
- Consumes: `examples/duration/spec.md` and `examples/duration/acceptance/test_acceptance.py` from Task 1. `DURATION.task_spec` is read by `_conditions`, so those files must exist before this task runs.
- Produces:
  - `harness.runner.Suite(name: str, task_spec: Path, acceptance: Path, source_allowlist: tuple[str, ...])`, frozen.
  - `harness.runner.AGENTCLINIC_PHASE_1` and `harness.runner.DURATION`.
  - `harness.runner.run_suite(suite: Suite, *, model: str = DEFAULT_MODEL, timeout: int = 600) -> RunResult`.
  - `harness.runner._conditions(suite: Suite, model: str, command: list[str], timeout: int, extensions: tuple[Path, ...] = EXTENSIONS) -> RunConditions`.
  - `harness.runner.run_batch(checkpoint_path: Path, *, suite: Suite, target: int = 16, model: str = DEFAULT_MODEL) -> list[RunResult]`.
  - `harness.grading.grade(workspace: Path, acceptance: Path, timeout: int | float = 30, *, source_allowlist: tuple[str, ...]) -> GradeResult`.
  - `harness.runner.PHASE_1` and `harness.runner.TASK_SPEC` are **removed**.

- [ ] **Step 1: Write the failing test for the descriptor**

Add to `tests/test_runner.py`, near the other module-level tests:

```python
def test_both_suites_point_at_files_that_exist():
    """A Suite whose paths are wrong fails at run time, inside a live
    invocation, where the failure is expensive and reads like a model
    problem. Catch it here instead."""
    for suite in (runner.AGENTCLINIC_PHASE_1, runner.DURATION):
        assert suite.task_spec.is_file(), f"{suite.name}: {suite.task_spec}"
        assert suite.acceptance.is_file(), f"{suite.name}: {suite.acceptance}"
        assert suite.source_allowlist


def test_the_two_suites_use_different_allowlists():
    """The allowlist is the seam BRIEF.md names by example
    (`_SOURCE_FILES = ("app.py", "models.py")`). Two suites differing in
    both arity and kind -- file+directory versus a single file -- is what
    shows it is a parameter rather than decoration."""
    assert runner.AGENTCLINIC_PHASE_1.source_allowlist == ("app.py", "templates")
    assert runner.DURATION.source_allowlist == ("duration.py",)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_runner.py::test_both_suites_point_at_files_that_exist -v`

Expected: FAIL with `AttributeError: module 'harness.runner' has no attribute 'AGENTCLINIC_PHASE_1'`

- [ ] **Step 3: Add the descriptor and the two instances**

In `harness/runner.py`, replace lines 12-17:

```python
REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_1 = REPO_ROOT / "examples" / "agentclinic" / "phase-1"
TASK_SPEC = REPO_ROOT / "examples" / "agentclinic" / "specs" / "roadmap.md"
EXTENSIONS: tuple[Path, ...] = (REPO_ROOT / ".pi" / "extensions" / "hello-world.ts",)
DEFAULT_MODEL = "omlx/gemma-4-12B-it-MLX-8bit"
EXPECTED_PI_VERSION = "0.83.0"
```

with:

```python
REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = REPO_ROOT / "examples"
EXTENSIONS: tuple[Path, ...] = (REPO_ROOT / ".pi" / "extensions" / "hello-world.ts",)
DEFAULT_MODEL = "omlx/gemma-4-12B-it-MLX-8bit"
EXPECTED_PI_VERSION = "0.83.0"


@dataclass(frozen=True)
class Suite:
    """One workload the harness can run: the prompt a model is given, the
    harness-owned contract it is graded against, and which model-written
    paths are copied out of the workspace for grading.

    Known-good and known-broken solutions are deliberately absent. A *run*
    never needs them; only the evidence-floor tests do, and those name the
    paths directly. `Suite` carries what a run requires and nothing else.

    Seeding is likewise absent. `prepare_workspace` already accepts a
    `source_dir`, but no suite uses it, and a field no caller sets is
    machinery ahead of the contract it serves.
    """

    name: str
    task_spec: Path
    acceptance: Path
    source_allowlist: tuple[str, ...]


AGENTCLINIC_PHASE_1 = Suite(
    name="agentclinic-phase-1",
    task_spec=EXAMPLES / "agentclinic" / "specs" / "roadmap.md",
    acceptance=EXAMPLES / "agentclinic" / "phase-1" / "acceptance" / "test_acceptance.py",
    source_allowlist=("app.py", "templates"),
)

DURATION = Suite(
    name="duration",
    task_spec=EXAMPLES / "duration" / "spec.md",
    acceptance=EXAMPLES / "duration" / "acceptance" / "test_acceptance.py",
    source_allowlist=("duration.py",),
)
```

`dataclass` and `Path` are already imported at `harness/runner.py:4-5`.

- [ ] **Step 4: Run the two new tests to verify they pass**

Run: `uv run pytest tests/test_runner.py -k "both_suites or different_allowlists" -v`

Expected: 2 passed.

- [ ] **Step 5: Rename `grade()`'s parameter and require the allowlist**

In `harness/grading.py`, replace the signature at `:75-80`:

```python
def grade(
    workspace: Path,
    suite: Path,
    timeout: int | float = 30,
    source_allowlist: tuple[str, ...] = ("app.py", "templates"),
) -> GradeResult:
```

with:

```python
def grade(
    workspace: Path,
    acceptance: Path,
    timeout: int | float = 30,
    *,
    source_allowlist: tuple[str, ...],
) -> GradeResult:
```

Then in the body: `_test_count(suite)` at `:92` becomes
`_test_count(acceptance)`; `shutil.copy2(suite, grading_dir / suite.name)`
at `:122` becomes
`shutil.copy2(acceptance, grading_dir / acceptance.name)`; and
`suite.name` in the pytest argv at `:139` becomes `acceptance.name`.

Rename `_test_count`'s parameter at `:159` from `suite` to `acceptance`
and update its two body references (`suite.read_text()`, `filename=str(suite)`).

In the `grade` docstring, change "Copy source_allowlist paths (and the
suite)" to "Copy source_allowlist paths (and the acceptance file)".

Add to the `grade` docstring, after the existing paragraphs:

```
    `source_allowlist` is required rather than defaulted. It used to
    default to `("app.py", "templates")` -- the first workload's shape --
    which is precisely the hardcode-wearing-a-parameter's-clothes that
    `BRIEF.md` names as the previous project's one real cost. Every caller
    now states which workload it is grading.
```

- [ ] **Step 6: Update every `grade()` call site**

There are twelve. In `tests/test_grading.py`, add after `PHASE_1` at `:21`:

```python
ALLOWLIST = ("app.py", "templates")
```

and add `source_allowlist=ALLOWLIST` to the calls at `:241`, `:251`,
`:262`, `:271`, `:307`, and `:329`. The call at `:350` already passes
`source_allowlist=("app.py", "templates", "harness")` — leave it alone.

In `tests/test_config_refusal.py`, add `ALLOWLIST = ("app.py", "templates")`
beside the existing `SUITE` constant and add `source_allowlist=ALLOWLIST`
to the calls at `:75`, `:85`, and `:96`.

In `tests/test_subversion.py`, do the same for the calls at `:55` and `:71`.

In `harness/runner.py`, the call at `:101` is replaced wholesale in Step 7.

- [ ] **Step 7: Re-plumb the runner**

In `harness/runner.py`, replace `run_agentclinic_phase1` (`:61-111`) — the
signature, the two suite-dependent lines, and the grade call:

```python
def run_suite(
    suite: Suite,
    *,
    model: str = DEFAULT_MODEL,
    timeout: int = 600,
) -> RunResult:
    check_model_server_alive()

    with prepare_workspace() as workspace:
        initial_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

        prompt = suite.task_spec.read_text()
        extensions = EXTENSIONS
        command = _pi_command(model, prompt, extensions)
        conditions = _conditions(suite, model, command, timeout, extensions)
        pi_proc = run_process(
            command,
            timeout=timeout,
            cwd=workspace,
        )

        # Stage everything before diffing: plain `git diff <commit>` never
        # shows untracked files, and the model's new files (app.py, etc.)
        # start out untracked. `git add -A` first, then diff the initial
        # commit against the index, so new files appear as additions.
        subprocess.run(
            ["git", "add", "-A"], cwd=workspace, check=True, capture_output=True
        )
        diff = subprocess.run(
            ["git", "diff", "--cached", initial_commit],
            cwd=workspace,
            check=True,
            capture_output=True,
            text=True,
        ).stdout

        grade_result = grade(
            workspace,
            suite.acceptance,
            source_allowlist=suite.source_allowlist,
        )

    return RunResult(
        diff=diff,
        grade=grade_result,
        pi_stdout=pi_proc.stdout,
        pi_stderr=pi_proc.stderr,
        pi_returncode=pi_proc.returncode,
        pi_timed_out=pi_proc.timed_out,
        conditions=conditions,
    )
```

Replace `_conditions` (`:147-165`):

```python
def _conditions(
    suite: Suite,
    model: str,
    command: list[str],
    timeout: int,
    extensions: tuple[Path, ...] = EXTENSIONS,
) -> RunConditions:
    """The conditions a run of `suite` happens under.

    `suite.task_spec`'s digest is load-bearing beyond recording the
    prompt: it is the **only** field of `RunConditions` that differs
    between two suites. `pi_command` normalizes the prompt away to
    `"<task-spec>"`, and model, Pi version, harness revision, both
    timeouts, and the extension digests are shared. Hash the suite that
    was passed in, never a module-level constant -- otherwise two suites'
    checkpoints become mutually resumable and runs graded against
    different contracts accumulate in one file looking like data.
    """
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    version = subprocess.run(
        ["pi", "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    normalized = tuple("<task-spec>" if item == command[-1] else item for item in command)
    return RunConditions(
        model=model, pi_command=normalized, pi_version=version,
        task_spec_sha256=hashlib.sha256(suite.task_spec.read_bytes()).hexdigest(),
        harness_revision=revision, run_timeout=timeout, grade_timeout=30,
        extension_digests=tuple(_extension_digest(path) for path in extensions),
    )
```

In `preflight_model` (`:168-174`), no suite is involved — the prompt is
the literal `"Reply with exactly SATYRN."` — so leave it unchanged.

In `run_batch` (`:199-237`), change the signature and the three
suite-dependent lines:

```python
def run_batch(
    checkpoint_path: Path,
    *,
    suite: Suite,
    target: int = 16,
    model: str = DEFAULT_MODEL,
) -> list[RunResult]:
    """Run sequential attempts until the requested checkpoint length.

    `suite` is required and undefaulted on purpose. A default would let a
    caller record a batch under a workload they never named, and since
    `task_spec_sha256` is the only condition that distinguishes two
    suites, that mistake produces a checkpoint that looks valid.
    """
    from harness.checkpoint import append_checkpoint, load_checkpoint

    if target < 0:
        raise ValueError("target must not be negative")
    records = load_checkpoint(checkpoint_path)
    extensions = EXTENSIONS
    command = _pi_command(model, suite.task_spec.read_text(), extensions)
    requested = _conditions(suite, model, command, 600, extensions)
```

The `EXPECTED_PI_VERSION` check, the conditions comparison, the early
return, and the run loop below it are unchanged except for the one call:
`result = run_agentclinic_phase1(model=model)` becomes
`result = run_suite(suite, model=model)`.

- [ ] **Step 8: Update `tests/test_runner.py` for the new signatures**

Six changes, all mechanical:

1. The import at `:21` — `run_agentclinic_phase1` becomes `run_suite`.
2. In `test_run_agentclinic_phase1_calls_pi_and_returns_its_result` (`:37`), rename the test to `test_run_suite_calls_pi_and_returns_its_result`; change `fake_grade(actual_workspace, suite)` to `fake_grade(actual_workspace, acceptance, *, source_allowlist)` and its assertion to:

```python
        assert acceptance == runner.AGENTCLINIC_PHASE_1.acceptance
        assert source_allowlist == ("app.py", "templates")
```

3. In the same test, the `_conditions` stub becomes
   `lambda suite, model, command, timeout, extensions: None`, and the call
   becomes `run_suite(runner.AGENTCLINIC_PHASE_1)`.
4. Every `monkeypatch.setattr(runner, "run_agentclinic_phase1", ...)` becomes `"run_suite"`, and each fake's signature changes from `(model)` to `(suite, *, model)`. There are six, at `:220`, `:240`, `:263`, `:278`, `:296`, and `:317`.
5. Every `runner.run_batch(checkpoint, target=N, model="model")` call gains `suite=runner.AGENTCLINIC_PHASE_1`. There are six.
6. The live test at `:330` — rename to `test_run_suite_produces_live_model_evidence` and change its body's first line to `result = run_suite(runner.AGENTCLINIC_PHASE_1)`. The reader at `:370` becomes `run_suite(runner.AGENTCLINIC_PHASE_1).pi_stdout`.

The `lambda *args: conditions` stubs for `_conditions` need no change —
they already absorb any positional arity.

- [ ] **Step 9: Run the whole suite**

Run: `uv run pytest -q`

Expected: all pass, with the same skip count as before this task (the
`SATYRN_LIVE` tests). If `_conditions` raises `FileNotFoundError` on
`examples/duration/spec.md`, Task 1 was not completed first.

- [ ] **Step 10: Verify no reference to the removed constants survives**

Run: `grep -rn "PHASE_1\|TASK_SPEC\|run_agentclinic_phase1" harness/ docs/setup.md README.md`

Expected: no output from `harness/`. Test modules define their own local
`PHASE_1` constants from `REPO_ROOT` — those are fine and stay. If
`docs/setup.md` or `README.md` names `run_agentclinic_phase1`, update it
to `run_suite(AGENTCLINIC_PHASE_1)`; those files are prose a contributor
follows, and a stale function name there is a broken instruction.

- [ ] **Step 11: Run the four gates**

```bash
uv run pytest && uv run ruff check . && uv run pyrefly check && uv run sphinx-build -W -b html docs docs/_build/html
```

Expected: all pass.

- [ ] **Step 12: Commit**

```bash
git add harness tests docs README.md
git commit -m "refactor(second-suite): dissolve the workload constants into a Suite"
```

---

### Task 3: Proving the two suites do not contaminate each other

The tests that make the design's central claim checkable, plus the live
end-to-end run of the new suite.

**Files:**
- Modify: `tests/test_runner.py`

**Interfaces:**
- Consumes: `Suite`, `AGENTCLINIC_PHASE_1`, `DURATION`, `run_suite`, `_conditions`, `run_batch(suite=...)` from Task 2. `RunConditions` is unchanged and has eight fields, in this order: `model`, `pi_command`, `pi_version`, `task_spec_sha256`, `harness_revision`, `run_timeout`, `grade_timeout`, `extension_digests`.
- Produces: nothing other tasks consume.

- [ ] **Step 1: Write the failing discrimination tests**

Add to `tests/test_runner.py`:

```python
def test_conditions_differ_between_the_two_suites(monkeypatch):
    """`task_spec_sha256` is the only field of RunConditions that
    distinguishes two suites -- everything else is shared, and
    `pi_command` normalizes the prompt away. If `_conditions` ever hashes
    a module-level constant again instead of the suite it was handed,
    this is what catches it."""
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda command, **kwargs: SimpleNamespace(stdout="stub\n"),
    )
    monkeypatch.setattr(runner, "_extension_digest", lambda path: "digest")

    agentclinic = runner._conditions(
        runner.AGENTCLINIC_PHASE_1, "model", ["pi", "prompt"], 600
    )
    duration = runner._conditions(runner.DURATION, "model", ["pi", "prompt"], 600)

    assert agentclinic.task_spec_sha256 != duration.task_spec_sha256
    assert agentclinic != duration
    # Non-vacuity: the two differ *only* there. Were another field to
    # start varying, this assertion would fail and the claim in the
    # docstring above would need rewriting rather than quietly rotting.
    assert dataclasses.replace(
        agentclinic, task_spec_sha256=duration.task_spec_sha256
    ) == duration


def test_run_batch_refuses_a_checkpoint_recorded_under_another_suite(
    tmp_path, monkeypatch
):
    """The failure this cycle exists to prevent: a duration batch resuming
    an AgentClinic checkpoint, accumulating runs graded against different
    contracts in one file that looks like data."""
    checkpoint = tmp_path / "runs.jsonl"
    agentclinic_conditions = RunConditions(
        "model", ("pi",), runner.EXPECTED_PI_VERSION, "agentclinic-sha",
        "rev", 600, 30, ("digest",),
    )
    duration_conditions = dataclasses.replace(
        agentclinic_conditions, task_spec_sha256="duration-sha"
    )
    append_checkpoint(
        checkpoint,
        RunResult("diff", _grade_result(), "", "", 0, conditions=agentclinic_conditions),
    )

    monkeypatch.setattr(runner, "_conditions", lambda *args: duration_conditions)
    monkeypatch.setattr(
        runner, "preflight_model", lambda model: pytest.fail("preflight called")
    )
    monkeypatch.setattr(
        runner, "run_suite", lambda suite, **kwargs: pytest.fail("run called")
    )

    with pytest.raises(ValueError, match="conditions"):
        runner.run_batch(checkpoint, suite=runner.DURATION, target=2, model="model")
```

Add `import dataclasses` to the module's imports if it is not already
there. `SimpleNamespace`, `pytest`, `append_checkpoint`, `RunConditions`,
`RunResult`, and `_grade_result` are already imported or defined in this
module.

- [ ] **Step 2: Run them to verify they pass**

Run: `uv run pytest tests/test_runner.py -k "differ_between or another_suite" -v`

Expected: 2 passed. These pass immediately against Task 2's code — they
are regression locks on a property Task 2 established, not drivers of new
behavior.

- [ ] **Step 3: Verify the first test is not vacuous**

Temporarily revert `_conditions` to hash a fixed path — in
`harness/runner.py`, change `suite.task_spec.read_bytes()` to
`AGENTCLINIC_PHASE_1.task_spec.read_bytes()`.

Run: `uv run pytest tests/test_runner.py -k "differ_between" -v`

Expected: FAIL on `agentclinic.task_spec_sha256 != duration.task_spec_sha256`.

Restore `suite.task_spec.read_bytes()` and re-run to confirm it passes
again. A test that cannot fail is this project's named recurring hazard;
this step is how the task earns the assertion.

- [ ] **Step 4: Add the live end-to-end test**

Add to `tests/test_runner.py`, beside the existing `SATYRN_LIVE` tests:

```python
@pytest.mark.skipif(
    os.environ.get("SATYRN_LIVE") != "1",
    reason="set SATYRN_LIVE=1 to require an actual Pi/model run",
)
def test_run_suite_produces_live_model_evidence_for_the_duration_suite():
    """The second suite end-to-end through a real Pi invocation: the
    seam's proof, as opposed to the offline floor tests' proof that the
    grader discriminates. No assertion on acceptance -- whether a 12B
    local model solves this on any given attempt is a measurement, and
    this cycle claims no number."""
    result = run_suite(runner.DURATION)

    assert result.pi_returncode == 0
    assert result.pi_stdout.strip()
    assert result.grade.tests_expected == 6
    assert result.conditions is not None
    assert (
        result.conditions.task_spec_sha256
        != runner._conditions(
            runner.AGENTCLINIC_PHASE_1, runner.DEFAULT_MODEL, ["pi", "x"], 600
        ).task_spec_sha256
    )
```

- [ ] **Step 5: Verify the model server, then run the live test**

First confirm the server returns real output — when it is down, `pi`
exits 0 with empty stderr and the harness records a fabricated result:

```bash
curl -s -m 10 http://127.0.0.1:8001/v1/models
```

That lists the models the server is actually serving; an empty or failed
response means it is not up. *(Corrected 2026-08-04: this step originally
said `/Users/pauleveritt/.omlx/bin/omlx diagnose`, which is not a valid
invocation — that subcommand requires a target argument, so it is not a
liveness check.)*

If it is not serving, start it with `/Users/pauleveritt/.omlx/bin/omlx start`
and re-check. Then:

```bash
SATYRN_LIVE=1 uv run pytest tests/test_runner.py -k "duration_suite" -v
```

Expected: 1 passed, in roughly one to ten minutes. Do not run this
concurrently with anything else touching the model server, and do not
abandon the process — a queued run consumes the single-threaded server.

If it fails on `result.grade.tests_expected == 6`, the acceptance file was
not found or `_test_count` miscounted; that is an engine failure, not a
model failure, and it must be fixed rather than retried.

- [ ] **Step 6: Run the four gates**

```bash
uv run pytest && uv run ruff check . && uv run pyrefly check && uv run sphinx-build -W -b html docs docs/_build/html
```

Expected: all pass, with the `SATYRN_LIVE` tests skipped.

- [ ] **Step 7: Commit**

```bash
git add tests/test_runner.py
git commit -m "test(second-suite): lock the seam against cross-suite contamination"
```

---

### Task 4: The record

The docs the cycle owes: the phase transition, the concept-budget
redefinition, the backlog entry for what was deliberately not fixed, and
the research record naming what `harness/` edits the second suite actually
required — the finding the cycle's modest bar exists to produce.

**Files:**
- Create: `docs/superpowers/research/2026-08-04-phase4-cycle1-what-the-second-suite-cost.md`
- Modify: `docs/superpowers/index.md` (Plans and Research toctrees)
- Modify: `docs/superpowers/specs/2026-08-04-phase4-cycle1-second-suite-design.md`
- Modify: `ROADMAP.md`

**Interfaces:**
- Consumes: the completed Tasks 1-3 and their commits, which the research record describes.
- Produces: nothing other tasks consume.

- [ ] **Step 1: Correct the spec's description of the broken fixture**

The spec says the broken variant "gets one row wrong: `"1h30m"` → `3600`,
stopping at the first unit." That is inaccurate — the single defect fails
*two* rows, `"1h30m"` and `"2h15m30s"`. Per this project's practice,
correct it in place rather than silently rewriting.

In `docs/superpowers/specs/2026-08-04-phase4-cycle1-second-suite-design.md`,
replace:

```
The broken variant gets one row
wrong: `"1h30m"` → `3600`, stopping at the first unit. Nothing else
differs.
```

with:

```
The broken variant has one *defect* — it stops at the first unit — which
fails the two multi-unit rows: `"1h30m"` → `3600` and `"2h15m30s"` →
`7200`. The four single-unit and unparseable rows still pass, so the
fixture proves the grader discriminates on behavior rather than rejecting
anything that merely looks different. *(Corrected 2026-08-04: this
paragraph previously said "one row wrong", which was wrong — one defect is
not one row.)*
```

- [ ] **Step 2: Add the plan and spec to the toctrees**

In `docs/superpowers/index.md`, add to the `Research` toctree, after its
last existing entry (`research/2026-08-03-phase3-cycle2-pi-gotchas`):

```
research/2026-08-04-phase4-cycle1-what-the-second-suite-cost
```

The spec and the plan were added to the `Specs` and `Plans` toctrees when
they were committed. Verify `specs/2026-08-04-phase4-cycle1-second-suite-design`
and `plans/2026-08-04-phase4-cycle1-second-suite` are present, and do not
duplicate them. Only the research entry is new.

- [ ] **Step 3: Write the research record**

Create
`docs/superpowers/research/2026-08-04-phase4-cycle1-what-the-second-suite-cost.md`.

Its job is the one deliverable this plan cannot fully specify in advance:
**what `harness/` edits the second suite actually required.** Write it
from the real diff, not from this plan's predictions.

```bash
git log --oneline main..HEAD
git diff --stat main..HEAD -- harness/
```

The document must contain, with exact file and line citations:

1. **Every `harness/` change the second suite forced**, one line each,
   each labeled *seam extraction* (a constant becoming a parameter) or
   *genuine gap* (something that was not general and had to be built). The
   design's bar was "the harness runs two suites"; this list is what that
   bar was chosen to produce.
2. **What was already general and needed nothing** — `prepare_workspace`,
   the grading plugin, the checkpoint format, `_pi_command`, the process
   group handling. Naming these is as much a finding as naming the gaps.
3. **What is still not general**, each with why it was left:
   - Seeding. `prepare_workspace(source_dir=...)` still has zero real
     callers; the generality claim covers the spec and grading seams only.
   - The grading subprocess's dependencies. `harness/grading.py:204` sets
     `PYTHONPATH` to the repo root, so an acceptance suite can only import
     what the harness's own venv provides. AgentClinic's imports
     `starlette` and `turbohtml`; the duration suite is stdlib-only, so
     this cycle did not force the question. `Suite` does not capture it.
   - Within-suite condition discrimination — see Step 5.
4. **The `_test_count` / parametrize trap**, with the reasoning for
   choosing a documented constraint over extending `_test_count`, and
   where the rule is recorded.
5. **What this cycle does not claim:** that a third suite is free. n=2
   shows a parameter is a parameter. It does not show a suite author never
   needs the engine.

- [ ] **Step 4: Update the ROADMAP's phase records**

In `ROADMAP.md`:

In the `## Now` section, change the Phase 3 paragraph's opening from
"**Phase 3 — Build the extension half.** In progress; see the cycles
below." to "**Phase 3 — Build the extension half. Complete.**" and keep
the rest of that paragraph and all its parenthetical corrections
unchanged — this project keeps superseded framings in place.

Add a new paragraph after it:

```markdown
**Phase 4 — Prove the engine generalizes beyond one workload.** In
progress. Three phases built the engine against a single workload, so the
parameters standing where hardcodes used to be had exactly one caller
apiece — which `BRIEF.md` names as the one thing that actually cost the
previous project. Cycle 1 adds a second suite and demonstrates the spec
and grading seams with a real second caller.
```

In the `## Phases` table, change Phase 3's Status cell from `in progress`
to `complete`, and add a row:

```markdown
| 4 | Prove the engine generalizes beyond one workload | A second, differently-shaped suite runs through the same harness, each grader having accepted a known-good and rejected a known-broken solution | in progress |
```

Add a `### Phase 4 feature cycles` section immediately before
`### Deferred candidates`, using the same three-column table the Phase 3
cycles section uses:

```markdown
### Phase 4 feature cycles

| Cycle | Summary | State |
|-------|---------|-------|
| 1 | A second eval suite — a stdlib-only duration parser under `examples/duration/`, so the spec and grading seams have a real second caller instead of a parameter with one caller and a workload-shaped default. Dissolves `PHASE_1`, `TASK_SPEC`, and `run_agentclinic_phase1` into a `Suite` descriptor; makes `grade()`'s `source_allowlist` required; makes `_conditions` hash the suite it was handed, which is load-bearing because `task_spec_sha256` is the only `RunConditions` field distinguishing two suites. Claims no number and runs no batch. [spec](docs/superpowers/specs/2026-08-04-phase4-cycle1-second-suite-design.md), [plan](docs/superpowers/plans/2026-08-04-phase4-cycle1-second-suite.md), [research](docs/superpowers/research/2026-08-04-phase4-cycle1-what-the-second-suite-cost.md) | Done |
```

- [ ] **Step 5: Update the concept budget**

In `ROADMAP.md`'s `## Concept budget` table, three entries change. Each is
a **redefinition of a term already spent**, not an addition, and the table
note below must say so.

Replace the `suite` row:

```markdown
| suite | one workload the harness can run: its prompt, its acceptance contract, and its source allowlist (`harness.runner.Suite`) | cycle 1; **redefined phase 4 cycle 1** — it previously meant only the acceptance test suite a solution is graded against, which is now called the *acceptance* (the parameter name in `grade()`) |
```

Replace the `task spec` row, which named one workload:

```markdown
| task spec | the document a model builds a solution from — AgentClinic's roadmap, the duration suite's `spec.md` | cycle 6; generalized phase 4 cycle 1 |
```

Replace the `allowlist` row, likewise:

```markdown
| allowlist | which model-written paths get copied into a fresh directory and graded at all; per-suite, and required rather than defaulted since phase 4 cycle 1 | cycle 5's close, implemented cycle 9 |
```

Add this paragraph immediately after the table, before the "**Retired, not
currently spent:**" paragraph:

```markdown
**Redefined, phase 4 cycle 1.** Three terms above were narrowed to the
first workload without anyone noticing: *suite* meant an acceptance file,
*task spec* meant AgentClinic's roadmap specifically, and *allowlist*
named `app.py` and `templates` in its own definition. A second workload
made all three read as wrong. A redefinition costs a contributor *more*
than a new term — they must unlearn something — so it is recorded here
rather than quietly edited. The count of terms is unchanged.
```

- [ ] **Step 6: Add the backlog entry**

Add to `ROADMAP.md`'s `## Backlog`, in the same voice as the entries
already there:

```markdown
- **`RunConditions` does not record the acceptance contract or the
  allowlist — a real gap, deliberately left open.** Phase 4 cycle 1 made
  `task_spec_sha256` the field that distinguishes two suites, and tests
  now lock that. Discrimination *within* a suite is a different matter:
  nothing records the acceptance file's *contents* or the
  `source_allowlist`, and `harness_revision` is `git rev-parse HEAD`
  (`harness/runner.py:153-155`), so an **uncommitted** edit to an
  acceptance file, or a changed allowlist, leaves conditions
  byte-identical and a batch resumes a checkpoint graded under a different
  contract. This is exactly the bug class `extension_digests` was added to
  close in phase 3 cycle 1 — the same mistake, one layer over.

  **Why it was not fixed there.** Every field added to `RunConditions`
  makes existing checkpoints non-matching, and the recorded evidence lives
  outside version control in `~/local-ai-pi-evidence/`. Cycle 1's claim
  did not need it, and paying for it would have cost the existing
  checkpoints' resumability.

  **The gate:** fix it when a second contributor's evidence has to be
  compared against ours, or the first time an acceptance file is edited
  mid-batch. The `("<pre-cycle1>",)` sentinel pattern (`runner.py:29-33`)
  is the precedent — old checkpoints become unresumable-but-readable, not
  lost.
```

- [ ] **Step 7: Run the four gates**

```bash
uv run pytest && uv run ruff check . && uv run pyrefly check && uv run sphinx-build -W -b html docs docs/_build/html
```

Expected: all pass. The strict Sphinx build is what catches a document
missing from a toctree, and a table row inserted at the wrong place is
what it will **not** catch — read `git diff ROADMAP.md` and confirm the
Phases table and the concept-budget table each remain contiguous. A
concept-budget note was once inserted between two rows of the Phase 2
cycles table and the strict build did not complain.

- [ ] **Step 8: Commit**

```bash
git add docs ROADMAP.md
git commit -m "docs(second-suite): close Phase 3, open Phase 4, record what it cost"
```

---

## Definition of done

- Both suites accept their known-good solution and reject their
  known-broken one, offline, with no model required.
- `harness/runner.py` contains no workload-specific constant; `PHASE_1`,
  `TASK_SPEC`, and `run_agentclinic_phase1` are gone.
- `grade()` requires `source_allowlist`; no workload-shaped default
  survives anywhere in `harness/`.
- `_conditions` hashes the suite it was handed, with a test that fails if
  it stops doing so, and `run_batch` refuses a cross-suite checkpoint.
- The `SATYRN_LIVE` duration run has passed at least once against a
  verified-alive model server.
- The research record names what `harness/` actually had to change,
  written from the diff.
- The four gates pass.
