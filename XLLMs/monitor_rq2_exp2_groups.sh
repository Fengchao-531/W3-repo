#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"
SLURM_ACCOUNT="${SLURM_ACCOUNT:-OD-237777}"
SLEEP_SECONDS="${RQ2_EXP2_MONITOR_SLEEP:-300}"
LOG_DIR="$HERE/logs/rq2_exp2_monitor"
LOG_FILE="$LOG_DIR/monitor.log"
LOCK_FILE="$LOG_DIR/monitor.lock"
mkdir -p "$LOG_DIR" "$HERE/logs/rq2_exp2_slurm"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Another RQ2 Exp2 monitor is already running: $LOCK_FILE" >&2
  exit 3
fi

models_for_group() {
  case "$1" in
    1) echo "Gemma Qwen" ;;
    2) echo "Mistral OLMo" ;;
    3) echo "Llama3.1 DeepSeek" ;;
    *) return 1 ;;
  esac
}

completed_for_model() {
  local model="$1"
  local root="$HERE/$model/RQ2/Exp2_SafetyIntent/02_runs"
  if [[ ! -d "$root" ]]; then
    echo 0
    return
  fi
  find "$root" -name 15_trace_summary.json 2>/dev/null | wc -l
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

active_job_count() {
  local job_name="$1"
  squeue -h -u "$USER" -n "$job_name" -t PD,R,CG,CF,CONFIGURING,COMPLETING 2>/dev/null | wc -l
}

submit_group() {
  local group="$1"
  local job_name="RQ2Exp2-$group"
  local job_id
  job_id="$(sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="$job_name" "$HERE/rq2_exp2_group_job.sbatch" "$group")"
  echo "[$(date -Is)] SUBMIT group=$group job=$job_name id=$job_id" | tee -a "$LOG_FILE"
}

status_line() {
  local group="$1"
  local completed="$2"
  local active="$3"
  echo "[$(date -Is)] STATUS group=$group models=$(models_for_group "$group") completed=$completed/720 active_jobs=$active" | tee -a "$LOG_FILE"
}

echo "[$(date -Is)] MONITOR_START sleep=${SLEEP_SECONDS}s" | tee -a "$LOG_FILE"

while true; do
  all_done=1
  for group in 1 2 3; do
    job_name="RQ2Exp2-$group"
    completed="$(completed_for_group "$group" | tr -d ' ')"
    active="$(active_job_count "$job_name" | tr -d ' ')"
    status_line "$group" "$completed" "$active"
    if [[ "$completed" -lt 720 ]]; then
      all_done=0
      if [[ "$active" -eq 0 ]]; then
        submit_group "$group"
      fi
    fi
  done
  if [[ "$all_done" -eq 1 ]]; then
    echo "[$(date -Is)] MONITOR_DONE all groups complete" | tee -a "$LOG_FILE"
    exit 0
  fi
  sleep "$SLEEP_SECONDS"
done
