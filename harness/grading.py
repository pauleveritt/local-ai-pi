import ast
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from harness.grading_plugin import DONE_MARKER, RESULTS_ENV_VAR
from harness.processes import run_process

_REFUSED_CONFIG = (
    "pyproject.toml",
    "pytest.ini",
    ".pytest.ini",
    "tox.ini",
    "setup.cfg",
    "conftest.py",
    "sitecustomize.py",
)


@dataclass(frozen=True)
class GradeResult:
    accepted: bool
    tests_executed: int
    tests_expected: int
    returncode: int | None
    stdout: str
    stderr: str
    refused_config: tuple[str, ...]
    timed_out: bool = False


def _verdict(
    results_text: str,
    tests_expected: int,
    returncode: int | None,
    stdout: str,
    stderr: str,
    timed_out: bool = False,
) -> GradeResult:
    lines = results_text.splitlines()
    done = DONE_MARKER in lines

    outcomes: dict[str, str] = {}
    for line in lines:
        if "\t" not in line:
            continue
        nodeid, outcome = line.split("\t", 1)
        outcomes[nodeid] = outcome
    tests_executed = len(outcomes)

    accepted = (
        done
        and tests_executed == tests_expected
        and tests_expected > 0
        and all(outcome == "passed" for outcome in outcomes.values())
        and returncode == 0
        and not timed_out
    )

    return GradeResult(
        accepted=accepted,
        tests_executed=tests_executed,
        tests_expected=tests_expected,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        refused_config=(),
        timed_out=timed_out,
    )


def grade(
    workspace: Path,
    suite: Path,
    timeout: int | float = 30,
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
        env = _grading_environment(repo_root, grading_dir, results_path)

        proc = run_process(
            [
                sys.executable, "-m", "pytest", "-q",
                "-p", "harness.grading_plugin",
                # Collect the acceptance suite and nothing else. Cycle 9's
                # allowlist copy already keeps model-written test files out
                # of the grading directory, so this is now a second,
                # independent guard rather than the only one -- it is what
                # cycle 6 added when a model following the task spec (which
                # tells it to write tests/test_app.py) inflated
                # tests_executed past tests_expected and a correct solution
                # was rejected.
                suite.name,
            ],
            timeout=timeout,
            cwd=grading_dir,
            env=env,
        )
        results_text = results_path.read_text() if results_path.is_file() else ""
        return _verdict(
            results_text,
            tests_expected=tests_expected,
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            timed_out=proc.timed_out,
        )
    finally:
        results_path.unlink(missing_ok=True)
        shutil.rmtree(grading_dir, ignore_errors=True)


def _test_count(suite: Path) -> int:
    """How many tests the suite declares, counted from its source.

    Counts module-level `def test_*` and `async def test_*`. Class-grouped
    tests are deliberately unsupported: no suite uses them, and counting
    them would mean deciding what pytest would collect rather than reading
    what the file declares.

    Undercounting here is not a cosmetic bug. `tests_expected` feeds the
    `tests_executed == tests_expected` condition, so a miscount rejects a
    *correct* solution -- the engine-looks-like-a-model-failure confusion
    Phase 1 exists to prevent. Async was missed until a review caught it,
    and would have bitten the first suite written against an async client.
    """
    tree = ast.parse(suite.read_text(), filename=str(suite))
    return sum(
        isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and node.name.startswith("test_")
        for node in tree.body
    )


def _grading_environment(
    repo_root: Path, grading_dir: Path, results_path: Path
) -> dict[str, str]:
    """Return the complete environment for the grading subprocess.

    The verdict must not depend on a caller's pytest switches, Python path,
    user site, or user configuration. The subprocess receives only the values
    the harness deliberately provides.
    """
    home = grading_dir / ".home"
    config_home = home / ".config"
    cache_home = home / ".cache"
    for path in home, config_home, cache_home:
        path.mkdir(parents=True, exist_ok=True)

    return {
        "PATH": os.defpath,
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(config_home),
        "XDG_CACHE_HOME": str(cache_home),
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "PYTHONPATH": str(repo_root),
        "PYTHONNOUSERSITE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        RESULTS_ENV_VAR: str(results_path),
    }


def _refused_config(workspace: Path) -> tuple[str, ...]:
    """Model-written config present in the workspace, as sorted
    workspace-relative paths.

    Root-level for all names in _REFUSED_CONFIG, plus a recursive sweep for
    conftest.py only: a nested conftest.py affects collection in its own
    subtree, while a nested pytest.ini/.pytest.ini or sitecustomize.py is
    inert -- pytest reads ini files at the rootdir, and sitecustomize is
    imported from sys.path.

    **Since cycle 9, none of these names can reach the graded run at all.**
    pytest runs in an allowlist-copied grading directory, and no refused
    name is on the allowlist, so nothing here is load-bearing against
    execution any more. Refusal is retained for two reasons: it is
    defense-in-depth if the allowlist ever widens, and `refused_config` in
    the verdict is useful evidence of what the model *attempted*,
    independent of whether the attempt could have worked.

    Historical, and the reason the list looks like it does -- when grading
    ran with `cwd=workspace` (pre-cycle-9), two of these executed code
    rather than merely configuring the run: conftest.py at collection
    time, and any ini-style file (pytest.ini, .pytest.ini, pyproject.toml,
    tox.ini, setup.cfg) whose addopts loads a plugin. That was confirmed
    directly at the time: a workspace-root .pytest.ini with
    `addopts = -p evil` ran evil.py's pytest_configure() before collection.
    sitecustomize.py never executed even then; it was refused purely as
    defense-in-depth against the invocation shape changing.

    The five ini-style names above (pytest.ini, .pytest.ini, pyproject.toml,
    tox.ini, setup.cfg) should track pytest's own config-discovery order
    rather than being independently re-derived by hand -- see
    _pytest/config/findpaths.py's locate_config() (checked against pytest
    8.3.4), whose config_names is exactly that five-name set. A
    hand-enumerated list is how .pytest.ini was missed here. conftest.py
    and sitecustomize.py are separate additions with their own rationale
    above -- they are not part of pytest's own config_names, and syncing
    this constant against that list must not drop them.
    """
    found = {name for name in _REFUSED_CONFIG if (workspace / name).is_file()}
    # rglob's `**` defaults to recurse_symlinks=False since Python 3.13, so
    # a conftest.py reachable only via a symlinked directory is invisible
    # here. Safe today only because callers are expected to pass a
    # prepare_workspace-provisioned directory: shutil.copytree's default
    # symlinks=False resolves symlinks into real files during the copy, so
    # such a workspace cannot contain one. Not safe for an arbitrary Path.
    found.update(
        str(path.relative_to(workspace))
        for path in workspace.rglob("conftest.py")
        if path.is_file()
    )
    return tuple(sorted(found))
