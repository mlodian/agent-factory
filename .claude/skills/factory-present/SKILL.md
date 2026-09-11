---
name: factory-present
description: Run the presentation team on a verified project — story, visual identity, charts, README, deck, and a QA loop — so it ships with a unique, insight-driven presentation
argument-hint: "[slug — defaults to .slug]"
---

## Instructions

Slug: **$ARGUMENTS** — if empty, read it from `.slug`. If a slug was given, write it to
`.slug` first (no trailing newline), because every team skill reads it from there.

The project is built and verified. This turns it into something worth presenting. Run these
in order, since each one builds on the last. Invoke each step with the Skill tool, which
waits for it to finish. If a skill is ever unavailable, call its agent directly with the
Agent tool and `run_in_background: false`. Never background a step and then poll for it.

1. **Story:** `/factory-story` → `deck/STORY.md` (+ `data/CONTEXT.md` if it cites outside facts)
2. **Identity:** `/factory-art` → `deck/identity.json`, `deck/theme.css`
3. **Charts:** `/factory-viz` → `deck/charts/make_charts.py`, SVGs, `FIGURES.md`
4. **README:** `/factory-docs` → `README.md`, `ARCHITECTURE.md`, `DEMO.md`, led by the story
   with the hero chart embedded
5. **Deck:** `/factory-deck` → `deck/deck.md`
6. **QA:** `/factory-qa 1` → `deck/QA.md`

### The revision loop

If `deck/QA.md` says `VERDICT: FAIL`, fix it, **up to two more rounds**:

- Route each blocking finding to whoever owns it. Deck text, structure, and layout go to
  `/factory-deck revise`. A chart problem (collision, wrong emphasis, a misleading scale)
  goes to `/factory-viz` first. A palette or theme defect (contrast, overflow caused by
  CSS) goes to `/factory-art` first. An untraceable claim is removed or re-sourced; it is
  never waved through.
- Then run `/factory-qa <round>` again.

After round 3, stop, even on FAIL. Leave the honest `VERDICT: FAIL` in `QA.md`. The
workflow will open the PR as a draft labelled `needs-work`, and the human can take it from
there. Never edit `QA.md` into a PASS without actually fixing the problems.

### Report

End with the story's one insight, the identity's name and mood, the number of charts, the
QA verdict and the rounds it took, and anything a reviewer should look at closely.
