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


from harness.grading import _verdict


def test_verdict_accepts_when_all_conjuncts_hold():
    results_text = (
        "test_acceptance.py::test_a\tpassed\n"
        "test_acceptance.py::test_b\tpassed\n"
        "test_acceptance.py::test_c\tpassed\n"
        "test_acceptance.py::test_d\tpassed\n"
        "__DONE__\n"
    )

    result = _verdict(results_text, tests_expected=4, returncode=0, stdout="", stderr="")

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

    result = _verdict(results_text, tests_expected=4, returncode=0, stdout="", stderr="")

    assert result.accepted is False


def test_verdict_rejects_a_partial_run():
    results_text = (
        "test_acceptance.py::test_a\tpassed\n"
        "test_acceptance.py::test_b\tpassed\n"
        "__DONE__\n"
    )

    result = _verdict(results_text, tests_expected=4, returncode=0, stdout="", stderr="")

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

    result = _verdict(results_text, tests_expected=4, returncode=0, stdout="", stderr="")

    assert result.accepted is False


def test_verdict_rejects_on_nonzero_returncode_even_if_everything_else_passed():
    results_text = (
        "test_acceptance.py::test_a\tpassed\n"
        "test_acceptance.py::test_b\tpassed\n"
        "test_acceptance.py::test_c\tpassed\n"
        "test_acceptance.py::test_d\tpassed\n"
        "__DONE__\n"
    )

    result = _verdict(results_text, tests_expected=4, returncode=1, stdout="", stderr="")

    assert result.accepted is False
