---
name: factory-qa
description: Run the deck's quality check — fact-checker, audience-critic, and visual-qa in parallel — and write a consolidated verdict to deck/QA.md
---

## Instructions

Project: `projects/$(cat .slug)/`. QA round: **$ARGUMENTS** (default 1).

### 1. Run the three reviewers in parallel

Launch all three with the Agent tool **in a single message**, each with
**`run_in_background: false`**. Foreground calls in the same message still run
concurrently, and you get all three reports back at once without polling. Background
agents make you wait and poll, which burns the turn budget; that's how an earlier run
hit its turn cap. Give each the slug and ask for its findings as its final reply:

| Agent | Ask it to |
|---|---|
| `fact-checker` | Trace every number and claim in `deck/deck.md`, `deck/STORY.md`, and `README.md`, and audit the charts' honesty. Blocking vs minor. |
| `audience-critic` | Review the deck as the target audience: score hook, insight, clarity, so-what, credibility, and distinctiveness 1–5, and give the three highest-impact changes. |
| `visual-qa` | Run `bash scripts/preview_deck.sh <slug>`, open every slide image, and report layout defects per slide. |

Also run the mechanical gates yourself, so the verdict agrees with what CI will enforce:

```bash
python3 scripts/check_provenance.py <slug> --offline
python3 scripts/check_deck.py <slug>
```

(`check_deck` fails until `QA.md` exists. Ignore only that one line on this pass.)

### 2. Write `deck/QA.md`

```markdown
# Deck QA — round <n>

VERDICT: PASS            <!-- or FAIL -->

## Blocking
- [fact-checker] slide 4: "…" — <problem> → <fix>
- [visual-qa] slide 7: headline overlaps chart → <fix, and which file>
- [gate] <any FAIL from check_provenance / check_deck>

## Should fix
- …

## Audience scores
| Hook | Insight | Clarity | So-what | Credibility | Distinct |
|---|---|---|---|---|---|
| 4 | 3 | … |
Top changes: 1. … 2. … 3. …

## What works — keep it
- …
```

**The verdict is FAIL if** there is any blocking fact-check finding, any visual defect of
overflow, clipping, collision, a broken image, or illegible text, any FAIL from the
mechanical gates (other than QA.md itself missing on this pass), or any audience score
≤ 2. Otherwise PASS. Report the verdict as it is. QA exists to stop a weak deck, not to
wave one through.

### 3. Fix what failed, then re-check — up to two more rounds

If the verdict is FAIL, route each blocking finding to whoever owns it:

- Deck text, structure, ordering, or layout → `/factory-deck revise`
- A chart problem (label collision, wrong emphasis, a misleading scale) → `/factory-viz`
- A palette or theme defect (contrast, text overflowing its box) → `/factory-art`
- An untraceable claim → it gets removed or re-sourced, never waved through

Then run the three reviewers again and rewrite `deck/QA.md` as round *n+1*.

Stop after round 3 even if it still fails. Leave the honest `VERDICT: FAIL` in place: the
workflow opens the PR as a draft labelled `needs-work` with your report in the body, and a
human takes it from there. Never edit a verdict to PASS without fixing the problem.
