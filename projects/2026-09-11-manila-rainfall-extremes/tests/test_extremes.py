"""Percentile, threshold, annual indices, and decade aggregation."""

from __future__ import annotations

from datetime import date

import pytest

from src.extremes import annual_series, by_decade, percentile, r99p_threshold
from src.load import Daily


def days(year: int, values: list[float]) -> list[Daily]:
    start = date(year, 1, 1).toordinal()
    return [Daily(date.fromordinal(start + i), v) for i, v in enumerate(values)]


def test_percentile_endpoints_are_min_and_max():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert percentile(values, 0) == 1.0
    assert percentile(values, 100) == 5.0


def test_percentile_interpolates_linearly():
    # 0..100 over 101 points: the nth percentile is exactly n.
    values = [float(i) for i in range(101)]
    assert percentile(values, 99) == pytest.approx(99.0)
    assert percentile(values, 50) == pytest.approx(50.0)

    # Interpolation between two points: position = 1.5 -> midpoint.
    assert percentile([0.0, 10.0, 20.0, 30.0], 50) == pytest.approx(15.0)


def test_percentile_ignores_input_order():
    assert percentile([5.0, 1.0, 3.0, 2.0, 4.0], 50) == pytest.approx(3.0)


def test_percentile_of_single_value():
    assert percentile([42.0], 99) == 42.0


def test_percentile_rejects_empty_and_out_of_range():
    with pytest.raises(ValueError, match="empty"):
        percentile([], 99)
    with pytest.raises(ValueError, match=r"\[0, 100\]"):
        percentile([1.0, 2.0], 101)


def test_threshold_uses_wet_days_only():
    """Dry days must not drag the extreme percentile toward zero."""
    wet = [float(i) for i in range(1, 101)]  # 1..100 mm, all wet
    dry = [0.0] * 900

    wet_only = r99p_threshold(days(2000, wet))
    with_dry = r99p_threshold(days(2000, wet + dry))

    assert wet_only == pytest.approx(with_dry)
    assert with_dry > 90.0


def test_threshold_needs_a_wet_day():
    with pytest.raises(ValueError, match="no wet days"):
        r99p_threshold(days(2000, [0.0, 0.1, 0.5]))


def test_annual_series_indices():
    records = days(2001, [0.0, 5.0, 100.0, 0.5]) + days(2002, [20.0, 20.0])
    series = annual_series(records, [2001, 2002], threshold=50.0)

    assert series.years == [2001, 2002]
    assert series.rx1day == [100.0, 20.0]
    assert series.total_mm == [pytest.approx(105.5), pytest.approx(40.0)]
    assert series.wet_days == [2.0, 2.0]   # 5.0 and 100.0; then 20.0 and 20.0
    assert series.r99p_days == [1.0, 0.0]  # only 100.0 beats 50.0


def test_annual_series_skips_excluded_years():
    records = days(2001, [10.0]) + days(2002, [20.0])
    series = annual_series(records, [2002], threshold=5.0)

    assert series.years == [2002]
    assert series.rx1day == [20.0]


def test_decade_bucketing_and_per_year_normalisation():
    records = days(1995, [100.0, 1.0]) + days(2001, [100.0, 1.0]) + days(2002, [100.0])
    rows = by_decade(records, [1995, 2001, 2002], threshold=50.0)

    assert [r.decade for r in rows] == [1990, 2000]
    assert rows[0].label == "1990s"

    nineties, noughties = rows
    assert nineties.years == 1
    assert nineties.exceedance_days == 1
    assert nineties.days_per_year == pytest.approx(1.0)

    # Two years, two extreme days -> 1.0/yr, not 2.
    assert noughties.years == 2
    assert noughties.exceedance_days == 2
    assert noughties.days_per_year == pytest.approx(1.0)
    assert noughties.mean_intensity_mm == pytest.approx(100.0)
    assert noughties.total_mm_per_year == pytest.approx(100.5)


def test_decade_with_no_exceedances_reports_zero_not_nan():
    rows = by_decade(days(2010, [1.0, 2.0]), [2010], threshold=500.0)

    assert rows[0].exceedance_days == 0
    assert rows[0].mean_intensity_mm == 0.0
    assert rows[0].max_day_mm == 2.0


def test_threshold_is_strict_greater_than():
    """A day exactly at the threshold is not an exceedance."""
    records = days(2000, [50.0, 50.1])
    series = annual_series(records, [2000], threshold=50.0)
    assert series.r99p_days == [1.0]
