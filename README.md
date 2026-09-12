# agent-factory

A Claude Code pipeline that builds one small, documented, demo-ready project every day
from real public data. It verifies each project independently, then opens a pull request
for a human to review.

**Showcase:** [mlodian.github.io/agent-factory](https://mlodian.github.io/agent-factory)

Every project ships with a README, an architecture note, a five-minute demo script, and a
10-slide deck (HTML, PDF, PPTX). Every dataset is cited with its URL, licence, and SHA256
checksum. Nothing merges on its own.

## How a day works

```
05:00 Manila   GitHub Actions cron → claude-code-action → /factory-run
                 1  factory-pick-idea   idea-scout        choose an idea, confirm its source is live
                 2  factory-build       builder           fetch real data, write code + tests
                 3  factory-verify      verifier          clean-venv run, write VERIFY.md
                 4  factory-present     the presentation team (below)
                 5  factory-ship        —                 metadata, ledger, PR body
               then scripts/gate.sh, which trusts none of the above:
                 charts      rebuilt from the committed chart script + data
                 verify      verify.sh in a fresh venv, output captured
                 provenance  data, checksums, fabrication, every slide number vs that log
                 deck        own identity, ≥ 2 real charts, no walls of text, QA signed off
                 render      Marp → HTML / PDF / PPTX
                 → pull request: "verified", or a draft labelled "needs-work"
on merge       publish.yml → PDF/PPTX to a GitHub Release, rebuild the showcase site
Mondays        check-sources.yml → probe every data source, open an issue if one is down
Saturdays      weekly-review.yml → a read-only reviewer opens a review issue (see below)
```

## The weekly review

Every Saturday at 09:00 Manila, a reviewer agent reads the week's projects and the
factory's health, then opens an issue titled **"Weekly review — week of …"**. GitHub emails
it to you.

1. **Read it.** Each project gets a verdict and a reason: *Feature*, *Keep*, *Fix before
   featuring*, or *Retire*. The reviewer holds a hard bar and checks methods, not just
   numbers. After that come factory health (failed runs, source outages, stale PRs,
   backlog depth) and up to three suggested ideas.
2. **Tick** the recommendations you agree with, then comment **`/apply`**.
3. `/apply` validates the ticked items and opens a PR that changes only `featured` / `retired`
   flags and the backlog. It reports anything it had to skip, such as "merge its PR first".
   **Merge the PR** to publish.

Nothing is featured unless you tick it *and* merge it. The reviewer has no shell, no web
access, and no way to commit. Only the repo owner's `/apply` comment triggers changes.
Run a review on demand from **Actions → Weekly review → Run workflow**, or locally with
`/factory-review`.

## Usage limits and resuming

A full run is a lot of agent work, and it can hit your Claude plan's usage limit partway
through. That used to throw the run away. Now it doesn't:

- **Every phase checkpoints.** As soon as a phase finishes, its output is committed to the
  project's branch and the phase name is recorded in `projects/<slug>/.phases`.
- **A paused run leaves an open PR** labelled `in-progress`, listing the phases already done.
- **`resume.yml` retries hourly.** It re-dispatches the workflow, which skips finished
  phases and continues. It gives up after 8 attempts and labels the PR `stalled`.
- **Rerunning by hand does the same thing.** Run the workflow again with the same slug. To
  start over instead, tick **fresh** on Present project.

So a usage limit costs you one phase, not a run. To lower usage: Opus does the work where
taste shows (story, art direction, audience critique, docs, idea picking) and Sonnet does
the rest (build, verify, charts, slide composition, fact-checking, visual QA).

## The presentation team

Each project gets a presentation built for its own finding, not poured into a template.

| Step | Agent | Produces |
|---|---|---|
| Story | **story-strategist** | `deck/STORY.md`: audience, the tension, one insight, an arc chosen for this finding, evidence for every beat |
| Identity | **art-director** | `deck/identity.json` + `deck/theme.css`: its own palette, type pairing, and layouts, validated for contrast and colorblind separation, and distinct from recent decks |
| Charts | **viz-designer** | `deck/charts/make_charts.py`: one chart per beat, rendered from the real data with the project's identity via `scripts/chartkit.py` |
| README | **doc-writer** | Leads with the insight and the hero chart |
| Deck | **slide-composer** | 8–14 story-driven slides with varied layouts and speaker notes |
| QA | **fact-checker** · **audience-critic** · **visual-qa**, in parallel | `deck/QA.md`: every claim traced, the deck scored as its audience would see it, and every slide rendered and inspected. Failures loop back for up to two revision rounds. |

To give an existing project a new presentation: **Actions → Present project → Run workflow**,
then enter its slug. It opens a PR with the new deck.

## Why you can trust the output

An unattended generator tends to drift into slop: code that doesn't run, READMEs that
describe code that isn't there, and decks with invented numbers. The defences here, from
softest to hardest:

| Layer | What it stops |
|---|---|
| **Source allowlist** (`sources/registry.yml`) | 28 sources across 8 domains, 27 verified live for automated use, plus a `denied:` list (app-store scraping, yfinance, Google Trends, personal data, synthetic data). The agent can't invent a source. |
| **Split agents** | The doc and deck agents have no shell, so they can only describe what they can read. |
| **Provenance gate** (`scripts/check_provenance.py`) | Fails the build on a checksum mismatch, an undeclared data file, an HTML error page saved as data, an unregistered or denied source, synthetic-data generators outside `tests/`, a deck number missing from `VERIFY.md`, or leftover template placeholders. |
| **Independent re-verification** | The workflow re-runs every project in a fresh venv. If the agent's claim and the real result disagree, the disagreement shows up in the PR. |
| **Scoped commits** | The PR can only contain `projects/<slug>/` and `backlog/`. |
| **Human merge** | Every project is a PR, and `featured` is set only by a person. |

When every candidate source is down, the correct result is an empty day. The agent is
told so explicitly.

## Setup

You need a Claude Pro, Max, Team, or Enterprise plan, and admin rights on the repo.

```bash
# 1. Claude Code CLI (native installer, no Node needed)
curl -fsSL https://claude.ai/install.sh | bash

# 2. A one-year OAuth token for CI (prints the token; it isn't saved anywhere)
claude setup-token

# 3. GitHub CLI
brew install gh && gh auth login

# 4. Create the repo and push
cd ~/Documents/agent-factory
gh repo create mlodian/agent-factory --public --source=. --push
```

Then, under **Settings → Secrets and variables → Actions**:

| Name | Kind | Required | Purpose |
|---|---|---|---|
| `CLAUDE_CODE_OAUTH_TOKEN` | Secret | **Yes** | The token from step 2. Runs bill against your Claude plan. |
| `FACTORY_CONTACT_EMAIL` | Variable | Recommended | Sent in the User-Agent to SEC EDGAR, OpenAlex, and Crossref, which ask for a contact address. Pick which address they see. |
| `FACTORY_ANTHROPIC_API_KEY` | Secret | Optional | Unlocks backlog ideas whose projects call the Claude API themselves. |

> **Don't name that last one `ANTHROPIC_API_KEY`.** Claude Code gives `ANTHROPIC_API_KEY`
> precedence over `CLAUDE_CODE_OAUTH_TOKEN`. Under that name it would quietly move every
> factory run from your subscription to per-token API billing.

Finally, set **Settings → Pages → Source** to "GitHub Actions", and **Settings → Actions →
General → Workflow permissions** to allow Actions to create pull requests.

### First runs

Run it by hand before trusting the cron: **Actions → Daily project → Run workflow**.
You can pass an idea slug, for example `cvss-vs-exploitation`. Once three runs in a row
produce a PR labelled `verified`, leave the schedule on.

## Using it by hand

Open Claude Code in this directory:

| Command | What it does |
|---|---|
| `/factory-run [slug]` | The whole pipeline, locally |
| `/factory-add-idea "…"` | Add an idea, checked against the source registry |
| `/factory-present [slug]` | Run the presentation team on a built project |
| `/factory-review` | The weekly review, run locally (writes `.review.md`) |
| `/factory-promote review` | Ad-hoc curation: which recent projects deserve `featured` |
| `/factory-sync-profile` | Update the "Recent builds" section of your GitHub profile README |
| `/factory-rehearse [slug]` | Practise a demo. It asks the questions an audience would. |

```bash
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/check_sources.py              # is every data source up?
.venv/bin/python scripts/check_provenance.py <slug>    # gate one project
bash scripts/verify.sh <slug>                          # re-run one project cleanly
.venv/bin/python scripts/build_index.py && open site/index.html
```

## Layout

```
sources/registry.yml   data-source allowlist (+ denied list)
backlog/ideas.yml      32 ideas across finance, cyber, health, environment,
                       marketing, civic, science, data engineering, agents
backlog/built.yml      append-only ledger — stops repeat builds
.claude/skills/        factory-* — the procedures
.claude/agents/        idea-scout, builder, verifier, doc-writer, reviewer, and the
                       presentation team: story-strategist, art-director, viz-designer,
                       slide-composer, fact-checker, audience-critic, visual-qa
.github/               workflows + agent-settings.json / reviewer-settings.json (CI permission rules)
scripts/               deterministic checks the agent can run but not edit
templates/             README, DEMO, and deck skeletons + Marp theme
projects/<date>-<slug>/  one directory per shipped project
```

## Costs and limits

Runs draw on your Claude plan's usage limits, not per-token billing. A full build is a
heavy agentic run. The builder and verifier use Sonnet, while picking, writing, and deck
design use Opus. `--max-turns 150` and a 60-minute job timeout cap a runaway. If daily
runs crowd out your own usage, change the cron to Mon/Wed/Fri.

GitHub turns off scheduled workflows in public repos after 60 days without activity.
Daily PRs count as activity, so this only matters if you pause the factory.
