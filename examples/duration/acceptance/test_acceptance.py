"""Acceptance contract -- duration parser. Harness-owned; the model cannot edit this.

Contract source: examples/duration/spec.md.

**No `@pytest.mark.parametrize` here, or in any acceptance suite.**
`harness.grading._test_count` counts module-level `def test_*` declarations,
while the grading plugin records one line per *executed* nodeid. Parametrize
splits them -- 1 declared, N executed -- so `tests_executed == tests_expected`
fails and a *correct* solution is rejected. One test function per contract
behavior. This constraint is on acceptance suites only; the harness's own
tests under `tests/` may parametrize freely.

Assert only the contract in spec.md. Do not assert on internal helper names,
module layout, or the exception message -- a correct-but-different solution
must pass.
"""
import pytest

from duration import parse_duration


def test_seconds_alone():
    assert parse_duration("30s") == 30


def test_minutes_alone():
    assert parse_duration("5m") == 300


def test_hours_alone():
    assert parse_duration("1h") == 3600


def test_hours_and_minutes_combine():
    """The defining case: a parser that stops at the first unit returns 3600."""
    assert parse_duration("1h30m") == 5400


def test_all_three_units_combine():
    assert parse_duration("2h15m30s") == 8130


def test_unparseable_input_raises_value_error():
    with pytest.raises(ValueError):
        parse_duration("banana")
