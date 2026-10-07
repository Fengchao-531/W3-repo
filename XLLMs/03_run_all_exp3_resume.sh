#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPECTED_RUNS=540
GPU_INDEX="${XLLMS_EXP3_GPU:-0}"
QUEUE_LOG="$HERE/03_all_exp3_resume.log"
LOCK_FILE="$HERE/03_all_exp3_resume.lock"

declare -A RUNNERS=(
  [Llama3.1]="run_llama31_experiments.sh"
  [Mistral]="run_mistral_experiments.sh"
  [DeepSeek]="run_deepseek_experiments.sh"
  [Gemma]="run_gemma_experiments.sh"
  [OLMo]="run_olmo_experiments.sh"
  [Qwen]="run_qwen_experiments.sh"
)

MODELS=(Llama3.1 Mistral DeepSeek Gemma OLMo Qwen)

usage() {
  printf 'Usage: %s [--gpu INDEX] [MODEL ...]\n' "$0"
  printf 'Models: Llama3.1 Mistral DeepSeek Gemma OLMo Qwen\n'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gpu)
      GPU_INDEX="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      MODELS=("$@")
      break
      ;;
  esac
done

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  printf 'Another Exp3 resume queue already holds %s\n' "$LOCK_FILE" >&2
  exit 3
fi

count_completed() {
  local model="$1"
  local raw_root="$HERE/$model/RQ2/Exp3_ Controlled_Source-Provenance_Intervention/02_controlled_source/raw_runs"
  if [[ ! -d "$raw_root" ]]; then
    printf '0\n'
    return
  fi
  find "$raw_root" -type f -name 10_trace_summary.json -print | wc -l
}

run_model() {
  local model="$1"
  local runner="${RUNNERS[$model]:-}"
  local completed
  local model_log="$HERE/$model/03_exp3_resume.log"

  if [[ -z "$runner" ]]; then
    printf '[%s] UNKNOWN_MODEL model=%s\n' "$(date -u +%FT%TZ)" "$model" | tee -a "$QUEUE_LOG"
    return 2
  fi

  completed="$(count_completed "$model" | tr -d ' ')"
  if [[ "$completed" -ge "$EXPECTED_RUNS" ]]; then
    printf '[%s] SKIP_COMPLETE model=%s completed=%s/%s\n' \
      "$(date -u +%FT%TZ)" "$model" "$completed" "$EXPECTED_RUNS" | tee -a "$QUEUE_LOG"
    return 0
  fi

  printf '[%s] START_OR_RESUME model=%s completed=%s/%s gpu=%s\n' \
    "$(date -u +%FT%TZ)" "$model" "$completed" "$EXPECTED_RUNS" "$GPU_INDEX" \
    | tee -a "$QUEUE_LOG" "$model_log"

  # The model runners omit --force, so each existing trace summary is a checkpoint.
  if CUDA_VISIBLE_DEVICES="$GPU_INDEX" PYTHONUNBUFFERED=1 \
      bash "$HERE/$runner" exp3 2>&1 | tee -a "$model_log"; then
    completed="$(count_completed "$model" | tr -d ' ')"
    if [[ "$completed" -eq "$EXPECTED_RUNS" ]]; then
      printf '[%s] COMPLETE model=%s completed=%s/%s\n' \
        "$(date -u +%FT%TZ)" "$model" "$completed" "$EXPECTED_RUNS" \
        | tee -a "$QUEUE_LOG" "$model_log"
    else
      printf '[%s] INCOMPLETE model=%s completed=%s/%s\n' \
        "$(date -u +%FT%TZ)" "$model" "$completed" "$EXPECTED_RUNS" \
        | tee -a "$QUEUE_LOG" "$model_log"
      return 4
    fi
  else
    local exit_code="${PIPESTATUS[0]}"
    completed="$(count_completed "$model" | tr -d ' ')"
    printf '[%s] INTERRUPTED model=%s completed=%s/%s exit_code=%s\n' \
      "$(date -u +%FT%TZ)" "$model" "$completed" "$EXPECTED_RUNS" "$exit_code" \
      | tee -a "$QUEUE_LOG" "$model_log"
    return "$exit_code"
  fi
}

printf '[%s] QUEUE_START gpu=%s models=%s\n' \
  "$(date -u +%FT%TZ)" "$GPU_INDEX" "${MODELS[*]}" | tee -a "$QUEUE_LOG"

for model in "${MODELS[@]}"; do
  run_model "$model"
done

printf '[%s] QUEUE_COMPLETE\n' "$(date -u +%FT%TZ)" | tee -a "$QUEUE_LOG"
