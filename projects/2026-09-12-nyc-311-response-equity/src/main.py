"""Build the report and the headline chart.

    python3 -m src.main --report          full report to stdout, writes deck/borough_gap.svg
    python3 -m src.main --report --no-svg skip writing the chart
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

from . import chart
from .aggregate import common_basis, build_day_cells, totals_by_borough_type
from .bootstrap import DEFAULT_REPLICATES, bootstrap_intervals
from .dataset import BOROUGHS, Record, load_records
from .decompose import collapse_all, decompose
from .median import censored_share, report_median

SVG_PATH = Path(__file__).resolve().parent.parent / "deck" / "borough_gap.svg"
TOP_N_TYPES = 10


@dataclass(frozen=True)
class Analysis:
    records: list[Record]
    by_borough_count: dict[str, int]
    open_share: dict[str, float]
    decomps: list  # decompose.Decomposition, one per borough
    intervals: dict  # borough -> {"open"/"raw"/"standardized": bootstrap.Interval}
    totals: dict  # borough -> complaint_type -> aggregate.Cell
    basis: set[str]


def analyse(records: list[Record], replicates: int = DEFAULT_REPLICATES) -> Analysis:
    by_borough_count = {b: sum(1 for r in records if r.borough == b) for b in BOROUGHS}

    day_cells = build_day_cells(records)
    totals = totals_by_borough_type(day_cells)
    basis = common_basis(totals)
    collapsed = collapse_all(totals, basis)
    decomps = decompose(collapsed)

    open_share = {
        b: sum(c.open_ for c in totals[b].values()) / sum(c.n for c in totals[b].values())
        for b in BOROUGHS
    }
    point = {
        d.borough: {"open": open_share[d.borough], "raw": d.raw_rate, "standardized": d.standardized_rate}
        for d in decomps
    }
    intervals = bootstrap_intervals(day_cells, basis, point, replicates=replicates)

    return Analysis(records, by_borough_count, open_share, decomps, intervals, totals, basis)


def pct(value: float, places: int = 1) -> str:
    return f"{value * 100:.{places}f}%"


def rule(title: str) -> str:
    return f"\n{title}\n{'-' * len(title)}"


def population_section(a: Analysis) -> list[str]:
    out = [rule("POPULATION")]
    total = len(a.records)
    out.append("  311 requests created on 1 of the 37 sampled days of 2025, 5-borough only")
    out.append("")
    out.append("  borough           sampled requests")
    for b in BOROUGHS:
        out.append(f"    {b:<15}{a.by_borough_count[b]:>10,}")
    out.append(f"    {'TOTAL':<15}{total:>10,}")

    check = sum(a.by_borough_count.values())
    if check != total:
        raise AssertionError(f"borough counts sum to {check}, population is {total}")
    out.append(f"\n  Borough counts sum exactly to the population total ({check:,}). OK")
    return out


def borough_rate_section(a: Analysis) -> list[str]:
    out = [rule("72-HOUR CLOSURE RATE, RAW vs. MIX-STANDARDISED (95% cluster-bootstrap CI)")]
    out.append("  borough           n       open (95% CI)              raw 72h (95% CI)"
               "              standardised 72h (95% CI)")
    for d in a.decomps:
        iv = a.intervals[d.borough]
        out.append(
            f"    {d.borough:<15}{d.n:>7,}   {pct(a.open_share[d.borough]):>6} "
            f"({pct(iv['open'].lo)}-{pct(iv['open'].hi)})"
            f"       {pct(d.raw_rate):>6} ({pct(iv['raw'].lo)}-{pct(iv['raw'].hi)})"
            f"          {pct(d.standardized_rate):>6} ({pct(iv['standardized'].lo)}-{pct(iv['standardized'].hi)})"
        )
    return out


def decomposition_section(a: Analysis) -> tuple[list[str], float]:
    out = [rule("DECOMPOSITION: raw_rate - citywide_rate = mix_effect + speed_effect")]
    out.append(f"  citywide rate: {pct(a.decomps[0].citywide_rate)}")
    out.append("")
    out.append("  borough           gap       mix_effect   speed_effect   check")
    max_error = 0.0
    for d in a.decomps:
        max_error = max(max_error, abs(d.identity_error))
        out.append(
            f"    {d.borough:<15}{d.gap:>+7.3%}   {d.mix_effect:>+10.3%}   "
            f"{d.speed_effect:>+11.3%}   {'OK' if abs(d.identity_error) < 1e-9 else 'FAIL'}"
        )
    if max_error >= 1e-9:
        raise AssertionError(f"decomposition identity failed: max error {max_error!r}")
    out.append(f"\n  Identity holds for every borough (max |error| = {max_error:.2e} < 1e-9). OK")
    return out, max_error


def common_basis_section(a: Analysis) -> list[str]:
    out = [rule("COMMON BASIS: complaint types with >=100 requests in every borough")]
    total_population = len(a.records)
    covered = sum(a.totals[b][t].n for b in BOROUGHS for t in a.basis)
    out.append(f"  {len(a.basis)} complaint types qualify, covering "
               f"{covered:,}/{total_population:,} requests ({pct(covered / total_population)})")
    out.append("")
    ranked = sorted(a.basis, key=lambda t: sum(a.totals[b][t].n for b in BOROUGHS), reverse=True)
    top = ranked[:TOP_N_TYPES]
    out.append("  10 largest common-basis types, 72h closure rate by borough:")
    header = "    " + f"{'complaint type':<28}" + "".join(f"{b[:4]:>10}" for b in BOROUGHS) + f"{'spread':>10}"
    out.append(header)
    for t in top:
        rates = {b: (a.totals[b][t].closed72 / a.totals[b][t].n if a.totals[b][t].n else 0.0) for b in BOROUGHS}
        spread = max(rates.values()) - min(rates.values())
        row = "    " + f"{t[:28]:<28}" + "".join(f"{pct(rates[b]):>10}" for b in BOROUGHS) + f"{pct(spread):>10}"
        out.append(row)
    return out


def median_section(a: Analysis) -> list[str]:
    out = [rule("TYPICAL TIME TO CLOSE (weighted median hours; censored share per cell)")]
    out.append(f"  {'borough':<15}{'median':>10}{'censored':>12}")
    for b in BOROUGHS:
        pairs = [
            (r.hours_to_close if r.hours_to_close is not None else math.inf, 1)
            for r in a.records if r.borough == b
        ]
        out.append(f"  {b:<15}{report_median(pairs):>10}{pct(censored_share(pairs)):>12}")
    return out


def report(a: Analysis) -> str:
    lines = [
        "NYC 311 RESPONSE EQUITY -- does the borough gap survive a like-for-like comparison?",
        f"{len(a.records):,} requests across {len({r.day for r in a.records})} sampled days of 2025",
    ]
    lines += population_section(a)
    lines += borough_rate_section(a)
    decomp_lines, _ = decomposition_section(a)
    lines += decomp_lines
    lines += common_basis_section(a)
    lines += median_section(a)
    return "\n".join(lines)


def write_chart(a: Analysis) -> None:
    bars = []
    for d in a.decomps:
        iv = a.intervals[d.borough]
        bars.append({
            "name": d.borough, "raw": d.raw_rate, "raw_lo": iv["raw"].lo, "raw_hi": iv["raw"].hi,
            "std": d.standardized_rate, "std_lo": iv["standardized"].lo, "std_hi": iv["standardized"].hi,
        })
    svg = chart.render_borough_bars(
        bars, a.decomps[0].citywide_rate,
        f"{len(a.records):,} 311 requests, 37 sampled days of 2025 (SPEC.md); "
        f"whiskers are 95% cluster-bootstrap intervals",
    )
    SVG_PATH.parent.mkdir(parents=True, exist_ok=True)
    SVG_PATH.write_text(svg, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true", help="print the full report")
    parser.add_argument("--no-svg", action="store_true", help="do not write the chart")
    parser.add_argument("--replicates", type=int, default=DEFAULT_REPLICATES)
    args = parser.parse_args(argv)
    if not args.report:
        parser.print_help()
        return 2

    records = load_records()
    a = analyse(records, replicates=args.replicates)
    print(report(a))
    if not args.no_svg:
        write_chart(a)
        print(f"\nWrote {SVG_PATH.relative_to(SVG_PATH.parents[1])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
