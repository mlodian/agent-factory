#!/usr/bin/env python3
"""Work out what an owner's comment on a proposal issue is actually asking for.

    python3 scripts/classify_request.py <issue-body-file> --comment "<text>"

Prints one line:
    build <idea-slug>        start a new project from a backlog idea
    present <project-slug>   re-present an existing project
    error <message>          nothing runs; the message is posted back on the issue

Distinguishes the two kinds of slug, which look alike and mean different things:
  backlog idea    manila-rainfall-extremes              -> something to build
  built project   2026-09-11-manila-rainfall-extremes   -> something that exists
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TICKED = re.compile(r"^\s*[-*]\s*\[[xX]\]\s.*?<!--\s*proposal:\s*([a-z0-9-]{3,60})\s*-->", re.M)
OFFERED = re.compile(r"<!--\s*proposal:\s*([a-z0-9-]{3,60})\s*-->")
BUILD = re.compile(r"^/build(?:\s+([a-z0-9-]{3,60}))?(\s+--new\b)?\s*$", re.M)
PRESENT = re.compile(r"^/present\s+([a-z0-9-]{3,60})\s*$", re.M)
DATED = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$")


def ideas() -> dict[str, dict]:
    data = yaml.safe_load((ROOT / "backlog" / "ideas.yml").read_text(encoding="utf-8"))
    return {i["slug"]: i for i in data["ideas"]}


def project_for(idea_slug: str) -> str | None:
    """The built project directory for a backlog idea, if there is one."""
    for path in sorted((ROOT / "projects").glob(f"*-{idea_slug}")):
        if path.is_dir():
            return path.name
    return None


def classify(body: str, comment: str) -> str:
    known = ideas()

    if (m := PRESENT.search(comment)):
        slug = m.group(1)
        if (ROOT / "projects" / slug).is_dir():
            return f"present {slug}"
        if (existing := project_for(slug)):
            return f"present {existing}"
        return (f"error There's no project `{slug}`. Existing projects: "
                + ", ".join(f"`{p.name}`" for p in sorted((ROOT / 'projects').iterdir()) if p.is_dir()))

    m = BUILD.search(comment)
    if not m:
        return "error I didn't understand that. Use `/build` with one box ticked, `/build <idea-slug>`, `/present <project-slug>`, or `/more`."
    named, force_new = m.group(1), bool(m.group(2))

    if named:
        slug = named
    else:
        picked = TICKED.findall(body)
        if len(picked) == 1:
            slug = picked[0]
        elif not picked:
            offered = ", ".join(f"`{s}`" for s in OFFERED.findall(body))
            return f"error Nothing is ticked. Tick one of {offered or 'the proposals'} and comment `/build` again, or name one with `/build <slug>`."
        else:
            return (f"error {len(picked)} boxes are ticked ({', '.join(picked)}). "
                    "One project runs at a time — leave exactly one ticked and comment `/build` again.")

    # A dated slug is a project that already exists, not something to build.
    if DATED.match(slug):
        if (ROOT / "projects" / slug).is_dir():
            return (f"error `{slug}` is an existing project, not a backlog idea. To give it a new "
                    f"story, look and deck, comment `/present {slug}`. To build a fresh project on the "
                    f"same question, use its idea slug: `/build {slug[11:]} --new`.")
        return f"error `{slug}` looks like a project slug, but there's no such project."

    if slug not in known:
        close = [s for s in known if slug in s or s in slug]
        hint = (" Did you mean " + ", ".join(f"`{s}`" for s in close[:3]) + "?") if close else ""
        return f"error `{slug}` isn't in `backlog/ideas.yml`.{hint} Add it with `/factory-add-idea` first, or tick one of the proposals."

    if known[slug].get("status") == "built" and not force_new:
        existing = project_for(slug)
        where = f" It shipped as `{existing}`." if existing else ""
        return (f"error `{slug}` has already been built.{where} To give that project a new story, look "
                f"and deck, comment `/present {existing or '<project-slug>'}`. To build it again from "
                f"scratch as a separate project, comment `/build {slug} --new`.")

    return f"build {slug}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("body", type=Path)
    parser.add_argument("--comment", default="")
    args = parser.parse_args()
    print(classify(args.body.read_text(encoding="utf-8"), args.comment))
    return 0


if __name__ == "__main__":
    sys.exit(main())
