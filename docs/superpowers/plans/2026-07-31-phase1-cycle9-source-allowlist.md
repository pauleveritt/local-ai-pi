# Source Allowlist Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `grade()` run pytest against a fresh directory containing
only allowlisted paths copied from the workspace, so a model-written
module can never shadow `harness.grading_plugin` (or anything else) on
`sys.path`.

**Architecture:** One change to `harness/grading.py::grade()`: instead of
copying the suite into `workspace` and running pytest with
`cwd=workspace`, build a temporary "grading directory" containing only
`source_allowlist`-named paths copied from `workspace` plus the suite, and
run pytest there instead. `GradeResult`'s shape is unchanged.

**Tech Stack:** Python 3.14 stdlib (`shutil`, `tempfile`, `subprocess`,
`pathlib`). pytest 8.3.4.

## Global Constraints

- `grade(workspace: Path, suite: Path, timeout: int = 30,
  source_allowlist: tuple[str, ...] = ("app.py", "templates")) ->
  GradeResult` is the exact new signature — `source_allowlist` is a seam
  with a Phase-1-specific default, not a hardcode.
- `_refused_config(workspace)` still runs first, against the *original*
  workspace, unchanged. It stays for its diagnostic value in
  `GradeResult.refused_config`, even though none of its filenames can
  reach the grading directory once this cycle ships.
- A missing allowlisted path (e.g. `broken`'s missing `templates/`) is
  skipped, not an error.
- The original `workspace` is never mutated by `grade()` after this
  change — it's read from, not written to. (Today's code writes the
  suite into `workspace`; that side effect goes away.)

---

## File Structure

```
harness/
  grading.py             # MODIFY: grade() builds an allowlist-copied
                          #   grading directory instead of using workspace
tests/
  test_grading.py        # MODIFY: add the shadow-attack regression test
  test_config_refusal.py # MODIFY: fix a test made vacuous by this change
```

---

### Task 1: Grade against an allowlist-copied directory

**Files:**
- Modify: `harness/grading.py`
- Modify: `tests/test_grading.py`
- Modify: `tests/test_config_refusal.py`

**Interfaces:**
- Consumes: `harness.workspace.prepare_workspace` (unchanged); the
  `PHASE_1` / `reference` / `broken` fixtures (unchanged).
- Produces: `harness.grading.grade(workspace: Path, suite: Path, timeout:
  int = 30, source_allowlist: tuple[str, ...] = ("app.py", "templates"))
  -> GradeResult` — same `GradeResult` shape as before, new fourth
  parameter.

- [ ] **Step 1: Write the failing test — the shadow attack**

This is the cycle's real proof, verified directly against the current
code before writing this plan: a workspace-root `harness/grading_plugin.py`
that just raises on import gets imported by pytest today (confirmed via a
manual reproduction — `SHADOW_MARKER` appeared in `result.stderr` and
`tests_executed` was `0`, meaning pytest crashed during collection before
running anything). After this task, the model's `harness/` package is
never copied into the grading directory, so pytest resolves the real
plugin and grades `broken` on its actual, unrelated failure.

Add to `tests/test_grading.py` (after the existing tests):

```python
def test_grade_is_not_shadowed_by_a_workspace_root_harness_package(tmp_path):
    """Before this fix, `cwd=workspace` put a model-written harness/
    package ahead of the real one on sys.path, so `-p
    harness.grading_plugin` could import the model's copy instead of the
    real plugin. Verified directly: a rogue harness/grading_plugin.py
    that raises on import crashes collection (tests_executed == 0) and
    its exception text reaches stderr, under today's implementation."""
    source = tmp_path / "shadow-attempt"
    shutil.copytree(PHASE_1 / "broken", source)
    rogue_pkg = source / "harness"
    rogue_pkg.mkdir()
    (rogue_pkg / "__init__.py").write_text("")
    (rogue_pkg / "grading_plugin.py").write_text(
        "raise RuntimeError('SHADOW_MARKER')\n"
    )

    with prepare_workspace(source) as workspace:
        result = grade(workspace, PHASE_1 / "acceptance" / "test_acceptance.py")

    assert "SHADOW_MARKER" not in result.stderr
    assert result.tests_executed == 4
    assert result.accepted is False
```

`shutil` is already imported in `tests/test_grading.py` (used by the
existing model-written-tests test).

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_grading.py::test_grade_is_not_shadowed_by_a_workspace_root_harness_package -v`
Expected: FAIL — `assert "SHADOW_MARKER" not in result.stderr` fails,
because `SHADOW_MARKER` IS in `result.stderr` under today's
implementation.

- [ ] **Step 3: Rewrite `grade()` to build and use a grading directory**

Replace `harness/grading.py`'s `grade` function (lines 67-127) with:

```python
def grade(
    workspace: Path,
    suite: Path,
    timeout: int = 30,
    source_allowlist: tuple[str, ...] = ("app.py", "templates"),
) -> GradeResult:
    """Copy source_allowlist paths (and the suite) from workspace into a
    fresh grading directory, run pytest there with the grading plugin
    loaded, and return the verdict read from the results file the
    plugin's hooks wrote. Refuses before doing any of that, when the
    workspace carries model-written config.

    Grading a fresh, allowlist-copied directory instead of workspace
    itself means a model-written module can never shadow anything on
    sys.path -- including harness.grading_plugin -- since only
    allowlisted paths are ever present for pytest's cwd to see.
    """
    tests_expected = _test_count(suite)
    refused = _refused_config(workspace)
    if refused:
        return GradeResult(
            accepted=False,
            tests_executed=0,
            tests_expected=tests_expected,
            returncode=None,
            stdout="",
            stderr="",
            refused_config=refused,
        )

    grading_dir = Path(tempfile.mkdtemp(prefix="satyrn-grading-"))
    results_fd, results_path = tempfile.mkstemp(
        prefix="satyrn-grade-results-", suffix=".txt"
    )
    os.close(results_fd)
    results_path = Path(results_path)
    try:
        for name in source_allowlist:
            source_path = workspace / name
            if not source_path.exists():
                continue
            dest_path = grading_dir / name
            if source_path.is_dir():
                shutil.copytree(source_path, dest_path)
            else:
                shutil.copy2(source_path, dest_path)

        shutil.copy2(suite, grading_dir / suite.name)

        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env[RESULTS_ENV_VAR] = str(results_path)
        env["PYTHONPATH"] = str(repo_root)

        proc = subprocess.run(
            [
                sys.executable, "-m", "pytest", "-q",
                "-p", "harness.grading_plugin",
                # Collect the acceptance suite and nothing else. See
                # module-level notes: the allowlist copy already keeps
                # model-written test files out of the grading directory,
                # but this stays as a second, independent guard.
                suite.name,
            ],
            cwd=grading_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        results_text = results_path.read_text() if results_path.is_file() else ""
        return _verdict(
            results_text,
            tests_expected=tests_expected,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
        )
    finally:
        results_path.unlink(missing_ok=True)
        shutil.rmtree(grading_dir, ignore_errors=True)
```

This is a straight replacement — same function name, same decorator-free
signature style, three new lines of parameters/behavior. No other
function in `harness/grading.py` changes.

- [ ] **Step 4: Run the new test to verify it passes**

Run: `uv run pytest tests/test_grading.py::test_grade_is_not_shadowed_by_a_workspace_root_harness_package -v`
Expected: PASS

- [ ] **Step 5: Fix the test this change makes vacuous**

`tests/test_config_refusal.py` has a test,
`test_grade_refuses_before_copying_the_suite_into_the_workspace`, that
asserts `not (workspace / SUITE.name).exists()` after calling `grade()`.
Before this task, `grade()` copied the suite into `workspace` on the
non-refused path, so this assertion meaningfully distinguished "refused"
from "not refused." After this task, `grade()` never copies the suite
into `workspace` under *any* outcome — it copies into the grading
directory instead — so this assertion would now pass unconditionally,
regardless of whether refusal worked. That's a vacuous test: remove it.
The claim it existed to prove — "refusal precedes every side effect, not
just the subprocess" — remains proven by the sibling test immediately
above it, `test_grade_refuses_a_workspace_carrying_config_without_running_pytest`,
whose `returncode is None` assertion is explicitly documented as "the
load-bearing assertion: None proves no process ran."

Delete this test from `tests/test_config_refusal.py`:

```python
def test_grade_refuses_before_copying_the_suite_into_the_workspace(tmp_path):
    """Refusal precedes every side effect, not just the subprocess."""
    source = _attack_with_collect_only(tmp_path)
    with prepare_workspace(source) as workspace:
        grade(workspace, SUITE)

        assert not (workspace / SUITE.name).exists()
```

- [ ] **Step 6: Run the whole suite to confirm no regressions**

Run: `uv run pytest -q`
Expected: all tests pass. Count: 38 existing tests, minus the one removed
in Step 5, plus the one added in Step 1 — net 38 (unchanged count),
all passing. (`test_runner.py`'s live-model test will run for real if
`pi` and the `omlx` server are available on this machine, or skip
cleanly otherwise — either is correct, per cycle 8's own plan.)

- [ ] **Step 7: Commit**

```bash
git add harness/grading.py tests/test_grading.py tests/test_config_refusal.py
git commit -m "feat(grading): grade against an allowlist-copied directory, not the workspace itself"
```

---

## Plan Self-Review Notes

- **Spec coverage:** new `source_allowlist` parameter and default —
  Task 1 Step 3. Missing-path-is-skipped behavior — Task 1 Step 3 (the
  `if not source_path.exists(): continue` line), and implicitly proven
  by the unchanged `broken`-fixture tests still passing in Step 6 (no
  `templates/` there, no error). `_refused_config` staying first, against
  the original workspace, for diagnostic value — Task 1 Step 3
  (unchanged placement and behavior). The shadow-attack proof — Task 1
  Steps 1-4, verified directly against the current implementation before
  this plan was written, not asserted speculatively. The now-vacuous
  refusal test — Task 1 Step 5.
- **Type consistency:** `grade`'s signature matches the spec's Interface
  section exactly (`source_allowlist: tuple[str, ...] = ("app.py",
  "templates")`, `GradeResult` unchanged). `GradeResult` field names used
  in the new test (`stderr`, `tests_executed`, `accepted`) match the
  existing dataclass.
- **No placeholders:** every step shows complete, runnable code and an
  exact command with an expected result. The removed test is shown in
  full so its deletion is unambiguous.
