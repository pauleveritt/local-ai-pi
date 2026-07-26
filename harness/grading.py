"""Isolated, harness-owned acceptance grading."""

import ast
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from harness.grading_plugin import DONE_SENTINEL, RESULTS_ENV_VAR

_SOURCE_FILES = ("app.py", "models.py")
_REFUSED_CONFIGS = (
    "pyproject.toml", "pytest.ini", "tox.ini", "setup.cfg", "conftest.py",
    "sitecustomize.py",
)


@dataclass(frozen=True)
class GradeResult:
    passed: bool
    stdout: str
    stderr: str
    tests_executed: int
    tests_expected: int
    refused_config_files: list[str]


def grade_acceptance(workspace: Path, suite: Path, timeout: int) -> GradeResult:
    """Grade allowlisted model source in a directory the model never controls."""
    expected = _test_count(suite)
    refused = _refused_configs(workspace)
    grader = Path(tempfile.mkdtemp(prefix="pi-eval-grade-"))
    results_fd, results_path = tempfile.mkstemp(prefix="pi-eval-grade-results-", suffix=".txt")
    os.close(results_fd)
    results_path = Path(results_path)
    try:
        for name in _SOURCE_FILES:
            source = workspace / name
            if source.is_file():
                shutil.copy2(source, grader / name)
        templates = workspace / "templates"
        if templates.is_dir():
            shutil.copytree(templates, grader / "templates")

        (grader / "tests").mkdir()
        shutil.copy2(suite, grader / "tests" / "test_acceptance.py")
        (grader / "pyproject.toml").write_text(
            """[project]\nname = \"pi-eval-grader\"\nversion = \"0.0.0\"\nrequires-python = \">=3.14,<3.15\"\ndependencies = [\n  \"fastapi[standard]==0.115.10\",\n  \"pytest==8.3.4\",\n  \"turbohtml==1.5.0\",\n]\n"""
        )
        config = grader / "pytest.ini"
        config.write_text("[pytest]\npythonpath = .\n")

        # Harness-owned plugin -- see harness/grading_plugin.py for why this
        # replaced trusting captured stdout/stderr text (Rule 8, Fable,
        # 2026-07-26). Copied in, not imported from the repo, so the grader
        # directory stays a self-contained allowlist like everything else
        # copied here.
        shutil.copy2(
            Path(__file__).resolve().parent / "grading_plugin.py",
            grader / "_pi_grading_plugin.py",
        )

        env = dict(os.environ)
        env[RESULTS_ENV_VAR] = str(results_path)
        # -p _pi_grading_plugin is resolved before pytest applies the ini
        # file's `pythonpath = .` setting, so that alone won't make the
        # plugin importable -- PYTHONPATH is read by the interpreter itself
        # at startup, ahead of pytest's own plugin-loading (empirically
        # verified: -p resolution failed with pythonpath = . alone).
        env["PYTHONPATH"] = str(grader)
        proc = subprocess.run(
            ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider",
             "-p", "_pi_grading_plugin", "-c", str(config),
             "--rootdir", str(grader), "tests/test_acceptance.py"],
            cwd=grader, capture_output=True, text=True, timeout=timeout, env=env,
        )
        executed, done = _read_results(results_path)
        return GradeResult(
            passed=proc.returncode == 0 and done and executed == expected and executed > 0,
            stdout=proc.stdout,
            stderr=proc.stderr,
            tests_executed=executed,
            tests_expected=expected,
            refused_config_files=refused,
        )
    except subprocess.TimeoutExpired:
        return GradeResult(False, "", "", 0, expected, refused)
    finally:
        shutil.rmtree(grader, ignore_errors=True)
        results_path.unlink(missing_ok=True)


def _test_count(suite: Path) -> int:
    tree = ast.parse(suite.read_text(), filename=str(suite))
    return sum(isinstance(node, ast.FunctionDef) and node.name.startswith("test_") for node in tree.body)


def _read_results(path: Path) -> tuple[int, bool]:
    """Read the trusted, hook-written results file -- never pytest's own
    captured stdout/stderr, which model-imported code shares a process with
    and can write into directly (see harness/grading_plugin.py)."""
    if not path.is_file():
        return 0, False
    lines = path.read_text(errors="replace").splitlines()
    done = DONE_SENTINEL in lines
    executed = sum(1 for line in lines if "\t" in line)
    return executed, done


def _refused_configs(workspace: Path) -> list[str]:
    refused = [name for name in _REFUSED_CONFIGS if (workspace / name).exists()]
    refused.extend(str(path.relative_to(workspace)) for path in workspace.rglob("conftest.py"))
    return sorted(set(refused))
