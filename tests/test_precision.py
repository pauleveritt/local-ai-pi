from harness.precision import (
    bootstrap_ci_halfwidth,
    leave_one_out_spread,
    minimum_n_for_precision,
)

ZERO_VARIANCE = [5.0] * 20
SPREAD_1_TO_20 = list(range(1, 21))


def test_zero_variance_sample_has_zero_halfwidth_at_any_n():
    for n in (1, 5, 20, 100):
        assert bootstrap_ci_halfwidth(ZERO_VARIANCE, n, seed=0) == 0.0


def test_zero_variance_sample_needs_only_the_smallest_allowed_n():
    assert minimum_n_for_precision(ZERO_VARIANCE, target_halfwidth=0.1, seed=0) == 1


def test_halfwidth_decreases_across_doublings_on_a_spread_sample():
    # Not adjacent-n monotonicity (resampling noise can produce tiny local
    # upticks there) -- across doublings, the ~1/sqrt(n) trend dominates.
    halfwidths = [
        bootstrap_ci_halfwidth(SPREAD_1_TO_20, n, seed=0)
        for n in (1, 2, 4, 8, 16, 32, 64)
    ]
    assert halfwidths == [9.5, 8.0, 5.5, 4.0, 2.8125, 1.984375, 1.421875]
    assert halfwidths == sorted(halfwidths, reverse=True)


def test_minimum_n_self_consistency_the_returned_n_actually_satisfies_target():
    # The non-vacuity pin for the search: returning the wrong n would pass
    # a test that only checked the return type.
    n = minimum_n_for_precision(SPREAD_1_TO_20, target_halfwidth=2.0, seed=0)
    assert n == 31
    assert bootstrap_ci_halfwidth(SPREAD_1_TO_20, n, seed=0) == 2.0
    assert bootstrap_ci_halfwidth(SPREAD_1_TO_20, n - 1, seed=0) > 2.0


def test_unreachable_target_returns_none_specifically():
    # A search that silently returned max_n instead would also "not
    # raise," and would be wrong in exactly the way that matters.
    result = minimum_n_for_precision(
        SPREAD_1_TO_20, target_halfwidth=0.5, max_n=4, seed=0
    )
    assert result is None


def test_same_seed_produces_the_same_result():
    a = bootstrap_ci_halfwidth(SPREAD_1_TO_20, 10, seed=42)
    b = bootstrap_ci_halfwidth(SPREAD_1_TO_20, 10, seed=42)
    assert a == b == 3.55


def test_leave_one_out_spread_matches_a_hand_computed_example():
    # drop 1 -> mean(2,3,4)=3.0; drop 2 -> mean(1,3,4)=2.667;
    # drop 3 -> mean(1,2,4)=2.333; drop 4 -> mean(1,2,3)=2.0
    # spread = 3.0 - 2.0 = 1.0
    assert leave_one_out_spread([1, 2, 3, 4]) == 1.0


def test_leave_one_out_spread_is_zero_for_a_constant_sample():
    assert leave_one_out_spread(ZERO_VARIANCE) == 0.0
