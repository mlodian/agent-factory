---
name: factory-art
description: Create the project's own visual identity — palette, typography, layout classes — as a validated Marp theme
context: fork
agent: art-director
background: false
allowed-tools: Read, Glob, Grep, Write, Edit, Bash(python3 scripts/check_palette.py *)
---

## Recent identities to stay clear of

!`python3 scripts/recent_identities.py`

## Instructions

Project: `projects/$(cat .slug)/`. Read `deck/STORY.md`, especially the audience, the
insight, and the **mood**.

### 1. `deck/identity.json`

```json
{
  "name": "<a two-word name for this look>",
  "mood": "<from the story, refined>",
  "rationale": "<two sentences: why this look fits this subject and this story>",
  "fonts": { "display": "<family>", "body": "<family>", "mono": "<family, optional>" },
  "colors": {
    "background": "#rrggbb", "surface": "#rrggbb",
    "ink": "#rrggbb", "muted": "#rrggbb",
    "accent": "#rrggbb", "context": "#rrggbb",
    "categorical": ["#rrggbb", "…up to 6; the first is usually the accent"]
  },
  "layouts": ["<class names you define in theme.css, e.g. hero, chart, split, quote>"]
}
```

Fonts must come from the verified list in `scripts/check_deck.py`, since anything else fails
the deck gate. Then validate the palette, and **fix it until it passes**:

```bash
python3 scripts/check_palette.py projects/$(cat .slug)/deck/identity.json
```

### 2. `deck/theme.css`

A complete Marp theme. Name it after the slug so it can't collide with another project:

```css
/* @theme af-<slug> */
@import url('https://fonts.googleapis.com/css2?family=<Display>:wght@…&family=<Body>:wght@400;600&display=swap');
@import 'default';

section { /* 1280×720; background, ink, body font ≥ 28px, generous padding, content pinned to top */ }
h1, h2 { /* display face; strong hierarchy */ }
/* footer, page number, lists, strong, tables (sparingly), code, images */

section.title { … }   /* the opening: this is where the identity announces itself */
section.hero  { … }   /* one enormous number and a line of context */
section.chart { … }   /* headline + full-width chart, minimal chrome */
section.split { … }   /* text on one side, chart on the other */
/* …plus any motif this identity needs: quote, section, closing */
```

Requirements:
- Every color comes from `identity.json`. Contrast was validated there, so don't drift from it.
- Body text is at least 28 px and headlines are clearly larger. Nothing smaller than 18 px
  except the footer.
- Images scale to fit their area (`max-width:100%; max-height:…`) and never overflow.
- Define every class listed in `identity.json` → `layouts`. The composer relies on them.
- Tasteful and specific, not generic. The title slide should make the identity obvious
  within a second.
