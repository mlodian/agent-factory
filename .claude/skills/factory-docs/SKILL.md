---
name: factory-docs
description: Write README, ARCHITECTURE, and DEMO docs from the code and verification output
context: fork
agent: doc-writer
background: false
allowed-tools: Read, Edit, Glob, Grep
---

## Instructions

The project exists on disk and has already been verified. Read it, then document it.

You have **no shell**. That is deliberate: it means you can only describe what you can
actually read, which is the whole point of this phase.

Read first, in this order: `SPEC.md`, `VERIFY.md`, `data/SOURCE.md`, `src/`, `tests/`,
`verify.sh`. Then write three files from `templates/`.

### `README.md`

Lead with what it does and how to run it. Structure:

1. **One-line description**, then one paragraph of context — why this is interesting.
2. **Quickstart** — the exact commands, copied verbatim from `verify.sh`. If a command
   isn't in `verify.sh` or the source, don't invent it.
3. **What it found** — the results. Every number comes from `VERIFY.md`'s headline
   section. No number there means no number here.
4. **Data** — source name, link, licence, record count, and the one-line fetch command,
   all from `data/SOURCE.md`. Credit the source properly; several licences require it.
5. **How it works** — three or four sentences, then link to `ARCHITECTURE.md`.
6. **Limitations** — required, and specific.

### `ARCHITECTURE.md`

How it works and why it's built that way. Include the data flow from source to output,
the key design decisions with their trade-offs, and what you'd change with more time.
Where a decision is visible in the code, cite the file.

### `DEMO.md`

A five-minute script someone can follow cold. Timings that add to 5:00, the exact
commands to type, what to say while each runs, the one number to point at, and the
question you'll most likely be asked with its answer. Presenting is the deliverable
here — write it for a person standing in front of an audience with a terminal open.

## Rules

- **If `VERIFY.md` says `STATUS: FAILED`, say so in the README**, near the top, with the
  real error. Do not write around it. A documented failure is honest; a disguised one
  discredits every other project in the repo.
- Every claim traces to a file you read. Every command appears verbatim in `verify.sh` or
  the source.
- "Limitations" must be specific. "Could be improved" is not a limitation; "only handles
  single-page PDFs — multi-page input is silently truncated" is.
- No marketing voice. No "powerful", "seamless", "cutting-edge". Describe what it does.
- Write for two readers at once: someone opening the repo in six months, and someone
  watching a five-minute demo.
