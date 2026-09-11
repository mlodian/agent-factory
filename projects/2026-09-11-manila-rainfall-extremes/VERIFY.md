# Verification

STATUS: PASSED
Date:   2026-09-11T10:10:52Z
Python: Python 3.12.14
Env:    clean venv (built by scripts/verify.sh, nothing preinstalled)
Command: `bash scripts/verify.sh 2026-09-11-manila-rainfall-extremes`
Attempts: 1 (passed first run)

## verify.sh output

```
==> verifying projects/2026-09-11-manila-rainfall-extremes in a clean venv
==============================================================================
1/4  Environment
==============================================================================
Python 3.12.14
deps installed: iniconfig==2.3.0 packaging==26.3 pluggy==1.6.0 pytest==8.3.3

==============================================================================
2/4  Data provenance
==============================================================================
Source: https://archive-api.open-meteo.com/v1/archive?latitude=14.6&longitude=120.98&start_date=1940-01-01&end_date=2025-12-31&daily=precipitation_sum&timezone=Asia%2FManila
UA    : agent-factory/1.0

Cached  : data/raw/manila_precip_1940_2025.json
  SHA256       : 58395218e52271fd666c13f89deac258850a1fa316c214cbd708b70cc1fb5670 (matches SOURCE.md — skipping download)
  Content SHA256: 7621a5cc26ad35393f78acbd99a519f642d8d7a536b3cfd392eb86d910eaaed5
  records      : 31412 daily observations
  range        : 1940-01-01 .. 2025-12-31
  nulls        : 1
  max mm/day   : 226.7
  mean mm/day  : 4.252
  elevation    : 12.0 m, tz Asia/Manila

==============================================================================
3/4  Tests
==============================================================================
..................................                                       [100%]
34 passed in 0.06s

==============================================================================
4/4  Analysis on the real record
==============================================================================
==============================================================================
Are Metro Manila's heaviest rainfall days getting heavier?
ERA5 reanalysis via Open-Meteo — 14.6 N, 120.98 E
==============================================================================

RECORD
  daily observations used : 31,411
  null days dropped       : 1 (1940-01-01)
  calendar years present  : 86
  complete years used     : 86 (1940-2025)
  years excluded          : none — every year has >= 360 valid days

EXTREME THRESHOLD
  wet day                 : >= 1.0 mm
  wet days in record      : 14,178 of 31,411 (45.1%)
  R99p (99th pct wet day) : 67.01 mm
  base period             : 1940-2025 (whole record)
  wettest day observed    : 226.7 mm

EXTREME DAYS BY DECADE
  A day counts as extreme if it beat the R99p threshold above.

  decade    yrs   days   days/yr   mean mm   max mm   total mm/yr
  --------------------------------------------------------------------------
  1940s      10     19       1.9      83.2    117.8          1656
  1950s      10     11       1.1     106.3    209.2          1246
  1960s      10      8       0.8     121.2    204.8          1033
  1970s      10     32       3.2      98.6    226.7          1647
  1980s      10     12       1.2     104.4    216.6          1449
  1990s      10     15       1.5     102.1    175.9          1506
  2000s      10     18       1.8      95.2    189.4          1577
  2010s      10     16       1.6      95.6    220.3          1864
  2020s       6     11       1.8     106.2    178.4          2294

  Partial decades, compare per-year columns only: 2020s (6y)

TRENDS  (Mann-Kendall two-sided test, Theil-Sen slope)
  86 years, 1940-2025, alpha = 0.05

  Rx1day (wettest day of the year)
    tau = +0.0572   S = +209   Z = +0.776   p = 0.4379
    Theil-Sen slope = +1.400 mm/decade
    -> no detectable trend (p = 0.4379, not < 0.05); the Theil-Sen slope is +1.40 mm/decade but it is not distinguishable from zero

  PRCPTOT (total annual rainfall)
    tau = +0.2963   S = +1083   Z = +4.036   p = 0.0001
    Theil-Sen slope = +78.604 mm/decade
    -> rising at +78.60 mm/decade (p = 0.0001 < 0.05)

  Wet days per year (>= 1 mm)
    tau = +0.1937   S = +708   Z = +2.638   p = 0.0083
    Theil-Sen slope = +4.118 days/decade
    -> rising at +4.12 days/decade (p = 0.0083 < 0.05)

  Extreme days per year (> R99p)
    tau = +0.0509   S = +186   Z = +0.710   p = 0.4777
    Theil-Sen slope = +0.000 days/decade
    -> no detectable trend (p = 0.4777, not < 0.05); the Theil-Sen slope is +0.00 days/decade but it is not distinguishable from zero

------------------------------------------------------------------------------
ANSWER
------------------------------------------------------------------------------
  Not on this evidence. The wettest day of the year shows no trend
  distinguishable from zero (p = 0.4379, Theil-Sen +1.40 mm/decade).
  That is a real result, not a failed one: 86 years of ERA5 at this
  grid point do not support the claim that peak days are intensifying.

  Indices that did move:
    - PRCPTOT (total annual rainfall): rising at +78.60 mm/decade (p = 0.0001 < 0.05)
    - Wet days per year (>= 1 mm): rising at +4.12 days/decade (p = 0.0083 < 0.05)

  Note the split: the annual total moved but the peak day did not.

  Decadal endpoints: 1940s 1.9 extreme days/yr at 83.2 mm mean, 2020s 1.8 at 106.2 mm.
  Endpoint decades are partial where the year count says so; the trend
  tests above use every complete year and are the claim that counts.

  Caveat that bounds all of the above: ERA5 is a ~9-25 km reanalysis, not
  a gauge. It smooths convective peaks, so these are trends in the
  reanalysis at this grid point, not in what fell on Manila's streets.
==============================================================================

verify.sh: OK
==> finished in 3s with exit code 0
```

## Provenance gate

```
$ python3 scripts/check_provenance.py 2026-09-11-manila-rainfall-extremes --data-only

## Provenance check: PASSED

Project: `2026-09-11-manila-rainfall-extremes`

- ✅ **provenance** — source `open-meteo` is registered (CC BY 4.0, free for non-commercial)
- ✅ **provenance** — `raw/manila_precip_1940_2025.json` checksum matches and content parses as data
- ✅ **provenance** — cited URL is live (HTTP 200)
- ✅ **fabrication** — no synthetic-data generators outside tests/
```

## Headline numbers

Every figure below was printed by the run above.

- Records processed: 31,412 daily observations; 31,411 used, 1 null dropped (1940-01-01)
- Date range: 1940-01-01 .. 2025-12-31, 86 calendar years, 0 excluded
- Wet days (>= 1 mm): 14,178 of 31,411 (45.1%)
- R99p threshold: 67.01 mm
- Wettest day in the record: 226.7 mm
- **Rx1day trend: tau = +0.0572, p = 0.4379 — NOT significant** (Theil-Sen +1.400 mm/decade)
- **Extreme days/yr trend: tau = +0.0509, p = 0.4777 — NOT significant** (Theil-Sen +0.000 days/decade)
- **PRCPTOT trend: tau = +0.2963, p = 0.0001 — significant** (Theil-Sen +78.604 mm/decade)
- **Wet days/yr trend: tau = +0.1937, p = 0.0083 — significant** (Theil-Sen +4.118 days/decade)
- Decadal extreme-day rate: 1940s 1.9/yr at 83.2 mm mean; 2020s 1.8/yr at 106.2 mm mean
- Decadal total rainfall: 1960s 1033 mm/yr, low; 2020s 2294 mm/yr, high
- Tests: 34 passed in 0.06s
- Runtime: 3s total in a clean venv (including venv build and pip install)

## Data integrity

- SHA256 re-check: **MATCH** — `58395218e52271fd666c13f89deac258850a1fa316c214cbd708b70cc1fb5670`,
  identical to `data/SOURCE.md`. `fetch_data.py` took the cache path and skipped the download.
- Content SHA256: `7621a5cc26ad35393f78acbd99a519f642d8d7a536b3cfd392eb86d910eaaed5`,
  stable across all five fetches made on 2026-09-11.
- Two forced re-downloads (`--force`) returned bodies differing in byte length
  (569,462 vs the stored 569,463) but carrying an identical content hash, and the
  stored file was correctly left in place.

## Repairs made

None were needed for verification — `verify.sh` exited 0 on the first attempt. Two
defects were found and fixed during the build phase, before verification ran:

1. **Wrong units in the summary block.** `Trend.verdict()` defaults to `"mm"`, and
   `_conclusion()` called it with no argument, so the wet-day-count result printed as
   `+4.12 mm/decade` when it is `+4.12 days/decade`. Units are now carried alongside each
   result and passed explicitly. The number was right; the label was wrong.
2. **`.slug` held the wrong identifier.** It was written as `manila-rainfall-extremes`,
   but `scripts/verify.sh` and `scripts/check_provenance.py` both resolve `projects/$slug`
   and `.github/workflows/daily-project.yml` validates the value against
   `^[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9-]{3,60}$`. The undated form would have failed the
   workflow's own check and aborted the run. It now reads
   `2026-09-11-manila-rainfall-extremes`.

## Known weaknesses

Look at these closely — several bear directly on how much the headline result is worth.

1. **The significant PRCPTOT trend is probably not all climate.** Decadal mean rainfall
   runs 1033 mm/yr in the 1960s to 2294 mm/yr in the 2020s — a 2.2x change. A genuine
   precipitation increase of that size over 60 years would be extraordinary. The more
   likely explanation is inhomogeneity in ERA5: the 1940-1978 back-extension assimilates
   far fewer observations than the satellite era, and reanalysis precipitation is known to
   drift as the observing system changes underneath it. **This project does not test for
   that inhomogeneity, so the `p = 0.0001` should not be read as a confident claim about
   Manila's climate.** It is a confident claim about the ERA5 series, which is a weaker
   thing. A breakpoint test at 1979 is the obvious next step and is not implemented.

2. **The 1970s are anomalous and unexplained.** 32 extreme days in that decade against 8
   in the 1960s — a 4x swing between adjacent decades that no physical mechanism
   comfortably explains. Same concern as above.

3. **The Rx1day null result is "not detected", not "not there".** No power analysis was
   run, so the size of trend this test could have detected at n = 86 is unknown. Annual
   maxima are heavy-tailed and the interannual spread is large, so a real but modest
   intensification could sit inside the noise. The honest claim is the one the report
   makes: the data do not support the claim. That is not the same as refuting it.

4. **The `+0.000 days/decade` Theil-Sen slope is a tie artifact, not a measurement.**
   Extreme days per year are small integers (mostly 0, 1, 2, 3), so the majority of
   pairwise slopes are exactly zero and their median is exactly zero. The number is
   arithmetically correct and practically uninformative; the tau and p-value are the
   meaningful outputs for that index. `test_ties_reduce_variance_and_p_stays_valid` covers
   the variance correction but nothing asserts on this degenerate-slope behaviour.

5. **Whole-record base period.** R99p is computed over 1940-2025 rather than a fixed
   1961-1990 WMO baseline, so the threshold is not independent of the years being tested,
   and these numbers are not directly comparable to published ETCCDI work.

6. **One grid point stands in for a metro of 13 million.** 14.6 N, 120.98 E, elevation
   12 m. No spatial averaging, no sensitivity check against a neighbouring cell.

7. **ERA5 underestimates the tail.** The record maximum of 226.7 mm/day is far below the
   ~455 mm the Port Area gauge recorded during Ondoy on 2009-09-26. Anyone reading these
   as gauge values will be misled, which is why the report prints the caveat itself.

8. **No test exercises `src/main.py` end to end.** The 34 tests cover `load`, `trend`, and
   `extremes`; the report assembly and formatting are only covered by `verify.sh` running
   it for real and exiting 0. A formatting regression that did not raise would pass.
