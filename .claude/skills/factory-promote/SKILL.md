---
name: factory-promote
description: Weekly curation pass — review recent projects and mark the good ones as featured
argument-hint: "[slug or 'review']"
allowed-tools: Read, Edit, Glob, Grep, Bash(python3 *), Bash(git log *)
---

## Recent projects

!`ls -1t projects/ 2>/dev/null | head -10`

## Instructions

Argument: **$ARGUMENTS** — a slug to promote, or `review` to assess the recent batch.

This skill exists because volume without curation makes a profile worse, not better. The
factory builds daily; you promote weekly. Only featured projects reach the top of the
showcase and the GitHub profile README.

### With `review`

Read `project.json`, `README.md`, and `VERIFY.md` for each of the last 7 projects. For
each, give a two-line verdict and a recommendation:

- **Promote** — would survive a recruiter clicking into it, or makes a genuinely good
  five-minute demo.
- **Keep** — fine, stays in the archive, not featured.
- **Fix** — one specific problem stands between it and promotion. Name the problem.
- **Retire** — flawed enough that it weakens the repo. Say why, plainly.

Judge against a hard bar, and apply it honestly:

1. Verification passed, and the data source is real and cited.
2. The finding is genuinely interesting to someone who doesn't know the author.
3. The README makes sense to a stranger in under a minute.
4. The deck could be presented cold without embarrassment.
5. It isn't a near-duplicate of something already featured.

Most projects should get **Keep**. If you're recommending promotion for more than two or
three out of seven, your bar has slipped — the whole point is that `featured` stays scarce
enough to mean something.

### With a slug

Set `featured: true` in that project's `project.json`, then run
`python3 scripts/build_index.py` to regenerate the showcase.

Tell the user to run `/factory-sync-profile` afterwards if they want it on their GitHub
profile too.
