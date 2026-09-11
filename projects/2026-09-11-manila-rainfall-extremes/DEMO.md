# Demo script — Are Metro Manila's heaviest rainfall days getting heavier?

**Total: 5:00.** Open the deck (`deck/dist/deck.html`) and a terminal in this directory
before you start.

The shape of this talk is a setup and a reversal. You spend two minutes on a question the
audience thinks they know the answer to, then show them the test says no. Don't telegraph
it — let slide 7 land.

## Setup (do this before you're on)

```bash
pip install -q -r requirements.txt
python3 data/fetch_data.py
```

That leaves the data cached and checksum-verified, so the live run needs no network. Check
it's ready:

```bash
python3 -m src.main --report | tail -20
```

Then clear the screen. Have `VERIFY.md` open in a second tab as a fallback.

## Run of show

| Time | Slide | Say | Do |
|---|---|---|---|
| 0:00–0:30 | 1–2 | "Metro Manila floods. Everyone knows extreme rain is getting worse. I wanted to check that against a specific place, with a real test — 86 years of daily rainfall, 1940 to 2025." | — |
| 0:30–1:00 | 3 | "One point over Manila, ERA5 reanalysis via Open-Meteo. 31,412 daily records, one null, no credentials needed. The whole dataset is 569 kilobytes." | — |
| 1:00–1:45 | 4–5 | "Two rank-based tests — Mann-Kendall and Theil-Sen. Not least squares, because annual maximum rainfall is heavy-tailed and one typhoon year would set the slope. The test only asks whether later years tend to beat earlier ones." | — |
| 1:45–3:15 | 6 | "Running it now. Four indices: the wettest day of each year, the annual total, how many wet days, and how many days beat the extreme threshold." Let it finish, then read the threshold line out: 67.01 mm. | `python3 -m src.main --report` |
| 3:15–4:00 | 7 | "Total rainfall is up, strongly — p of 0.0001. Wet days up, p of 0.008. And the wettest day of the year…" pause "…p of 0.4379. Nothing. Manila is getting more rain by raining more *often*, not harder." | Point at **p = 0.4379** |
| 4:00–4:40 | 8–9 | "Two caveats I'd want from anyone showing me this. ERA5 is a 9-to-25-kilometre grid cell, not a gauge — its record max is 226.7 mm, but Ondoy dropped about 455 mm on the Port Area gauge. And that significant total-rainfall trend? Decadal means go from 1033 to 2294 mm. That's a doubling. I don't believe it's all climate — it's probably ERA5 changing underneath itself at the 1979 satellite boundary. I flag it; I don't test it. That's the next thing to build." | — |
| 4:40–5:00 | 10 | "Null result, honestly reported, with the one number I don't trust labelled as such. Code, data provenance and the full verification output are in the repo." | — |

## If the live run fails

Open `VERIFY.md` and scroll to the `## verify.sh output` block — it contains the complete
run, verbatim, including the decade table and all four trend results. Say: "here's the
output from the verified run," and read from it. The numbers are identical because that
file is where every number in the deck comes from.

If the terminal is the problem rather than the code, slide 7 carries the four trend rows on
its own.

## Likely questions

**Q: Isn't a null result just a failure to find anything? How do you know your test works?**
A: Two answers. The test fires correctly on data where the answer is known —
`tests/test_trend.py` checks a strictly increasing series (detected, p < 1e-6), a flat
series (p = 1.0), and a sawtooth with big swings but no drift (not detected). And in this
very run, the same test found the PRCPTOT trend at p = 0.0001. It's not that the test can't
detect anything; it detected two of four indices and not the other two. That contrast is
the result.

**Q: So extreme rainfall isn't intensifying in Manila?**
A: That's not what I can claim. "Not detected at n = 86" is not "not happening." I didn't
run a power analysis, so I can't tell you the smallest trend this test would have caught,
and annual maxima are noisy. What I can say is that this record doesn't support the claim —
which is different from refuting it, and I'd rather say the weaker true thing.

**Q: Why should I trust ERA5 for extremes at all?**
A: You shouldn't, entirely, and that's why the caveat is printed by the program itself
rather than buried in a README. A ~9–25 km grid cell smooths convective peaks; the record
maximum here is 226.7 mm against roughly 455 mm at the Port Area gauge during Ondoy. What
ERA5 is good for is a long, spatially consistent series — the trend *in that series* is a
real measurement. Whether it tracks the gauge trend is untested, and that's limitation
number one.

**Q: You said the significant result might be an artifact. Then why show it?**
A: Because hiding it would be worse, and because the contrast between it and the null is
the actual finding. If I'd only shown the annual-total chart, you'd have walked out
believing Manila's rainfall doubled. The two-index split is what stops that reading.

**Q: Why no scipy?**
A: Mann-Kendall and Theil-Sen are about 40 lines together, and the whole verify run
installs four wheels and finishes in 3 seconds. The cost is that the variance-with-ties and
continuity corrections are mine to get right, so they're tested against series with known
answers, including the normal-tail identity.

**Q: One grid point for the whole metro?**
A: Yes, 14.6 N, 120.98 E — and that's a limitation, not a design win. Four or five cells
across the metro would show whether this is a Manila result or a one-cell result. It's on
the list in ARCHITECTURE.md.
