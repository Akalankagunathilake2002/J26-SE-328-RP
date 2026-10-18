#!/usr/bin/env bash
# Runs the interview evaluator on Mohler ASAG inside the running interview-service container and
# copies the results out. Needs fetch_datasets.sh first and the local LLM (Huggingbay/start-llm.sh).
#
#   scripts/datasets/run_mohler_eval.sh [extra eval_mohler.py args, e.g. --limit 40]
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATA="${MOHLER_DATA:-/Volumes/Dilmith Ext/datasets/raw/mohler-asag/open_ended.jsonl}"
RESULTS="${MOHLER_RESULTS:-/Volumes/Dilmith Ext/datasets/results}"
CONTAINER="${INTERVIEW_CONTAINER:-skill-bridge-interview-service-1}"
STAMP="$(date +%Y%m%d-%H%M%S)"

[ -s "$DATA" ] || { echo "No Mohler data at $DATA; run scripts/datasets/fetch_datasets.sh"; exit 1; }
mkdir -p "$RESULTS"

docker exec "$CONTAINER" mkdir -p /tmp/mohler
docker cp "$DATA" "$CONTAINER:/tmp/mohler/open_ended.jsonl" >/dev/null
docker cp "$REPO/services/interview-service/evaluation" "$CONTAINER:/app/" >/dev/null

docker exec -w /app "$CONTAINER" python -m evaluation.eval_mohler \
  --data /tmp/mohler/open_ended.jsonl --out "/tmp/mohler/results-$STAMP.json" "$@"

docker cp "$CONTAINER:/tmp/mohler/results-$STAMP.json" "$RESULTS/mohler-$STAMP.json" >/dev/null
echo "Results: $RESULTS/mohler-$STAMP.json"
