#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT="${INPUT:-${ROOT}/prediction result/our-attack-full-set.jsonl}"
RUN_DIR="${RUN_DIR:-${ROOT}/runs/datasentinel_our_attack_full_set}"
LIMIT_ARG=()

mkdir -p "${RUN_DIR}"

if [[ -n "${LIMIT:-}" ]]; then
  LIMIT_ARG=(--limit "${LIMIT}")
fi

LOG="${LOG:-${RUN_DIR}/datasentinel_$(date +%Y%m%d_%H%M%S).log}"

{
  echo "Input: ${INPUT}"
  echo "Run dir: ${RUN_DIR}"
  echo "Log: ${LOG}"
  echo "Resume: rows with existing datasentinel_verdict are skipped"

  "${ROOT}/run_datasentinel_prediction_results.sh" \
    --input "${INPUT}" \
    "${LIMIT_ARG[@]}"
} 2>&1 | tee "${LOG}"
