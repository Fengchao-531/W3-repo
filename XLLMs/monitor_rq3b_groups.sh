#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLURM_ACCOUNT="${SLURM_ACCOUNT:-OD-237777}"
SLEEP_SECONDS="${RQ3B_MONITOR_SLEEP:-300}"
RERUN_MODE="${RQ3B_MONITOR_MODE:-all_with_deepseek_fixed_parser}"
LOG_DIR="$HERE/logs/rq3b_monitor"
LOG_FILE="$LOG_DIR/monitor.log"
LOCK_FILE="$LOG_DIR/monitor.lock"
mkdir -p "$LOG_DIR" "$HERE/logs/rq3b_slurm" "$HERE/logs/rq3b_groups"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Another RQ3-B monitor is already running: $LOCK_FILE" >&2
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

completed_for_model() {
  local model="$1"
  if [[ "$RERUN_MODE" == "all_with_deepseek_fixed_parser" && "$model" == "DeepSeek" ]]; then
    local marker="$LOG_DIR/deepseek_fixed_parser.done"
    [[ -f "$marker" ]] && { expected_for_model "$model"; return; }
    echo 0
    return
  fi
  local root="$HERE/$model/RQ3/RQ3-BDefenseCoverage/02_runs"
  [[ -d "$root" ]] || { echo 0; return; }
  find "$root" -name 15_trace_summary.json 2>/dev/null | wc -l
}

expected_for_model() {
  local model="$1"
  local q="$HERE/$model/RQ3/RQ3-BDefenseCoverage/01_matched_manifest/02_run_queue.jsonl"
  if [[ -f "$q" ]]; then
    wc -l < "$q"
  else
    echo 2880
  fi
}

completed_for_group() {
  local total=0 count
  for model in $(models_for_group "$1"); do
    count="$(completed_for_model "$model" | tr -d ' ')"
    total=$((total + count))
  done
  echo "$total"
}

expected_for_group() {
  local total=0 count
  for model in $(models_for_group "$1"); do
    count="$(expected_for_model "$model" | tr -d ' ')"
    total=$((total + count))
  done
  echo "$total"
}

active_job_count() {
  squeue -h -u "$USER" -n "$1" -t PD,R,CG,CF,CONFIGURING,COMPLETING 2>/dev/null | wc -l
}

active_job_rows() {
  squeue -h -u "$USER" -n "$1" -t PD,R,CG,CF,CONFIGURING,COMPLETING \
    -o "id=%i name=%j state=%T elapsed=%M limit=%l partition=%P node=%N reason=%R" 2>/dev/null || true
}

submit_group() {
  local group="$1"
  local job_name="RQ3B-$group"
  local job_id
  if [[ "$RERUN_MODE" == "all_with_deepseek_fixed_parser" ]]; then
    job_id="$(sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="$job_name" --export=ALL,RQ3B_FORCE_MODELS=deepseek,MAX_NEW_TOKENS=2048 "$HERE/rq3b_group_job.sbatch" "$group")"
  else
    job_id="$(sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="$job_name" "$HERE/rq3b_group_job.sbatch" "$group")"
  fi
  echo "[$(date -Is)] SUBMIT group=$group job=$job_name id=$job_id" | tee -a "$LOG_FILE"
}

echo "[$(date -Is)] MONITOR_START sleep=${SLEEP_SECONDS}s account=$SLURM_ACCOUNT excluded=OLMo mode=$RERUN_MODE" | tee -a "$LOG_FILE"

while true; do
  all_done=1
  for group in 1 2 3; do
    models="$(models_for_group "$group")"
    [[ -n "$models" ]] || continue
    job_name="RQ3B-$group"
    completed="$(completed_for_group "$group" | tr -d ' ')"
    expected="$(expected_for_group "$group" | tr -d ' ')"
    active="$(active_job_count "$job_name" | tr -d ' ')"
    echo "[$(date -Is)] STATUS group=$group models=$models completed=$completed/$expected active_jobs=$active" | tee -a "$LOG_FILE"
    rows="$(active_job_rows "$job_name")"
    if [[ -z "$rows" ]]; then
      echo "[$(date -Is)] ACTIVE group=$group none" | tee -a "$LOG_FILE"
    else
      while IFS= read -r row; do
        echo "[$(date -Is)] ACTIVE group=$group $row" | tee -a "$LOG_FILE"
      done <<< "$rows"
    fi
    if [[ "$completed" -lt "$expected" ]]; then
      all_done=0
      if [[ "$active" -eq 0 ]]; then
        submit_group "$group"
      fi
    elif [[ "$RERUN_MODE" == "all_with_deepseek_fixed_parser" && "$group" == "3" ]]; then
      touch "$LOG_DIR/deepseek_fixed_parser.done"
    fi
  done
  if [[ "$all_done" -eq 1 ]]; then
    echo "[$(date -Is)] MONITOR_DONE all RQ3-B groups complete" | tee -a "$LOG_FILE"
    exit 0
  fi
  sleep "$SLEEP_SECONDS"
done
