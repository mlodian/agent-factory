#!/usr/bin/env bash
# Render every slide to PNG so a person, or the visual-qa agent, can look at them.
#
#   bash scripts/preview_deck.sh <slug>
#
# Writes deck/preview/slide.001.png, slide.002.png, … (gitignored). Rebuilds the
# charts first, so the preview shows what the workflow will actually ship.
set -euo pipefail

MARP_VERSION="4.5.1"
slug="${1:?usage: scripts/preview_deck.sh <slug>}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
deck="$root/projects/$slug/deck"

bash "$root/scripts/build_charts.sh" "$slug"
if [[ -f "$deck/architecture.mmd" ]]; then
  npx --yes -p "@mermaid-js/mermaid-cli@11.17.0" mmdc -i "$deck/architecture.mmd" \
    -o "$deck/architecture.svg" -b transparent -p "$root/scripts/puppeteer.json"
fi

themes=(--theme-set "$root/templates/theme.css")
[[ -f "$deck/theme.css" ]] && themes+=("$deck/theme.css")

rm -rf "$deck/preview" && mkdir -p "$deck/preview"
npx --yes "@marp-team/marp-cli@$MARP_VERSION" "${themes[@]}" --allow-local-files \
  --images png "$deck/deck.md" -o "$deck/preview/slide.png"

echo "==> $(ls "$deck/preview" | wc -l | tr -d ' ') slides rendered to projects/$slug/deck/preview/"
ls -1 "$deck/preview"
