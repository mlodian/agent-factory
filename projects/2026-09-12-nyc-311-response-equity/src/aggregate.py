"""Per-day, per-borough, per-complaint-type counts the rest of the analysis is built on.

Everything downstream — the raw rate, the mix standardisation, and the cluster
bootstrap — is a sum over these small integer cells, never a re-scan of the
individual records. That's what keeps a few thousand bootstrap replicates fast.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from .dataset import BOROUGHS, Record

MIN_COMMON_COUNT = 100


@dataclass
class Cell:
    n: int = 0
    closed72: int = 0
    open_: int = 0

    def add(self, other: "Cell") -> None:
        self.n += other.n
        self.closed72 += other.closed72
        self.open_ += other.open_


DayCells = dict[date, dict[str, dict[str, Cell]]]


def build_day_cells(records: list[Record]) -> DayCells:
    """day -> borough -> complaint_type -> Cell."""
    table: DayCells = defaultdict(lambda: defaultdict(lambda: defaultdict(Cell)))
    for r in records:
        cell = table[r.day][r.borough][r.complaint_type]
        cell.n += 1
        if r.is_open:
            cell.open_ += 1
        elif r.closed_within_window:
            cell.closed72 += 1
    return table


def totals_by_borough_type(day_cells: DayCells) -> dict[str, dict[str, Cell]]:
    """Collapse the day axis: borough -> complaint_type -> Cell, summed over all days."""
    out: dict[str, dict[str, Cell]] = defaultdict(lambda: defaultdict(Cell))
    for by_borough in day_cells.values():
        for borough, by_type in by_borough.items():
            for ctype, cell in by_type.items():
                out[borough][ctype].add(cell)
    return out


def common_basis(totals: dict[str, dict[str, Cell]], min_count: int = MIN_COMMON_COUNT) -> set[str]:
    """Complaint types with >= `min_count` sampled requests in *every* borough."""
    per_borough_sets = []
    for borough in BOROUGHS:
        by_type = totals.get(borough, {})
        per_borough_sets.append({t for t, c in by_type.items() if c.n >= min_count})
    return set.intersection(*per_borough_sets) if per_borough_sets else set()
