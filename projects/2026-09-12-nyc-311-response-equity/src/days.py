"""The 37 sampled calendar days: day-of-year 1, 11, 21, ..., 361 of 2025.

Fixed by SPEC.md before any data was seen: a stride of 10 spreads evenly across the
seasons, and because 10 and 7 are coprime it cycles through all seven weekdays 5-6
times each, so it does not over-sample weekends. 2025 is not a leap year, so
day-of-year `n` maps to `date(2025, 1, 1) + (n - 1) days`.

Both `data/fetch_data.py` (which requests one slice per day) and `src/dataset.py`
(which validates every loaded record falls on one of these days) call this function,
so the two can never silently disagree about which days were sampled.
"""

from __future__ import annotations

from datetime import date, timedelta

YEAR = 2025
STRIDE = 10
FIRST_DAY_OF_YEAR = 1
LAST_DAY_OF_YEAR = 361  # 1, 11, ..., 361: 37 days


def sampled_dates() -> list[date]:
    base = date(YEAR, 1, 1)
    return [
        base + timedelta(days=doy - 1)
        for doy in range(FIRST_DAY_OF_YEAR, LAST_DAY_OF_YEAR + 1, STRIDE)
    ]
