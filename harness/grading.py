import ast
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from harness.grading_plugin import DONE_MARKER, RESULTS_ENV_VAR

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


def _verdict(
    results_text: str, tests_expected: int, returncode: int, stdout: str, stderr: str
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
    )

    return GradeResult(
        accepted=accepted,
        tests_executed=tests_executed,
        tests_expected=tests_expected,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
        refused_config=(),
    )


def grade(workspace: Path, suite: Path, timeout: int = 30) -> GradeResult:
    """Copy suite into workspace, run pytest there with the grading
    plugin loaded, and return the verdict read from the results file the
    plugin's hooks wrote. Refuses before doing either, when the workspace
    carries model-written config."""
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

    shutil.copy2(suite, workspace / suite.name)

    results_fd, results_path = tempfile.mkstemp(
        prefix="satyrn-grade-results-", suffix=".txt"
    )
    os.close(results_fd)
    results_path = Path(results_path)
    try:
        repo_root = Path(__file__).resolve().parents[1]
        env = dict(os.environ)
        env[RESULTS_ENV_VAR] = str(results_path)
        env["PYTHONPATH"] = str(repo_root)

        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "harness.grading_plugin"],
            cwd=workspace,
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


def _test_count(suite: Path) -> int:
    tree = ast.parse(suite.read_text(), filename=str(suite))
    return sum(
        isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        for node in tree.body
    )


def _refused_config(workspace: Path) -> tuple[str, ...]:
    """Model-written config present in the workspace, as sorted
    workspace-relative paths.

    Root-level for all names in _REFUSED_CONFIG, plus a recursive sweep for
    conftest.py only: a nested conftest.py affects collection in its own
    subtree, while a nested pytest.ini/.pytest.ini or sitecustomize.py is
    inert -- pytest reads ini files at the rootdir, and sitecustomize is
    imported from sys.path.

    Two of these currently execute code, not just configure the run:
    conftest.py at collection time, and any ini-style file (pytest.ini,
    .pytest.ini, pyproject.toml, tox.ini, setup.cfg) whose addopts loads a
    plugin -- confirmed directly: a workspace-root .pytest.ini with
    `addopts = -p evil` runs evil.py's pytest_configure() before
    collection, under this module's invocation of pytest (cwd=workspace,
    python -m pytest). sitecustomize.py is the one entry refused purely as
    defense-in-depth: it does not execute under the current invocation
    shape (site processes it before -m puts the workspace directory on
    sys.path), only against how that invocation might change (e.g. if the
    workspace directory ever ends up on PYTHONPATH or sys.path earlier).

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
