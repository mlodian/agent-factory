# Chart guide for factory decks

The deck exists to make one insight land. Every chart is evidence for a specific story
beat, and a chart that isn't evidence for anything gets cut.

## 1. Choose the form before touching color

| The beat says… | Use | Not |
|---|---|---|
| "The answer is one number" | **Hero number** slide: huge figure, one line of context | A one-bar chart |
| "This one thing differs from the rest" | **Emphasis**: one series in the accent, everything else gray | A rainbow of categories |
| "It changed over time" | Line, or area for a single series | Bars per year when there are 30+ years |
| "Compare these magnitudes" | Horizontal bar, sorted | Pie, 3D, donut for close values |
| "Before vs after, per item" | Dumbbell | Grouped bars |
| "Part of a whole" | One stacked bar, ≤ 6 parts | Pie with 12 slices |
| "Distribution / spread" | Histogram, strip plot, box | Mean-only bar |
| "Two measures relate" | Scatter, or small multiples | **Dual-axis chart** |
| "It's a ranking with many items" | Sorted bar, top-N plus "Other" | 20 colored bars |

Emphasis is the best default for a slide. The audience has 10 seconds per chart, so
highlight the thing the beat is about and push everything else into gray.

## 2. Non-negotiables

- **One y-axis. Never a dual-axis chart.** Two scales on one plot invent a correlation.
  Use two charts, or index both series to 100 at a shared start.
- **The title states the finding** ("Exploitation rate triples from HIGH to CRITICAL"),
  not the variables ("Exploitation rate by severity"). Put a short subtitle underneath
  with the unit and scope.
- **A source line on every chart**, bottom-left, small, muted:
  `Source: CISA KEV, NVD · n = 20,149 CVEs published in 2021`.
- **Bars start at zero.** A line chart may use a non-zero baseline, but then the axis must
  show it clearly and the subtitle should say so if the difference is being dramatised.
- **No cherry-picked windows.** If you show a date range, it's the full range the project
  analysed, unless the story is specifically about a sub-period and the subtitle says so.
- **Sequential scales use one hue, light → dark. Diverging scales use two opposite hues with
  a neutral gray midpoint.** Never a rainbow.
- **At most ~6 categorical colors.** Past that, fold into "Other" or use small multiples.
  Color follows the entity, and the same series is the same color on every slide.
- **Text is never in a series color.** Labels use the ink colors, and a colored mark beside
  them carries identity.
- **Label selectively.** Label the endpoint, the extreme, or the one bar that matters.
  Don't put a number on every point.

## 3. Marks and chrome

- Thin marks: 2 px lines, bars with a small gap between them, markers ≥ 6 px.
- Gridlines are optional. When used, they're solid hairlines one shade off the
  background, never dashed. Drop the top and right spines.
- Generous padding. Charts fill roughly 80% of the slide width.
- Large type. On a 1280×720 slide, tick labels ≥ 14 pt, direct labels ≥ 16 pt, and
  the chart title ≥ 24 pt. If it's too small to read from the back of a room, it doesn't count.

## 4. Palette: compute it, don't eyeball it

Use the colors in the project's `deck/identity.json`. Before committing, run:

```bash
python3 scripts/check_palette.py deck/identity.json
```

It checks WCAG contrast (text ≥ 4.5:1 on the background, large text and chart marks
≥ 3:1) and whether the categorical colors stay distinguishable under normal vision and
simulated red-green colorblindness. A FAIL gets fixed before anything else.

## 5. matplotlib specifics

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({
    "svg.fonttype": "path",        # text as outlines, so it renders identically everywhere
    "svg.hashsalt": "factory",     # deterministic ids, so SVGs don't churn between runs
    "figure.figsize": (12.8, 6.4), # 2:1 fits a 16:9 slide under a title
    "axes.spines.top": False, "axes.spines.right": False,
})
fig.savefig(path, format="svg", bbox_inches="tight", metadata={"Date": None})
```

- Read the data from `data/raw/` or import the project's own `src/` functions. **Never
  type a data value into the chart script.** The workflow re-runs the script from the
  committed data, and the provenance gate rejects `np.random` and friends.
- Every number the script prints into an annotation, and every derived figure the story
  needs that isn't already in `VERIFY.md` (a ratio, a "1 in N"), must also be written to
  `deck/charts/FIGURES.md` by the same script. That file is how the fact-checker and the
  provenance gate trace deck numbers that `VERIFY.md` doesn't contain.

## 6. Render it and look at it

A chart that validates can still have colliding labels, a clipped axis, or a legend
covering the data. `bash scripts/preview_deck.sh <slug>` renders every slide to PNG in
`deck/preview/`. Open the images and look before calling it done.
