#!/usr/bin/env python3
"""Summarise the visual identities of the most recent projects.

    python3 scripts/recent_identities.py [--exclude <slug>] [-n 5]

Used by the art director's skill so a new identity can be made clearly different.
Prints one line per project: name | mood | fonts | background | accent.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exclude", default="")
    parser.add_argument("-n", type=int, default=5)
    args = parser.parse_args()

    rows = []
    for path in sorted((ROOT / "projects").glob("*/deck/identity.json"), reverse=True):
        slug = path.parent.parent.name
        if slug == args.exclude:
            continue
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            c, f = d.get("colors", {}), d.get("fonts", {})
            rows.append(f"- {slug}: {d.get('name', '?')} | mood: {d.get('mood', '?')} | "
                        f"fonts: {f.get('display', '?')} / {f.get('body', '?')} | "
                        f"background {c.get('background', '?')} | accent {c.get('accent', '?')}")
        except (OSError, ValueError):
            continue
        if len(rows) >= args.n:
            break
    print("\n".join(rows) if rows else "(no earlier project has a visual identity yet — you're setting the first one)")


if __name__ == "__main__":
    main()
