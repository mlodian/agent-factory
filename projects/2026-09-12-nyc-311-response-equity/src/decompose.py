"""Complaint-mix standardisation and the raw / mix / speed decomposition.

    raw_rate(b)          = borough b's actual share closed inside 72h
    citywide_rate        = the same, city-wide
    standardized_rate(b) = borough b's own per-type speed, applied to the citywide mix
    mix_effect(b)        = (borough's mix - citywide mix), weighted by borough's own speed
    speed_effect(b)      = standardized_rate(b) - citywide_rate

By construction (see the algebra in tests/test_decompose.py):

    raw_rate(b) - citywide_rate == mix_effect(b) + speed_effect(b)

Standardisation needs a per-type rate that is defined for *every* borough, which is
exactly what `common_basis()` guarantees for the types in it. Complaint types outside
that basis (too rare in at least one borough to estimate a stable rate) are folded
into a single `OTHER` bucket per borough, so `basis | {OTHER}` still partitions every
borough's population exactly and the identity above holds for every borough, always.
"""

from __future__ import annotations

from dataclasses import dataclass

from .aggregate import Cell
from .dataset import BOROUGHS

OTHER = "OTHER"


def collapse_to_basis(
    by_type: dict[str, Cell], basis: set[str]
) -> dict[str, Cell]:
    """Re-key one borough's per-type cells onto `basis | {OTHER}`."""
    merged: dict[str, Cell] = {t: Cell() for t in basis}
    merged[OTHER] = Cell()
    for t, cell in by_type.items():
        dst = merged[t] if t in basis else merged[OTHER]
        dst.add(cell)
    return merged


def collapse_all(
    totals: dict[str, dict[str, Cell]], basis: set[str]
) -> dict[str, dict[str, Cell]]:
    return {b: collapse_to_basis(totals.get(b, {}), basis) for b in BOROUGHS}


def _rate(cell: Cell) -> float:
    return cell.closed72 / cell.n if cell.n else 0.0


@dataclass(frozen=True)
class Decomposition:
    borough: str
    n: int
    raw_rate: float
    standardized_rate: float
    citywide_rate: float
    mix_effect: float
    speed_effect: float

    @property
    def gap(self) -> float:
        return self.raw_rate - self.citywide_rate

    @property
    def identity_error(self) -> float:
        return self.gap - (self.mix_effect + self.speed_effect)


def decompose(collapsed: dict[str, dict[str, Cell]]) -> list[Decomposition]:
    """`collapsed`: borough -> type -> Cell, where every borough shares the same
    key set (typically `basis | {OTHER}`, produced by `collapse_all`)."""
    types = sorted(next(iter(collapsed.values())).keys())

    city_by_type = {t: Cell() for t in types}
    for by_type in collapsed.values():
        for t, cell in by_type.items():
            city_by_type[t].add(cell)
    city_total_n = sum(c.n for c in city_by_type.values())
    if city_total_n == 0:
        raise ValueError("no records to decompose")
    citywide_rate = sum(c.closed72 for c in city_by_type.values()) / city_total_n
    city_weight = {t: city_by_type[t].n / city_total_n for t in types}
    city_rate = {t: _rate(city_by_type[t]) for t in types}

    results = []
    for b in BOROUGHS:
        by_type = collapsed[b]
        n_b = sum(c.n for c in by_type.values())
        raw_rate = sum(c.closed72 for c in by_type.values()) / n_b if n_b else 0.0
        borough_weight = {t: (by_type[t].n / n_b if n_b else 0.0) for t in types}
        # A type a borough never saw has no borough-specific rate to speak of; its
        # weight there is 0, so whatever we substitute cannot move raw_rate or
        # standardized_rate. Falling back to the citywide rate keeps every quantity
        # finite without touching the decomposition identity.
        borough_rate = {t: (_rate(by_type[t]) if by_type[t].n else city_rate[t]) for t in types}
        standardized_rate = sum(city_weight[t] * borough_rate[t] for t in types)
        mix_effect = sum((borough_weight[t] - city_weight[t]) * borough_rate[t] for t in types)
        speed_effect = standardized_rate - citywide_rate
        results.append(
            Decomposition(b, n_b, raw_rate, standardized_rate, citywide_rate, mix_effect, speed_effect)
        )
    return results
