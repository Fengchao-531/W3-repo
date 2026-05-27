#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PYTHON="/scratch3/che489/Ha/.conda/envs/vllm/bin/python"
if [[ -x "${DEFAULT_PYTHON}" ]]; then
  PYTHON="${PYTHON:-${DEFAULT_PYTHON}}"
else
  PYTHON="${PYTHON:-python}"
fi

export DATASENTINEL_MODEL_CONFIG="${DATASENTINEL_MODEL_CONFIG:-${ROOT}/Detection-based/Open-Prompt-Injection/configs/model_configs/mistral_config.json}"

if [[ -z "${DATASENTINEL_FT_PATH:-}" ]]; then
  echo "DATASENTINEL_FT_PATH is not set." >&2
  exit 1
fi

echo "Python: ${PYTHON}"
"${PYTHON}" "${ROOT}/run_datasentinel_prediction_results.py" "$@"
