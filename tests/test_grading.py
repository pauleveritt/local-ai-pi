from types import SimpleNamespace

from harness.grading_plugin import (
    DONE_MARKER,
    RESULTS_ENV_VAR,
    pytest_runtest_logreport,
    pytest_sessionfinish,
)


def test_plugin_appends_outcome_line_on_call_phase(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    report = SimpleNamespace(when="call", outcome="passed", nodeid="test_call.py::test_alpha")
    pytest_runtest_logreport(report)

    assert results.read_text() == "test_call.py::test_alpha\tpassed\n"


def test_plugin_records_a_failed_call_phase(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    report = SimpleNamespace(when="call", outcome="failed", nodeid="test_call.py::test_beta")
    pytest_runtest_logreport(report)

    assert results.read_text() == "test_call.py::test_beta\tfailed\n"


def test_plugin_ignores_successful_setup_and_teardown(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    setup_report = SimpleNamespace(when="setup", outcome="passed", nodeid="test_setup_ok.py::test_gamma")
    teardown_report = SimpleNamespace(when="teardown", outcome="passed", nodeid="test_setup_ok.py::test_gamma")
    pytest_runtest_logreport(setup_report)
    pytest_runtest_logreport(teardown_report)

    assert not results.exists()


def test_plugin_records_a_setup_failure(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    report = SimpleNamespace(when="setup", outcome="failed", nodeid="test_setup_fail.py::test_delta")
    pytest_runtest_logreport(report)

    assert results.read_text() == "test_setup_fail.py::test_delta\tfailed\n"


def test_plugin_records_a_teardown_failure_after_a_passed_call(tmp_path, monkeypatch):
    results = tmp_path / "results.txt"
    monkeypatch.setenv(RESULTS_ENV_VAR, str(results))

    call_report = SimpleNamespace(when="call", outcome="passed", nodeid="test_teardown.py::test_epsilon")
    teardown_report = SimpleNamespace(when="teardown", outcome="failed", nodeid="test_teardown.py::test_epsilon")
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
