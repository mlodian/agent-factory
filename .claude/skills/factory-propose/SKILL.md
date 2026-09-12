---
name: factory-propose
description: Propose three candidate projects for the owner to choose from, each with a source verified live
context: fork
agent: idea-scout
background: false
allowed-tools: Read, Glob, Grep, WebFetch, Write, Edit, Bash(python3 *), Bash(date *)
---

## Today

!`date -u +%Y-%m-%d`

## Already built

!`tail -40 backlog/built.yml 2>/dev/null || echo "(nothing yet)"`

## Instructions

Ideas the owner already passed over (don't propose these again): **$ARGUMENTS**

Pick **three** candidates and write them to `.proposals.md` for the owner to choose from.
Write the file with the Write tool — it becomes a GitHub issue, and a proposal that exists
only in your reply is lost.

1. Read `backlog/ideas.yml`, `backlog/built.yml`, and `sources/registry.yml`.
2. Consider entries with `status: ready`, skipping anything whose `requires:` secret isn't
   set, anything on a `unattended: false` source, and anything listed above as passed over.
3. **Choose three that differ from each other** — different themes, different data, different
   shapes of answer. Three cybersecurity dashboards is a bad menu. At least one should be
   an easy, high-confidence build.
4. **Fetch each source before proposing it.** Confirm it returns 2xx and the shape you
   expect, and note what you saw. Never propose a source you didn't just check.
5. If fewer than three good candidates exist in the backlog, propose new ones — but only
   against sources already in the registry.

## Format for `.proposals.md`

```markdown
Three candidates for the next project. **Tick one and comment `/build`.**
For three different ones, comment `/more`. To pick something else, comment `/build <slug>`.

---

- [ ] **<Title — the question it answers>** <!-- proposal: <backlog slug> -->

  **Why it's worth building:** <2 sentences — what's surprising or useful about the answer>
  **Data:** `<registry id>` — <what you saw when you fetched it: n records, range, HTTP 200>
  **Likely headline:** <the finding you expect, hedged honestly — you haven't run it yet>
  **Shape:** <the charts/visuals it would produce>
  **Effort:** easy | medium | hard — <what makes it that>
  **Risk:** <what could make this fall flat: thin data, a null result, a slow API>

- [ ] …  (three in total)
```

Be honest in **Likely headline**: you're predicting, not reporting. If the honest answer is
"the interesting part is whether there's any effect at all", say that. And in **Risk**, say
the real risk — a proposal that hides its weakness wastes the owner's pick.
