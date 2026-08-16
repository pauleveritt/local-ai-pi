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


def fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p for the 2x2 table [[a, b], [c, d]].

    Rows are arms, columns are (accepted, not accepted). Added
    2026-08-15: three separate write-ups had by then quoted Fisher
    p-values computed by throwaway inline functions, and one of them
    claimed this module as their source when it had no Fisher at all.
    That is precisely the hand-computed-statistic failure this module
    exists to prevent -- see `wilson_interval`'s own history -- so the
    computation lives here, tested, or it does not get quoted.

    Exact, not an approximation: it enumerates every table with the same
    margins and sums the probability of those no more likely than the
    observed one (the conventional two-sided criterion). Small integer
    margins only, which is all this project's arms produce; there is no
    attempt at the large-sample shortcuts a general library would need.
    """
    for name, value in (("a", a), ("b", b), ("c", c), ("d", d)):
        if value < 0:
            raise ValueError(f"{name}={value} must be non-negative")
    total = a + b + c + d
    if total == 0:
        raise ValueError("the table is empty")

    row_a, row_c = a + b, c + d
    col_accepted = a + c

    def table_probability(x: int) -> float:
        # Hypergeometric probability of `x` acceptances in the first row,
        # holding both margins fixed.
        return (
            math.comb(row_a, x)
            * math.comb(row_c, col_accepted - x)
            / math.comb(total, col_accepted)
        )

    observed = table_probability(a)
    low = max(0, col_accepted - row_c)
    high = min(row_a, col_accepted)
    # 1e-12 slack: equally-likely mirror tables must be counted, and exact
    # float equality would drop them on some margins.
    return min(
        1.0,
        sum(
            table_probability(x)
            for x in range(low, high + 1)
            if table_probability(x) <= observed + 1e-12
        ),
    )
