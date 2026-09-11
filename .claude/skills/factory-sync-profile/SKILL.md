---
name: factory-sync-profile
description: Regenerate the "Recent builds" section of the mlodian/mlodian GitHub profile README from featured projects
disable-model-invocation: true
allowed-tools: Read, Edit, Glob, Bash(gh *), Bash(python3 *), Bash(git *)
---

## Featured projects

!`grep -l '"featured": true' projects/*/project.json 2>/dev/null || echo "(none featured yet)"`

## Instructions

Your GitHub profile README lives in a separate repo named after your username:
`github.com/mlodian/mlodian`. Its README renders at the top of your profile page.

1. If `../mlodian` doesn't exist locally, clone it:
   `gh repo clone mlodian/mlodian ../mlodian`.
   If the repo doesn't exist on GitHub yet, stop and tell the user to create it —
   `gh repo create mlodian/mlodian --public --add-readme` — rather than creating it
   yourself. It's their public profile; that's their call.

2. Collect every `project.json` with `"featured": true`, newest first, **max 6**.
   Never include unfeatured projects, however many there are.

3. In `../mlodian/README.md`, replace only the content between these markers, leaving
   everything else untouched:

   ```markdown
   <!-- factory:start -->
   <!-- factory:end -->
   ```

   If the markers are missing, append them in a section titled `## Recent builds` at the
   end, and tell the user so they can move the section wherever they like.

4. Each entry is one line:

   ```markdown
   - **[Title](https://github.com/mlodian/agent-factory/tree/main/projects/<slug>)** — headline · [deck](https://mlodian.github.io/agent-factory/projects/<slug>/deck/dist/deck.html)
   ```

5. Show the user the diff. **Do not commit or push** — the profile is public-facing and
   they should see the change before it goes live. Give them the exact commands:
   `cd ../mlodian && git commit -am "Update recent builds" && git push`.
