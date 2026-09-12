from pathlib import Path

import pytest

from src.dataset import load_records

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_records_happy_path_filters_and_derives_fields():
    records = load_records(FIXTURES / "sample_311.csv")

    # The Unspecified-borough row is dropped; the other 5 rows are kept.
    assert len(records) == 5
    assert {r.borough for r in records} == {"BRONX", "QUEENS"}

    closed_same_day = next(r for r in records if r.complaint_type == "Noise - Residential"
                            and r.borough == "QUEENS")
    assert closed_same_day.closed_within_window is True
    assert closed_same_day.hours_to_close == pytest.approx(1.0)

    still_open = next(r for r in records if r.closed is None)
    assert still_open.is_open is True
    assert still_open.hours_to_close is None
    assert still_open.closed_within_window is False

    slow_close = next(r for r in records if r.complaint_type == "HEAT/HOT WATER"
                       and r.borough == "BRONX")
    assert slow_close.hours_to_close == pytest.approx(96.0)
    assert slow_close.closed_within_window is False  # closed, but after 72h


def test_load_records_drops_non_borough_rows():
    records = load_records(FIXTURES / "sample_311.csv")
    assert all(r.borough != "UNSPECIFIED" for r in records)
    assert sum(1 for r in records if r.borough == "BRONX") == 3


def test_load_records_raises_on_malformed_timestamp():
    with pytest.raises(ValueError, match="unparsable"):
        load_records(FIXTURES / "bad_date_311.csv")


def test_load_records_raises_on_day_outside_sample():
    with pytest.raises(ValueError, match="outside the 37 sampled days"):
        load_records(FIXTURES / "stray_day_311.csv")
