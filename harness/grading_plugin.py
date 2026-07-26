"""Harness-owned pytest plugin: records real test outcomes via pytest's own
internal hooks, not captured stdout/stderr text.

Copied into the isolated grading directory by ``harness/grading.py`` and
loaded with ``-p _pi_grading_plugin``. The grader's ``app.py``/``models.py``
are model-authored and imported into this same process at collection time,
so they share memory with this plugin -- there is no process boundary
between "trusted" and "untrusted" code here. What changed is *what* the
harness trusts: previously ``_executed_count()`` regex-scanned pytest's
captured stdout/stderr for a summary line, and a model-imported module can
write arbitrary bytes into any fd pytest captures (verified forge, Rule 8
review 2026-07-26 -- Fable: ``os.write()`` a fake "N passed" line into
pytest's captured-stdout fd, then ``os._exit(0)`` before any real test ran,
and the regex believed it). Reading real per-test hook events -- which only
fire when pytest's own runner actually executes a test -- closes that
specific attack, because the forged text is simply never read.

KNOWN, ACCEPTED, LIVE GAP -- not closed, backlogged deliberately. A second
Rule 8 round (Fable, 2026-07-26) reproduced a forge against this exact
mechanism: model-imported ``app.py`` reads ``os.environ[RESULTS_ENV_VAR]``
(same process, same environ) and writes directly-formatted fake
``nodeid\\toutcome`` lines plus the ``__DONE__`` sentinel into the results
file itself, before or instead of running any real test. This is not a
narrower or harder variant of the closed attack -- it is comparably cheap
(~7 lines), and no in-process secret can close it: anything this plugin
can read, model-imported code sharing its process and memory can read
too. What this mechanism DOES still correctly close: the original
captured-stdout-text forge (Rule 8, Fable, first round) and the classic
bare ``os._exit(0)`` and ``pytest.ini addopts=--collect-only`` defeats,
all pinned in ``tests/test_grading.py``. The env-var-forge gap itself is
tracked in ``docs/superpowers/roadmap.md``, Backlog, "Acceptance grading
still trusts a same-process signal a model can forge" -- the real fix
requires moving model-authored code out of the grading process entirely
(an out-of-process, HTTP-driven suite against a live app subprocess,
instead of in-process ``TestClient(app)``), which is a materially larger
change than this plugin and was deliberately deferred rather than done
here.
"""
import os

RESULTS_ENV_VAR = "PI_EVAL_GRADE_RESULTS"
DONE_SENTINEL = "__DONE__"

_outcomes: dict[str, str] = {}


def pytest_runtest_logreport(report):
    if report.when == "call":
        _outcomes[report.nodeid] = report.outcome
    elif report.when in ("setup", "teardown") and report.outcome in ("failed", "error"):
        _outcomes.setdefault(report.nodeid, report.outcome)
    else:
        return
    _append(f"{report.nodeid}\t{_outcomes[report.nodeid]}\n")


def pytest_sessionfinish(session, exitstatus):
    _append(f"{DONE_SENTINEL}\n")


def _append(line: str) -> None:
    path = os.environ[RESULTS_ENV_VAR]
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, line.encode())
        os.fsync(fd)
    finally:
        os.close(fd)
