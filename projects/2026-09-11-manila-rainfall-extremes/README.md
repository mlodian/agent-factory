# Are Metro Manila's heaviest rainfall days getting heavier?

Eighty-six years of daily rainfall over Metro Manila, put through two rank-based trend
tests — with a null result as the headline.

"Extreme rainfall is intensifying" is one of those claims everyone has heard and few have
checked against a specific place. This project checks it for one point over Manila, using
the longest daily record available without credentials, and reports what the test actually
says rather than what the framing invites. The answer has two halves that point in
different directions: **more rain is falling, on more days, but the single wettest day of
the year is not getting wetter** — at least not detectably. The second half is the
interesting one, because it is the half that a chart of annual totals would hide.

> **Status:** PASSED — `verify.sh` exited 0 on the first attempt, 34 tests in 0.06s, 3s
> end to end in a clean venv. See [VERIFY.md](VERIFY.md).
> **Deck:** [slides](https://mlodian.github.io/agent-factory/projects/2026-09-11-manila-rainfall-extremes/deck/dist/deck.html) · [PDF](https://github.com/mlodian/agent-factory/releases/download/deck-2026-09-11-manila-rainfall-extremes/deck.pdf) · [PPTX](https://github.com/mlodian/agent-factory/releases/download/deck-2026-09-11-manila-rainfall-extremes/deck.pptx) · **Demo script:** [DEMO.md](DEMO.md)

## Quickstart

```bash
pip install -q -r requirements.txt
python3 data/fetch_data.py
python3 -m pytest -q tests/
python3 -m src.main --report
```

Or run all four the way CI does:

```bash
./verify.sh
```

The only dependency is `pytest`. The analysis itself imports nothing outside the standard
library.

## What it found

Every number below is from [VERIFY.md](VERIFY.md).

**The record.** 31,412 daily observations, 1940-01-01 to 2025-12-31. One null (1940-01-01,
the first day of the ERA5 back-extension) dropped, leaving 31,411 days across 86 complete
calendar years — none excluded. 14,178 days (45.1%) were wet days of at least 1 mm. The
R99p extreme threshold — the 99th percentile of wet-day rainfall — is **67.01 mm**. The
wettest day in the whole record is 226.7 mm.

**The four trends,** Mann-Kendall two-sided with a Theil-Sen slope, α = 0.05, n = 86:

| Index | Kendall's tau | p | Theil-Sen slope | Verdict |
|---|---|---|---|---|
| Rx1day — wettest day of the year | +0.0572 | 0.4379 | +1.400 mm/decade | **not significant** |
| Extreme days per year (> R99p) | +0.0509 | 0.4777 | +0.000 days/decade | **not significant** |
| PRCPTOT — total annual rainfall | +0.2963 | 0.0001 | +78.604 mm/decade | significant |
| Wet days per year (≥ 1 mm) | +0.1937 | 0.0083 | +4.118 days/decade | significant |

**The split is the finding.** Total rainfall and wet-day count both rise with strong
significance. The two extremity indices — how hard the hardest day rains, and how often
the threshold is beaten — do not move at all. In this record, Manila is getting more rain
by raining *more often*, not by raining *harder* on its worst day.

**By decade,** extreme days stay roughly flat in frequency while their mean intensity
drifts: the 1940s had 1.9 extreme days/year averaging 83.2 mm; the 2020s (6 years so far)
have 1.8 per year averaging 106.2 mm. The 1970s are the outlier at 3.2 days/year, against
0.8 in the 1960s.

**Read the significant result with suspicion.** Decadal mean rainfall runs from 1033 mm/yr
in the 1960s to 2294 mm/yr in the 2020s. A genuine 2.2x increase in Manila's rainfall over
60 years would be extraordinary; inhomogeneity in ERA5 across the 1979 satellite boundary
is the likelier explanation, and this project does not test for it. The `p = 0.0001` is a
confident statement about the ERA5 series, not about Manila's climate. That distinction is
the most important thing on this page.

## Data

| | |
|---|---|
| Source | [Open-Meteo Historical Weather API](https://archive-api.open-meteo.com/v1/archive?latitude=14.6&longitude=120.98&start_date=1940-01-01&end_date=2025-12-31&daily=precipitation_sum&timezone=Asia%2FManila) (ERA5 reanalysis) |
| Licence | CC BY 4.0, free for non-commercial use |
| Records | 31,412 daily observations × 2 fields, 1940-01-01 .. 2025-12-31 |
| Retrieved | 2026-09-11T10:05:31Z |
| Re-fetch | `python3 data/fetch_data.py` |

Weather data by [Open-Meteo.com](https://open-meteo.com/). ERA5 data from the Copernicus
Climate Change Service.

Full provenance, including both checksums, is in [data/SOURCE.md](data/SOURCE.md).

> Open-Meteo stamps every response with `generationtime_ms`, so identical data downloads to
> a different file checksum each time. `SOURCE.md` therefore records two hashes: `SHA256`
> over the bytes (what the provenance gate verifies) and `Content SHA256` over the
> measurements alone (what tells you whether the data actually changed). `fetch_data.py`
> will not overwrite the stored file when only the timestamp differs.

## How it works

`data/fetch_data.py` downloads one JSON document, validates that it really is the daily
payload rather than an HTML error or bot-challenge page, and writes the server's bytes
verbatim. `src/load.py` parses it into daily records, dropping nulls rather than
interpolating them, and refuses any calendar year with fewer than 360 valid days.
`src/extremes.py` computes the ETCCDI indices — R99p threshold, Rx1day, PRCPTOT, wet-day
and exceedance counts. `src/trend.py` runs Mann-Kendall and Theil-Sen, both rank-based
because annual maxima are heavy-tailed enough that least squares would let one typhoon year
set the slope. `src/main.py` prints the report.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the design decisions and their trade-offs.

## Limitations

- **ERA5 is a reanalysis, not a rain gauge.** The grid cell averages roughly 9–25 km and a
  convective cell is smaller than that, so daily peaks are smoothed. The record maximum of
  226.7 mm/day is well under the ~455 mm the Port Area gauge recorded during Tropical Storm
  Ketsana (Ondoy) on 2009-09-26. These numbers describe ERA5 at this point, not what fell
  on Manila's streets.
- **The significant PRCPTOT trend is not tested for inhomogeneity.** ERA5's 1940–1978
  back-extension assimilates far fewer observations than the satellite era, and reanalysis
  precipitation drifts as the observing system changes. No breakpoint test at 1979 is
  implemented, so part of that +78.604 mm/decade may be an artifact of the data rather than
  the climate. The 1960s-to-2020s doubling in decadal totals and the unexplained 1970s
  spike (32 extreme days against 8 in the 1960s) are both consistent with this.
- **The Rx1day null result means "not detected", not "not happening".** No power analysis
  was run, so the smallest trend this test could have found at n = 86 is unknown. Annual
  maxima have a wide interannual spread; a real but modest intensification could sit inside
  the noise.
- **The `+0.000 days/decade` slope is a tie artifact.** Extreme-day counts are small
  integers (mostly 0–3), so most pairwise slopes are exactly zero and their median is zero.
  The tau and p-value are the meaningful outputs for that row; the slope is not.
- **R99p uses a whole-record base period,** 1940–2025, not the WMO 1961–1990 baseline. The
  threshold is therefore not independent of the years being tested, and these figures are
  not directly comparable to published ETCCDI results.
- **One grid point, 14.6 N / 120.98 E, elevation 12 m,** stands in for a metro area of 13
  million across 16 cities. No spatial averaging and no sensitivity check against a
  neighbouring cell.
- **Calendar years, not water years.** A wet season straddling New Year is split across two
  annual values. Manila's wet season (roughly June–November) sits inside a calendar year,
  so the effect should be small, but it is not measured.
- **`src/main.py` has no end-to-end test.** The 34 tests cover `load`, `trend`, and
  `extremes`; report assembly is only exercised by `verify.sh` running it and checking the
  exit code. A formatting regression that didn't raise would pass unnoticed.

---

*Built by [agent-factory](../../README.md) on 2026-09-11. Reviewed by a human before merge.*
