from datetime import date, timedelta

from src.aggregate import Cell
from src.bootstrap import bootstrap_intervals
from src.dataset import BOROUGHS


def _synthetic_day_cells(n_days=10):
    """Every day looks similar (small random-ish variation via the day index), so
    the point estimate should sit comfortably inside its own bootstrap interval."""
    day_cells = {}
    base = date(2025, 1, 1)
    for i in range(n_days):
        day = base + timedelta(days=i)
        day_cells[day] = {
            b: {
                "NOISE": Cell(n=20 + i, closed72=15 + (i % 3)),
                "HEAT": Cell(n=10, closed72=2),
            }
            for b in BOROUGHS
        }
    return day_cells


def _point_estimate(borough_cells):
    n = sum(c.n for c in borough_cells.values())
    closed = sum(c.closed72 for c in borough_cells.values())
    open_ = sum(c.open_ for c in borough_cells.values())
    return n, closed, open_


def test_bootstrap_interval_contains_the_point_estimate():
    day_cells = _synthetic_day_cells()
    basis = {"NOISE", "HEAT"}

    totals = {b: {"NOISE": Cell(), "HEAT": Cell()} for b in BOROUGHS}
    for by_borough in day_cells.values():
        for b, by_type in by_borough.items():
            for t, cell in by_type.items():
                totals[b][t].add(cell)

    point = {}
    for b in BOROUGHS:
        n, closed, open_ = _point_estimate(totals[b])
        point[b] = {"open": open_ / n, "raw": closed / n, "standardized": closed / n}

    intervals = bootstrap_intervals(day_cells, basis, point, replicates=300, seed=1)

    for b in BOROUGHS:
        for key in ("open", "raw", "standardized"):
            iv = intervals[b][key]
            assert iv.lo <= iv.point <= iv.hi


def test_bootstrap_is_deterministic_for_a_fixed_seed():
    day_cells = _synthetic_day_cells()
    basis = {"NOISE", "HEAT"}
    point = {b: {"open": 0.0, "raw": 0.75, "standardized": 0.75} for b in BOROUGHS}

    first = bootstrap_intervals(day_cells, basis, point, replicates=200, seed=42)
    second = bootstrap_intervals(day_cells, basis, point, replicates=200, seed=42)

    for b in BOROUGHS:
        assert first[b]["raw"].lo == second[b]["raw"].lo
        assert first[b]["raw"].hi == second[b]["raw"].hi
