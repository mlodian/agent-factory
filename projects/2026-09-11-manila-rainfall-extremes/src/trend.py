"""Distribution-free trend detection: Mann-Kendall and Theil-Sen.

Both are rank-based, which is why they are the standard pair for hydrological
extremes. Annual-maximum rainfall is skewed and heavy-tailed, so ordinary least
squares gives a slope that a single typhoon year can swing, and its t-test
assumes a normality the data does not have. Mann-Kendall asks only whether later
values tend to exceed earlier ones; Theil-Sen takes the median of pairwise
slopes and tolerates roughly 29% of the points being outliers.

Implemented against `math` rather than pulling in scipy for two functions.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from statistics import median

#: Conventional significance level. Reported explicitly so nobody has to guess
#: what "significant" meant.
ALPHA = 0.05


@dataclass(frozen=True)
class Trend:
    n: int
    s: int
    tau: float
    z: float
    p_value: float
    slope_per_year: float
    intercept: float

    @property
    def slope_per_decade(self) -> float:
        return self.slope_per_year * 10.0

    @property
    def significant(self) -> bool:
        return self.p_value < ALPHA

    @property
    def direction(self) -> str:
        if not self.significant:
            return "no detectable trend"
        return "rising" if self.s > 0 else "falling"

    def verdict(self, units: str = "mm") -> str:
        """A sentence a non-statistician can read without being misled."""
        if self.significant:
            return (
                f"{self.direction} at {self.slope_per_decade:+.2f} {units}/decade "
                f"(p = {self.p_value:.4f} < {ALPHA})"
            )
        return (
            f"no detectable trend (p = {self.p_value:.4f}, not < {ALPHA}); "
            f"the Theil-Sen slope is {self.slope_per_decade:+.2f} {units}/decade "
            f"but it is not distinguishable from zero"
        )


def mann_kendall_s(values: list[float]) -> int:
    """The Mann-Kendall S statistic: later-greater pairs minus later-smaller."""
    n = len(values)
    s = 0
    for i in range(n - 1):
        vi = values[i]
        for j in range(i + 1, n):
            diff = values[j] - vi
            if diff > 0:
                s += 1
            elif diff < 0:
                s -= 1
    return s


def _variance_s(values: list[float]) -> float:
    """Var(S) under the null, with the standard correction for tied values."""
    n = len(values)
    total = n * (n - 1) * (2 * n + 5)
    for tie_length in Counter(values).values():
        if tie_length > 1:
            total -= tie_length * (tie_length - 1) * (2 * tie_length + 5)
    return total / 18.0


def theil_sen(times: list[float], values: list[float]) -> tuple[float, float]:
    """Median pairwise slope, and the intercept that centres it on the medians."""
    slopes = [
        (values[j] - values[i]) / (times[j] - times[i])
        for i in range(len(times) - 1)
        for j in range(i + 1, len(times))
        if times[j] != times[i]
    ]
    if not slopes:
        raise ValueError("need at least two distinct time points")
    slope = median(slopes)
    return slope, median(values) - slope * median(times)


def analyse(times: list[float], values: list[float]) -> Trend:
    """Test `values` against `times` for a monotonic trend.

    Two-sided Mann-Kendall with the continuity correction, plus a Theil-Sen
    slope. The p-value uses the normal approximation to S, which is reliable
    from about n >= 10; below that it is optimistic and this raises instead.
    """
    if len(times) != len(values):
        raise ValueError(f"length mismatch: {len(times)} times vs {len(values)} values")
    n = len(values)
    if n < 10:
        raise ValueError(
            f"need at least 10 points for the normal approximation, got {n}"
        )

    s = mann_kendall_s(values)
    variance = _variance_s(values)

    # Continuity correction: S is a discrete statistic being read off a
    # continuous curve, so step one unit toward zero before standardising.
    if s > 0:
        z = (s - 1) / math.sqrt(variance)
    elif s < 0:
        z = (s + 1) / math.sqrt(variance)
    else:
        z = 0.0

    # Two-sided p. erfc(|z|/sqrt2) is exactly 2*(1 - Phi(|z|)) and stays
    # accurate in the far tail, where 1 - Phi(z) loses all its precision.
    p_value = math.erfc(abs(z) / math.sqrt(2.0))

    tau = s / (0.5 * n * (n - 1))
    slope, intercept = theil_sen(times, values)

    return Trend(
        n=n, s=s, tau=tau, z=z, p_value=p_value,
        slope_per_year=slope, intercept=intercept,
    )
