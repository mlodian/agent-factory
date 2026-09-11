---
name: factory-story
description: Find the insight in a verified project and write the data story — audience, tension, arc, and the evidence each beat needs
context: fork
agent: story-strategist
background: false
allowed-tools: Read, Glob, Grep, Write, Edit
---

## Instructions

Project: `projects/$(cat .slug)/`

Read `SPEC.md`, `VERIFY.md` (especially the printed output and headline numbers),
`data/SOURCE.md`, and enough of `src/` to understand what was actually measured. Skim the
`deck/STORY.md` of the last five projects under `projects/` too. This story should not reuse
their arc.

Write `deck/STORY.md`:

```markdown
# Story: <working title — a claim, not a topic>

**Audience:** <who, specifically, and what they do with this>
**What they believe going in:** <the default assumption>
**What the data says instead:** <the tension, plainly>
**The one insight:** <one sentence a colleague could repeat>
**Arc:** <name it — e.g. myth vs. reality · the hidden base rate · slow reveal ·
  before/after · the outlier that explains the rest · decision between two options>
  — <why this arc fits THIS finding>
**Mood for the art director:** <3–5 words, e.g. "clinical, urgent, nocturnal"> —
  <one line on why>

## Beats

1. **<Beat headline, written as a claim>**
   - Evidence: <exact figure> — from <VERIFY.md: the printed line> | <FIGURES.md: to be
     computed — define it precisely> | <CONTEXT.md: cited>
   - Visual: <form — hero number / emphasis bar / line / dumbbell / …> showing <what>,
     emphasis on <the thing>
   - Why it's here: <what this beat does for the arc>
2. …   (5–8 beats)

## The so-what
<The action or implication, stated no more strongly than the evidence allows.>

## Caveats that must appear on a slide
- <the limitation that would change a decision, and why>

## For the chart script — derived figures
- <label>: <exact definition, computed from which file or function>

## Outside context
- <fact> — <source URL>   (also written to data/CONTEXT.md; omit the section if none)
```

If the story needs an outside fact (a population, a historical record, a regulation), write
it to `data/CONTEXT.md` as a bullet **with a source URL**. A number without a URL there
fails the provenance gate, and should.

## What makes it good

- The insight is specific and a little uncomfortable, not "X varies by Y."
- Every beat has evidence the project really produced, or that the chart script can
  compute from the committed data.
- It's honest. If the finding is modest, the story is about the modest finding told well,
  not an inflated one.
