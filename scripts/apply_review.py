#!/usr/bin/env python3
"""Apply the ticked items of a weekly-review issue.

    python3 scripts/apply_review.py <issue-body-file> [--out .apply-summary.md]

Only lines that are BOTH ticked (`- [x]`) AND carry a well-formed
`<!-- action:… -->` marker do anything. Everything is validated first:

  feature / unfeature   the project must exist on this checkout (i.e. be merged)
  retire                sets retired: true and featured: false; the showcase hides it
  add-idea              the hidden YAML block must parse, name a registered,
                        automatable, non-denied source, and use a new slug

Writes changes to the working tree only. The workflow turns them into a PR.
The summary (applied + skipped, with reasons) goes to --out for the issue comment.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TICKED = re.compile(r"^\s*[-*]\s*\[[xX]\]\s.*?<!--\s*action:([a-z-]+)\s+(slug|id):([A-Za-z0-9-]+)\s*-->", re.M)
TICKED_ANY = re.compile(r"^\s*[-*]\s*\[[xX]\]\s.*?<!--\s*action:.*$", re.M)
IDEA_BLOCK = re.compile(r"<!--\s*idea:(\d+)\s*\n(.*?)-->", re.S)
SLUG = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]{3,60}$")
IDEA_SLUG = re.compile(r"^[a-z0-9-]{3,60}$")
THEMES = {"finance", "cyber", "health", "environment", "marketing", "science", "civic", "ml", "data-eng", "agents", "web"}
REQUIRED = {"slug", "title", "theme", "tags", "source", "difficulty", "note"}


def set_flags(slug: str, **flags: bool) -> str | None:
    """Update project.json; returns an error string, or None on success."""
    if not SLUG.match(slug):
        return "malformed slug"
    path = ROOT / "projects" / slug / "project.json"
    if not path.exists():
        return "not on main yet — merge its PR, then /apply again"
    data = json.loads(path.read_text(encoding="utf-8"))
    if all(data.get(k) == v for k, v in flags.items()):
        return "already in that state"
    data.update(flags)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return None


def validate_idea(raw: str, registry: dict, existing: set[str]) -> tuple[dict | None, str | None]:
    try:
        idea = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        return None, f"YAML doesn't parse ({exc.__class__.__name__})"
    if not isinstance(idea, dict):
        return None, "idea block isn't a mapping"
    missing = REQUIRED - idea.keys()
    if missing:
        return None, "missing fields: " + ", ".join(sorted(missing))
    sources = {s["id"]: s for s in registry["sources"]}
    denied = {d["id"] for d in registry["denied"]}
    src = idea["source"]
    if src in denied:
        return None, f"source `{src}` is denied"
    if src not in sources:
        return None, f"source `{src}` isn't in the registry"
    if sources[src].get("unattended") is False:
        return None, f"source `{src}` is manual-only (unattended: false)"
    if not IDEA_SLUG.match(str(idea["slug"])):
        return None, "slug must be kebab-case, 3–60 chars"
    if idea["slug"] in existing:
        return None, f"slug `{idea['slug']}` already exists in the backlog"
    if idea["theme"] not in THEMES:
        return None, f"unknown theme `{idea['theme']}`"
    if idea["difficulty"] not in {"easy", "medium", "hard"}:
        return None, "difficulty must be easy, medium, or hard"
    clean = {k: idea[k] for k in ["slug", "title", "theme", "tags", "source", "difficulty"]}
    clean.update(status="ready", added=date.today().isoformat(), note=idea["note"])
    return clean, None


def append_ideas(ideas: list[dict]) -> None:
    """Append as text so the backlog's comments and layout survive."""
    path = ROOT / "backlog" / "ideas.yml"
    text = path.read_text(encoding="utf-8").rstrip("\n") + "\n\n  # ── Added by weekly review ──\n"
    for idea in ideas:
        block = yaml.safe_dump([idea], sort_keys=False, allow_unicode=True, width=100)
        text += "\n" + "\n".join("  " + line if line else line for line in block.splitlines()) + "\n"
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("body", type=Path)
    parser.add_argument("--out", default=".apply-summary.md")
    args = parser.parse_args()

    body = args.body.read_text(encoding="utf-8")
    registry = yaml.safe_load((ROOT / "sources" / "registry.yml").read_text(encoding="utf-8"))
    backlog = yaml.safe_load((ROOT / "backlog" / "ideas.yml").read_text(encoding="utf-8"))["ideas"]
    existing = {i["slug"] for i in backlog}
    blocks = {m.group(1): m.group(2) for m in IDEA_BLOCK.finditer(body)}

    applied, skipped, new_ideas, seen = [], [], [], set()
    for action, key, value in TICKED.findall(body):
        if (action, value) in seen:
            continue
        seen.add((action, value))
        label = f"**{action}** `{value}`"
        if action in {"feature", "unfeature", "retire"} and key == "slug":
            flags = {"feature": {"featured": True},
                     "unfeature": {"featured": False},
                     "retire": {"retired": True, "featured": False}}[action]
            err = set_flags(value, **flags)
        elif action == "add-idea" and key == "id":
            if value not in blocks:
                err = "no matching hidden idea block"
            else:
                idea, err = validate_idea(blocks[value], registry, existing)
                if idea:
                    new_ideas.append(idea)
                    existing.add(idea["slug"])
                    label = f"**add-idea** `{idea['slug']}` (source `{idea['source']}`)"
        else:
            err = "unknown action"
        (skipped if err else applied).append(f"- {label}" + (f" — skipped: {err}" if err else ""))

    # A ticked line whose marker didn't parse is reported, not silently dropped.
    for line in TICKED_ANY.findall(body):
        if not TICKED.match(line):
            marker = re.search(r"<!--.*?-->", line)
            shown = marker.group(0) if marker else line.strip()
            skipped.append(f"- ticked line with a malformed marker — skipped: `{shown[:80]}`")

    if new_ideas:
        append_ideas(new_ideas)

    lines = ["### /apply result", ""]
    if not applied and not skipped:
        lines.append("No ticked items with an action marker were found, so nothing was changed.")
    if applied:
        lines += ["Applied:"] + applied + [""]
    if skipped:
        lines += ["Skipped:"] + skipped + [""]
    summary = "\n".join(lines) + "\n"
    (ROOT / args.out).write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
