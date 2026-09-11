"""Extreme-rainfall indices, computed from daily records.

The indices follow the ETCCDI conventions used in the climate literature so the
numbers mean the same thing here as they do elsewhere:

  R99p threshold   99th percentile of wet-day (>= 1 mm) rainfall over the base period
  Rx1day           each year's wettest single day
  PRCPTOT          each year's total rainfall
  wet days         each year's count of days >= 1 mm

The base period is the whole record rather than a fixed 1961-1990 window. That
is a deliberate trade: a whole-record base keeps every year comparable against
one fixed threshold, at the cost of not being directly comparable to papers that
use the WMO baseline. `base_period` makes the choice explicit.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from statistics import mean

from src.load import Daily, WET_DAY_MM


@dataclass(frozen=True)
class DecadeStats:
    decade: int
    years: int
    exceedance_days: int
    days_per_year: float
    mean_intensity_mm: float
    max_day_mm: float
    total_mm_per_year: float

    @property
    def label(self) -> str:
        return f"{self.decade}s"


@dataclass(frozen=True)
class AnnualSeries:
    years: list[int]
    rx1day: list[float]
    total_mm: list[float]
    wet_days: list[float]
    r99p_days: list[float]


def percentile(values: list[float], pct: float) -> float:
    """Linear-interpolation percentile, matching numpy's default ("linear") method.

    Interpolates on (n-1), so percentile(xs, 0) is min and percentile(xs, 100) is
    max. Written out rather than routed through `statistics.quantiles` because
    that function's `n=100` form only addresses whole-number percentiles.
    """
    if not values:
        raise ValueError("percentile of an empty sequence")
    if not 0 <= pct <= 100:
        raise ValueError(f"percentile must be in [0, 100], got {pct}")

    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])

    position = (len(ordered) - 1) * (pct / 100.0)
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return float(ordered[low])
    return float(ordered[low] + (ordered[high] - ordered[low]) * (position - low))


def wet_day_values(records: list[Daily]) -> list[float]:
    return [r.mm for r in records if r.is_wet]


def r99p_threshold(records: list[Daily]) -> float:
    """The rainfall total a day must beat to count as extreme here."""
    wet = wet_day_values(records)
    if not wet:
        raise ValueError(f"no wet days (>= {WET_DAY_MM} mm) in the record")
    return percentile(wet, 99)


def annual_series(records: list[Daily], years: list[int], threshold: float) -> AnnualSeries:
    """Per-year indices, restricted to `years` (the complete ones)."""
    keep = set(years)
    by_year: dict[int, list[Daily]] = defaultdict(list)
    for record in records:
        if record.year in keep:
            by_year[record.year].append(record)

    ordered = sorted(by_year)
    return AnnualSeries(
        years=ordered,
        rx1day=[max(r.mm for r in by_year[y]) for y in ordered],
        total_mm=[sum(r.mm for r in by_year[y]) for y in ordered],
        wet_days=[float(sum(1 for r in by_year[y] if r.is_wet)) for y in ordered],
        r99p_days=[float(sum(1 for r in by_year[y] if r.mm > threshold)) for y in ordered],
    )


def by_decade(records: list[Daily], years: list[int], threshold: float) -> list[DecadeStats]:
    """Aggregate exceedances of `threshold` into decades.

    A decade is included whole or not at all in the year count, but a partial
    decade at either end of the record still appears — with its real year count,
    so a reader can see that the 2020s are six years and not ten.
    """
    keep = set(years)
    buckets: dict[int, list[Daily]] = defaultdict(list)
    decade_years: dict[int, set[int]] = defaultdict(set)
    for record in records:
        if record.year not in keep:
            continue
        decade = (record.year // 10) * 10
        buckets[decade].append(record)
        decade_years[decade].add(record.year)

    out: list[DecadeStats] = []
    for decade in sorted(buckets):
        days = buckets[decade]
        n_years = len(decade_years[decade])
        extreme = [r.mm for r in days if r.mm > threshold]
        out.append(
            DecadeStats(
                decade=decade,
                years=n_years,
                exceedance_days=len(extreme),
                days_per_year=len(extreme) / n_years,
                mean_intensity_mm=mean(extreme) if extreme else 0.0,
                max_day_mm=max(r.mm for r in days),
                total_mm_per_year=sum(r.mm for r in days) / n_years,
            )
        )
    return out
