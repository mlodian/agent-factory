# Architecture

## Data flow

```
Open-Meteo archive API  (ERA5 reanalysis, 14.6 N / 120.98 E)
        │
        │  data/fetch_data.py  — one GET, shape validation, two checksums
        ▼
data/raw/manila_precip_1940_2025.json      569,463 bytes, verbatim server bytes
        │
        │  src/load.py  — parse, drop nulls, decide which years are complete
        ▼
list[Daily]  (date, mm)                    31,411 records across 86 years
        │
        ├── src/extremes.py  — R99p threshold, per-year indices, per-decade table
        │           │
        │           ▼
        │   AnnualSeries(rx1day, total_mm, wet_days, r99p_days) + list[DecadeStats]
        │           │
        ├── src/trend.py  — Mann-Kendall S/tau/Z/p, Theil-Sen slope
        │           │
        ▼           ▼
   src/main.py  — formats the report, prints the answer and its caveats
```

Five modules, each with one job, and no shared mutable state. Every function takes its
inputs and returns a value; the only I/O is the fetch in `data/fetch_data.py`, the file
read in `src/load.py`, and the printing in `src/main.py`. That is why the tests need no
mocks and no network.

## Decisions, and what they cost

### No dependencies beyond pytest

`requirements.txt` pins `pytest==8.3.3` and nothing else. Mann-Kendall, Theil-Sen, and the
linear-interpolation percentile are about 40 lines of `src/trend.py` and `src/extremes.py`
between them, against `json`, `math`, `statistics`, `collections`, `dataclasses` and
`datetime` from the standard library.

*Trade-off:* pulling in scipy would have given `scipy.stats.kendalltau` and
`scipy.stats.theilslopes` as one-liners that are better tested than mine. Writing them out
means the variance-with-ties correction and the continuity correction are my bugs to own —
which is why `tests/test_trend.py` checks them against series whose answers are known in
advance, including a flat series (p must be 1.0), a sawtooth (must not fire), and the
normal-tail identity `erfc(|z|/√2) == 2(1 − Φ(|z|))`. The payoff is a verify run that
installs four small wheels and finishes in 3 seconds.

### Rank-based statistics, not least squares

Annual maximum rainfall is skewed and heavy-tailed. A single typhoon year can swing an OLS
slope, and the OLS t-test assumes a normality this data does not have. Mann-Kendall asks
only whether later values tend to exceed earlier ones, and Theil-Sen takes the median of
pairwise slopes, tolerating roughly 29% outliers.

This is asserted rather than assumed: `test_one_outlier_does_not_swing_theil_sen` plants a
10,000 mm freak year in a flat series, checks Theil-Sen still returns exactly 0.0, and
computes the OLS slope on the same input to show it is dragged past 10.0.

*Trade-off:* Theil-Sen degenerates on small-integer series. Extreme days per year are
mostly 0–3, so most pairwise slopes are exactly zero and the median is exactly zero — the
`+0.000 days/decade` in the report is a tie artifact, not a measurement. The tau and
p-value remain meaningful. This is called out in `VERIFY.md` and the README rather than
being quietly presented as a result.

### Drop gaps, never fill them

`src/load.py` drops null days, records their dates in `Loaded.dropped_nulls`, and counts
valid days per year. A year needs `MIN_DAYS_PER_YEAR = 360` valid observations to carry an
annual statistic; short years land in `excluded_years` and the report names them.

Interpolating a missing day would be easy and would make the series look better behaved
than it is — a filled gap in a rainfall record is a fabricated zero most of the time, and
zeros drag the annual maximum and the wet-day count in opposite directions.
`test_year_of_all_nulls_is_excluded_not_invisible` guards the subtle case: `parse_payload`
seeds `days_per_year` from every date it sees, before the null check, so a year whose
observations are all null is reported as excluded with 0 days rather than disappearing.
Counting years from the surviving records instead would have made such a year invisible —
which reads identically to a year that was never requested. On this dataset nothing is excluded
— all 86 years clear 360 days — but the guard is what lets the report say "none" honestly
instead of not looking.

### Two checksums

Open-Meteo stamps `generationtime_ms` into every response, so the same data downloads to a
different SHA256 each time — measured across five fetches on 2026-09-11, bodies ran
569,461 to 569,463 bytes. A file checksum alone therefore cannot answer "has the data
changed?".

`data/fetch_data.py` keeps both: `SHA256` over the bytes on disk, which
`scripts/check_provenance.py` verifies to prove the committed file is the one that was
analysed, and `content_sha256()` over a canonical dump of the `time` and
`precipitation_sum` arrays, which changes only when the measurements do. When a
re-download carries an unchanged content hash the script **leaves the existing file
alone**, so the declared `SHA256` stays valid. It overwrites only on a genuine change, and
prints a loud warning when it does.

*Trade-off:* the raw file is now slightly stale by construction — it holds the
`generationtime_ms` of the first fetch forever. That is the right way round: the raw file
is provenance, and provenance should be the bytes that were actually analysed.

### Validate the body, not just the status code

`validate()` in `data/fetch_data.py` parses the JSON, checks for the `daily` block and both
arrays, checks they are the same length, checks the record count against
`MIN_EXPECTED_DAYS = 31_000`, and checks that not every value is null. A 200 response is
not proof of success — APIs serve HTML error pages and bot challenges under 200, and a
client that doesn't follow redirects saves the redirect page. There is no fallback or
sample-data path anywhere in the file; on a bad response it raises `SystemExit`.

### Whole-record base period for R99p

The extreme threshold is the 99th percentile of wet days across 1940–2025, rather than the
WMO 1961–1990 baseline. A whole-record base keeps every year measured against one fixed
number.

*Trade-off:* the threshold is not independent of the years being tested, and the figures
are not directly comparable to published ETCCDI work. `extremes.py` documents the choice at
module level and `main.py` prints the base period next to the threshold so it can never be
read as the WMO one by accident.

### The report explains its own limits

`_conclusion()` in `src/main.py` prints the ERA5 caveat as part of the output, not as a
footnote someone might not reach. When the headline result is a null, the surrounding text
says why a null is a real answer. The formatting branches on significance, so the phrasing
can't drift out of sync with the numbers.

## What I'd change with more time

1. **A breakpoint test at 1979.** This is the biggest gap. The significant +78.604
   mm/decade PRCPTOT trend is the number most likely to be an ERA5 inhomogeneity artifact
   rather than climate, and a Pettitt test or a simple pre/post-1979 split would say a
   great deal about how much of it to believe. Right now the project flags the suspicion
   without testing it.
2. **A power analysis for the Rx1day null.** Without one, "no detectable trend" carries no
   information about how large a trend could have hidden. A bootstrap over the observed
   interannual spread would put a number on the minimum detectable effect.
3. **Several grid points.** Fetching four or five cells across the metro and comparing
   would show whether the result is a property of Manila or of one cell.
4. **Gauge comparison for the overlap period.** Any PAGASA station series covering even
   20 years would let the ERA5 tail bias be quantified instead of asserted.
5. **An end-to-end test of `src/main.py`.** Currently only `verify.sh` exercises the report
   path, and only by exit code. A golden-output test over a small fixture payload would
   catch formatting regressions.
6. **Water years instead of calendar years,** or at least a sensitivity check, to confirm
   the December/January split doesn't matter as much as it appears not to.
