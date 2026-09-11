---
name: factory-viz
description: Design and render the deck's charts from the project's real data, via a reproducible chart script
context: fork
agent: viz-designer
background: false
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(bash scripts/build_charts.sh *), Bash(python3 *)
---

## Instructions

Project: `projects/$(cat .slug)/`. Read, in this order:
1. `templates/viz-guide.md`, the rules. Follow them.
2. `deck/STORY.md`: the beats, each beat's evidence, its suggested visual, and the derived
   figures the story needs.
3. `deck/identity.json`: the palette and fonts. `chartkit` applies them for you.
4. `data/SOURCE.md` and the project's `src/`, for how to load and compute from the data.

### Write `deck/charts/make_charts.py`

One chart per beat that needs one (a hero-number beat usually doesn't). Use the shared
toolkit, which handles fonts, colors, titles, source lines, and deterministic SVGs:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))
import chartkit as ck

kit = ck.Kit()                       # identity.json → rcParams, fonts, palette
# …load from data/raw/ or import from src/ — never type data values in…
fig, ax = kit.figure()
ax.bar(labels, values, color=kit.emphasis(labels, highlight="CRITICAL"))
kit.title(fig, "<the finding, as a sentence>", "<unit and scope>")
kit.source(fig, "Source: <name> · n = <n>")
kit.save(fig, "02-<beat-name>")      # → deck/charts/02-<beat-name>.svg
kit.figures.add("<label>", value, "{:.1f}%")
kit.figures.write()                  # → deck/charts/FIGURES.md
```

- The script runs **from the project directory**, so paths are relative: `data/raw/…`.
- Write **every derived figure the story lists**, and every number you print onto a chart,
  through `kit.figures.add(...)`. That's how the deck is allowed to quote them.
- Name charts by order and beat (`01-hook.svg`, `02-severity-bands.svg`, …) so the composer
  can map them.
- Standard figure size is 12.8×6.4 in. For a `split` layout, use about 7×6.4.

### Write `deck/charts/requirements.txt`

Pinned, for example `matplotlib==3.11.1`. Add only what the script imports beyond the
project's own `requirements.txt`.

### Build it and look

```bash
bash scripts/build_charts.sh $(cat .slug)
```

Fix errors until it runs clean from the committed data. Then check each chart against
`templates/viz-guide.md` → Non-negotiables: finding-as-title, source line, honest axes, no
dual axis, emphasis over rainbow, and labels legible at slide size. You'll see the charts
in context once the deck exists. Visual QA renders every slide and reports defects back.
