#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT="${INPUT:-${ROOT}/prediction result/our-attack-full-set.jsonl}"
RUN_DIR="${RUN_DIR:-${ROOT}/runs/datasentinel_our_attack_full_set}"
DEFAULT_FT_PATH="/tmp/w3_models/datasentinel/detector_large/checkpoint-5000"
DEFAULT_MODEL_CONFIG="/tmp/w3_mistral_config_gpu0.json"
LIMIT_ARG=()

mkdir -p "${RUN_DIR}"

if [[ -z "${DATASENTINEL_FT_PATH:-}" && -f "${DEFAULT_FT_PATH}/adapter_config.json" ]]; then
  export DATASENTINEL_FT_PATH="${DEFAULT_FT_PATH}"
fi
if [[ -z "${DATASENTINEL_MODEL_CONFIG:-}" && -f "${DEFAULT_MODEL_CONFIG}" ]]; then
  export DATASENTINEL_MODEL_CONFIG="${DEFAULT_MODEL_CONFIG}"
fi
if [[ -d /tmp/w3_hf ]]; then
  export HF_HOME="${HF_HOME:-/tmp/w3_hf}"
  export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-/tmp/w3_hf/transformers}"
fi
if [[ -d /tmp/w3_triton ]]; then
  export TRITON_CACHE_DIR="${TRITON_CACHE_DIR:-/tmp/w3_triton}"
fi
if [[ -d /tmp/w3_cache ]]; then
  export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/tmp/w3_cache}"
fi

if [[ -n "${LIMIT:-}" ]]; then
  LIMIT_ARG=(--limit "${LIMIT}")
fi

LOG="${LOG:-${RUN_DIR}/datasentinel_$(date +%Y%m%d_%H%M%S).log}"

{
  echo "Input: ${INPUT}"
  echo "Run dir: ${RUN_DIR}"
  echo "Log: ${LOG}"
  echo "DATASENTINEL_FT_PATH: ${DATASENTINEL_FT_PATH:-}"
  echo "DATASENTINEL_MODEL_CONFIG: ${DATASENTINEL_MODEL_CONFIG:-}"
  echo "Resume: rows with existing datasentinel_verdict are skipped"
  if [[ "${DRY_RUN:-0}" == "1" ]]; then
    echo "DRY_RUN=1, not launching DataSentinel."
    exit 0
  fi

  "${ROOT}/run_datasentinel_prediction_results.sh" \
    --input "${INPUT}" \
    "${LIMIT_ARG[@]}"
} 2>&1 | tee "${LOG}"
