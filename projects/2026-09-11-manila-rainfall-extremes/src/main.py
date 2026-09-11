"""Print the rainfall-extremes report.

    python3 -m src.main --report

Every number the README and the deck quote is printed here, by the code that
computed it from the raw file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src import extremes, trend
from src.load import MIN_DAYS_PER_YEAR, WET_DAY_MM, Loaded, load_daily, default_raw_path

RULE = "=" * 78
THIN = "-" * 78


def _header(loaded: Loaded, threshold: float) -> None:
    records = loaded.records
    years = loaded.complete_years
    wet = extremes.wet_day_values(records)

    print(RULE)
    print("Are Metro Manila's heaviest rainfall days getting heavier?")
    print("ERA5 reanalysis via Open-Meteo — 14.6 N, 120.98 E")
    print(RULE)
    print()
    print("RECORD")
    print(f"  daily observations used : {len(records):,}")
    print(f"  null days dropped       : {len(loaded.dropped_nulls)}"
          + (f" ({', '.join(loaded.dropped_nulls[:3])})" if loaded.dropped_nulls else ""))
    print(f"  calendar years present  : {len(loaded.days_per_year)}")
    print(f"  complete years used     : {len(years)} ({years[0]}-{years[-1]})")

    excluded = loaded.excluded_years
    if excluded:
        detail = ", ".join(f"{y} ({n} days)" for y, n in excluded)
        print(f"  years excluded          : {len(excluded)} — {detail}")
        print(f"    (a year needs >= {MIN_DAYS_PER_YEAR} valid days to carry an annual statistic)")
    else:
        print(f"  years excluded          : none — every year has >= {MIN_DAYS_PER_YEAR} valid days")

    print()
    print("EXTREME THRESHOLD")
    print(f"  wet day                 : >= {WET_DAY_MM} mm")
    print(f"  wet days in record      : {len(wet):,} of {len(records):,} "
          f"({100 * len(wet) / len(records):.1f}%)")
    print(f"  R99p (99th pct wet day) : {threshold:.2f} mm")
    print(f"  base period             : {years[0]}-{years[-1]} (whole record)")
    print(f"  wettest day observed    : {max(r.mm for r in records):.1f} mm")


def _decade_table(rows: list[extremes.DecadeStats]) -> None:
    print()
    print("EXTREME DAYS BY DECADE")
    print("  A day counts as extreme if it beat the R99p threshold above.")
    print()
    print(f"  {'decade':<8}{'yrs':>5}{'days':>7}{'days/yr':>10}"
          f"{'mean mm':>10}{'max mm':>9}{'total mm/yr':>14}")
    print("  " + THIN[:74])
    for row in rows:
        print(f"  {row.label:<8}{row.years:>5}{row.exceedance_days:>7}"
              f"{row.days_per_year:>10.1f}{row.mean_intensity_mm:>10.1f}"
              f"{row.max_day_mm:>9.1f}{row.total_mm_per_year:>14.0f}")
    partial = [r for r in rows if r.years < 10]
    if partial:
        names = ", ".join(f"{r.label} ({r.years}y)" for r in partial)
        print(f"\n  Partial decades, compare per-year columns only: {names}")


def _trends(series: extremes.AnnualSeries) -> dict[str, tuple[trend.Trend, str]]:
    times = [float(y) for y in series.years]
    tests = {
        "Rx1day (wettest day of the year)": (series.rx1day, "mm"),
        "PRCPTOT (total annual rainfall)": (series.total_mm, "mm"),
        f"Wet days per year (>= {WET_DAY_MM:g} mm)": (series.wet_days, "days"),
        "Extreme days per year (> R99p)": (series.r99p_days, "days"),
    }

    print()
    print("TRENDS  (Mann-Kendall two-sided test, Theil-Sen slope)")
    print(f"  {len(series.years)} years, {series.years[0]}-{series.years[-1]}, "
          f"alpha = {trend.ALPHA}")
    print()

    # Units travel with each result: a wet-day count measured in mm would be a
    # quietly wrong number in the summary below.
    results: dict[str, tuple[trend.Trend, str]] = {}
    for label, (values, units) in tests.items():
        result = trend.analyse(times, values)
        results[label] = (result, units)
        print(f"  {label}")
        print(f"    tau = {result.tau:+.4f}   S = {result.s:+d}   "
              f"Z = {result.z:+.3f}   p = {result.p_value:.4f}")
        print(f"    Theil-Sen slope = {result.slope_per_decade:+.3f} {units}/decade")
        print(f"    -> {result.verdict(units)}")
        print()
    return results


def _conclusion(
    results: dict[str, tuple[trend.Trend, str]], rows: list[extremes.DecadeStats]
) -> None:
    rx1day = next(v for k, (v, _) in results.items() if k.startswith("Rx1day"))
    total = next(v for k, (v, _) in results.items() if k.startswith("PRCPTOT"))

    print(THIN)
    print("ANSWER")
    print(THIN)
    if rx1day.significant:
        print(f"  Yes, measurably. The wettest day of the year is {rx1day.direction} at")
        print(f"  {rx1day.slope_per_decade:+.2f} mm/decade (p = {rx1day.p_value:.4f}).")
    else:
        print("  Not on this evidence. The wettest day of the year shows no trend")
        print(f"  distinguishable from zero (p = {rx1day.p_value:.4f}, Theil-Sen "
              f"{rx1day.slope_per_decade:+.2f} mm/decade).")
        print("  That is a real result, not a failed one: 86 years of ERA5 at this")
        print("  grid point do not support the claim that peak days are intensifying.")

    print()
    significant = [k for k, (v, _) in results.items() if v.significant]
    if significant:
        print("  Indices that did move:")
        for key in significant:
            result, units = results[key]
            print(f"    - {key}: {result.verdict(units)}")
    else:
        print("  None of the four indices moved significantly at alpha = "
              f"{trend.ALPHA}.")

    if not rx1day.significant and total.significant:
        print()
        print("  Note the split: the annual total moved but the peak day did not.")

    first, last = rows[0], rows[-1]
    print()
    print(f"  Decadal endpoints: {first.label} {first.days_per_year:.1f} extreme days/yr "
          f"at {first.mean_intensity_mm:.1f} mm mean, "
          f"{last.label} {last.days_per_year:.1f} at {last.mean_intensity_mm:.1f} mm.")
    print("  Endpoint decades are partial where the year count says so; the trend")
    print("  tests above use every complete year and are the claim that counts.")

    print()
    print("  Caveat that bounds all of the above: ERA5 is a ~9-25 km reanalysis, not")
    print("  a gauge. It smooths convective peaks, so these are trends in the")
    print("  reanalysis at this grid point, not in what fell on Manila's streets.")
    print(RULE)


def run_report(path: Path) -> int:
    loaded = load_daily(path)
    threshold = extremes.r99p_threshold(loaded.records)
    years = loaded.complete_years

    _header(loaded, threshold)
    rows = extremes.by_decade(loaded.records, years, threshold)
    _decade_table(rows)
    series = extremes.annual_series(loaded.records, years, threshold)
    results = _trends(series)
    _conclusion(results, rows)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true", help="print the full report")
    parser.add_argument("--data", type=Path, default=None,
                        help="path to the raw Open-Meteo JSON")
    args = parser.parse_args(argv)

    path = args.data or default_raw_path()
    if not path.exists():
        print(f"FATAL: {path} not found. Run: python3 data/fetch_data.py", file=sys.stderr)
        return 2

    if not args.report:
        parser.print_help()
        return 0
    return run_report(path)


if __name__ == "__main__":
    sys.exit(main())
