---
marp: true
theme: factory
paginate: true
footer: "agent-factory · 2026-09-11"
---

<!-- _class: title -->
<!-- _paginate: false -->

# Are Metro Manila's heaviest rainfall days getting heavier?

86 years of daily rainfall, two rank-based trend tests, and a null result worth reporting.

2026-09-11 · github.com/mlodian/agent-factory

<!--
Open with the question, not the tech.

"Everyone has heard that extreme rain is intensifying. I wanted to check it for one
specific place, with a test that could have said no — and it did say no, for the index
that matters most. That's the talk."

Verification passed: verify.sh exited 0 first attempt, 34 tests, 3 seconds.
Don't give away the reversal yet. Slide 7 is where it lands.
-->

---

## The problem

Manila floods. "Extreme rainfall is getting worse" is repeated constantly — and rarely
tested against a specific place with a test that could have come back negative.

<!--
Concrete about who asks this: city drainage engineers sizing culverts, DRRM planners
writing evacuation triggers, insurers pricing flood risk. Today they mostly reach for a
regional climate projection or a chart of annual totals.

The problem with a chart of annual totals is the whole point of this project — it answers
a different question from the one they're asking. "More rain per year" and "worse worst
day" are not the same claim, and drainage capacity depends on the second one.
-->

---

## Why it matters

- **Drainage is sized for the worst day**, not the annual total
- 13 million people in a metro that floods on a bad afternoon
- The usual evidence — a rising annual-rainfall chart — answers the wrong question

<!--
Culvert and pump capacity is set by peak intensity. If you tell a drainage engineer
"annual rainfall is up 8%", you have given them nothing actionable. If you tell them "the
wettest day of the year is 15% wetter", every design assumption changes.

So the distinction between total and peak isn't pedantry — it's the difference between a
number that changes a decision and one that doesn't.

That's why this project tests four indices separately rather than one.
-->

---

## Architecture

![w:1000](architecture.svg)

<!--
Walk it left to right, fast — 20 seconds, this isn't the interesting slide.

API to a single validated JSON file with two checksums. Parse into daily records,
dropping nulls rather than filling them. Compute the ETCCDI extreme indices. Run the
trend tests. Print a report that states its own caveats.

Five modules, no shared state, no mocks in the tests because the only I/O is at the two
ends.
-->

---

## How it works

**Rank-based statistics, not least squares.**

Mann-Kendall asks only whether later years tend to beat earlier ones. Theil-Sen takes the
median of all pairwise slopes.

One typhoon year cannot set the trend.

<!--
This is the one decision worth explaining.

Annual maximum rainfall is skewed and heavy-tailed. Fit ordinary least squares and a
single freak year swings the slope; its t-test also assumes a normality this data
does not have.

There's a test that states this as an assertion rather than a claim: plant a 10,000 mm
year in an otherwise flat series. Theil-Sen still returns exactly zero. The same test
computes OLS on the identical input and shows it dragged past 10.

Cost: it's about 40 lines I wrote instead of importing scipy, so the tied-variance and
continuity corrections are mine to get right. They're tested against series whose answers
are known in advance — increasing, flat, sawtooth — plus the normal-tail identity.
-->

---

<!-- _class: demo -->

## Demo

```bash
python3 -m src.main --report
```

<!--
Switch to the terminal. Data is already cached and checksum-verified, so this needs no
network and returns in well under a second.

Narrate while it scrolls: 86 complete years, no years excluded, the extreme threshold,
then the four trend blocks.

Point at: p = 0.4379 on Rx1day. Pause before you say it.
-->

---

## Results

| Measure | Value |
|---|---|
| Daily records, 1940–2025 | 31,412 |
| Complete years used | 86 |
| R99p extreme threshold | 67.01 mm |
| **Rx1day — wettest day/yr** | **p = 0.4379 — not significant** |
| **Extreme days/yr** | **p = 0.4777 — not significant** |
| Total annual rainfall | p = 0.0001 — significant |
| Wet days/yr | p = 0.0083 — significant |

More rain, on more days. Not a harder worst day.

<!--
Every number here is from VERIFY.md.

Say it plainly: two indices moved, two didn't. Manila is getting more rain by raining
more OFTEN, not by raining HARDER on its worst day.

What it means: for drainage sizing, this record gives you no evidence that peak intensity
is rising.

What it does NOT mean: that extreme rainfall isn't intensifying. "Not detected at n = 86"
is not "not happening" — I ran no power analysis, so I can't tell you the smallest trend
this would have caught.

If someone asks whether the test works at all: it found two of four. It wasn't blind.
-->

---

## Limitations

- **ERA5 is a reanalysis, not a gauge** — record max 226.7 mm vs ~455 mm at Port Area during Ondoy
- **The significant trend is the suspicious one** — decadal means run 1033 to 2294 mm/yr
- **One grid point** stands in for a 16-city metro
- **A null is not a refutation** — no power analysis was run

<!--
Own this slide. Slow down here.

The ERA5 point: a 9-to-25 km grid cell smooths convective peaks. These are trends in the
reanalysis at this point, not in what fell on the streets. The program prints that caveat
itself rather than leaving it to a README.

The second bullet is the one I'd want a reviewer to catch. A 2.2x rise in decadal rainfall
over 60 years would be extraordinary. I think a good chunk of it is ERA5 changing
underneath itself at the 1979 satellite boundary, when the observing system shifts. The
1970s also show 32 extreme days against 8 in the 1960s, which no physical mechanism
explains comfortably. I flag it. I do not test it. That's the honest state of it.

So: p = 0.0001 is a confident claim about the ERA5 series, not about Manila's climate.
-->

---

## What's next

1. **A breakpoint test at 1979** — settle how much of the total-rainfall trend is ERA5 changing, not climate
2. **A power analysis** — put a number on what the Rx1day null can actually rule out

<!--
Just these two. Both are directly aimed at the weakest claims in the talk, which is the
point.

The breakpoint test — Pettitt, or even a simple pre/post-1979 split — is first because it
decides whether the one significant result survives.

The power analysis turns "not detected" into "we can rule out a trend larger than X",
which is a far more useful sentence for anyone sizing infrastructure.

Everything else — more grid points, gauge comparison, water years — is in ARCHITECTURE.md.
-->

---

<!-- _class: title -->

## Links & data

**Code:** github.com/mlodian/agent-factory/tree/main/projects/2026-09-11-manila-rainfall-extremes

**Data:** Open-Meteo Historical Weather API (ERA5) — CC BY 4.0, free for non-commercial use

*Weather data by Open-Meteo.com. ERA5 data from the Copernicus Climate Change Service.*

<!--
Thank them.

The attribution above is a licence obligation, not a courtesy.

Full provenance is in data/SOURCE.md — exact URL, retrieval timestamp, both checksums,
and the reason there are two of them.

The question I'm best prepared for: "isn't a null result just a failure?" Invite it.
-->
