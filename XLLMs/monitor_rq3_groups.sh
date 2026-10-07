#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLURM_ACCOUNT="${SLURM_ACCOUNT:-OD-237777}"
SLEEP_SECONDS="${RQ3_MONITOR_SLEEP:-300}"
LOG_DIR="$HERE/logs/rq3_monitor"
LOG_FILE="$LOG_DIR/monitor.log"
LOCK_FILE="$LOG_DIR/monitor.lock"
mkdir -p "$LOG_DIR" "$HERE/logs/rq3_slurm" "$HERE/logs/rq3_groups"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Another RQ3 monitor is already running: $LOCK_FILE" >&2
  exit 3
fi

models_for_group() {
  case "$1" in
    1) echo "Gemma Qwen" ;;
    2) echo "Mistral" ;;
    3) echo "Llama3.1 DeepSeek" ;;
    *) return 1 ;;
  esac
}

model_key() {
  case "$1" in
    Gemma) echo gemma ;;
    Qwen) echo qwen ;;
    Mistral) echo mistral ;;
    Llama3.1) echo llama ;;
    DeepSeek) echo deepseek ;;
    *) return 1 ;;
  esac
}

completed_for_model() {
  local model="$1"
  local root="$HERE/$model/RQ3/RQ3-AControlledVerification/02_runs"
  [[ -d "$root" ]] || { echo 0; return; }
  find "$root" -name 15_trace_summary.json 2>/dev/null | wc -l
}

expected_for_model() {
  local model="$1"
  local q="$HERE/$model/RQ3/RQ3-AControlledVerification/01_dataset/04_run_queue.jsonl"
  if [[ -f "$q" ]]; then
    wc -l < "$q"
  else
    echo 360
  fi
}

completed_for_group() {
  local group="$1"
  local total=0
  local count
  for model in $(models_for_group "$group"); do
    count="$(completed_for_model "$model" | tr -d ' ')"
    total=$((total + count))
  done
  echo "$total"
}

expected_for_group() {
  local group="$1"
  local total=0
  local count
  for model in $(models_for_group "$group"); do
    count="$(expected_for_model "$model" | tr -d ' ')"
    total=$((total + count))
  done
  echo "$total"
}

active_job_count() {
  local job_name="$1"
  squeue -h -u "$USER" -n "$job_name" -t PD,R,CG,CF,CONFIGURING,COMPLETING 2>/dev/null | wc -l
}

active_job_rows() {
  local job_name="$1"
  squeue -h -u "$USER" -n "$job_name" -t PD,R,CG,CF,CONFIGURING,COMPLETING \
    -o "id=%i name=%j state=%T elapsed=%M limit=%l partition=%P node=%N reason=%R" 2>/dev/null || true
}

submit_group() {
  local group="$1"
  local job_name="RQ3-$group"
  local job_id
  job_id="$(sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="$job_name" "$HERE/rq3_group_job.sbatch" "$group")"
  echo "[$(date -Is)] SUBMIT group=$group job=$job_name id=$job_id" | tee -a "$LOG_FILE"
}

status_line() {
  local group="$1"
  local completed="$2"
  local expected="$3"
  local active="$4"
  echo "[$(date -Is)] STATUS group=$group models=$(models_for_group "$group") completed=$completed/$expected active_jobs=$active" | tee -a "$LOG_FILE"
  local rows
  rows="$(active_job_rows "RQ3-$group")"
  if [[ -z "$rows" ]]; then
    echo "[$(date -Is)] ACTIVE group=$group none" | tee -a "$LOG_FILE"
  else
    while IFS= read -r row; do
      echo "[$(date -Is)] ACTIVE group=$group $row" | tee -a "$LOG_FILE"
    done <<< "$rows"
  fi
}

echo "[$(date -Is)] MONITOR_START sleep=${SLEEP_SECONDS}s account=$SLURM_ACCOUNT excluded=OLMo" | tee -a "$LOG_FILE"

while true; do
  all_done=1
  for group in 1 2 3; do
    job_name="RQ3-$group"
    completed="$(completed_for_group "$group" | tr -d ' ')"
    expected="$(expected_for_group "$group" | tr -d ' ')"
    active="$(active_job_count "$job_name" | tr -d ' ')"
    status_line "$group" "$completed" "$expected" "$active"
    if [[ "$completed" -lt "$expected" ]]; then
      all_done=0
      if [[ "$active" -eq 0 ]]; then
        submit_group "$group"
      fi
    fi
  done
  if [[ "$all_done" -eq 1 ]]; then
    echo "[$(date -Is)] MONITOR_DONE all RQ3 groups complete" | tee -a "$LOG_FILE"
    exit 0
  fi
  sleep "$SLEEP_SECONDS"
done
