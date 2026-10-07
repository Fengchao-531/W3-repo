#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLURM_ACCOUNT="${SLURM_ACCOUNT:-OD-237777}"
SLEEP_SECONDS="${SLEEP_SECONDS:-300}"
MAX_LOOPS="${MAX_LOOPS:-0}"
MODELS=(llama mistral deepseek qwen gemma)

model_dir() {
  case "$1" in
    llama) echo "$HERE/Llama3.1" ;;
    mistral) echo "$HERE/Mistral" ;;
    deepseek) echo "$HERE/DeepSeek" ;;
    qwen) echo "$HERE/Qwen" ;;
    gemma) echo "$HERE/Gemma" ;;
  esac
}

count_files() {
  local root="$1"
  local pattern="$2"
  [[ -d "$root" ]] || { echo 0; return; }
  find "$root" -name "$pattern" 2>/dev/null | wc -l
}

active_job() {
  local pattern="$1"
  squeue -h -u "$USER" -o '%j' | rg -q "^${pattern}$"
}

any_active_group_a0() {
  squeue -h -u "$USER" -o '%j' | rg -q '^Exp4A0-[123]$'
}

submit_a0_model() {
  local model="$1"
  local job_name="Exp4A0-${model}"
  echo "[$(date -Is)] submit $job_name"
  sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="$job_name" "$HERE/exp4_a0_model_job.sbatch" "$model"
}

submit_a1a2_model() {
  local model="$1"
  local job_name="Exp4A12-${model}"
  echo "[$(date -Is)] submit $job_name"
  sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="$job_name" "$HERE/exp4_a1a2_model_job.sbatch" "$model"
}

loop=0
while true; do
  loop=$((loop + 1))
  echo
  echo "[$(date -Is)] monitor loop=$loop"
  "$HERE/progress_exp4_a0.sh"

  all_done=1
  a0_group_active=0
  if any_active_group_a0; then
    a0_group_active=1
  fi

  for model in "${MODELS[@]}"; do
    root="$(model_dir "$model")"
    a0_count="$(count_files "$root/Exp4_General_Preference_Control/04_runs/A0" 13_trace_summary.json)"
    a1a2_count="$(count_files "$root/Exp4_General_Preference_Control/03_reference_A1_A2/03_runs" 16_trace_summary.json)"

    if [[ "$a1a2_count" -lt 360 ]]; then
      all_done=0
      if ! active_job "Exp4A12-${model}"; then
        submit_a1a2_model "$model"
      fi
    fi

    if [[ "$a0_count" -lt 180 ]]; then
      all_done=0
      if [[ "$a0_group_active" -eq 0 ]] && ! active_job "Exp4A0-${model}"; then
        submit_a0_model "$model"
      fi
    fi

    if [[ "$a0_count" -ge 180 && "$a1a2_count" -ge 360 ]]; then
      "$HERE/finalize_exp4_for_model.sh" "$model"
    fi
  done

  if [[ "$all_done" -eq 1 ]]; then
    echo "[$(date -Is)] all models complete"
    exit 0
  fi
  if [[ "$MAX_LOOPS" -gt 0 && "$loop" -ge "$MAX_LOOPS" ]]; then
    echo "[$(date -Is)] reached MAX_LOOPS=$MAX_LOOPS"
    exit 0
  fi
  sleep "$SLEEP_SECONDS"
done
