# agent-factory

An autonomous pipeline that builds one small, documented, demo-ready project per day.
A GitHub Actions cron invokes `/factory-run`, which runs six phases and opens a pull request.

## Non-negotiables

These hold on every automated run. If following one means shipping nothing today, ship
nothing. (Rules 1–4 also hold in interactive sessions. Rule 5 binds the unattended agent;
in an interactive session the human directing the work is the one changing the guardrails.)

1. **Never fabricate data.** Every dataset comes from an id in `sources/registry.yml`.
   If a source is unreachable, mark the idea `status: blocked` and pick another. If every
   candidate is blocked, stop and say so. A blocked run is a correct run; a fabricated one
   silently poisons the portfolio.
2. **Never state a number you did not measure.** Results in the README and the deck must
   appear in `VERIFY.md`, which is written by the thing that actually ran the code.
3. **Never claim a passing test you did not see pass.** The workflow re-runs verification
   independently; a false claim becomes a visible failure, not a hidden one.
4. **Scope is one unattended run.** Roughly ≤400 lines of source, no credentials beyond
   repo secrets, no paid APIs, no unbounded downloads. Prefer a small thing that runs to
   an ambitious thing that doesn't.
5. **Don't touch `.github/`, `.claude/`, `scripts/`, or `sources/registry.yml`** when
   running unattended. Those are the guardrails and they are a human's to change. The
   workflow enforces this with `.github/agent-settings.json` and by committing only
   `projects/<slug>/` and `backlog/`; don't look for a way around either.

## Layout

| Path | What |
|---|---|
| `sources/registry.yml` | The data-source allowlist. Read-only to you. |
| `backlog/ideas.yml` | Candidate projects. You may set `status:` and append ideas. |
| `backlog/built.yml` | Ledger of everything shipped. Append-only. |
| `projects/<date>-<slug>/` | Today's output. |
| `templates/` | README, DEMO, and Marp deck skeletons. Follow them. |
| `scripts/` | Deterministic checks. You may run them; don't edit them. |

## Project contract

Every project directory must contain:

```
SPEC.md              what we set out to build, written before any code
data/SOURCE.md       registry id, URL, licence, retrieval time, SHA256, record count
data/fetch_data.py   re-downloads the raw data and re-verifies the checksum
src/                 the implementation
tests/               pytest; the only place fabricated fixtures are allowed
verify.sh            one command, exit 0 = the project works
VERIFY.md            what verification actually printed, including timings and metrics
data/CONTEXT.md      optional: outside facts the story cites, each with a source URL
README.md            leads with the insight and hero chart; how to run it; what it can't do
ARCHITECTURE.md      how it works and why it's built that way
DEMO.md              a 5-minute script with timings and exact commands to type
deck/STORY.md        the data story: audience, tension, one insight, arc, evidence per beat
deck/identity.json   this project's own palette, fonts, and layouts (validated)
deck/theme.css       this project's own Marp theme, generated from identity.json
deck/charts/         make_charts.py + requirements.txt → SVG charts and FIGURES.md
deck/deck.md         story-driven Marp deck, 8–14 slides, speaker notes on each
deck/QA.md           fact-check, audience critique, and visual QA, with a VERDICT
project.json         metadata for the showcase index
```

## Presentation rules

- **Every project looks like itself.** Its own palette, type, and layouts, clearly
  different from recent projects. No shared template.
- **Every number on a slide traces** to what `verify.sh` printed, to `deck/charts/FIGURES.md`
  (computed by the committed chart script), or to a cited line in `data/CONTEXT.md`. The
  workflow checks every slide against its own verification log.
- **Charts are rebuilt by the workflow** from `deck/charts/make_charts.py` and the committed
  data. A chart can't show anything the data doesn't.
- **Lead with the insight.** A deck that reads like a results table has failed, even if
  every number in it is right.

## Style

- Python 3.12. Standard library first; add a dependency only when it earns its place.
- `requirements.txt` with pinned versions. No `latest`.
- Tests are real assertions about behaviour, not `assert True`.
- Write documentation for someone opening the repo in six months, and for someone
  watching a five-minute demo. Lead with what it does and how to run it.
- A "Limitations" section is required and must be specific. "Could be improved" is not a
  limitation; "only handles single-page PDFs, multi-page input silently truncates" is.
