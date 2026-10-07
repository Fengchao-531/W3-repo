#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GPU_INDEX="${XLLMS_EXP3_GPU:-2}"
QUEUE_LOG="$HERE/02_missing_exp3_queue.log"

run_model() {
  local model="$1"
  local runner="$2"
  local model_log="$HERE/$model/02_exp3_run.log"

  printf '[%s] START model=%s gpu=%s\n' "$(date -u +%FT%TZ)" "$model" "$GPU_INDEX" | tee -a "$QUEUE_LOG" "$model_log"
  if CUDA_VISIBLE_DEVICES="$GPU_INDEX" PYTHONUNBUFFERED=1 bash "$HERE/$runner" exp3 2>&1 | tee -a "$model_log"; then
    printf '[%s] COMPLETE model=%s\n' "$(date -u +%FT%TZ)" "$model" | tee -a "$QUEUE_LOG" "$model_log"
  else
    local exit_code="${PIPESTATUS[0]}"
    printf '[%s] FAILED model=%s exit_code=%s\n' "$(date -u +%FT%TZ)" "$model" "$exit_code" | tee -a "$QUEUE_LOG" "$model_log"
    return "$exit_code"
  fi
}

printf '[%s] QUEUE_START gpu=%s\n' "$(date -u +%FT%TZ)" "$GPU_INDEX" | tee -a "$QUEUE_LOG"
run_model DeepSeek run_deepseek_experiments.sh
run_model Gemma run_gemma_experiments.sh
run_model OLMo run_olmo_experiments.sh
run_model Qwen run_qwen_experiments.sh
printf '[%s] QUEUE_COMPLETE\n' "$(date -u +%FT%TZ)" | tee -a "$QUEUE_LOG"
