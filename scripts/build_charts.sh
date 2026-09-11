#!/usr/bin/env bash
# Rebuild a project's charts from its committed data.
#
#   bash scripts/build_charts.sh <slug>
#
# Runs deck/charts/make_charts.py in a fresh venv, from the project directory, so
# charts and deck/charts/FIGURES.md are always what the committed script produces
# from the committed data. The workflow runs this BEFORE the provenance gate, so
# anything the agent committed in deck/charts/ is regenerated before it's checked.
set -euo pipefail

slug="${1:?usage: scripts/build_charts.sh <slug>}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
project="$root/projects/$slug"
script="$project/deck/charts/make_charts.py"

if [[ ! -f "$script" ]]; then
  echo "no deck/charts/make_charts.py — nothing to build"
  exit 0
fi
[[ -f "$project/deck/charts/requirements.txt" ]] || {
  echo "deck/charts/requirements.txt is missing — pin the chart dependencies" >&2; exit 2; }

venv="$(mktemp -d)/venv"
python3 -m venv "$venv"
trap 'rm -rf "$(dirname "$venv")"' EXIT
"$venv/bin/python" -m pip install -q --upgrade pip
[[ -f "$project/requirements.txt" ]] && "$venv/bin/python" -m pip install -q -r "$project/requirements.txt"
"$venv/bin/python" -m pip install -q -r "$project/deck/charts/requirements.txt"

echo "==> building charts for $slug"
(cd "$project" && MPLBACKEND=Agg "$venv/bin/python" deck/charts/make_charts.py)
ls -1 "$project/deck/charts" | grep -vE '\.py$|requirements\.txt$' | sed 's/^/    /'
