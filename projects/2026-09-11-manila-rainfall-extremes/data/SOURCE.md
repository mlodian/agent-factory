# Data provenance
- Source:     Open-Meteo Historical Weather API (ERA5 / ERA5-Land reanalysis)
- Registry:   open-meteo
- URL:        https://archive-api.open-meteo.com/v1/archive?latitude=14.6&longitude=120.98&start_date=1940-01-01&end_date=2025-12-31&daily=precipitation_sum&timezone=Asia%2FManila
- Retrieved:  2026-09-11T10:05:31Z
- Licence:    CC BY 4.0, free for non-commercial use. Attribution: "Weather data by Open-Meteo.com", ERA5 data from Copernicus Climate Change Service.
- File:       raw/manila_precip_1940_2025.json
- SHA256:     58395218e52271fd666c13f89deac258850a1fa316c214cbd708b70cc1fb5670
- Content SHA256: 7621a5cc26ad35393f78acbd99a519f642d8d7a536b3cfd392eb86d910eaaed5
- Bytes:      569463
- Records:    31,412 daily observations × 2 fields (date, precipitation_sum), 1940-01-01 .. 2025-12-31
- Nulls:      1 (1940-01-01, the first day of the ERA5 back-extension)
- Units:      precipitation_sum in mm, dates ISO-8601 in Asia/Manila local time
- Point:      14.6 N, 120.98 E — grid cell elevation 12.0 m
- Fetch:      python3 data/fetch_data.py

## Two checksums, and why

Open-Meteo stamps every response with a `generationtime_ms` field, so downloading
the identical data twice produces files that differ by a byte or two. Five fetches
on 2026-09-11 returned response bodies of 569,461 / 569,462 / 569,463 / 569,462 /
569,462 bytes. Every one whose content hash was computed gave the same
`7621a5cc…` — the measurements never moved; only the server's timing field did.

That makes a plain file checksum useless as an "is this still the same data?"
test, so this project records both:

| Field | Covers | Changes when |
|---|---|---|
| `SHA256` | the exact bytes on disk | any re-download, even of identical data |
| `Content SHA256` | canonical JSON of the `time` and `precipitation_sum` arrays | and only when the measurements change |

`SHA256` is what `scripts/check_provenance.py` verifies — it proves the committed
file is the one that was analysed. `Content SHA256` is what tells a human whether
Open-Meteo has revised the series.

`fetch_data.py` uses both: on a re-run it skips the download when `SHA256` matches,
and if it does download and the content hash is unchanged it **leaves the existing
file in place** so the declared `SHA256` stays valid. It overwrites only when the
measurements actually changed, and prints a loud warning when it does.

## What this data is, and is not

ERA5 is a **reanalysis** — a physical model reconstruction constrained by
observations, not a rain gauge. For a coastal, convective, typhoon-exposed site
like Manila, reanalysis is known to smooth extreme daily totals: the grid cell
averages roughly 9–25 km, and a thunderstorm cell is smaller than that. The
record's maximum of 226.7 mm/day is well below the ~455 mm Port Area gauge reading
during Tropical Storm Ketsana (Ondoy) on 2009-09-26.

So this file supports the question "is the extreme tail of *ERA5 at this grid
point* shifting over time?" It does not support "what is the heaviest rain Manila
has recorded?" — for that you need PAGASA station data, which is not available
through an unauthenticated API.

The 1940–1978 portion comes from ERA5's back-extension, which assimilates far fewer
observations than the post-1979 satellite era. Treat the early decades as the
weakest part of the record.
