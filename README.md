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
                 1  factory-pick-idea   idea-scout     choose an idea, confirm its source is live
                 2  factory-build       builder        fetch real data, write code + tests
                 3  factory-verify      verifier       clean-venv run, write VERIFY.md
                 4  factory-docs        doc-writer     README, ARCHITECTURE, DEMO (no shell)
                 5  factory-deck        deck-designer  10-slide Marp deck (no shell)
                 6  factory-ship        —              metadata, ledger, PR body
               then the workflow, which trusts none of the above:
                 scripts/verify.sh          re-runs the project in a fresh venv
                 scripts/check_provenance.py checks data, checksums, and claims
                 scripts/render_deck.sh      Marp → HTML / PDF / PPTX
                 → pull request: "verified", or a draft labelled "needs-work"
on merge       publish.yml → PDF/PPTX to a GitHub Release, rebuild the showcase site
Mondays        check-sources.yml → probe every data source, open an issue if one is down
```

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
| `/factory-promote review` | Weekly curation: which recent projects deserve `featured` |
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
.claude/agents/        idea-scout, builder, verifier, doc-writer, deck-designer
.github/               workflows + agent-settings.json (the CI agent's permission rules)
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
