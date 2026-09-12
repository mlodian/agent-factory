---
name: factory-review
description: Weekly review of the factory — assess this week's projects and pipeline health, and draft checkbox recommendations for the owner to confirm with /apply
context: fork
agent: reviewer
background: false
allowed-tools: Read, Glob, Grep, Write
---

## Instructions

Read `.review-context.md` first. It's the week's verified facts: PRs, runs, source
outages, backlog, and what's featured. Then read every project it lists as **Readable here**,
under `projects/<slug>/`: `project.json`, `README.md`, `VERIFY.md`, `data/SOURCE.md`, and
`deck/deck.md`. Skim `SPEC.md`, `ARCHITECTURE.md`, and `src/` as needed to judge method.
Also read `sources/registry.yml`, `backlog/ideas.yml`, and `backlog/built.yml`.

**Write the review to `.review.md` with the Write tool.** That file is the deliverable and
it becomes the GitHub issue body — a review that exists only as your reply is lost, and the
workflow fails. Write the file first, then reply with a two-line summary, not the review
itself. Follow the format below exactly. The `/apply` step parses the hidden `<!-- action:… -->` markers, so a marker you
mangle is an action that silently won't happen.

## Format

```markdown
**The week in one line:** <the single most important thing, plainly>

## Projects

### `<slug>` — <title>
<2–4 sentences: what it found, whether the method holds, the strongest and weakest point.>

- [ ] **Feature** — <one-line reason> <!-- action:feature slug:<slug> -->

<Repeat per project. Offer exactly ONE verdict line per project, chosen from:>
- [ ] **Feature** — … <!-- action:feature slug:<slug> -->
- [ ] **Unfeature** — … <!-- action:unfeature slug:<slug> -->     (only if currently featured)
- [ ] **Retire** — … <!-- action:retire slug:<slug> -->           (hides it from the showcase)
<or, when the right call is to leave it as is, write this with NO checkbox:>
**Keep** — <reason>
<or, when it needs work first, write this with NO checkbox, because a fix is not auto-applied:>
**Fix before featuring** — <the specific problem, with file and line>

## Factory health

<Bullets. Only what the context shows. For example: failed or blocked runs and why; open
source outages; stale PRs, which cause backlog conflicts; ready ideas left and the theme
balance; whether the daily schedule is on. End with the one action you'd take this week, if
any. None of these have checkboxes; they're for the human to act on.>

## Suggested ideas

<0–3 new backlog ideas, ONLY against sources already in the registry that are not
`unattended: false` and not denied. Each is a checkbox plus a hidden YAML block:>

- [ ] **Add idea:** <title> (source: `<registry id>`) — <why it's worth building> <!-- action:add-idea id:<n> -->
<!-- idea:<n>
slug: <kebab-case, unique vs backlog/ideas.yml>
title: <a question the data can answer>
theme: <finance | cyber | health | environment | marketing | science | civic | ml | data-eng | agents | web>
tags: [<3-5 tags>]
source: <registry id>
difficulty: <easy | medium | hard>
note: <what makes it interesting>
-->

---
<sub>Tick what you agree with, then comment <code>/apply</code>. Only ticked items are applied, as a pull request you merge.</sub>
```

## Rules

- **Only projects marked "Readable here" get a verdict.** For a project whose PR isn't merged
  yet, you may still recommend Feature, but add "(merge PR #N first)" to the reason, because
  `/apply` can only feature a project that's already on `main`.
- One verdict per project, and at most one checkbox per project.
- Number `add-idea` ids 1, 2, 3 in order. Each `<!-- idea:n` block sits directly under its
  checkbox and holds valid YAML.
- Don't write outside `.review.md`. Don't edit any project.
- If there were no projects this week, say so under Projects, and put the effort into
  Factory health and Suggested ideas.
