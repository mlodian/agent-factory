---
name: factory-rehearse
description: Rehearse a project demo — quiz the presenter on the deck and tighten DEMO.md
argument-hint: "[project slug]"
allowed-tools: Read, Edit, Glob, Grep
---

## Instructions

Project: **$ARGUMENTS**. If empty, use the most recent directory under `projects/`.

Read the project's `README.md`, `VERIFY.md`, `ARCHITECTURE.md`, `DEMO.md`, and
`deck/deck.md`. Then act as a sharp, fair audience member — someone technical who wasn't
there when it was built.

### 1. Ask five questions, one at a time

Wait for the answer to each before asking the next. Mix:

- **Two about the data** — "Why this source and not X?", "What's in the 3% of rows you
  dropped?", "How old is this data?"
- **Two about the finding** — "Is that number significant or noise?", "What would change
  your conclusion?"
- **One hostile-but-fair** — the question a skeptic in the room would actually ask.

After each answer, say briefly what was strong and what a better answer would include.
Base that on what's actually in the project files. If the user's answer claims something
the files don't support, point it out — they'd rather hear it from you than on stage.

### 2. Tighten `DEMO.md`

After the five questions, propose concrete edits:

- Add any question they struggled with to the "Likely questions" section, with the answer
  the project files support.
- Cut anything that won't fit the five-minute timing.
- Flag any command in the script that isn't in `verify.sh`, since those are the ones that
  fail live.

Show the proposed edits and apply them only after the user agrees.
