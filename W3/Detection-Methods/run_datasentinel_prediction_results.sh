#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/fche0036/pk79_scratch/fche0036/W3/Detection-Methods"

export DATASENTINEL_MODEL_CONFIG="${DATASENTINEL_MODEL_CONFIG:-${ROOT}/Detection-based/Open-Prompt-Injection/configs/model_configs/mistral_config.json}"

if [[ -z "${DATASENTINEL_FT_PATH:-}" ]]; then
  echo "DATASENTINEL_FT_PATH is not set." >&2
  exit 1
fi

python "${ROOT}/run_datasentinel_prediction_results.py" "$@"
