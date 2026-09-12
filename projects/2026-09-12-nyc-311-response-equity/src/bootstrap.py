"""Cluster bootstrap over the 37 sampled days.

Complaints within a day are correlated — a single sampled Tuesday, a single cold
snap — so resampling individual complaints would understate the uncertainty.
Instead each replicate resamples the 37 *days* with replacement and recomputes every
rate from day-level `Cell` aggregates; no individual record is touched again after
`aggregate.build_day_cells`, which is what keeps a few thousand replicates fast in
plain Python.

Seeded and deterministic: the same seed always produces the same intervals.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date

from .aggregate import Cell, DayCells
from .decompose import OTHER, collapse_to_basis, decompose
from .dataset import BOROUGHS

SEED = 20250912
DEFAULT_REPLICATES = 2000


@dataclass(frozen=True)
class Interval:
    point: float
    lo: float
    hi: float


def _sum_cells(draw: list[date], per_day: dict, borough: str, ctype: str) -> Cell:
    total = Cell()
    for day in draw:
        total.add(per_day[day][borough][ctype])
    return total


def _percentile(sorted_values: list[float], p: float) -> float:
    n = len(sorted_values)
    idx = (p / 100) * (n - 1)
    lo_i, hi_i = int(idx), min(int(idx) + 1, n - 1)
    frac = idx - lo_i
    return sorted_values[lo_i] + frac * (sorted_values[hi_i] - sorted_values[lo_i])


def bootstrap_intervals(
    day_cells: DayCells,
    basis: set[str],
    point: dict[str, dict[str, float]],
    replicates: int = DEFAULT_REPLICATES,
    seed: int = SEED,
) -> dict[str, dict[str, Interval]]:
    """Returns, per borough: {"open": Interval, "raw": Interval, "standardized": Interval}.

    `point[borough]` supplies the point estimates (from the full, unresampled data,
    e.g. `{"open": ..., "raw": ..., "standardized": ...}`) that each Interval is
    centred on for reporting — the bootstrap only ever estimates the spread.
    """
    rng = random.Random(seed)
    days = sorted(day_cells)
    n_days = len(days)
    per_day = {
        day: {b: collapse_to_basis(by_borough.get(b, {}), basis) for b in BOROUGHS}
        for day, by_borough in day_cells.items()
    }
    types = sorted(basis | {OTHER})

    raw_samples: dict[str, list[float]] = {b: [] for b in BOROUGHS}
    std_samples: dict[str, list[float]] = {b: [] for b in BOROUGHS}
    open_samples: dict[str, list[float]] = {b: [] for b in BOROUGHS}

    for _ in range(replicates):
        draw = [days[rng.randrange(n_days)] for _ in range(n_days)]
        collapsed = {b: {t: _sum_cells(draw, per_day, b, t) for t in types} for b in BOROUGHS}
        for d in decompose(collapsed):
            raw_samples[d.borough].append(d.raw_rate)
            std_samples[d.borough].append(d.standardized_rate)
            cells = collapsed[d.borough].values()
            n = sum(c.n for c in cells)
            opened = sum(c.open_ for c in cells)
            open_samples[d.borough].append(opened / n if n else 0.0)

    out: dict[str, dict[str, Interval]] = {}
    for b in BOROUGHS:
        out[b] = {}
        for name, samples in (("open", open_samples[b]), ("raw", raw_samples[b]),
                              ("standardized", std_samples[b])):
            xs = sorted(samples)
            out[b][name] = Interval(point[b][name], _percentile(xs, 2.5), _percentile(xs, 97.5))
    return out
