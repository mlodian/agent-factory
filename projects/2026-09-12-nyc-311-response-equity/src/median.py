"""A weighted median that knows about right-censoring.

A still-open request has no known close time, only a lower bound on it (it has been
open at least this long, and may stay open far longer). Treating that as `+inf`
places every censored item at the top of the distribution, which is exactly where it
belongs for the purpose of a median: if fewer than half a cell's weight is censored,
the true median is a real, finite number of hours; if half or more is censored, the
honest answer is "we don't know, but it's more than the cutoff" — reported as the
sentinel `CENSORED`, never as a made-up number.

`weighted_median` treats each `(value, weight)` pair as `weight` identical copies of
`value` in a conceptually expanded, sorted list, and returns the same thing
`statistics.median` would return on that expansion (the middle element for an odd
total weight, the average of the two middle elements for an even one) — without
actually building the expansion. `tests/test_median.py` checks this against a
brute-force expansion directly.
"""

from __future__ import annotations

import math

CENSORED = "CENSORED"


def weighted_median(pairs: list[tuple[float, int]]) -> float:
    """`pairs`: [(value, weight)], weight a positive integer. Censored observations
    should be passed as `(math.inf, weight)`. Returns `math.inf` when the resulting
    median falls among the censored items."""
    items = [(v, w) for v, w in pairs if w > 0]
    if not items:
        raise ValueError("weighted_median of an empty (or all-zero-weight) input")
    items.sort(key=lambda p: p[0])
    total = sum(w for _, w in items)

    # 0-based positions of the "middle" element(s) of the length-`total` expansion.
    lower_idx = (total - 1) // 2
    upper_idx = total // 2

    def value_at(index: int) -> float:
        seen = 0
        for value, weight in items:
            seen += weight
            if index < seen:
                return value
        return items[-1][0]  # unreachable if total is correct

    lower_value = value_at(lower_idx)
    upper_value = value_at(upper_idx)
    return (lower_value + upper_value) / 2.0


def censored_share(pairs: list[tuple[float, int]]) -> float:
    total = sum(w for _, w in pairs)
    if total == 0:
        return 0.0
    censored = sum(w for v, w in pairs if math.isinf(v))
    return censored / total


def report_median(pairs: list[tuple[float, int]]) -> str:
    """The value to print: an hours figure, or `"> 72h"` when at least half the
    cell's weight is censored (SPEC.md's rule, and exactly the condition under
    which `weighted_median` itself would return `inf`)."""
    value = weighted_median(pairs)
    if math.isinf(value):
        return "> 72 h"
    return f"{value:.1f}h"
