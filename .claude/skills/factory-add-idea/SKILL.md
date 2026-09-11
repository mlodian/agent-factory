---
name: factory-add-idea
description: Add a new project idea to the backlog, checked against the source registry
argument-hint: "[one-line description of the idea]"
allowed-tools: Read, Edit, Grep, WebFetch
---

## Instructions

Idea: **$ARGUMENTS**

1. Read `sources/registry.yml`. Find the registry source that best supports this idea.

   - If one fits, use its `id`.
   - If the idea needs a source that **isn't** in the registry, say so and stop. Name the
     source you'd want, its URL, and its licence, so the user can decide whether to add it
     to the registry. Don't add it to the backlog with an unregistered source — the
     factory will skip it anyway, and a backlog full of ineligible ideas is misleading.
   - If the idea would need a denied source (app-store reviews, yfinance, Google Trends…),
     say which rule it hits and suggest the registry alternative.

2. Check `backlog/ideas.yml` and `backlog/built.yml` for near-duplicates. If one exists,
   say so and ask whether this is meaningfully different before adding it.

3. Fetch the source endpoint once to confirm it's live and returns what the idea needs.

4. Sharpen the idea into something buildable in one run. A good idea asks a question the
   data can actually answer: "Does CVSS predict exploitation?" beats "cybersecurity
   dashboard". If the user's phrasing is vague, propose the sharpened version and use it.

5. Append to `backlog/ideas.yml`:

   ```yaml
   - slug: <kebab-case, ≤5 words>
     title: <the question or the thing>
     theme: <finance | cyber | health | environment | marketing | science | civic | ml | data-eng | agents>
     tags: [<3-5 tags>]
     source: <registry id>
     difficulty: easy | medium | hard
     status: ready
     added: <YYYY-MM-DD>
     note: <what makes this interesting, one line>
   ```

6. Report the entry you added in one or two lines.
