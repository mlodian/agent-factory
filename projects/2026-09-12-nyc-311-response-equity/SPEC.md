# Do 311 complaints get resolved at the same speed across NYC boroughs?

**Pitch:** Staten Island's 311 complaints close far slower than the Bronx's — but the
boroughs don't file the same complaints, so this project measures how much of that gap
survives when every borough is compared on a like-for-like complaint mix.
**Audience:** city-government analysts and civic-tech people who publish borough
league tables, plus anyone who has ever read "agency X is slower in borough Y" and
wondered whether the comparison was fair.

## The question, sharpened

The headline number — share of complaints closed within 72 hours, by borough — is a
mix of two different things: how fast each agency works in that borough, and which
complaints that borough files. A borough full of heat-and-hot-water complaints (days to
close) will look slow next to one full of illegal-parking complaints (minutes to close),
even if every single agency is equally fast in both.

So the project asks: **after standardising every borough onto the same citywide
complaint mix, how much of the borough gap is left?** The answer is a decomposition —
borough gap = complaint-mix effect + like-for-like speed effect — not an opinion.

A five-day pilot run on 2026-09-12 (48,465 complaints) showed this is a real question
with a non-obvious answer: the raw 72-hour closure rate ranked the Bronx first (80.1%)
and Manhattan fourth (73.6%), but standardising on the citywide mix reversed them.
The full build re-measures this properly; the pilot numbers are not results and appear
nowhere outside this paragraph.

## Data source

- Registry id: `nyc-open-data` (NYC Open Data, Socrata SODA — 311 Service Requests, dataset `erm2-nwe9`)
- Endpoint:    `https://data.cityofnewyork.us/resource/erm2-nwe9.csv?$select=created_date,closed_date,complaint_type,agency,borough&$where=created_date >= '2025-01-01T00:00:00' and created_date < '2025-01-02T00:00:00'&$limit=100000&$order=created_date,complaint_type`
  (one request per sampled day; 37 requests in total)
- Licence:     Open (NYC Open Data terms; City of New York)
- Observed:    HTTP 200 confirmed live at 10:0x–10:2x UTC on 2026-09-12. Single-day probes
  returned 10,873 rows / 959,440 bytes (2025-01-01), 9,348 rows (2025-06-19),
  10,755 rows (2025-09-08) and 8,013 rows (2025-12-21), in 0.6–1.7 s each. A five-day
  pilot pull returned 48,520 rows, of which 48,465 carry one of the five boroughs.

`nyc-open-data` is in `sources/registry.yml`, is not on the `denied:` list, and is not
marked `unattended: false`. The endpoint returns intermittent 503/500 responses under
repeated querying (observed twice during probing), so the fetcher must retry with backoff.

## The population

Every 311 service request **created on one of 37 sampled days of calendar year 2025** —
day-of-year 1, 11, 21, … 361 — whose `borough` is one of the five boroughs.

Why a sample rather than the whole year: 2025 holds roughly 3.4 million requests, about
290 MB over the wire, which breaks the one-run scope rule. A fixed stride of 10 days is
a systematic sample that (a) spreads evenly across the seasons, so winter heat complaints
and summer noise complaints both appear in proportion, and (b) because 10 and 7 are
coprime, cycles through all seven weekdays 5–6 times each, so it does not over-sample
weekends. The stride is fixed in code, not chosen after looking at results, and the
sampled dates are listed in `data/SOURCE.md`.

Because the sampling unit is the day, every interval in the report is a **cluster
bootstrap over the 37 days** with a fixed seed — resampling individual complaints would
understate the uncertainty.

Right-censoring is small but real: 1.0–2.9% of each probe day's requests were still open
at fetch time. They are never dropped. They count in the denominator of "closed within
72 hours" (an open request is not closed within 72 hours) and they sit at the top of the
distribution when a median is taken, so a median is only reported when the censored
share of that cell is below 50%.

## Acceptance criteria

1. `python3 data/fetch_data.py` fetches the 37 daily slices (retrying on 5xx), writes a
   field projection to `data/raw/`, and prints a SHA256 that matches `data/SOURCE.md`.
   Re-running it with the extract present re-verifies the checksum and skips the network;
   `--refresh` re-downloads and prints a `DRIFT` line instead of failing, because closed
   dates keep being written to the live dataset.
2. The report prints, per borough: the number of sampled requests, the share still open,
   the raw share closed within 72 hours, and the mix-standardised share, each with a
   95% cluster-bootstrap interval. Borough counts sum exactly to the population total and
   the report asserts it.
3. The report prints the decomposition `raw_rate(borough) - citywide_rate = mix_effect +
   speed_effect` for each borough, and asserts the identity holds to within 1e-9. A test
   verifies the decomposition on a hand-built Simpson's-paradox fixture where the raw
   ranking and the standardised ranking are opposite.
4. The report prints the complaint types used as the common basis (those with at least
   100 sampled requests in *every* borough), the share of the population they cover, and
   for the 10 largest of them the per-borough 72-hour rate and the max-minus-min spread.
5. The weighted-median implementation is tested against a brute-force expansion of the
   weights on fixtures, including the even/odd and all-weight-on-one-item cases, and the
   censored case where the median is reported as "> 72 h".
6. `bash verify.sh` installs dependencies, runs pytest, and regenerates the whole report
   from the committed extract in under two minutes with no network access.

## Stack

Python 3.12, standard library only (`csv`, `datetime`, `statistics`, `random`,
`urllib`) plus `pytest`. The extract is a few hundred thousand short rows; sorting and
counting them needs no dataframe library. One hand-written SVG chart, following the
previous project's approach.

## Non-goals

- **No sub-borough geography.** ZIP code, community board and council district are all in
  the dataset and all tempting; they multiply the cells by 50× and the sample would not
  support them. Borough only.
- **No income, race or demographic join.** This measures service *speed*, not equity in
  the socioeconomic sense, and the project must not imply it has measured the latter.
  "Response equity" here means like-for-like comparability between boroughs, nothing more.
- **No multi-year trend.** One year, sampled properly, rather than five sampled thinly.
- **No agency league table.** Agency is carried in the extract for context and is used
  only to label complaint types, not to rank agencies against each other.
- **No causal claim.** A surviving borough gap is a gap, not evidence of intent,
  staffing, or neglect; possible explanations are listed as hypotheses and not tested.
- **`closed_date` is administrative closure, not repair.** NYPD closes a noise complaint
  when an officer files a response; DOT closes a pothole report on referral to a
  maintenance unit. The README and deck must say so plainly — a fast close is not
  necessarily a fixed problem, and the closure clock is not comparable across agencies
  (which is exactly why the comparison is made *within* complaint type).
- No interactive dashboard and no map; the deliverable is a text report plus static SVGs.
