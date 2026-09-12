#!/usr/bin/env python3
"""Read the owner's choice out of a project-proposal issue.

    python3 scripts/selected_proposal.py <issue-body-file> [--comment <text>]

Prints the chosen backlog slug on stdout, or exits non-zero with the reason on
stderr. A choice is either:

  - exactly one ticked `- [x] … <!-- proposal: <slug> -->` line, or
  - an explicit `/build <slug>` in the comment, which wins over the ticks.

Refuses on zero or several ticks, so an ambiguous issue never starts a build.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TICKED = re.compile(r"^\s*[-*]\s*\[[xX]\]\s.*?<!--\s*proposal:\s*([a-z0-9-]{3,60})\s*-->", re.M)
OFFERED = re.compile(r"<!--\s*proposal:\s*([a-z0-9-]{3,60})\s*-->")
EXPLICIT = re.compile(r"^/build\s+([a-z0-9-]{3,60})\s*$", re.M)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("body", type=Path)
    parser.add_argument("--comment", default="")
    args = parser.parse_args()

    if (m := EXPLICIT.search(args.comment)):
        print(m.group(1))
        return 0

    body = args.body.read_text(encoding="utf-8")
    picked = TICKED.findall(body)
    if len(picked) == 1:
        print(picked[0])
        return 0

    offered = OFFERED.findall(body)
    if not picked:
        print(f"Nothing is ticked. Tick one of {', '.join(f'`{s}`' for s in offered) or 'the proposals'} "
              f"and comment /build again, or comment `/build <slug>` to name one directly.", file=sys.stderr)
    else:
        print(f"{len(picked)} boxes are ticked ({', '.join(picked)}). "
              "One project runs at a time — leave exactly one ticked and comment /build again.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
