---
name: factory-build
description: Build the implementation, tests, and data-fetch layer from SPEC.md
context: fork
agent: builder
background: false
allowed-tools: Read, Edit, Write, Glob, Grep, Bash, WebFetch
---

## Instructions

Read `projects/$(cat .slug)/SPEC.md`. Build exactly what it specifies — not more.

Work in this order. The data comes first, because everything downstream depends on it
being real.

### 1. `data/fetch_data.py`

A standalone script that downloads the raw data from the SPEC's endpoint into
`data/raw/`, then prints the SHA256 and record count. It must:

- Use only `urllib`/`requests` against the exact URL in the SPEC.
- Send a `User-Agent` of exactly `agent-factory/1.0 (<email>)`, where `<email>` comes from the
  `FACTORY_CONTACT_EMAIL` environment variable. Read it at runtime and never hardcode an
  address. **Don't put a URL in the User-Agent.** SEC EDGAR's firewall returns 403 for
  any UA containing one, even when an email is present too. If the variable is unset, send
  `agent-factory/1.0` and expect SEC to refuse the request.
- For OpenAlex and Crossref, pass the same email as `&mailto=` to join the polite pool.
- Be re-runnable: if `data/raw/<file>` exists and its SHA256 matches `SOURCE.md`, skip
  the download and say so.
- Follow redirects, then fail loudly on a non-2xx final response. Before saving, confirm
  the body really is the expected format: parse the JSON, count the CSV rows. APIs
  sometimes answer with a 200 HTML error page or a bot-challenge page, and a client that
  doesn't follow redirects saves the redirect page itself. The provenance gate rejects
  both. Never write a fallback or sample file.

**Run it.** If it fails, the source is not usable — report that and stop, rather than
working around it.

### 2. `data/SOURCE.md`

Fill in from what you actually observed:

```markdown
# Data provenance
- Source:     <name>
- Registry:   <id — must match sources/registry.yml>
- URL:        <exact endpoint>
- Retrieved:  <ISO-8601 UTC>
- Licence:    <from registry>
- File:       raw/<filename>
- SHA256:     <real hash from the download>
- Records:    <n rows × m cols, date range if applicable>
- Fetch:      python3 data/fetch_data.py
```

### 3. `src/`

The implementation. Python 3.12, standard library first. Small modules, named for what
they do. Put helper scripts under `src/`. Don't create a `scripts/`, `templates/`, or
`sources/` directory inside the project, because the CI permission rules block edits to
those names at any depth. No `np.random`, no `faker`, no `make_classification` — `factory-verify` and the
workflow both grep for these and will fail the build.

### 4. `tests/`

Real pytest assertions about behaviour. This is the **only** place fabricated fixtures
belong, and there they're correct — a unit test that depends on a live network call is a
bad test. Cover at least: the happy path, one edge case, one malformed input.

### 5. `requirements.txt`

Pinned versions (`pandas==2.2.3`, not `pandas`). Only what's actually imported, **plus
`pytest`**. `verify.sh` runs in a brand-new virtualenv with nothing preinstalled, so a
project that forgets pytest fails verification before a single test runs.

### 6. `verify.sh`

One executable script; exit 0 means the project works. Install deps, run the tests, then
run the project end-to-end on the real data and print the headline numbers. Keep it under
two minutes.

```bash
#!/usr/bin/env bash
set -euo pipefail
pip install -q -r requirements.txt
pytest -q tests/
python3 -m src.main --report
```

## Discipline

- Every acceptance criterion in the SPEC must be exercised by `verify.sh`.
- If a criterion turns out to be unachievable, don't silently drop it — implement what you
  can and record the gap under the SPEC's Non-goals. `factory-docs` will surface it.
- Don't write the README. That's a later phase, handled by an agent that has no shell and
  can therefore only describe what it can actually read.
