#!/usr/bin/env bash
# Builds services/interview-service/data/public_question_bank.json from the open interview sets and the
# learning curriculum. Needs fetch_datasets.sh, build_learning_corpus.py (with the corpus loaded into
# the learning service) and the local LLM. Resumable: rerun to continue after an interruption.
#
#   scripts/datasets/build_interview_bank.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK="${BANK_WORK_DIR:-/Volumes/Dilmith Ext/datasets}"
CONTAINER="${LEARNING_CONTAINER:-skill-bridge-learning-service-1}"
PY="$WORK/.venv/bin/python"

"$PY" "$REPO/scripts/datasets/extract_interview_candidates.py" "$WORK/raw"

docker exec "$CONTAINER" mkdir -p /tmp/bank
docker cp "$WORK/interview-candidates.jsonl" "$CONTAINER:/tmp/bank/candidates.jsonl" >/dev/null
docker cp "$REPO/scripts/datasets/generate_interview_bank.py" "$CONTAINER:/app/generate_interview_bank.py" >/dev/null
# Resume from earlier output if there is any
[ -s "$WORK/interview-generated.jsonl" ] && docker cp "$WORK/interview-generated.jsonl" "$CONTAINER:/tmp/bank/generated.jsonl" >/dev/null

docker exec -w /app "$CONTAINER" python generate_interview_bank.py /tmp/bank/candidates.jsonl /tmp/bank/generated.jsonl
docker exec -w /app "$CONTAINER" python generate_interview_bank.py --finalize /tmp/bank/generated.jsonl /tmp/bank/bank.json /tmp/bank/candidates.jsonl

docker cp "$CONTAINER:/tmp/bank/generated.jsonl" "$WORK/interview-generated.jsonl" >/dev/null
docker cp "$CONTAINER:/tmp/bank/bank.json" "$REPO/services/interview-service/data/public_question_bank.json" >/dev/null
echo "Bank: services/interview-service/data/public_question_bank.json (raw LLM output: $WORK/interview-generated.jsonl)"
