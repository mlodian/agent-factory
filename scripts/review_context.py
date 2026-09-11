#!/usr/bin/env python3
"""Collect the facts the weekly reviewer works from.

    python3 scripts/review_context.py [--days 7] [--out .review-context.md]

Gathers, deterministically and before any model runs:
  - daily-project PRs opened in the window (state, labels, checks)
  - daily-project workflow runs (outcome, duration)
  - open source-outage issues
  - backlog depth and theme spread; what's featured
It also copies each OPEN daily PR's project directory into projects/ on this
checkout (never committed) so the reviewer can read unmerged work.

Needs `gh` authenticated (GH_TOKEN in CI) and runs from the repo root.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SLUG = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]{3,60}$")


def gh(*args: str) -> list | dict:
    out = subprocess.run(["gh", *args], capture_output=True, text=True, check=True, cwd=ROOT)
    return json.loads(out.stdout or "null")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True, cwd=ROOT).stdout


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def materialise(branch: str, slug: str) -> bool:
    """Copy an unmerged project into the working tree so the reviewer can read it."""
    if not SLUG.match(slug) or (ROOT / "projects" / slug).exists():
        return (ROOT / "projects" / slug).exists()
    try:
        git("fetch", "-q", "origin", branch)
        git("checkout", f"origin/{branch}", "--", f"projects/{slug}")
        git("reset", "-q", "--", f"projects/{slug}")  # leave it unstaged; nothing here is committed
        return True
    except subprocess.CalledProcessError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--out", default=".review-context.md")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=args.days)
    lines = [f"# Review context — {since:%Y-%m-%d} to {now:%Y-%m-%d}", "",
             "Collected by scripts/review_context.py before the reviewer ran. These are facts, not judgments.", ""]

    # ── Pull requests ────────────────────────────────────────────────────
    prs = gh("pr", "list", "--state", "all", "--limit", "100", "--json",
             "number,title,state,isDraft,labels,headRefName,createdAt,mergedAt,url,mergeable")
    daily = [p for p in prs if p["headRefName"].startswith("daily/") and parse_ts(p["createdAt"]) >= since]
    lines += ["## Daily-project PRs this week", ""]
    if not daily:
        lines.append("None.")
    else:
        lines += ["| PR | Slug | State | Labels | On main? | Readable here? | Mergeable | Age |", "|---|---|---|---|---|---|---|---|"]
        for p in sorted(daily, key=lambda p: p["createdAt"]):
            slug = p["headRefName"].removeprefix("daily/")
            merged = p["mergedAt"] is not None
            readable = merged or (p["state"] == "OPEN" and materialise(p["headRefName"], slug))
            age = (now - parse_ts(p["createdAt"])).days
            labels = ",".join(l["name"] for l in p["labels"]) or "—"
            state = "MERGED" if merged else ("DRAFT" if p["isDraft"] else p["state"])
            lines.append(f"| #{p['number']} | `{slug}` | {state} | {labels} | {'yes' if merged else 'no'} | "
                         f"{'yes' if readable else 'no'} | {p.get('mergeable') or '—'} | {age}d |")
    stale = [p for p in prs if p["headRefName"].startswith("daily/") and p["state"] == "OPEN"
             and (now - parse_ts(p["createdAt"])).days >= 3]
    if stale:
        lines += ["", f"**{len(stale)} daily PR(s) open 3+ days:** " + ", ".join(f"#{p['number']}" for p in stale)
                  + ". Unmerged PRs all edit backlog/built.yml, so each extra one raises the chance of merge conflicts."]

    # ── Workflow runs ────────────────────────────────────────────────────
    runs = gh("run", "list", "--workflow", "daily-project.yml", "--limit", "50", "--json",
              "databaseId,conclusion,status,createdAt,updatedAt,event,url")
    runs = [r for r in runs if parse_ts(r["createdAt"]) >= since]
    lines += ["", "## Daily-project runs this week", ""]
    if not runs:
        lines.append("None.")
    else:
        outcomes = Counter(r["conclusion"] or r["status"] for r in runs)
        lines.append("Outcomes: " + ", ".join(f"{k} × {v}" for k, v in outcomes.items()))
        lines += ["", "| Run | Trigger | Outcome | Duration |", "|---|---|---|---|"]
        for r in runs:
            mins = (parse_ts(r["updatedAt"]) - parse_ts(r["createdAt"])).total_seconds() / 60
            lines.append(f"| [{r['databaseId']}]({r['url']}) | {r['event']} | {r['conclusion'] or r['status']} | {mins:.0f} min |")
    workflow = (ROOT / ".github" / "workflows" / "daily-project.yml").read_text(encoding="utf-8")
    scheduled = bool(re.search(r"^\s*schedule:", workflow, re.M))
    lines += ["", f"Daily schedule: **{'ON' if scheduled else 'PAUSED (manual runs only)'}**"]

    # ── Source health ────────────────────────────────────────────────────
    outages = gh("issue", "list", "--label", "source-outage", "--state", "open", "--json", "number,title,url")
    lines += ["", "## Data-source outages", ""]
    lines.append("None open." if not outages else "\n".join(f"- #{i['number']} {i['title']}" for i in outages))

    # ── Backlog ──────────────────────────────────────────────────────────
    ideas = yaml.safe_load((ROOT / "backlog" / "ideas.yml").read_text(encoding="utf-8"))["ideas"]
    status = Counter(i.get("status", "?") for i in ideas)
    ready = [i for i in ideas if i.get("status") == "ready"]
    locked = [i for i in ready if i.get("requires")]
    lines += ["", "## Backlog", "",
              "Status: " + ", ".join(f"{k} × {v}" for k, v in sorted(status.items())),
              f"Ready and buildable today: **{len(ready) - len(locked)}** "
              f"({len(locked)} more need a secret: {', '.join(sorted({r for i in locked for r in i['requires']}))})",
              "Ready by theme: " + ", ".join(f"{k} {v}" for k, v in sorted(Counter(i['theme'] for i in ready).items()))]
    blocked = [i for i in ideas if i.get("status") == "blocked"]
    if blocked:
        lines += ["", "Blocked ideas:"] + [f"- `{i['slug']}` — {i.get('blocked_reason') or i.get('note', '')}" for i in blocked]

    # ── Showcase ─────────────────────────────────────────────────────────
    projects = []
    for pj in sorted((ROOT / "projects").glob("*/project.json")):
        try:
            projects.append(json.loads(pj.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass
    featured = [p for p in projects if p.get("featured")]
    lines += ["", "## Showcase", "",
              f"Projects readable in this checkout: {len(projects)} · featured: {len(featured)}"
              + (" — " + ", ".join(f"`{p['slug']}`" for p in featured) if featured else "")]

    (ROOT / args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
