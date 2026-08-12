"""Tests for the grading engine, in three sections:

1. `grading_plugin`'s hooks -- unit tests, no pytest subprocess.
2. `_verdict` -- unit tests of the pure verdict function.
3. `grade()` -- integration tests against the real fixtures.
"""

import shutil
from pathlib import Path
from types import SimpleNamespace

from harness.grading import _grading_environment, _test_count, _verdict, grade
from harness.grading_plugin import (
    DONE_MARKER,
    RESULTS_ENV_VAR,
    pytest_runtest_logreport,
    pytest_sessionfinish,
)
from harness.runner import AGENTCLINIC_PHASE_1 as AGENTCLINIC_SUITE
from harness.workspace import prepare_workspace

REPO_ROOT = Path(__file__).resolve().parents[1]
PHASE_1 = REPO_ROOT / "examples" / "agentclinic" / "phase-1"
# ACCEPTANCE and ALLOWLIST are consumed from harness.runner.AGENTCLINIC_PHASE_1,
# the suite a real run actually uses, rather than restated here -- so changing
# the suite's allowlist can never leave these floor tests certifying a
# configuration no run is graded under. PHASE_1 above stays a local path: only
# the fixtures' reference/broken directories are addressed through it, and
# Suite carries neither.
ACCEPTANCE = AGENTCLINIC_SUITE.acceptance
ALLOWLIST = AGENTCLINIC_SUITE.source_allowlist


# ---------------------------------------------------------------------
# 1. grading_plugin hooks
# ---------------------------------------------------------------------


def test_plugin_appends_outcome_line_on_call_phase(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    report = SimpleNamespace(
        when="call", outcome="passed", nodeid="test_call.py::test_alpha"
    )
    pytest_runtest_logreport(report)

    assert results.read_text() == "test_call.py::test_alpha\tpassed\n"


def test_plugin_records_a_failed_call_phase(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    report = SimpleNamespace(
        when="call", outcome="failed", nodeid="test_call.py::test_beta"
    )
    pytest_runtest_logreport(report)

    assert results.read_text() == "test_call.py::test_beta\tfailed\n"


def test_plugin_ignores_successful_setup_and_teardown(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    setup_report = SimpleNamespace(
        when="setup", outcome="passed", nodeid="test_setup_ok.py::test_gamma"
    )
    teardown_report = SimpleNamespace(
        when="teardown", outcome="passed", nodeid="test_setup_ok.py::test_gamma"
    )
    pytest_runtest_logreport(setup_report)
    pytest_runtest_logreport(teardown_report)

    assert not results.exists()


def test_plugin_records_a_setup_failure(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    report = SimpleNamespace(
        when="setup", outcome="failed", nodeid="test_setup_fail.py::test_delta"
    )
    pytest_runtest_logreport(report)

    assert results.read_text() == "test_setup_fail.py::test_delta\tfailed\n"


def test_plugin_records_a_teardown_failure_after_a_passed_call(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    call_report = SimpleNamespace(
        when="call", outcome="passed", nodeid="test_teardown.py::test_epsilon"
    )
    teardown_report = SimpleNamespace(
        when="teardown", outcome="failed", nodeid="test_teardown.py::test_epsilon"
    )
    pytest_runtest_logreport(call_report)
    pytest_runtest_logreport(teardown_report)

    assert results.read_text() == (
        "test_teardown.py::test_epsilon\tpassed\n"
        "test_teardown.py::test_epsilon\tfailed\n"
    )


def test_plugin_appends_done_marker_on_session_finish(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    pytest_sessionfinish(session=None, exitstatus=0)

    assert results.read_text() == f"{DONE_MARKER}\n"


# ---------------------------------------------------------------------
# 2. _verdict
# ---------------------------------------------------------------------


def test_verdict_accepts_when_all_conditions_hold():
    results_text = (
        "test_acceptance.py::test_a\tpassed\n"
        "test_acceptance.py::test_b\tpassed\n"
        "test_acceptance.py::test_c\tpassed\n"
        "test_acceptance.py::test_d\tpassed\n"
        "__DONE__\n"
    )

    result = _verdict(
        results_text, tests_expected=4, returncode=0, stdout="", stderr=""
    )

    assert result.accepted is True
    assert result.tests_executed == 4
    assert result.tests_expected == 4


def test_verdict_rejects_when_done_marker_missing():
    results_text = (
        "test_acceptance.py::test_a\tpassed\n"
        "test_acceptance.py::test_b\tpassed\n"
        "test_acceptance.py::test_c\tpassed\n"
        "test_acceptance.py::test_d\tpassed\n"
    )

    result = _verdict(
        results_text, tests_expected=4, returncode=0, stdout="", stderr=""
    )

    assert result.accepted is False


def test_verdict_rejects_a_partial_run():
    results_text = (
        "test_acceptance.py::test_a\tpassed\n"
        "test_acceptance.py::test_b\tpassed\n"
        "__DONE__\n"
    )

    result = _verdict(
        results_text, tests_expected=4, returncode=0, stdout="", stderr=""
    )

    assert result.accepted is False
    assert result.tests_executed == 2
    assert result.tests_expected == 4


def test_verdict_rejects_when_an_outcome_failed():
    results_text = (
        "test_acceptance.py::test_a\tpassed\n"
        "test_acceptance.py::test_b\tfailed\n"
        "test_acceptance.py::test_c\tpassed\n"
        "test_acceptance.py::test_d\tpassed\n"
        "__DONE__\n"
    )

    result = _verdict(
        results_text, tests_expected=4, returncode=0, stdout="", stderr=""
    )

    assert result.accepted is False


def test_verdict_rejects_on_nonzero_returncode_even_if_everything_else_passed():
    results_text = (
        "test_acceptance.py::test_a\tpassed\n"
        "test_acceptance.py::test_b\tpassed\n"
        "test_acceptance.py::test_c\tpassed\n"
        "test_acceptance.py::test_d\tpassed\n"
        "__DONE__\n"
    )

    result = _verdict(
        results_text, tests_expected=4, returncode=1, stdout="", stderr=""
    )

    assert result.accepted is False


def test_test_count_includes_module_level_async_tests(tmp_path):
    acceptance = tmp_path / "test_async_suite.py"
    acceptance.write_text(
        "def test_sync():\n"
        "    pass\n"
        "\n"
        "async def test_async():\n"
        "    pass\n"
        "\n"
        "def helper():\n"
        "    pass\n"
    )

    assert _test_count(acceptance) == 2


def test_grading_environment_excludes_ambient_pytest_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")
    monkeypatch.setenv("PYTEST_PLUGINS", "ambient_plugin")
    env = _grading_environment(
        tmp_path / "repo", tmp_path / "grading", tmp_path / "results"
    )

    assert env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] == "1"
    assert env["PYTHONNOUSERSITE"] == "1"
    assert "PYTEST_ADDOPTS" not in env
    assert "PYTEST_PLUGINS" not in env
    assert env["PYTHONPATH"] == str(tmp_path / "repo")


# ---------------------------------------------------------------------
# 3. grade() against the real fixtures
# ---------------------------------------------------------------------


def _shadow_attack_source(tmp_path):
    """The broken solution plus a rogue `harness.grading_plugin` that
    forges a passing results file and exits 0.

    Shared by the shadowing test and its non-vacuity control so both
    provably run the same payload."""
    source = tmp_path / "shadow-attempt"
    shutil.copytree(PHASE_1 / "broken", source)
    rogue_pkg = source / "harness"
    rogue_pkg.mkdir()
    (rogue_pkg / "__init__.py").write_text("")
    (rogue_pkg / "grading_plugin.py").write_text(
        "import os\n"
        "\n"
        "RESULTS_ENV_VAR = 'SATYRN_GRADE_RESULTS_PATH'\n"
        "DONE_MARKER = '__DONE__'\n"
        "\n"
        "\n"
        "def pytest_sessionfinish(session, exitstatus):\n"
        "    with open(os.environ[RESULTS_ENV_VAR], 'a') as f:\n"
        "        for name in (\n"
        "            'test_home_returns_200',\n"
        "            'test_home_shows_the_tagline_verbatim',\n"
        "            'test_home_extends_the_shared_layout',\n"
        "            'test_home_declares_html5_and_language',\n"
        "        ):\n"
        "            f.write(f'test_acceptance.py::{name}\\tpassed\\n')\n"
        "        f.write(DONE_MARKER + '\\n')\n"
        "        f.flush()\n"
        "        os.fsync(f.fileno())\n"
        "    os._exit(0)\n"
    )
    return source


def test_grade_accepts_the_reference_solution():
    with prepare_workspace(PHASE_1 / "reference") as workspace:
        result = grade(workspace, ACCEPTANCE, source_allowlist=ALLOWLIST)

    assert result.accepted is True
    assert result.tests_executed == result.tests_expected == 4


def test_grade_ignores_ambient_collect_only_option(monkeypatch):
    monkeypatch.setenv("PYTEST_ADDOPTS", "--collect-only")

    with prepare_workspace(PHASE_1 / "reference") as workspace:
        result = grade(workspace, ACCEPTANCE, source_allowlist=ALLOWLIST)

    assert result.accepted is True
    assert result.tests_executed == result.tests_expected == 4


def test_grade_returns_a_timed_out_rejection(tmp_path):
    acceptance = tmp_path / "test_timeout.py"
    acceptance.write_text("import time\n\n\ndef test_blocks():\n    time.sleep(30)\n")

    with prepare_workspace(PHASE_1 / "reference") as workspace:
        result = grade(workspace, acceptance, timeout=0.1, source_allowlist=ALLOWLIST)

    assert result.accepted is False
    assert result.timed_out is True
    assert result.returncode != 0


def test_grade_rejects_the_broken_solution():
    with prepare_workspace(PHASE_1 / "broken") as workspace:
        result = grade(workspace, ACCEPTANCE, source_allowlist=ALLOWLIST)

    assert result.accepted is False
    # Pins the contrast tests/test_subversion.py cites: unattacked, this
    # solution exits nonzero, so a naive exit-code grader rejects it too.
    # Attacked, it exits 0 -- which is what those attacks buy.
    assert result.returncode != 0


def test_grade_ignores_model_written_tests_and_grades_the_acceptance_file_alone(
    tmp_path,
):
    """The AgentClinic roadmap tells the model to write its own smoke test
    in tests/test_app.py, so a correct solution ships extra test files.
    Those must not count toward the verdict: pytest is given the
    acceptance suite's path explicitly, as the old harness did with
    `tests/test_acceptance.py` in its argv. Without that, a correct
    solution grades as executed=6 against expected=4 and is rejected."""
    source = tmp_path / "with-model-tests"
    shutil.copytree(PHASE_1 / "reference", source)
    model_tests = source / "tests"
    model_tests.mkdir()
    (model_tests / "test_app.py").write_text(
        "from starlette.testclient import TestClient\n"
        "from app import app\n"
        "\n"
        "client = TestClient(app)\n"
        "\n"
        "\n"
        "def test_home_ok():\n"
        "    assert client.get('/').status_code == 200\n"
        "\n"
        "\n"
        "def test_home_has_tagline():\n"
        "    assert 'Come in. Sit down.' in client.get('/').text\n"
    )

    with prepare_workspace(source) as workspace:
        result = grade(workspace, ACCEPTANCE, source_allowlist=ALLOWLIST)

    assert result.accepted is True
    assert result.tests_executed == result.tests_expected == 4


def test_grade_is_not_shadowed_by_a_workspace_root_harness_package(tmp_path):
    """Before cycle 9, `cwd=workspace` put a model-written harness/
    package ahead of the real one on sys.path, so `-p
    harness.grading_plugin` could import the model's copy instead of the
    real plugin. Verified directly against the pre-fix code: a rogue
    harness/grading_plugin.py was imported in place of the genuine one.

    The rogue here forges a full passing results file for the *broken*
    solution and then exits the process with status 0, defeating both
    the outcome check and the return-code veto. The companion test below
    proves that payload really does forge an acceptance when it is
    reachable, so this test's `accepted is False` means the rogue never
    ran -- not merely that something else went wrong."""
    source = _shadow_attack_source(tmp_path)

    with prepare_workspace(source) as workspace:
        result = grade(workspace, ACCEPTANCE, source_allowlist=ALLOWLIST)

    assert result.accepted is False
    assert result.tests_executed == 4


def test_the_shadow_attack_payload_really_forges_when_it_is_reachable(tmp_path):
    """Non-vacuity control for the test above.

    Same rogue package, but graded with an allowlist that copies
    `harness/` into the grading directory -- reproducing the exposure
    cycle 9 removed, where model-written files sat on the path pytest
    runs from. The forgery lands: a solution that 404s every route is
    accepted with four 'passing' tests.

    Without this control, the test above could pass for any reason at
    all -- a typo'd payload, a rogue that silently no-ops -- and still
    look like proof."""
    source = _shadow_attack_source(tmp_path)

    with prepare_workspace(source) as workspace:
        result = grade(
            workspace,
            ACCEPTANCE,
            source_allowlist=("app.py", "templates", "harness"),
        )

    assert result.accepted is True
    assert result.returncode == 0
