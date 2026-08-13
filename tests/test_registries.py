"""The name registries: suites and improvements addressable by short name.

Phase 8 cycle 1. The registries are the mild step short of a manifest --
the `Improvement` docstring parks that cycle ("that is the cycle that adds
the manifest"). The critical constraint is laziness: `import
harness.runner` must not fail on a machine without Pi, so `IMPROVEMENTS`
holds the *factories*, never their results. The CLI resolves a name by
invoking the factory, exactly as callers invoke `tech_stack_only()` today.
"""

import subprocess
import sys
from pathlib import Path

import harness.runner as runner
from harness.runner import IMPROVEMENTS, SUITES


def test_suites_keys_are_the_documented_short_names():
    assert set(SUITES) == {"agentclinic-phase-1", "user-story", "duration"}


def test_improvements_keys_are_the_documented_short_names():
    assert set(IMPROVEMENTS) == {
        "tech-stack-only",
        "sdd-orchestrator",
        "sdd-orchestrator-guarded",
        "sdd-orchestrator-guarded-stack",
    }


def test_every_suite_resolves_to_files_that_exist():
    for key, suite in SUITES.items():
        assert suite.task_spec.is_file(), f"{key}: {suite.task_spec}"
        assert suite.acceptance.is_file(), f"{key}: {suite.acceptance}"
        assert suite.source_allowlist, f"{key}: empty allowlist"


def test_improvements_hold_factories_not_instances():
    for key, factory in IMPROVEMENTS.items():
        assert callable(factory), f"{key}: {factory!r} is not callable"
        assert not isinstance(factory, runner.Improvement)


def test_every_improvement_resolves_to_its_keyed_name(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "pi_package_root", lambda: tmp_path)
    for key, factory in IMPROVEMENTS.items():
        improvement = factory()
        assert isinstance(improvement, runner.Improvement)
        assert improvement.name == key


def test_import_never_resolves_pi():
    """The constraint the registry exists to serve: importing the harness
    must not fail on a machine without Pi, and resolving an improvement is
    the moment Pi is touched -- never before.

    Runs in a subprocess so the `importlib.reload` re-executes the module
    in a fresh interpreter: an in-process reload would re-define
    runner's classes under the other test modules that already imported
    them, breaking their equality comparisons.
    """
    code = "\n".join(
        [
            "import importlib",
            "import harness.runner as runner",
            "def broken():",
            "    raise AssertionError('pi_package_root must not run at import time')",
            "runner.pi_package_root = broken",
            "# If import-time code called pi_package_root, this reload raises.",
            "reloaded = importlib.reload(runner)",
            "reloaded.pi_package_root = broken",
            "assert reloaded.IMPROVEMENTS['sdd-orchestrator'] is reloaded.sdd_orchestrator",
            "try:",
            "    reloaded.sdd_orchestrator()",
            "except AssertionError:",
            "    pass",
            "else:",
            "    raise SystemExit('factory did not resolve Pi lazily')",
        ]
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    assert result.returncode == 0, result.stderr
