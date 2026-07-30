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
    if report.when == "call":
        outcome = report.outcome
    elif report.when in ("setup", "teardown") and report.outcome == "failed":
        outcome = report.outcome
    else:
        return
    _append(f"{report.nodeid}\t{outcome}\n")


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
