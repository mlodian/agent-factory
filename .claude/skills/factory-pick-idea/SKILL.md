---
name: factory-pick-idea
description: Choose today's project from the backlog, confirm its data source is live, and write SPEC.md
context: fork
agent: idea-scout
background: false
allowed-tools: Read, Edit, Glob, Grep, WebFetch, Bash(python3 *), Bash(date *)
---

## Today

!`date -u +%Y-%m-%d`

## Recently built

!`tail -40 backlog/built.yml 2>/dev/null || echo "(none yet — this is the first run)"`

## Instructions

Requested **idea** slug from `backlog/ideas.yml` (may be empty): **$ARGUMENTS**
Today's project directory is `projects/<today>-<idea slug>`.

1. Read `backlog/ideas.yml` and `sources/registry.yml`.

2. If a slug was requested, use it. Otherwise consider only entries with `status: ready`,
   and **reject** any whose `tags` share 2 or more tags with anything built in the last 14
   days. Rotate across `theme` values — don't ship three dashboards in a row.

   Skip any idea with a `requires:` entry whose secret isn't set in the environment.
   `anthropic-api-key` means `FACTORY_ANTHROPIC_API_KEY` must be non-empty. Check with
   `python3 -c "import os; print(bool(os.environ.get('FACTORY_ANTHROPIC_API_KEY')))"`.
   The Claude Code OAuth token running you does **not** count; it can't serve a project's
   own API calls. (The key has that prefixed name on purpose. Under its standard name it
   would outrank the OAuth token and switch the factory's own billing to the API.)

   An idea with `source: none` has no dataset (a simulator, a tool). It skips step 3's
   source check, but the no-invented-results rule still applies in full.

3. **Source check, in this order:**
   - The idea's `source:` must name an `id` present in `sources/registry.yml`.
     An idea naming an unknown source is ineligible. You may not invent one.
   - The source must not appear in the registry's `denied:` block.
   - The source must not be marked `unattended: false`. Those sources block automated
     traffic intermittently, and they're reserved for projects a human fetches by hand.
   - **Actually fetch the endpoint** and confirm it returns 2xx and the shape you expect.
     Record the record count you observed.

4. If the source is unreachable or returns something unexpected, set that idea's
   `status: blocked` with a one-line reason and a date, then try the next candidate.
   Repeat up to 5 candidates.

   **Under no circumstances substitute generated, simulated, sample, or placeholder data
   for a source that did not respond.** If all 5 candidates are blocked, write no SPEC,
   report which sources failed, and stop. That is a successful run with no output.

5. If fewer than 5 `ready` ideas remain, append new ones — but only against sources
   already in the registry. Adding a *new* source is a human decision; note it in your
   report instead of doing it.

6. Write `projects/<date>-<slug>/SPEC.md`:

```markdown
# <Title>

**Pitch:** one sentence a non-specialist understands.
**Audience:** who this is for.

## Data source
- Registry id: <id from registry.yml>
- Endpoint:    <exact URL you fetched>
- Licence:     <from the registry>
- Observed:    <n records / bytes, confirmed live at HH:MM UTC>

## Acceptance criteria
1. <concrete, checkable by running something>
2. ...   (3–5 of these)

## Stack
<languages, libraries — keep it small>

## Non-goals
- <what this deliberately does not do>
```

7. Write the **project directory name** to `.slug` at the repo root, with no trailing
   newline. That's the dated one you created in step 6 — `2026-09-12-nyc-311-response-equity`,
   not the bare idea slug `nyc-311-response-equity`. The workflow reads this file to find the
   project, and a bare idea slug fails validation.

## Scope discipline

This must be buildable *and verifiable* in one unattended run: roughly ≤400 lines of
source, no credentials, no paid APIs, no download over ~50 MB. If the idea is bigger than
that, cut its scope in the SPEC and say so under Non-goals rather than picking something
else. An honest small project beats an abandoned ambitious one.
