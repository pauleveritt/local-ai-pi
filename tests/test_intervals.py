"""harness/intervals.py: Wilson and Newcombe confidence intervals.

The closed-form Wilson interval is cross-checked against an independently
derived quadratic-root solution of the same score-test equation (see
test_wilson_matches_the_quadratic_root_derivation) -- the roadmap's own
2026-08-10 review found a hand-computed statistic wrong once already
(Fisher one-sided off by a factor of five), and "computed by tested code"
means the test itself should not simply re-trust the implementation's own
algebra.
"""

import math

import pytest

from harness.intervals import Interval, newcombe_interval, wilson_interval


def _quadratic_wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Solve the Wilson score equation (p_hat - p)^2 = z^2 p(1-p)/n directly
    as a quadratic in p, independent of harness.intervals' derivation."""
    p_hat = successes / n
    a = 1 + z**2 / n
    b = -(2 * p_hat + z**2 / n)
    c = p_hat**2
    discriminant = b**2 - 4 * a * c
    root = math.sqrt(discriminant)
    low = (-b - root) / (2 * a)
    high = (-b + root) / (2 * a)
    return (max(0.0, low), min(1.0, high))


@pytest.mark.parametrize("successes,n", [(0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (3, 8), (6, 8), (0, 8), (8, 8), (3, 10)])
def test_wilson_matches_the_quadratic_root_derivation(successes, n):
    got = wilson_interval(successes, n)
    want_low, want_high = _quadratic_wilson(successes, n)
    assert got.low == pytest.approx(want_low, abs=1e-9)
    assert got.high == pytest.approx(want_high, abs=1e-9)


def test_zero_n_is_maximally_uninformative():
    assert wilson_interval(0, 0) == Interval(0.0, 1.0)


def test_zero_successes_touches_zero_but_not_one():
    interval = wilson_interval(0, 8)
    assert interval.low == 0.0
    assert interval.high < 1.0


def test_all_successes_touches_one_but_not_zero():
    interval = wilson_interval(8, 8)
    assert interval.high == 1.0
    assert interval.low > 0.0


def test_narrows_as_n_grows_at_the_same_rate():
    narrow = wilson_interval(3, 8)
    wide = wilson_interval(6, 16)  # same 37.5% rate, double n
    assert narrow.width > wide.width


def test_refuses_successes_outside_range():
    with pytest.raises(ValueError):
        wilson_interval(9, 8)
    with pytest.raises(ValueError):
        wilson_interval(-1, 8)


def test_newcombe_of_a_task_against_itself_straddles_zero():
    # Same data for both arms -- the true difference is exactly 0, so the
    # interval must contain it regardless of sample size.
    interval = newcombe_interval(3, 8, 3, 8)
    assert interval.includes_zero()


def test_newcombe_reflects_a_real_separation():
    # This session's actual n=8 numbers: flask-extensions (Arm B pilot
    # proxy) 6/8 oracle-passed vs. autowire 0/8 -- as distinct as this
    # cohort's pilot data gets. The interval for the difference must
    # exclude zero in the positive direction.
    interval = newcombe_interval(6, 8, 0, 8)
    assert interval.excludes_zero_above()


def test_newcombe_is_antisymmetric_in_its_arguments():
    forward = newcombe_interval(6, 8, 2, 8)
    backward = newcombe_interval(2, 8, 6, 8)
    assert forward.low == pytest.approx(-backward.high, abs=1e-9)
    assert forward.high == pytest.approx(-backward.low, abs=1e-9)


def test_interval_helpers_classify_correctly():
    assert Interval(0.1, 0.5).excludes_zero_above()
    assert not Interval(0.1, 0.5).excludes_zero_below()
    assert not Interval(0.1, 0.5).includes_zero()

    assert Interval(-0.5, -0.1).excludes_zero_below()
    assert not Interval(-0.5, -0.1).excludes_zero_above()

    assert Interval(-0.2, 0.3).includes_zero()
    assert not Interval(-0.2, 0.3).excludes_zero_above()
    assert not Interval(-0.2, 0.3).excludes_zero_below()
