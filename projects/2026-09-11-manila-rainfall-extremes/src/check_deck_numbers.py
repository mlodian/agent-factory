"""Local pre-flight for the claims gate.

Mirrors the Results-slide number check in scripts/check_provenance.py so a
mismatch shows up here rather than in CI. Not part of verify.sh.

    python3 -m src.check_deck_numbers
"""

import re
import sys
from pathlib import Path

NUMBER = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?%?")
PROJECT = Path(__file__).resolve().parent.parent


def numbers_in(text: str) -> set[str]:
    return {n.replace(",", "") for n in NUMBER.findall(text)}


def results_slide(deck: str) -> str | None:
    match = re.search(r"^##\s+Results\b(.*?)(?=^---\s*$|\Z)", deck, re.M | re.S)
    if not match:
        return None
    return re.sub(r"<!--.*?-->", "", match.group(1), flags=re.S)


def main() -> int:
    deck = (PROJECT / "deck" / "deck.md").read_text(encoding="utf-8")
    verify = (PROJECT / "VERIFY.md").read_text(encoding="utf-8")

    slide = results_slide(deck)
    if slide is None:
        print("FAIL: no '## Results' slide found")
        return 1

    on_slide = numbers_in(slide)
    supported = numbers_in(verify)
    unsupported = sorted(on_slide - supported)

    print(f"numbers on the Results slide : {sorted(on_slide)}")
    print(f"unsupported by VERIFY.md     : {unsupported or 'none'}")

    if unsupported:
        print("\nFAIL: the claims gate would reject these.")
        return 1
    print("\nOK: every number on the Results slide appears in VERIFY.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
