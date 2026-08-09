"""Pytest plugin: records verdict-relevant test outcomes via pytest's own
runtest hooks, and a completion marker, to a results file whose path is
given by an environment variable.

Reads real per-test hook events -- which only fire when pytest's own
runner actually executes a test -- rather than trusting captured
stdout/stderr text, which a model-imported module sharing this process
could write into directly.

Each phase appends its own current outcome, never a previously recorded
one -- a test whose call phase passes but whose teardown phase then fails
must append a second, later line saying `failed` for the same nodeid, so
that a genuine teardown failure is visible to a reader who dedups by
nodeid and keeps the last line (see harness/grading.py's verdict logic).
"""

import os

RESULTS_ENV_VAR = "SATYRN_GRADE_RESULTS_PATH"
DONE_MARKER = "__DONE__"


def pytest_runtest_logreport(report):
    # The call phase is always verdict-relevant. Setup and teardown are
    # relevant only when they fail: a passing setup says nothing, but a
    # failing one means the test never really ran, and a failing teardown
    # invalidates a call phase that looked fine.
    if report.when == "call" or (
        report.when in ("setup", "teardown") and report.outcome == "failed"
    ):
        _append(f"{report.nodeid}\t{report.outcome}\n")


def pytest_sessionfinish(session, exitstatus):
    _append(f"{DONE_MARKER}\n")


def _append(line: str) -> None:
    path = os.environ[RESULTS_ENV_VAR]
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, line.encode())
        os.fsync(fd)
    finally:
        os.close(fd)
