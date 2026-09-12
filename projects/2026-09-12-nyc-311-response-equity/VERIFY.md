# Verification

STATUS: PASSED
Date:   2026-09-12T10:11:01Z
Python: 3.12.14
Env:    clean venv (`scripts/verify.sh` — fresh `venv`, `pip install --upgrade pip`, then `bash verify.sh`)

## verify.sh output

```
==> verifying projects/2026-09-12-nyc-311-response-equity in a clean venv
==> python Python 3.12.14
==> installing dependencies
==> checking the committed extract against data/SOURCE.md
Source: https://data.cityofnewyork.us/resource/erm2-nwe9.csv
UA    : agent-factory/1.0
Days  : 37 sampled (stride 10, day-of-year 1..361)

Cached  : data/raw/nyc311_sample_2025.csv
  SHA256       : da9a7905f92eba4eebf354b9bacda96dce85762447c1fe7686227e7f1c9ee3a4 (matches SOURCE.md — skipping download)
  records      : 367,465 rows x 5 columns
==> running tests
........................                                                 [100%]
24 passed in 0.12s
==> running the analysis on the real data
NYC 311 RESPONSE EQUITY -- does the borough gap survive a like-for-like comparison?
367,201 requests across 37 sampled days of 2025

POPULATION
----------
  311 requests created on 1 of the 37 sampled days of 2025, 5-borough only

  borough           sampled requests
    BRONX              85,542
    BROOKLYN          108,461
    MANHATTAN          71,997
    QUEENS             87,578
    STATEN ISLAND      13,623
    TOTAL             367,201

  Borough counts sum exactly to the population total (367,201). OK

72-HOUR CLOSURE RATE, RAW vs. MIX-STANDARDISED (95% cluster-bootstrap CI)
-------------------------------------------------------------------------
  borough           n       open (95% CI)              raw 72h (95% CI)              standardised 72h (95% CI)
    BRONX           85,542     0.5% (0.4%-0.6%)        76.4% (72.4%-79.9%)           73.0% (70.7%-75.5%)
    BROOKLYN       108,461     1.7% (1.2%-2.3%)        73.9% (72.1%-75.8%)           72.9% (70.7%-75.1%)
    MANHATTAN       71,997     2.1% (1.7%-2.5%)        71.0% (68.6%-73.3%)           77.3% (75.2%-79.3%)
    QUEENS          87,578     2.0% (1.7%-2.3%)        79.3% (77.7%-81.0%)           76.7% (74.8%-78.7%)
    STATEN ISLAND   13,623     1.6% (1.3%-1.9%)        70.4% (67.9%-72.8%)           75.8% (73.4%-78.1%)

DECOMPOSITION: raw_rate - citywide_rate = mix_effect + speed_effect
-------------------------------------------------------------------
  citywide rate: 75.1%

  borough           gap       mix_effect   speed_effect   check
    BRONX          +1.319%      +3.362%       -2.043%   OK
    BROOKLYN       -1.187%      +1.040%       -2.228%   OK
    MANHATTAN      -4.032%      -6.250%       +2.218%   OK
    QUEENS         +4.231%      +2.582%       +1.649%   OK
    STATEN ISLAND  -4.715%      -5.390%       +0.675%   OK

  Identity holds for every borough (max |error| = 8.33e-17 < 1e-9). OK

COMMON BASIS: complaint types with >=100 requests in every borough
------------------------------------------------------------------
  30 complaint types qualify, covering 288,407/367,201 requests (78.5%)

  10 largest common-basis types, 72h closure rate by borough:
    complaint type                    BRON      BROO      MANH      QUEE      STAT    spread
    Illegal Parking                  99.8%     99.9%    100.0%     99.9%    100.0%      0.2%
    Noise - Residential             100.0%    100.0%    100.0%     99.7%    100.0%      0.3%
    HEAT/HOT WATER                   91.9%     86.5%     77.7%     80.3%     86.5%     14.2%
    Blocked Driveway                 99.8%     99.8%    100.0%     99.9%    100.0%      0.2%
    Noise - Street/Sidewalk         100.0%    100.0%    100.0%     99.9%    100.0%      0.1%
    UNSANITARY CONDITION             13.1%     14.7%      8.2%     16.5%     19.9%     11.8%
    Water System                     77.9%     80.5%     94.8%     67.5%     83.6%     27.3%
    PLUMBING                         21.9%     23.7%     23.3%     23.8%     23.2%      2.0%
    Abandoned Vehicle               100.0%     98.4%    100.0%     99.7%    100.0%      1.6%
    Street Condition                 59.7%     74.3%     84.1%     71.9%     80.0%     24.4%

TYPICAL TIME TO CLOSE (weighted median hours; censored share per cell)
----------------------------------------------------------------------
  borough            median    censored
  BRONX               12.9h        0.5%
  BROOKLYN             6.4h        1.7%
  MANHATTAN           13.0h        2.1%
  QUEENS               4.4h        2.0%
  STATEN ISLAND       17.6h        1.6%

Wrote deck/borough_gap.svg
==> finished in 11s with exit code 0
```

## Headline numbers

- Population: 367,201 five-borough requests across 37 sampled days of 2025
- Borough counts: BRONX 85,542; BROOKLYN 108,461; MANHATTAN 71,997; QUEENS 87,578; STATEN ISLAND 13,623 (sum verified equal to 367,201 by the report's own assertion)
- Raw 72h closure rate: BRONX 76.4% (72.4%-79.9%), BROOKLYN 73.9% (72.1%-75.8%), MANHATTAN 71.0% (68.6%-73.3%), QUEENS 79.3% (77.7%-81.0%), STATEN ISLAND 70.4% (67.9%-72.8%) — all 95% cluster-bootstrap CIs
- Mix-standardised 72h closure rate: BRONX 73.0% (70.7%-75.5%), BROOKLYN 72.9% (70.7%-75.1%), MANHATTAN 77.3% (75.2%-79.3%), QUEENS 76.7% (74.8%-78.7%), STATEN ISLAND 75.8% (73.4%-78.1%)
- Citywide rate: 75.1%
- Decomposition (gap = mix_effect + speed_effect), all `check: OK`:
  - BRONX +1.319% = +3.362% (mix) + -2.043% (speed)
  - BROOKLYN -1.187% = +1.040% (mix) + -2.228% (speed)
  - MANHATTAN -4.032% = -6.250% (mix) + +2.218% (speed)
  - QUEENS +4.231% = +2.582% (mix) + +1.649% (speed)
  - STATEN ISLAND -4.715% = -5.390% (mix) + +0.675% (speed)
  - Identity holds for every borough: max |error| = 8.33e-17 (< 1e-9)
- Common basis: 30 complaint types with >=100 requests in every borough, covering 288,407/367,201 requests (78.5%)
- Weighted-median time to close (censored share per cell): BRONX 12.9h (0.5%), BROOKLYN 6.4h (1.7%), MANHATTAN 13.0h (2.1%), QUEENS 4.4h (2.0%), STATEN ISLAND 17.6h (1.6%)
- Tests: 24 passed in 0.12s
- Runtime: 11 seconds (full `scripts/verify.sh` wrapper: fresh venv creation, dependency install, checksum check, tests, and analysis, per the wrapper's own `finished in 11s` line)
- Records processed: 367,201 (five-borough rows of 367,465 total rows in the extract)

## Data integrity

- SHA256 re-check: MATCH — `python3 data/fetch_data.py` re-verified the cached extract against the checksum in `data/SOURCE.md` (`da9a7905f92eba4eebf354b9bacda96dce85762447c1fe7686227e7f1c9ee3a4`) with no network access, printing the same "matches SOURCE.md — skipping download" result on a separate direct run and inside the clean-venv `verify.sh` run.

## Repairs made

- `data/SOURCE.md`'s `- URL:` field wrapped the URL in backticks and continued onto two more lines with the example query string, e.g. `` - URL:        `https://.../erm2-nwe9.csv` — one request per ``. `scripts/check_provenance.py --data-only` parses `- Key: value` as a single line and takes the first whitespace-delimited token of the value as the URL; the leading backtick made `url.startswith("http")` false, so the check failed with "SOURCE.md has no usable `URL:`". This was a documentation-format bug, not a data problem: the URL itself is correct and live. Fixed by putting the bare URL on the `- URL:` line (matching the convention used by every other project's SOURCE.md, e.g. `2026-09-11-cvss-vs-exploitation` and `2026-09-11-manila-rainfall-extremes`) and moving the example query-string suffix to a parenthetical on the following line. Re-ran `python3 scripts/check_provenance.py 2026-09-12-nyc-311-response-equity --data-only`, which now prints `## Provenance check: PASSED`, including "cited URL is live (HTTP 200)".

## Known weaknesses

- `raw/nyc311_sample_2025.csv` is 28,456,965 bytes, over the workflow's 10 MB commit threshold; `check_provenance.py` flags this as a warning (not a failure) because `fetch_data.py` recreates it from the pinned checksum. A reviewer should confirm the workflow does in fact drop it from the commit and that `fetch_data.py` continues to work from a clean checkout with no cached file present (only the checksum-match path was exercised here, since the file was already present).
- The runtime figure above (11s) is the wrapper's clean-venv total (venv creation + pip install + verify.sh); the project's own `verify.sh` run in a warm environment (dependencies already resolvable from cache) completed its internal work in about 9.2s wall-clock in a separate direct-invocation timing, consistent with the "under two minutes" acceptance criterion in SPEC.md.
- Verification exercises the committed extract only, per verify.sh's own design (no network). Live-source drift (closed_date continuing to update upstream) is handled by `fetch_data.py --refresh`'s `DRIFT` reporting, which was not exercised in this pass since `--refresh` was not run (SPEC.md's acceptance criteria only require the default no-network path for `verify.sh`).
- `check_provenance.py --data-only` was run against the current worktree, which does not yet have `README.md`, `deck/deck.md`, or other doc phases populated; the full provenance/claims gate (numbers-on-slides tracing to VERIFY.md/FIGURES.md/CONTEXT.md) will only run once those exist, per this skill's own scope.
