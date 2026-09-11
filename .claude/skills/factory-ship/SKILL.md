---
name: factory-ship
description: Record project metadata, update the backlog ledger, and write the pull-request body
allowed-tools: Read, Edit, Glob, Grep, Bash(python3 *), Bash(date *)
---

## Instructions

The project is built, verified, documented, and has a deck. Record it.

### 1. `projects/<slug>/project.json`

```json
{
  "slug": "2026-09-12-cve-severity-vs-exploitation",
  "title": "Does CVSS actually predict exploitation?",
  "pitch": "One sentence.",
  "date": "2026-09-12",
  "theme": "cyber",
  "tags": ["vulnerability", "classification", "public-data"],
  "source": { "registry_id": "cisa-kev", "name": "CISA KEV", "records": 1381 },
  "status": "passed",
  "featured": false,
  "stack": ["python", "pandas", "scikit-learn"],
  "headline": "CVSS ≥ 9.0 covers only 24% of actually-exploited CVEs",
  "links": { "readme": "README.md", "deck": "deck/dist/deck.html", "demo": "DEMO.md" }
}
```

`status` is `passed` or `failed`, taken from `VERIFY.md` — never assumed.
`headline` is the single most interesting true finding, and it must appear in `VERIFY.md`.

**`featured` is always `false`.** Only a human sets it, during a weekly `/factory-promote`
pass. Do not set it to `true` no matter how good the project seems; that judgment isn't
yours to make and the showcase depends on it staying scarce.

### 2. Append to `backlog/built.yml`

```yaml
- slug: <slug>
  date: <YYYY-MM-DD>
  theme: <theme>
  tags: [<tags>]
  source: <registry id>
  status: passed | failed
```

Append only. Never rewrite or reorder existing entries — this ledger is what stops the
pipeline rebuilding the same idea in three weeks.

### 3. Update `backlog/ideas.yml`

Set the used idea's `status: built` and add `built_on: <date>`. Leave everything else
alone.

### 4. Write `PR_BODY.md`

```markdown
## <Title>

<Pitch.>

**Source:** <name> (`<registry id>`) — <n> records, <licence>
**Verification:** PASSED / FAILED
**Headline:** <the finding>

### Review checklist
- [ ] The finding in the README matches VERIFY.md
- [ ] Quickstart commands work from a clean clone
- [ ] Deck slide 7 contains no number absent from VERIFY.md
- [ ] Limitations section is specific and honest

### Notes for the reviewer
<Anything genuinely worth a second look. Be specific about what you're least
confident in — this section is the most useful part of the PR.>
```

If verification failed, say so in the first line of the body. The workflow opens the PR as
a draft labelled `needs-work`, and the body should agree with the label rather than
contradict it.
