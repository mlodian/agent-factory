#!/usr/bin/env python3
"""Deck quality gate: structure, visuals, readability, identity, and QA sign-off.

    python3 scripts/check_deck.py <slug>

This complements check_provenance.py, which decides whether the deck is *true*.
This one decides whether it's *presentable*:

  identity   the project has its own theme.css and identity.json; the deck uses them;
             the palette passes check_palette.py; the fonts are on the known list;
             the look isn't a near-copy of a recent project (WARN)
  structure  8–14 slides; speaker notes on most slides
  visuals    every referenced image exists; data projects put >= 2 generated charts on
             slides; charts come from a committed deck/charts/make_charts.py
  density    no wall-of-text slides (> 90 words FAIL, > 60 WARN); no big tables
  qa         deck/QA.md exists and its verdict is PASS

Appends its report to .deck-report.md for the PR body. Exit 1 on any FAIL.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_palette import check as palette_check, delta_e  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# Families verified to exist on Google Fonts. The art director picks from these, so a
# typo'd or invented family can't silently fall back to a default face.
FONTS = {
    "Anton", "Archivo", "Archivo Black", "Barlow", "Barlow Condensed", "Bebas Neue",
    "Big Shoulders Display", "Bricolage Grotesque", "Chivo", "Chivo Mono", "Crimson Pro",
    "DM Mono", "DM Sans", "DM Serif Display", "EB Garamond", "Epilogue", "Figtree", "Fraunces",
    "Geist", "Geist Mono", "IBM Plex Mono", "IBM Plex Sans", "IBM Plex Serif", "Instrument Sans",
    "Instrument Serif", "Inter", "JetBrains Mono", "Libre Baskerville", "Libre Franklin", "Lora",
    "Manrope", "Merriweather", "Montserrat", "Newsreader", "Onest", "Oswald", "Outfit",
    "Plus Jakarta Sans", "Public Sans", "Red Hat Display", "Red Hat Mono", "Red Hat Text", "Rubik",
    "Sora", "Source Sans 3", "Source Serif 4", "Space Grotesk", "Space Mono", "Syne", "Unbounded",
    "Work Sans",
}


class Report:
    def __init__(self, slug: str) -> None:
        self.slug, self.rows = slug, []

    def add(self, level: str, group: str, msg: str) -> None:
        self.rows.append((level, group, msg))

    @property
    def failed(self) -> bool:
        return any(r[0] == "FAIL" for r in self.rows)

    def render(self) -> str:
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}
        head = f"## Deck quality: {'FAILED' if self.failed else 'PASSED'}"
        return "\n".join([head, ""] + [f"- {icon[l]} **{g}** — {m}" for l, g, m in self.rows]) + "\n"


def split_slides(deck: str) -> tuple[dict, list[str]]:
    fm, body = {}, deck
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", deck, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
        body = deck[m.end():]
    body = re.sub(r"```.*?```", lambda x: x.group(0).replace("\n---", "\n—"), body, flags=re.S)
    slides = [s for s in re.split(r"^---\s*$", body, flags=re.M) if s.strip()]
    return fm, slides


def visible_words(slide: str) -> int:
    text = re.sub(r"<!--.*?-->", " ", slide, flags=re.S)       # speaker notes and directives
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)             # images
    text = re.sub(r"<[^>]+>", " ", text)                          # html tags
    text = re.sub(r"[#*_>|`\-]+", " ", text)
    return len(re.findall(r"[A-Za-z0-9][\w'’.%,-]*", text))


def recent_identities(slug: str, n: int = 5) -> list[tuple[str, dict]]:
    out = []
    for path in sorted((ROOT / "projects").glob("*/deck/identity.json"), reverse=True):
        other = path.parent.parent.name
        if other != slug:
            try:
                out.append((other, json.loads(path.read_text(encoding="utf-8"))))
            except json.JSONDecodeError:
                pass
        if len(out) >= n:
            break
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    slug = sys.argv[1]
    project = ROOT / "projects" / slug
    deck_dir = project / "deck"
    report = Report(slug)

    deck_path = deck_dir / "deck.md"
    if not deck_path.exists():
        report.add("FAIL", "structure", "deck/deck.md is missing")
        return finish(report)
    deck = deck_path.read_text(encoding="utf-8")
    fm, slides = split_slides(deck)

    # ── identity ──
    theme_css, identity_path = deck_dir / "theme.css", deck_dir / "identity.json"
    identity: dict = {}
    if not theme_css.exists():
        report.add("FAIL", "identity", "deck/theme.css is missing — every project gets its own look")
    else:
        css = theme_css.read_text(encoding="utf-8")
        name = re.search(r"/\*\s*@theme\s+([\w-]+)\s*\*/", css)
        if not name:
            report.add("FAIL", "identity", "theme.css has no `/* @theme <name> */` declaration")
        elif fm.get("theme") != name.group(1):
            report.add("FAIL", "identity", f"deck front matter uses theme `{fm.get('theme')}`, not the project's `{name.group(1)}`")
        else:
            report.add("PASS", "identity", f"deck uses its own theme `{name.group(1)}`")
        if css.strip() == (ROOT / "templates" / "theme.css").read_text(encoding="utf-8").strip():
            report.add("FAIL", "identity", "theme.css is a copy of the shared template")
    if not identity_path.exists():
        report.add("FAIL", "identity", "deck/identity.json is missing")
    else:
        identity = json.loads(identity_path.read_text(encoding="utf-8"))
        rows = palette_check(identity)
        fails = [m for l, _, m in rows if l == "FAIL"]
        warns = [m for l, _, m in rows if l == "WARN"]
        if fails:
            report.add("FAIL", "identity", "palette: " + "; ".join(fails))
        else:
            report.add("PASS", "identity", f"palette passes contrast and colorblind separation ({len(rows)} checks)")
        for w in warns:
            report.add("WARN", "identity", "palette: " + w)
        fonts = identity.get("fonts", {})
        unknown = [f for f in fonts.values() if f not in FONTS]
        if not fonts:
            report.add("FAIL", "identity", "identity.json names no fonts")
        elif unknown:
            report.add("FAIL", "identity", "fonts not on the verified Google Fonts list: " + ", ".join(unknown))
        for other, oid in recent_identities(slug):
            try:
                close = delta_e(identity["colors"]["accent"], oid["colors"]["accent"]) < 12
                same_type = identity.get("fonts", {}).get("display") == oid.get("fonts", {}).get("display")
                same_bg = delta_e(identity["colors"]["background"], oid["colors"]["background"]) < 8
            except (KeyError, TypeError):
                continue
            if sum([close, same_type, same_bg]) >= 2:
                report.add("WARN", "identity", f"looks close to `{other}` (accent/display font/background) — make it more distinct")

    # ── structure ──
    n = len(slides)
    if not 8 <= n <= 14:
        report.add("FAIL", "structure", f"{n} slides — aim for 8–14")
    else:
        report.add("PASS", "structure", f"{n} slides")
    with_notes = sum(1 for s in slides if re.search(r"<!--(?!\s*_)(?!\s*(class|paginate|header|footer|backgroundColor|color)\b).*?-->", s, re.S))
    if with_notes < 0.8 * n:
        report.add("WARN", "structure", f"speaker notes on only {with_notes}/{n} slides")

    # ── visuals ──
    refs = re.findall(r"!\[[^\]]*\]\(([^)\s]+)", deck) + re.findall(r"url\(['\"]?([^'\")]+)", deck)
    local = [r for r in refs if not r.startswith(("http:", "https:", "data:"))]
    missing = [r for r in local if not (deck_dir / r).exists()]
    if missing:
        report.add("FAIL", "visuals", "referenced images missing: " + ", ".join(missing))
    charts = sorted({r for r in local if r.startswith("charts/") and r.endswith((".svg", ".png"))})
    needs_charts = (project / "data").exists()
    if needs_charts and len(charts) < 2:
        report.add("FAIL", "visuals", f"{len(charts)} generated chart(s) on slides — a data project needs at least 2")
    elif charts:
        report.add("PASS", "visuals", f"{len(charts)} generated charts on slides")
    if charts and not (deck_dir / "charts" / "make_charts.py").exists():
        report.add("FAIL", "visuals", "charts are used but deck/charts/make_charts.py is missing — charts must be reproducible")

    # ── density ──
    for i, s in enumerate(slides, 1):
        w = visible_words(s)
        if w > 90:
            report.add("FAIL", "density", f"slide {i} has {w} visible words — move the detail to speaker notes")
        elif w > 60:
            report.add("WARN", "density", f"slide {i} has {w} visible words")
        rows = len(re.findall(r"^\s*\|.*\|\s*$", s, re.M))
        if rows > 7:
            report.add("WARN", "density", f"slide {i} has a {rows - 2}-row table — would a chart say it better?")

    # ── qa ──
    qa = deck_dir / "QA.md"
    if not qa.exists():
        report.add("FAIL", "qa", "deck/QA.md is missing — the QA team didn't sign off")
    else:
        verdict = re.search(r"^VERDICT:\s*(PASS|FAIL)", qa.read_text(encoding="utf-8"), re.M)
        if not verdict:
            report.add("FAIL", "qa", "deck/QA.md has no `VERDICT: PASS|FAIL` line")
        elif verdict.group(1) == "FAIL":
            report.add("FAIL", "qa", "QA team's verdict is FAIL — see deck/QA.md")
        else:
            report.add("PASS", "qa", "QA team signed off")

    return finish(report)


def finish(report: Report) -> int:
    text = report.render()
    print(text)
    (ROOT / ".deck-report.md").write_text(text, encoding="utf-8")
    return 1 if report.failed else 0


if __name__ == "__main__":
    sys.exit(main())
