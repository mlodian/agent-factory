---
name: factory-verify
description: Run the project in a clean virtualenv until it passes, and record what actually happened
context: fork
agent: verifier
background: false
allowed-tools: Read, Edit, Grep, Glob, Bash
---

## Instructions

This is the gate the whole pipeline rests on. Your job is to find out whether the project
actually works — not to make the transcript look successful.

1. Run the project in a fresh virtualenv and capture **all** output:

   ```bash
   bash scripts/verify.sh "$(cat .slug)"
   ```

   The script builds a new venv every time. That clean environment is the point: it
   catches the dependency the builder forgot to pin because it happened to already be
   installed. The workflow runs this exact script again after you finish, so your result
   and the independent one should agree.

2. Also run the data half of the provenance gate:
   `python3 scripts/check_provenance.py "$(cat .slug)" --data-only`.
   (The docs don't exist yet at this phase. The workflow runs the full gate at the end.)
   Fix any `fabrication` or `provenance` failure in the project itself. The gate is
   correct by definition. Don't try to route around it.

3. If it fails, diagnose and fix. **Up to two repair attempts.** Fix causes, not symptoms:
   - Missing dependency → add it to `requirements.txt`, pinned.
   - Failing assertion → decide whether the test or the code is wrong, and say which.
   - Flaky network → retry with backoff, not `try/except: pass`.

   You may not make a test pass by weakening it, deleting it, or wrapping it in a bare
   except. If a test is genuinely wrong, fix it and say so in `VERIFY.md`.

4. Re-run `python3 data/fetch_data.py` and confirm the SHA256 still matches `SOURCE.md`.
   A mismatch means the upstream source changed — record the new hash and flag it.

5. Write `projects/<slug>/VERIFY.md`:

```markdown
# Verification

STATUS: PASSED            # or FAILED
Date:   <ISO-8601 UTC>
Python: <version>
Env:    clean venv

## verify.sh output
<the real, unedited output>

## Headline numbers
- <metric>: <value>       # only what the run actually printed
- Runtime: <seconds>
- Records processed: <n>

## Data integrity
- SHA256 re-check: MATCH / MISMATCH (<details>)

## Repairs made
- <what you changed and why, or "none">

## Known weaknesses
- <anything a reviewer should look at closely — be specific>
```

## The one rule

If it doesn't pass after two attempts, write `STATUS: FAILED` with the real error and
stop. Never claim a pass you didn't observe. The workflow re-runs this verification
independently, so a false claim becomes a visible contradiction in the pull request — and
an honest failure is genuinely more useful to a reviewer than a disguised one.

Every number that reaches the README and the deck comes from this file. If you didn't
measure it, don't write it down.
