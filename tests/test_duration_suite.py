"""The evidence floor for the duration suite.

From `BRIEF.md`: "A grader's verdict isn't evidence until it has accepted a
known-good solution and rejected a known-broken one." These are that proof
for this suite. They need no model and no Pi.
"""

from pathlib import Path

from harness.grading import grade
from harness.runner import DURATION as DURATION_SUITE
from harness.workspace import prepare_workspace

REPO_ROOT = Path(__file__).resolve().parents[1]
DURATION = REPO_ROOT / "examples" / "duration"
# Consumed from harness.runner.DURATION, the suite a real run actually uses,
# rather than restated here -- so changing the suite's allowlist can never
# leave these floor tests certifying a configuration no run is graded under.
ACCEPTANCE = DURATION_SUITE.acceptance
ALLOWLIST = DURATION_SUITE.source_allowlist


def test_grade_accepts_the_duration_reference_solution():
    with prepare_workspace(DURATION / "reference") as workspace:
        result = grade(workspace, ACCEPTANCE, source_allowlist=ALLOWLIST)

    assert result.accepted is True
    assert result.tests_executed == result.tests_expected == 6


def test_grade_rejects_the_duration_broken_solution():
    with prepare_workspace(DURATION / "broken") as workspace:
        result = grade(workspace, ACCEPTANCE, source_allowlist=ALLOWLIST)

    assert result.accepted is False
    # Non-vacuity: the broken solution is rejected for failing tests, not
    # for a collection error or an empty run. Four of six behaviors are
    # correct, so a grader that rejected everything would pass this test
    # for the wrong reason.
    assert result.tests_executed == result.tests_expected == 6
    assert result.refused_config == ()
