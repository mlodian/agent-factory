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

Run these five phases **in order**. Each is a gate: if one fails, stop and report. Do not
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

### 4. Present
Invoke `/factory-present`.

The presentation team turns the verified project into something worth presenting: a data
story, the project's own visual identity, charts rendered from the real data, a
story-led README, a deck with no fixed template, and a QA loop (fact-checker, audience
critic, visual QA) with up to two revision rounds. It writes `deck/QA.md` with an honest
verdict. The workflow rebuilds the charts and renders the deck. You don't run Marp for the
final output, though the team previews slides while it works.

If QA still fails after the revision rounds, continue to Ship anyway. The PR is opened as
a draft labelled `needs-work`, with the QA findings in the body.

### 5. Ship
Invoke `/factory-ship`.

Produces `project.json`, appends to `backlog/built.yml`, sets the used idea's
`status: built` in `backlog/ideas.yml`, and writes `PR_BODY.md`.

## Final report

End with a short summary: the slug, the data source and its record count, whether
verification passed, and anything a reviewer should look at closely. Be blunt about
weaknesses — the PR is reviewed by a human who benefits more from an honest caveat
than from a confident summary.
