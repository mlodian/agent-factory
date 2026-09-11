# Are Metro Manila's heaviest rainfall days getting heavier?

**Pitch:** Eighty-six years of daily rainfall over Metro Manila, asked one question — when
it pours, is it pouring harder than it used to, and can we prove it or not?
**Audience:** Anyone planning around Manila flooding — city drainage and DRRM planners,
climate-curious engineers, and analysts who want to see a trend claim tested rather than
asserted.

## Data source
- Registry id: open-meteo
- Endpoint:    `https://archive-api.open-meteo.com/v1/archive?latitude=14.6&longitude=120.98&start_date=1940-01-01&end_date=2025-12-31&daily=precipitation_sum&timezone=Asia%2FManila`
- Licence:     CC BY 4.0, free for non-commercial
- Observed:    31,412 daily records, 1940-01-01 → 2025-12-31, 569,461 bytes, 1 null value
  (1940-01-01), max 226.7 mm/day, mean 4.252 mm/day — confirmed live at 10:03 UTC on
  2026-09-11

## Acceptance criteria

1. `python3 data/fetch_data.py` downloads the endpoint above into `data/raw/`, prints a
   SHA256 and a record count, and on a second run detects the existing file, re-verifies
   its checksum against `data/SOURCE.md`, and skips the download.
2. The report computes the **R99p threshold** — the 99th percentile of wet days (≥1 mm) —
   over the full record, and prints, per decade, how many days exceeded it and their mean
   intensity in mm.
3. The report computes the annual **Rx1day** series (each year's wettest single day) and
   reports a Theil–Sen slope in mm/decade with a Mann–Kendall p-value, and states in words
   whether the trend is significant at α = 0.05 — including when it is not.
4. The report runs the same trend test on **total annual rainfall** and on **wet-day
   count**, so an intensifying-extremes claim can be read against whether the total is
   moving at all. All three verdicts are printed side by side.
5. Years with fewer than 360 valid daily observations are excluded from annual statistics,
   and the report prints which years were excluded and why.
6. `pytest tests/` passes, covering: percentile/threshold computation on a known array,
   Mann–Kendall on a strictly increasing series (must detect) and on a flat series (must
   not), and a malformed payload (nulls, short year) handled without crashing.

## Stack

Python 3.12. `pandas` and `numpy` for the series work; `pytest` for tests. The Mann–Kendall
and Theil–Sen estimators are implemented directly against the standard library `math`
module rather than pulling in `scipy` for two functions. No plotting library — the report
is text, and the deck quotes its numbers.

## Non-goals

- **No gauge validation.** Open-Meteo serves ERA5 reanalysis, not PAGASA station
  observations. Reanalysis is known to under-represent convective extremes. This project
  measures the trend *in ERA5 at this grid point*; it does not claim to measure the trend
  at Port Area or Science Garden.
- **No attribution.** Nothing here separates a warming signal from ENSO, the Pacific
  Decadal Oscillation, or urbanisation. A slope is not a cause.
- **One point, not a region.** A single coordinate (14.6 N, 120.98 E, elevation 12 m)
  stands in for Metro Manila. No spatial averaging across the metro's 16 cities.
- **No forecasting.** Historical description only; no projection past 2025.
- **No charts.** Text report only. Rendering is left to the deck.
