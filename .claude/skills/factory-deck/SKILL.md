---
name: factory-deck
description: Write the 10-slide Marp presentation with speaker notes for the day's project
context: fork
agent: deck-designer
background: false
allowed-tools: Read, Edit, Glob
---

## Instructions

Read `README.md`, `VERIFY.md`, `ARCHITECTURE.md`, `DEMO.md`, and `data/SOURCE.md`.
Write two files: `deck/deck.md`, based on `templates/deck.template.md` with every
`{{placeholder}}` replaced, and `deck/architecture.mmd` for the diagram.

You have no shell — you don't render the deck. The workflow runs Marp and produces HTML,
PDF, and PPTX from your markdown.

### The ten slides

| # | Slide | What earns its place |
|---|---|---|
| 1 | Title | Project name, one-line pitch, date, your name |
| 2 | The problem | A real question someone actually has |
| 3 | Why it matters | Who is affected, and what it costs them |
| 4 | Architecture | The diagram — source → processing → output |
| 5 | How it works | The one genuinely interesting technical decision |
| 6 | Demo | Cues only. The live terminal is the content here |
| 7 | Results | Numbers from `VERIFY.md`, and nothing else |
| 8 | Limitations | What it doesn't do. Own this slide; it builds credibility |
| 9 | What's next | The honest next step, not a roadmap fantasy |
| 10 | Links & data | Repo, source with licence, attribution |

### Craft

- **One idea per slide.** If a slide needs a paragraph, it's two slides or it's a note.
- **Speaker notes on every slide**, in Marp's `<!-- -->` comment syntax. Notes carry the
  sentences you'd actually say — the slide carries the anchor.
- **Slide 4's diagram goes in its own file, `deck/architecture.mmd`**, written as a Mermaid
  `flowchart LR`. Don't put a Mermaid block inside `deck.md`, because Marp doesn't render
  Mermaid and it would appear as raw code. The workflow renders `architecture.mmd` to
  `architecture.svg`, and the template's slide 4 already embeds that SVG. Keep it to five
  or six nodes. A diagram nobody can read from the back of the room is just decoration.
- Slide 7: every number must appear in `VERIFY.md`. If `VERIFY.md` has no numbers, say
  what was built and what remains unmeasured. **Never estimate a number for a slide.**
- Slide 8 is not optional and not filler. "Trained on 400 rows, so the confidence interval
  is wide" is the kind of thing that makes an audience trust slides 1 through 7.
- Attribution on slide 10 is a licence obligation for several sources, not a courtesy.

### If verification failed

Say so on slide 1 and again on slide 7. A deck that presents a broken project as working
is the single worst thing this pipeline could produce — it would embarrass you in the one
setting where it matters. Present it as "here's how far it got and where it broke", which
is a genuinely respectable five-minute talk.
