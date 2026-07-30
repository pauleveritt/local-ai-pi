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
    returncode: int
    stdout: str
    stderr: str


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
    )


def grade(workspace: Path, suite: Path, timeout: int = 30) -> GradeResult:
    """Copy suite into workspace, run pytest there with the grading
    plugin loaded, and return the verdict read from the results file the
    plugin's hooks wrote."""
    shutil.copy2(suite, workspace / suite.name)
    tests_expected = _test_count(suite)

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

    Root-level for all six names, plus a recursive sweep for conftest.py
    only: a nested conftest.py affects collection in its own subtree,
    while a nested pytest.ini or sitecustomize.py is inert -- pytest reads
    ini files at the rootdir, and sitecustomize is imported from sys.path.
    """
    found = {name for name in _REFUSED_CONFIG if (workspace / name).is_file()}
    found.update(
        str(path.relative_to(workspace))
        for path in workspace.rglob("conftest.py")
        if path.is_file()
    )
    return tuple(sorted(found))
