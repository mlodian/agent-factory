#!/usr/bin/env bash
# Exit 0 means the project works.
#
# Runs entirely against the committed extract in data/raw/ -- no network. Refreshing
# the data is data/fetch_data.py's job; verification should not need it.
set -euo pipefail

echo "==> python $(python3 --version 2>&1)"

echo "==> installing dependencies"
pip install -q -r requirements.txt

echo "==> checking the committed extract against data/SOURCE.md"
python3 data/fetch_data.py

echo "==> running tests"
pytest -q tests/

echo "==> running the analysis on the real data"
python3 -m src.main --report
