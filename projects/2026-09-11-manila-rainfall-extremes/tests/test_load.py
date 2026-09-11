"""Loading, gap handling, and year-completeness rules.

Fixtures are hand-built payloads shaped like Open-Meteo's, including the broken
shapes a real API occasionally returns.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.load import MIN_DAYS_PER_YEAR, WET_DAY_MM, parse_payload


def payload(times: list[str], values: list[float | None]) -> dict:
    return {"daily": {"time": times, "precipitation_sum": values}}


def full_year(year: int, value: float | None = 2.0, days: int = 365) -> dict:
    """A payload of `days` consecutive days starting 1 January of `year`."""
    start = date(year, 1, 1).toordinal()
    times = [date.fromordinal(start + i).isoformat() for i in range(days)]
    return payload(times, [value] * days)


def test_parses_days_and_values():
    loaded = parse_payload(payload(["2020-01-01", "2020-01-02"], [0.0, 12.5]))

    assert [r.mm for r in loaded.records] == [0.0, 12.5]
    assert loaded.records[0].day == date(2020, 1, 1)
    assert loaded.records[0].year == 2020


def test_nulls_are_dropped_and_named_not_filled():
    loaded = parse_payload(
        payload(["2020-01-01", "2020-01-02", "2020-01-03"], [None, 5.0, None])
    )

    assert [r.mm for r in loaded.records] == [5.0]
    assert loaded.dropped_nulls == ["2020-01-01", "2020-01-03"]
    # The gaps must not have been interpolated into zeros.
    assert len(loaded.records) == 1
    assert loaded.days_per_year[2020] == 1


def test_wet_day_boundary_is_inclusive():
    loaded = parse_payload(
        payload(["2020-01-01", "2020-01-02", "2020-01-03"], [0.99, WET_DAY_MM, 1.01])
    )
    assert [r.is_wet for r in loaded.records] == [False, True, True]


def test_complete_year_is_kept():
    loaded = parse_payload(full_year(2020, days=365))

    assert loaded.complete_years == [2020]
    assert loaded.excluded_years == []


def test_sparse_year_is_excluded_and_reported():
    short = MIN_DAYS_PER_YEAR - 1
    loaded = parse_payload(full_year(2021, days=short))

    assert loaded.complete_years == []
    assert loaded.excluded_years == [(2021, short)]


def test_year_of_all_nulls_is_excluded_not_invisible():
    """A year that lost every observation must be named, not silently skipped."""
    body = full_year(2019, days=365)
    body["daily"]["precipitation_sum"] = [None] * 365
    body["daily"]["time"].append("2020-01-01")
    body["daily"]["precipitation_sum"].append(4.0)

    loaded = parse_payload(body)

    assert 2019 in loaded.days_per_year
    assert loaded.days_per_year[2019] == 0
    assert (2019, 0) in loaded.excluded_years


def test_ragged_arrays_raise():
    with pytest.raises(ValueError, match="ragged"):
        parse_payload(payload(["2020-01-01", "2020-01-02"], [1.0]))


def test_missing_daily_block_raises():
    with pytest.raises(ValueError, match="no 'daily' block"):
        parse_payload({"latitude": 14.6, "longitude": 120.98})


def test_missing_field_raises():
    with pytest.raises(ValueError, match="precipitation_sum"):
        parse_payload({"daily": {"time": ["2020-01-01"]}})


def test_all_null_payload_raises():
    with pytest.raises(ValueError, match="no usable precipitation"):
        parse_payload(payload(["2020-01-01", "2020-01-02"], [None, None]))
