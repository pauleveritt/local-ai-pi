"""Precision analysis over a numeric sample: how many future draws are
needed to pin down the mean to a stated confidence-interval half-width.

Bootstrap-based, not a classical formula. The samples this module was
built to analyze are small, discrete, and visibly not normal -- a
floor-spike distribution, not a bell curve. The bootstrap makes no
distributional assumption beyond "future draws come from the same
population `sample` represents."

Resampling with replacement from a sample of size m cannot produce a
value the sample never contained. For n far larger than m, this
understates the true sampling variability -- a known property of the
bootstrap with a small original sample, not a bug here. Treat a
reported half-width as optimistic, not exact, once n approaches or
exceeds the original sample size by a large factor.
"""

import random
import statistics
from collections.abc import Sequence


def bootstrap_ci_halfwidth(
    sample: Sequence[float],
    n: int,
    confidence: float = 0.95,
    resamples: int = 10_000,
    seed: int | None = None,
) -> float:
    """Estimated half-width of a `confidence` CI on the mean of `n` future
    draws from the population `sample` was drawn from.

    Draws `n` values with replacement from `sample`, takes the mean;
    repeats `resamples` times; returns half the width of the central
    `confidence` interval of the resulting distribution of means.
    """
    rng = random.Random(seed)
    means = sorted(
        statistics.fmean(rng.choice(sample) for _ in range(n))
        for _ in range(resamples)
    )
    lo = int((1 - confidence) / 2 * resamples)
    hi = int((1 + confidence) / 2 * resamples) - 1
    return (means[hi] - means[lo]) / 2


def minimum_n_for_precision(
    sample: Sequence[float],
    target_halfwidth: float,
    confidence: float = 0.95,
    resamples: int = 10_000,
    max_n: int = 1000,
    seed: int | None = None,
) -> int | None:
    """Smallest n, 1 <= n <= max_n, whose bootstrap_ci_halfwidth(sample,
    n, ...) is <= target_halfwidth. None if max_n is reached without
    satisfying it.

    Searches by doubling from n=1 to find an n that satisfies the
    target, then binary search between the last failing n and the first
    succeeding one -- relies on bootstrap_ci_halfwidth's ~1/sqrt(n)
    trend, not strict monotonicity at every adjacent n (resampling
    noise can produce tiny local upticks there). The returned n is
    checked directly against the target inside the search, not merely
    inferred from it.
    """
    n = 1
    while bootstrap_ci_halfwidth(sample, n, confidence, resamples, seed) > target_halfwidth:
        n *= 2
        if n > max_n:
            return None
    lo, hi = n // 2, n
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if bootstrap_ci_halfwidth(sample, mid, confidence, resamples, seed) <= target_halfwidth:
            hi = mid
        else:
            lo = mid
    return hi


def leave_one_out_spread(sample: Sequence[float]) -> float:
    """max - min of the sample mean recomputed with each single element
    dropped in turn. A stability diagnostic, not a CI: a sample whose
    mean swings a lot when any one point is removed is fragile evidence,
    independent of what any bootstrap half-width reports about it.
    """
    sample = list(sample)
    means = [
        statistics.fmean(sample[:i] + sample[i + 1 :]) for i in range(len(sample))
    ]
    return max(means) - min(means)
