#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLURM_ACCOUNT="${SLURM_ACCOUNT:-OD-237777}"
SLEEP_SECONDS="${SLEEP_SECONDS:-300}"
MAX_LOOPS="${MAX_LOOPS:-144}"
READY_BYTES="${READY_BYTES:-10737418240}"

DEEPSEEK_SNAP="/scratch3/che489/FC-W2-SoK/model_cache/hub/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-7B/snapshots/916b56a44061fd5cd7d6a8fb632557ed4f724f60"
MISTRAL_SNAP="/scratch3/che489/FC-W2-SoK/model_cache/hub/models--mistralai--Ministral-8B-Instruct-2410/snapshots/2f494a194c5b980dfb9772cb92d26cbb671fce5a"

size_bytes() {
  local snap="$1"
  [[ -d "$snap" ]] || { echo 0; return; }
  find "$snap" -maxdepth 1 -name '*.safetensors' -printf '%s\n' \
    | awk '{s += $1} END {print s + 0}'
}

active_job() {
  local name="$1"
  squeue -h -u "$USER" -o '%j' | rg -q "^${name}$"
}

submit_deepseek_jobs() {
  if ! active_job "Exp4A0-deepseek"; then
    sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="Exp4A0-deepseek" \
      "$HERE/exp4_a0_model_job.sbatch" deepseek
  fi
  if ! active_job "Exp4A12-deepseek"; then
    sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="Exp4A12-deepseek" \
      "$HERE/exp4_a1a2_model_job.sbatch" deepseek
  fi
}

submit_mistral_jobs() {
  if ! active_job "Exp4A12-mistral"; then
    sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="Exp4A12-mistral" \
      "$HERE/exp4_a1a2_model_job.sbatch" mistral
  fi
}

submitted_deepseek=0
submitted_mistral=0
last_deepseek_bytes=-1
last_mistral_bytes=-1

echo "[$(date -Is)] watcher_start ready_bytes=${READY_BYTES} max_loops=${MAX_LOOPS} stable_required=1"

for loop in $(seq 1 "$MAX_LOOPS"); do
  deepseek_bytes="$(size_bytes "$DEEPSEEK_SNAP")"
  mistral_bytes="$(size_bytes "$MISTRAL_SNAP")"
  deepseek_stable=0
  mistral_stable=0
  [[ "$deepseek_bytes" -eq "$last_deepseek_bytes" ]] && deepseek_stable=1
  [[ "$mistral_bytes" -eq "$last_mistral_bytes" ]] && mistral_stable=1
  echo "[$(date -Is)] loop=${loop} deepseek_bytes=${deepseek_bytes} deepseek_stable=${deepseek_stable} mistral_bytes=${mistral_bytes} mistral_stable=${mistral_stable} submitted_deepseek=${submitted_deepseek} submitted_mistral=${submitted_mistral}"

  if [[ "$submitted_deepseek" -eq 0 && "$deepseek_bytes" -ge "$READY_BYTES" && "$deepseek_stable" -eq 1 ]]; then
    echo "[$(date -Is)] deepseek_ready_submit"
    submit_deepseek_jobs
    submitted_deepseek=1
  fi

  if [[ "$submitted_mistral" -eq 0 && "$mistral_bytes" -ge "$READY_BYTES" && "$mistral_stable" -eq 1 ]]; then
    echo "[$(date -Is)] mistral_ready_submit"
    submit_mistral_jobs
    submitted_mistral=1
  fi

  if [[ "$submitted_deepseek" -eq 1 && "$submitted_mistral" -eq 1 ]]; then
    echo "[$(date -Is)] all_retry_jobs_submitted"
    exit 0
  fi

  last_deepseek_bytes="$deepseek_bytes"
  last_mistral_bytes="$mistral_bytes"
  sleep "$SLEEP_SECONDS"
done

echo "[$(date -Is)] watcher_timeout"
