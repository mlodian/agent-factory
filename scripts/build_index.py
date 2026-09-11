#!/usr/bin/env python3
"""Build the GitHub Pages showcase from every projects/*/project.json.

    python3 scripts/build_index.py [--out site]

Writes site/index.html and copies each project's rendered deck to
site/projects/<slug>/deck/dist/ so the deck links resolve on Pages.
Featured projects sort first; the rest follow newest-first.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "https://github.com/mlodian/agent-factory"


def load_projects() -> list[dict]:
    projects = []
    for path in sorted((ROOT / "projects").glob("*/project.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"skipping {path}: {exc}")
            continue
        if data.get("retired"):
            continue  # retired via the weekly review; stays in the repo, off the showcase
        data.setdefault("slug", path.parent.name)
        data["_dir"] = path.parent
        projects.append(data)
    projects.sort(key=lambda p: p.get("date", ""), reverse=True)
    projects.sort(key=lambda p: not p.get("featured", False))  # stable: featured first
    return projects


def card(p: dict, released: set[str]) -> str:
    e = lambda v: html.escape(str(v or ""))  # noqa: E731
    slug = p["slug"]
    source = p.get("source") or {}
    source_line = e(source.get("name", "no dataset")) if isinstance(source, dict) else e(source)
    if isinstance(source, dict) and source.get("records"):
        source_line += f" · {int(source['records']):,} records"

    # deck.html is committed and copied into the site. PDF and PPTX live on a
    # per-project GitHub Release so binaries stay out of git history.
    links = []
    if (p["_dir"] / "deck" / "dist" / "deck.html").exists():
        links.append(f'<a href="projects/{e(slug)}/deck/dist/deck.html">Slides</a>')
    if f"deck-{slug}" in released:
        base = f"{REPO}/releases/download/deck-{e(slug)}"
        links.append(f'<a href="{base}/deck.pdf">PDF</a>')
        links.append(f'<a href="{base}/deck.pptx">PPTX</a>')
    links.append(f'<a href="{REPO}/tree/main/projects/{e(slug)}">Code</a>')

    failed = str(p.get("status", "")).lower() == "failed"
    badges = []
    if p.get("featured"):
        badges.append('<span class="badge featured">Featured</span>')
    if failed:
        badges.append('<span class="badge failed">Needs work</span>')

    return f"""
    <article class="card{' is-featured' if p.get('featured') else ''}" data-theme-tag="{e(p.get('theme'))}">
      <div class="meta"><span class="theme">{e(p.get('theme'))}</span><time>{e(p.get('date'))}</time>{''.join(badges)}</div>
      <h2>{e(p.get('title', slug))}</h2>
      <p class="pitch">{e(p.get('pitch'))}</p>
      {f'<p class="headline">{e(p["headline"])}</p>' if p.get('headline') else ''}
      <p class="source">{source_line}</p>
      <nav>{' · '.join(links)}</nav>
    </article>"""


def page(projects: list[dict], released: set[str]) -> str:
    themes = sorted({p.get("theme", "") for p in projects if p.get("theme")})
    filters = "".join(f'<button data-filter="{html.escape(t)}">{html.escape(t)}</button>' for t in themes)
    cards = "\n".join(card(p, released) for p in projects) or '<p class="empty">No projects yet. The first one lands after the next scheduled run.</p>'
    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    passed = sum(1 for p in projects if str(p.get("status")).lower() == "passed")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>agent-factory</title>
<style>
  :root {{
    --bg: #fbfbf9; --ink: #1b1f24; --muted: #5b6470; --rule: #e3e7ec;
    --card: #ffffff; --accent: #2f6fdb; --warn: #b54708; --warn-bg: #fef3e7;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg: #111418; --ink: #e8ecf1; --muted: #9aa4b0; --rule: #262c33;
             --card: #181c21; --accent: #7aa7ff; --warn: #f5a35c; --warn-bg: #2b1d10; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink);
         font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }}
  main {{ max-width: 1120px; margin: 0 auto; padding: 56px 24px 80px; }}
  header h1 {{ font-size: 2.2rem; margin: 0 0 .25rem; letter-spacing: -.02em; }}
  header p {{ color: var(--muted); margin: 0; max-width: 62ch; }}
  .stats {{ margin: 1.25rem 0 2rem; color: var(--muted); font-size: .9rem; }}
  .filters {{ display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: 1.5rem; }}
  .filters button {{ border: 1px solid var(--rule); background: var(--card); color: var(--ink);
                    padding: .35rem .8rem; border-radius: 999px; cursor: pointer; font: inherit; font-size: .85rem; }}
  .filters button[aria-pressed="true"] {{ background: var(--ink); color: var(--bg); border-color: var(--ink); }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }}
  .card {{ background: var(--card); border: 1px solid var(--rule); border-radius: 12px; padding: 20px;
          display: flex; flex-direction: column; }}
  .card.is-featured {{ border-color: var(--accent); }}
  .meta {{ display: flex; gap: .6rem; align-items: center; font-size: .78rem; color: var(--muted); flex-wrap: wrap; }}
  .theme {{ text-transform: uppercase; letter-spacing: .06em; font-weight: 600; }}
  .badge {{ padding: .1rem .5rem; border-radius: 999px; font-weight: 600; }}
  .badge.featured {{ background: var(--accent); color: var(--card); }}
  .badge.failed {{ background: var(--warn-bg); color: var(--warn); }}
  .card h2 {{ font-size: 1.1rem; margin: .6rem 0 .4rem; line-height: 1.3; }}
  .pitch {{ margin: 0 0 .6rem; color: var(--muted); }}
  .headline {{ margin: 0 0 .8rem; font-weight: 600; border-left: 3px solid var(--accent); padding-left: .7rem; }}
  .source {{ margin: auto 0 .7rem; font-size: .82rem; color: var(--muted); }}
  nav a {{ color: var(--accent); text-decoration: none; font-weight: 600; font-size: .9rem; }}
  nav a:hover {{ text-decoration: underline; }}
  .empty {{ color: var(--muted); }}
  footer {{ margin-top: 3rem; color: var(--muted); font-size: .82rem; }}
  footer a {{ color: inherit; }}
</style>
</head>
<body>
<main>
  <header>
    <h1>agent-factory</h1>
    <p>One small project a day, built by a Claude Code pipeline on real public data,
       verified independently, and reviewed by a human before it lands.</p>
  </header>
  <p class="stats">{len(projects)} project{'s' * (len(projects) != 1)} · {passed} verified · {sum(1 for p in projects if p.get('featured'))} featured</p>
  <div class="filters"><button data-filter="" aria-pressed="true">all</button>{filters}</div>
  <section class="grid">{cards}</section>
  <footer>Built {built} · <a href="{REPO}">source</a> · every dataset is cited, with its checksum, in the project's <code>data/SOURCE.md</code></footer>
</main>
<script>
  const buttons = document.querySelectorAll('.filters button');
  buttons.forEach(b => b.addEventListener('click', () => {{
    buttons.forEach(x => x.setAttribute('aria-pressed', x === b));
    document.querySelectorAll('.card').forEach(c => {{
      c.hidden = b.dataset.filter && c.dataset.themeTag !== b.dataset.filter;
    }});
  }}));
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="site")
    parser.add_argument("--released", type=Path,
                        help="file of release tags, one per line (from `gh release list`); "
                             "projects with a deck-<slug> release get PDF/PPTX links")
    args = parser.parse_args()
    out = ROOT / args.out
    released: set[str] = set()
    if args.released and args.released.exists():
        released = {line.strip() for line in args.released.read_text().splitlines() if line.strip()}

    projects = load_projects()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    for p in projects:
        dist = p["_dir"] / "deck" / "dist"
        if dist.is_dir():
            shutil.copytree(dist, out / "projects" / p["slug"] / "deck" / "dist")

    (out / "index.html").write_text(page(projects, released), encoding="utf-8")
    (out / ".nojekyll").touch()
    print(f"wrote {out / 'index.html'} with {len(projects)} project{'s' * (len(projects) != 1)}")


if __name__ == "__main__":
    main()
