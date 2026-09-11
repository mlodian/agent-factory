#!/usr/bin/env bash
# One command. Exit 0 means the project works.
#
#   ./verify.sh
#
# Steps, in dependency order: install, re-verify the data against its declared
# checksum, run the tests, then run the analysis end to end on the real file.
set -euo pipefail

cd "$(dirname "$0")"

echo "=============================================================================="
echo "1/4  Environment"
echo "=============================================================================="
python3 --version
pip install -q -r requirements.txt
echo "deps installed: $(pip freeze | tr '\n' ' ')"

echo
echo "=============================================================================="
echo "2/4  Data provenance"
echo "=============================================================================="
# Re-verifies raw/manila_precip_1940_2025.json against the SHA256 in
# data/SOURCE.md. Downloads only if the file is absent or its content changed.
python3 data/fetch_data.py

echo
echo "=============================================================================="
echo "3/4  Tests"
echo "=============================================================================="
python3 -m pytest -q tests/

echo
echo "=============================================================================="
echo "4/4  Analysis on the real record"
echo "=============================================================================="
python3 -m src.main --report

echo
echo "verify.sh: OK"
