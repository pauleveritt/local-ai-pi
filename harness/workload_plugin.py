"""Pytest plugin: records phase-tagged outcomes and structured collection failures.

Separate from `harness/grading_plugin.py` rather than an extension of it.
That plugin's `nodeid\\toutcome` format is parsed by `harness/grading.py`
and underpins banked evidence; widening it to carry a phase would change
a format that existing records were written in. This one is free to be
richer because nothing has been recorded with it yet.

Two things it captures that the older plugin discards:

**The phase.** `nodeid\\toutcome` cannot tell a failed assertion from a
missing fixture -- both arrive as `failed`. A setup failure means the
test never ran, which is a different fact about a task than an assertion
that ran and was wrong, and a replay task that declares
"assertion-failure" should not be satisfied by a broken fixture.

**Collection failures, with their exception.** A collection error
records no test outcomes at all, so a run that failed to collect is
otherwise indistinguishable from any other run that failed to collect.
Recording which file failed and what it raised is what lets a manifest
pre-register *why* a base is expected to reject.
"""

import os
import re

RESULTS_ENV_VAR = "SATYRN_WORKLOAD_RESULTS_PATH"
DONE_MARKER = "__DONE__"
TEST_PREFIX = "T"
COLLECT_PREFIX = "C"


def pytest_runtest_logreport(report):
    # Every phase is recorded, not only the verdict-relevant ones: the
    # reader needs to know a failure happened in `setup` to refuse to
    # call it an assertion failure, and that is only visible if the
    # phase is written down.
    if report.when == "call" or report.outcome == "failed":
        _append(f"{TEST_PREFIX}\t{report.nodeid}\t{report.when}\t{report.outcome}\n")


def pytest_collectreport(report):
    if report.outcome != "failed":
        return
    _append(f"{COLLECT_PREFIX}\t{report.nodeid}\t{_normalize(report.longrepr)}\n")


def pytest_sessionfinish(session, exitstatus):
    _append(f"{DONE_MARKER}\n")


# Absolute paths are stripped from recorded failures. Every run gets a
# fresh materialization under a new temporary directory, so a message
# like "cannot import name 'mul' from 'pkg' (/tmp/satyrn-workload-ab12/
# src/pkg/__init__.py)" differs on every single run -- which would make
# every collection-error task look nondeterministic and disqualify it
# for a difference that carries no information.
_ABSOLUTE_PATH = re.compile(r"/[^\s'\"()]+")


def _normalize(longrepr) -> str:
    """Reduce a collection failure to one path-free line naming the exception.

    The last non-empty line of pytest's representation is the raised
    exception and its message -- `ImportError: cannot import name 'mul'
    from 'pkg'` -- which is the part a manifest can pre-register. The
    symbol names survive; only the paths around them are replaced.
    """
    lines = [line.strip() for line in str(longrepr).splitlines() if line.strip()]
    if not lines:
        return "unknown collection failure"
    return _ABSOLUTE_PATH.sub("<path>", lines[-1].replace("\t", " "))


def _append(line: str) -> None:
    path = os.environ[RESULTS_ENV_VAR]
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, line.encode())
        os.fsync(fd)
    finally:
        os.close(fd)
