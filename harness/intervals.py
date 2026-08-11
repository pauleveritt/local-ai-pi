"""Confidence intervals for the Cycle 7 pre-registered comparison.

Deliberately small: two well-known closed-form formulas, tested, so
neither this batch nor any future one recomputes them by hand. That
matters here specifically -- the roadmap's 2026-08-10 external review
found a prespecified margin justified with a wrong statistic (Fisher
one-sided computed by hand, off by a factor of five), and the fix was
"margins must be computed by tested code, not by hand." This module is
that code for the two intervals
docs/superpowers/specs/2026-08-11-phase7-cycle7-preregistration-design.md
commits to.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Interval:
    low: float
    high: float

    @property
    def width(self) -> float:
        return self.high - self.low

    def excludes_zero_above(self) -> bool:
        """True iff this interval lies entirely above zero."""
        return self.low > 0

    def excludes_zero_below(self) -> bool:
        """True iff this interval lies entirely below zero."""
        return self.high < 0

    def includes_zero(self) -> bool:
        return self.low <= 0 <= self.high


def wilson_interval(successes: int, n: int, z: float = 1.96) -> Interval:
    """The Wilson score interval for a single binomial proportion.

    `z=1.96` is the two-sided 95% critical value. `n=0` returns the
    maximally uninformative [0, 1] rather than raising -- a void or
    not-yet-run cell should read as "no information," not crash a report.
    """
    if n == 0:
        return Interval(0.0, 1.0)
    if successes < 0 or successes > n:
        raise ValueError(f"successes={successes} must be within [0, n={n}]")
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return Interval(max(0.0, center - half), min(1.0, center + half))


def newcombe_interval(
    successes_a: int, n_a: int, successes_b: int, n_b: int, z: float = 1.96
) -> Interval:
    """Newcombe's interval for the difference of two independent proportions (a - b).

    Combines two Wilson intervals rather than a pooled-variance normal
    approximation, which is unreliable exactly where this pre-registration
    needs it most -- proportions near 0 or 1 at n=8. Order matters: this
    returns an interval for (a's rate) minus (b's rate).
    """
    wa = wilson_interval(successes_a, n_a, z)
    wb = wilson_interval(successes_b, n_b, z)
    p_a = successes_a / n_a if n_a else 0.0
    p_b = successes_b / n_b if n_b else 0.0
    low = p_a - p_b - math.sqrt((p_a - wa.low) ** 2 + (wb.high - p_b) ** 2)
    high = p_a - p_b + math.sqrt((wa.high - p_a) ** 2 + (p_b - wb.low) ** 2)
    return Interval(max(-1.0, low), min(1.0, high))
