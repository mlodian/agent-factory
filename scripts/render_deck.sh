#!/usr/bin/env bash
# Render a project's deck to HTML, PDF, and PPTX.
#
#   bash scripts/render_deck.sh <slug>
#
# Needs Node (npx) and a Chrome/Chromium the tools can find. GitHub's
# ubuntu runners have both.
set -euo pipefail

MARP_VERSION="4.5.1"
MERMAID_VERSION="11.17.0"

slug="${1:?usage: scripts/render_deck.sh <slug>}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
deck="$root/projects/$slug/deck"

[[ -f "$deck/deck.md" ]] || { echo "projects/$slug/deck/deck.md not found" >&2; exit 2; }
mkdir -p "$deck/dist"

# Marp can't render Mermaid, so the architecture diagram is drawn separately
# and embedded in slide 4 as an SVG.
if [[ -f "$deck/architecture.mmd" ]]; then
  echo "==> rendering architecture diagram"
  npx --yes -p "@mermaid-js/mermaid-cli@$MERMAID_VERSION" mmdc \
    -i "$deck/architecture.mmd" -o "$deck/architecture.svg" \
    -b transparent -p "$root/scripts/puppeteer.json"
fi

marp=(npx --yes "@marp-team/marp-cli@$MARP_VERSION"
      --theme-set "$root/templates/theme.css" --allow-local-files)

echo "==> rendering deck.html";  "${marp[@]}" "$deck/deck.md" --html -o "$deck/dist/deck.html"
echo "==> rendering deck.pdf";   "${marp[@]}" "$deck/deck.md" --pdf  -o "$deck/dist/deck.pdf"
echo "==> rendering deck.pptx";  "${marp[@]}" "$deck/deck.md" --pptx -o "$deck/dist/deck.pptx"

# The HTML deck references the SVG by relative path; keep a copy beside it.
[[ -f "$deck/architecture.svg" ]] && cp "$deck/architecture.svg" "$deck/dist/"

ls -la "$deck/dist"
