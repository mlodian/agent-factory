#!/usr/bin/env bash
# Every deterministic check a project must pass before its PR, in the right order.
#
#   bash scripts/gate.sh <slug>
#
#   1. charts      rebuild deck/charts from the committed script + data (so the gates
#                  below see regenerated charts and FIGURES.md, not what the agent left)
#   2. verify      verify.sh in a fresh venv; output captured to .verify-output.txt
#   3. provenance  data, checksums, fabrication, and every slide number checked
#                  against the log from step 2, not agent-written VERIFY.md
#   4. deck        identity, structure, visuals, density, QA sign-off
#   5. render      Marp → HTML, PDF, PPTX
#
# Never exits non-zero on a failed check. It records each outcome in .gate-results
# (NAME=success|failure) and writes .pr-checks.md for the pull-request body, so the
# workflow can open a draft PR that shows exactly what failed.
set -uo pipefail

slug="${1:?usage: scripts/gate.sh <slug>}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
: > .gate-results

run() {  # run NAME command... — record the outcome, keep going
  local name="$1"; shift
  echo "::group::gate: $name"
  if "$@"; then echo "$name=success" >> .gate-results; else echo "$name=failure" >> .gate-results; fi
  echo "::endgroup::"
}

run charts     bash scripts/build_charts.sh "$slug"
run verify     bash -o pipefail -c "bash scripts/verify.sh '$slug' 2>&1 | tee .verify-output.txt"
run provenance python3 scripts/check_provenance.py "$slug" --verify-log .verify-output.txt
run deck       python3 scripts/check_deck.py "$slug"
run render     bash scripts/render_deck.sh "$slug"

mark() { [ "$(grep "^$1=" .gate-results | cut -d= -f2)" = success ] && echo "✅ passed" || echo "❌ failed"; }
{
  echo "### Independent checks"
  echo "Run by the workflow after the agents finished. None of it is self-reported."
  echo
  echo "| Check | Result |"
  echo "|---|---|"
  echo "| Charts rebuilt from committed data | $(mark charts) |"
  echo "| \`verify.sh\` in a clean venv | $(mark verify) |"
  echo "| Provenance (every slide number vs. this run's log) | $(mark provenance) |"
  echo "| Deck quality (identity, visuals, density, QA) | $(mark deck) |"
  echo "| Render to HTML / PDF / PPTX | $(mark render) |"
  echo
  [ -f .provenance-report.md ] && cat .provenance-report.md && echo
  [ -f .deck-report.md ] && cat .deck-report.md && echo
  if [ -f "projects/$slug/deck/QA.md" ]; then
    echo "<details><summary>Presentation QA report</summary>"
    echo
    cat "projects/$slug/deck/QA.md"
    echo
    echo "</details>"
  fi
} > .pr-checks.md

echo "gate results:"; sed 's/^/  /' .gate-results
