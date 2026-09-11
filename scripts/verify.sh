#!/usr/bin/env bash
# Run one project's verify.sh in a fresh virtualenv.
#
#   bash scripts/verify.sh <slug>
#
# Used twice per run: by the verifier agent while repairing, and by the workflow
# afterwards as an independent check that doesn't take the agent's word for it.
set -euo pipefail

slug="${1:?usage: scripts/verify.sh <slug>}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
project="$root/projects/$slug"

[[ -d "$project" ]]           || { echo "no such project: projects/$slug" >&2; exit 2; }
[[ -f "$project/verify.sh" ]] || { echo "projects/$slug has no verify.sh" >&2; exit 2; }

venv="$(mktemp -d)/venv"
python3 -m venv "$venv"
trap 'rm -rf "$(dirname "$venv")"' EXIT

# Projects that call the Claude API read ANTHROPIC_API_KEY. The factory stores it
# as FACTORY_ANTHROPIC_API_KEY so it never reaches Claude Code itself, where it
# would outrank the subscription OAuth token and switch billing to the API.
if [[ -n "${FACTORY_ANTHROPIC_API_KEY:-}" ]]; then
  export ANTHROPIC_API_KEY="$FACTORY_ANTHROPIC_API_KEY"
fi

echo "==> verifying projects/$slug in a clean venv"
start=$(date +%s)
status=0
(
  cd "$project"
  export PATH="$venv/bin:$PATH" VIRTUAL_ENV="$venv"
  python -m pip install -q --upgrade pip
  bash verify.sh
) || status=$?
echo "==> finished in $(( $(date +%s) - start ))s with exit code $status"
exit $status
