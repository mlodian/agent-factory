"""Read the raw Open-Meteo payload into daily records, and decide which calendar
years are complete enough to carry an annual statistic.

Nothing here interpolates, fills, or smooths. A missing day is dropped and
counted; a year that loses too many days is excluded and named. Quietly filling
gaps would make the trend look better behaved than the data warrants.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

#: A "wet day" in the ETCCDI convention — days below this are drizzle or dry,
#: and including them would drag the extreme percentile down toward zero.
WET_DAY_MM = 1.0

#: A calendar year needs this many valid observations to get an annual statistic.
#: 360 of 365 tolerates a handful of gaps without letting a half-empty year
#: masquerade as a low-rainfall one.
MIN_DAYS_PER_YEAR = 360


@dataclass(frozen=True)
class Daily:
    """One day's total precipitation, in millimetres."""

    day: date
    mm: float

    @property
    def year(self) -> int:
        return self.day.year

    @property
    def is_wet(self) -> bool:
        return self.mm >= WET_DAY_MM


@dataclass(frozen=True)
class Loaded:
    records: list[Daily]
    dropped_nulls: list[str]
    #: year -> number of valid days, for every year present in the file
    days_per_year: dict[int, int]

    @property
    def complete_years(self) -> list[int]:
        return sorted(y for y, n in self.days_per_year.items() if n >= MIN_DAYS_PER_YEAR)

    @property
    def excluded_years(self) -> list[tuple[int, int]]:
        """(year, valid-day count) for years too sparse to use, oldest first."""
        return sorted(
            (y, n) for y, n in self.days_per_year.items() if n < MIN_DAYS_PER_YEAR
        )


def parse_payload(payload: dict) -> Loaded:
    """Turn an Open-Meteo `daily` block into records. Raises on the wrong shape."""
    if not isinstance(payload, dict) or "daily" not in payload:
        raise ValueError("payload has no 'daily' block")

    daily = payload["daily"]
    for key in ("time", "precipitation_sum"):
        if key not in daily:
            raise ValueError(f"'daily' block is missing {key!r}")

    days, precip = daily["time"], daily["precipitation_sum"]
    if len(days) != len(precip):
        raise ValueError(f"ragged arrays: {len(days)} dates vs {len(precip)} values")

    records: list[Daily] = []
    dropped: list[str] = []
    days_per_year: dict[int, int] = {}

    for stamp, value in zip(days, precip):
        parsed = date.fromisoformat(stamp)
        # Count every year we saw, even one whose days are all null, so a fully
        # missing year shows up as excluded rather than silently vanishing.
        days_per_year.setdefault(parsed.year, 0)
        if value is None:
            dropped.append(stamp)
            continue
        records.append(Daily(parsed, float(value)))
        days_per_year[parsed.year] += 1

    if not records:
        raise ValueError("no usable precipitation values in payload")

    return Loaded(records, dropped, days_per_year)


def load_daily(path: str | Path) -> Loaded:
    """Load the raw JSON file written by data/fetch_data.py."""
    return parse_payload(json.loads(Path(path).read_bytes()))


def default_raw_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "raw" / "manila_precip_1940_2025.json"
