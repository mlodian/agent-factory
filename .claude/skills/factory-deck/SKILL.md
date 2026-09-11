---
name: factory-deck
description: Compose the story-driven Marp deck from STORY.md, the charts, and the project's own theme — or revise it from deck/QA.md
context: fork
agent: slide-composer
background: false
allowed-tools: Read, Glob, Grep, Write, Edit
---

## Instructions

Project: `projects/$(cat .slug)/`. Mode: **$ARGUMENTS** (empty = compose from scratch;
`revise` = address the findings in `deck/QA.md`).

Read `deck/STORY.md`, `deck/identity.json` (especially `layouts`), `deck/theme.css` (the
classes and what they look like), the SVGs in `deck/charts/` and `deck/charts/FIGURES.md`,
plus `VERIFY.md`, `data/CONTEXT.md` if it exists, and `README.md`.

### Write `deck/deck.md`

```markdown
---
marp: true
theme: af-<slug>            # exactly the name in deck/theme.css's @theme comment
paginate: true
footer: "<short project name> · agent-factory"
---

<!-- _class: title -->
<!-- _paginate: false -->

# <The insight, as a headline>

<one line of context · the date · github.com/mlodian/agent-factory>

<!--
Speaker notes: the sentences you'd actually say.
-->

---

<!-- _class: hero -->
…
```

Structure, driven by the story rather than a template:
- **8–14 slides.** Title, then the answer within the first three slides, then the beats in
  the story's order, then credibility (the data and method, briefly), the caveat that
  matters, the so-what, and links with attribution.
- **Use the art director's classes** via `<!-- _class: … -->`, and vary them. A hero number,
  then a full-bleed chart, then a split feels designed. Ten identical layouts feel like a
  report.
- **Charts** go in as `![](charts/<file>.svg)`. The theme sizes them, so don't set
  dimensions unless the class requires it.
- **Headlines state the point** of the slide as a sentence.
- **≤ 40 visible words per slide** as a target (the gate fails above 90). The detail goes in
  the speaker notes. Every slide gets notes.
- An architecture diagram is optional. Include it only if the method *is* the story. If
  you do, write `deck/architecture.mmd` (a Mermaid `flowchart LR`) and embed
  `![](architecture.svg)`.

### The number rule

Every number on a slide must appear, exactly as written, in `VERIFY.md`'s printed output,
in `deck/charts/FIGURES.md`, or in a cited line of `data/CONTEXT.md`. Years and small
counts are exempt. The provenance gate checks every slide against the workflow's own
verification log. If you need a number that isn't in those files, **don't write it**. Note
it for the viz designer instead.

### In `revise` mode

Read `deck/QA.md`. Fix every **blocking** item and as many **should-fix** items as you can.
Where a fix needs a chart change (a label collision, the wrong emphasis), say so explicitly
at the end of your reply, so the orchestrator can route it to the viz designer.
