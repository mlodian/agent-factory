# Data provenance

- Source:     NYC Open Data (Socrata SODA) — 311 Service Requests from 2010 to Present
- Registry:   nyc-open-data
- Dataset:    `erm2-nwe9`
- URL:        https://data.cityofnewyork.us/resource/erm2-nwe9.csv
  (one request per sampled day; example query string appended to the base URL above:
  `?$select=created_date,closed_date,complaint_type,agency,borough&$where=created_date >= '2025-01-01T00:00:00' and created_date < '2025-01-02T00:00:00'&$limit=100000&$order=created_date,complaint_type`)
- Retrieved:  2026-09-12T09:55–10:00Z (37 requests, ~4 minutes including 5xx retries)
- Licence:    Open (NYC Open Data terms; City of New York)
- File:       raw/nyc311_sample_2025.csv
- SHA256:     da9a7905f92eba4eebf354b9bacda96dce85762447c1fe7686227e7f1c9ee3a4
- Records:    367,465 rows x 5 columns (`created_date,closed_date,complaint_type,agency,borough`);
  367,201 carry one of the five boroughs (264 rows say `Unspecified` and are dropped by
  the loader), date range 2025-01-01 .. 2025-12-27.
- Fetch:      `python3 data/fetch_data.py` (verifies the cached checksum, no network);
  `python3 data/fetch_data.py --refresh` re-downloads and reports drift.

## The 37 sampled days

Day-of-year 1, 11, 21, ..., 361 of calendar year 2025 (stride 10; computed by
`src/days.sampled_dates`, shared by the fetcher and the loader so they cannot disagree):

```
2025-01-01, 2025-01-11, 2025-01-21, 2025-01-31, 2025-02-10, 2025-02-20, 2025-03-02,
2025-03-12, 2025-03-22, 2025-04-01, 2025-04-11, 2025-04-21, 2025-05-01, 2025-05-11,
2025-05-21, 2025-05-31, 2025-06-10, 2025-06-20, 2025-06-30, 2025-07-10, 2025-07-20,
2025-07-30, 2025-08-09, 2025-08-19, 2025-08-29, 2025-09-08, 2025-09-18, 2025-09-28,
2025-10-08, 2025-10-18, 2025-10-28, 2025-11-07, 2025-11-17, 2025-11-27, 2025-12-07,
2025-12-17, 2025-12-27
```

## What actually happened during the fetch

The endpoint answered with intermittent `503 Service Unavailable`, `500`, and a few
read timeouts under back-to-back querying — expected, and noted in SPEC.md before the
fetch was attempted. `data/fetch_data.py` retries each day up to 6 times with
exponential backoff (2s, 4s, 8s, ...); 8 of the 37 days needed at least one retry, and
all 37 eventually returned HTTP 200 with the exact 5-column CSV requested. No day was
skipped, truncated, or replaced with placeholder data.

## Right-censoring

At fetch time, requests still open (`closed_date` empty) are not dropped. Across the
367,201 five-borough rows, the censored share is small but real (see `VERIFY.md` for
the measured per-borough figures) — this is expected, since the extract includes
requests created as recently as 2025-12-27 and 311 does not close every request the
same day.

## This file is a projection, not a verbatim body

The upstream table (`erm2-nwe9`) carries dozens of columns (location, ZIP, council
district, community board, vehicle type, ...). `fetch_data.py` keeps only the five
this project uses: `created_date`, `closed_date`, `complaint_type`, `agency`, `borough`.

## `closed_date` keeps moving

Because `closed_date` is written continuously to the live dataset, re-running
`python3 data/fetch_data.py --refresh` a week from now will download different bytes
for requests that were open in this extract and have since closed. That is real drift
in the source, not corruption — the script detects it, reports a `DRIFT` line, and
leaves the committed file and its declared checksum untouched unless a human updates
this file. Every number in `VERIFY.md`, `README.md`, and the deck comes from the
extract pinned by the checksum above.

## Attribution

NYC Open Data publishes 311 Service Requests under an open licence; the City of New
York does not endorse this analysis, and the interpretation of the numbers below is
this project's own.
