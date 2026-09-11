---
name: factory-run
description: Build one complete documented demo-ready project end to end — the daily pipeline entry point
disable-model-invocation: true
argument-hint: "[optional-idea-slug]"
---

## Today

!`date -u +%Y-%m-%d`

## Instructions

You are running unattended. Nobody will answer a question, so decide and proceed.
Requested idea slug (may be empty — then choose from the backlog): **$ARGUMENTS**

Run these phases **in order**. Each is a gate: if one fails, stop and report. Do not
skip ahead, and do not start writing documentation for code that does not exist yet.

### 1. Pick
Invoke `/factory-pick-idea $ARGUMENTS`.

Produces `projects/<date>-<slug>/SPEC.md`. Write the chosen slug to `.slug` at the repo
root — the workflow reads that file.

**If every candidate idea is blocked, stop here.** Write `.slug` as empty, explain which
sources were unreachable, and end the run. Shipping nothing is the correct outcome; do
not relax the source rules to produce output.

### 2. Build
Invoke `/factory-build`.

Produces `data/fetch_data.py`, `data/SOURCE.md`, `src/`, `tests/`, `requirements.txt`,
`verify.sh`. The data must actually be downloaded during this phase — not stubbed.

### 3. Verify
Invoke `/factory-verify`.

This is the hard gate. `verify.sh` must exit 0 in a clean venv. Up to two repair attempts.
Produces `VERIFY.md` containing the real output — metrics, timings, row counts.

If it still fails after two attempts, **continue anyway** but write `VERIFY.md` with an
honest `STATUS: FAILED` header and the actual error. The workflow will open a draft PR
labelled `needs-work`. Never paper over a failure; a documented failure is useful, a
disguised one is not.

### 4. Document
Invoke `/factory-docs`.

Produces `README.md`, `ARCHITECTURE.md`, `DEMO.md`. Every number traces to `VERIFY.md`.

### 5. Deck
Invoke `/factory-deck`.

Produces `deck/deck.md` — 10 Marp slides with speaker notes. The workflow renders it to
HTML, PDF, and PPTX; you do not run Marp yourself.

### 6. Ship
Invoke `/factory-ship`.

Produces `project.json`, appends to `backlog/built.yml`, sets the used idea's
`status: built` in `backlog/ideas.yml`, and writes `PR_BODY.md`.

## Final report

End with a short summary: the slug, the data source and its record count, whether
verification passed, and anything a reviewer should look at closely. Be blunt about
weaknesses — the PR is reviewed by a human who benefits more from an honest caveat
than from a confident summary.
