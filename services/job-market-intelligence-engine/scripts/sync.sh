#!/usr/bin/env bash
# Sync with the job sites: mark stored ads active / expired / removed, download new ads,
# then rebuild the processed data, the quality report and the skill profile.
#
#   scripts/sync.sh              # up to 25 new ads per sector
#   SYNC_LIMIT=50 scripts/sync.sh
#
# The output is also written to data/logs/sync-<date>.log. Step 8 runs this on a schedule.
set -euo pipefail

cd "$(dirname "$0")/.."
python="${PYTHON:-python3}"
[ -x .venv/bin/python ] && python=.venv/bin/python

mkdir -p data/logs
log="data/logs/sync-$(date +%Y-%m-%d).log"
echo "=== sync started $(date '+%Y-%m-%d %H:%M:%S %Z') ===" >> "$log"
"$python" -m app.collectors.run --site all --sector all --sync --limit "${SYNC_LIMIT:-25}" 2>&1 | tee -a "$log"
