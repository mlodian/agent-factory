"""Load the committed 311 extract and turn each row into a typed `Record`.

Only rows whose `borough` is one of the five boroughs are kept — `Unspecified` and
blank boroughs are dropped here, and nowhere else, so every downstream count is
already scoped to the population SPEC.md defines.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from .days import sampled_dates

RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "nyc311_sample_2025.csv"
BOROUGHS = ["BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"]
CLOSE_WINDOW_HOURS = 72.0
REQUIRED_COLUMNS = ("created_date", "closed_date", "complaint_type", "agency", "borough")


@dataclass(frozen=True)
class Record:
    created: datetime
    closed: datetime | None
    complaint_type: str
    agency: str
    borough: str
    day: date

    @property
    def is_open(self) -> bool:
        return self.closed is None

    @property
    def hours_to_close(self) -> float | None:
        if self.closed is None:
            return None
        return (self.closed - self.created).total_seconds() / 3600.0

    @property
    def closed_within_window(self) -> bool:
        hours = self.hours_to_close
        return hours is not None and hours <= CLOSE_WINDOW_HOURS


def _parse_timestamp(raw: str, *, field: str, line_no: int) -> datetime | None:
    raw = raw.strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(
            f"line {line_no}: unparsable {field!r} timestamp {raw!r}: {exc}"
        ) from exc


def load_records(path: Path = RAW_PATH) -> list[Record]:
    """Read the extract, keep the five-borough rows, and validate every date lands
    on one of the 37 sampled days.

    Raises ValueError on a malformed timestamp or an unexpected column set — this
    extract is a fixed, committed file, so a parse failure means real corruption,
    not something to paper over with a skip.
    """
    records: list[Record] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = set(REQUIRED_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"extract is missing columns {sorted(missing)}: {reader.fieldnames}")

        for line_no, row in enumerate(reader, start=2):  # header is line 1
            borough = row["borough"].strip().upper()
            if borough not in BOROUGHS:
                continue
            created = _parse_timestamp(row["created_date"], field="created_date", line_no=line_no)
            if created is None:
                raise ValueError(f"line {line_no}: created_date is required but blank")
            closed = _parse_timestamp(row["closed_date"], field="closed_date", line_no=line_no)
            records.append(
                Record(
                    created=created,
                    closed=closed,
                    complaint_type=row["complaint_type"].strip() or "UNSPECIFIED",
                    agency=row["agency"].strip() or "UNSPECIFIED",
                    borough=borough,
                    day=created.date(),
                )
            )

    validate_sampled_days(records)
    return records


def validate_sampled_days(records: list[Record]) -> None:
    """Every record must fall on one of the 37 fixed sample days — a violation
    means the extract does not match the sampling plan in SPEC.md."""
    expected = set(sampled_dates())
    stray = {r.day for r in records} - expected
    if stray:
        raise ValueError(
            f"{len(stray)} record day(s) fall outside the 37 sampled days: "
            f"{sorted(stray)[:5]}"
        )
