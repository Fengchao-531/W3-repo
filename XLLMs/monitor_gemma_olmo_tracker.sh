#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLURM_ACCOUNT="${SLURM_ACCOUNT:-OD-237777}"
GEMMA_ROOT="${GEMMA_RERUN_ROOT:-$HERE/Gemma}"
OLMO_ROOT="${OLMO_RERUN_ROOT:-$HERE/OLMo}"
SLEEP_SECONDS="${TRACKER_MONITOR_SLEEP:-300}"
LOG_DIR="$HERE/logs/rq2_tracker_monitor"
LOG_FILE="$LOG_DIR/monitor.log"
LOCK_FILE="$LOG_DIR/monitor.lock"
mkdir -p "$LOG_DIR" "$HERE/logs/rq2_tracker_slurm" "$HERE/logs/olmo_exp1_exp3_slurm"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Another Gemma/OLMo tracker monitor is already running: $LOCK_FILE" >&2
  exit 3
fi

model_root() {
  case "$1" in
    Gemma) echo "$GEMMA_ROOT" ;;
    OLMo) echo "$OLMO_ROOT" ;;
    *) return 1 ;;
  esac
}

role_model() {
  case "$1" in
    ReRunGemma) echo "Gemma" ;;
    ReRunOLMo) echo "OLMo" ;;
    *) return 1 ;;
  esac
}

exp1_count() {
  local model="$1"
  local root
  root="$(model_root "$model")"
  local total=0
  local dir count
  for dir in \
    "$root/Exp1_User_Context_Embedding/09_External_Runs" \
    "$root/Exp1_User_Context_Embedding/10_User_Context_Runs" \
    "$root/Exp1_User_Context_Embedding/10B_User_Context_Benign_Runs"; do
    if [[ -d "$dir" ]]; then
      count="$(find "$dir" -name 10_trace_summary.json 2>/dev/null | wc -l)"
      total=$((total + count))
    fi
  done
  echo "$total"
}

exp3_count() {
  local model="$1"
  local root
  root="$(model_root "$model")"
  local raw="$root/RQ2/Exp3_ Controlled_Source-Provenance_Intervention/02_controlled_source/raw_runs"
  [[ -d "$raw" ]] || { echo 0; return; }
  find "$raw" -name 10_trace_summary.json 2>/dev/null | wc -l
}

tracker_temporal_total() {
  local model="$1"
  local root
  root="$(model_root "$model")/RQ2Tracker"
  local total=0
  local path count
  for path in "$root/02_prefixes/01_rq1_prefix_manifest.jsonl" "$root/02_prefixes/02_exp3_prefix_manifest.jsonl"; do
    if [[ -f "$path" ]]; then
      count="$(wc -l < "$path")"
      total=$((total + count))
    fi
  done
  echo "$total"
}

tracker_temporal_done() {
  local model="$1"
  local root
  root="$(model_root "$model")/RQ2Tracker/03_activations"
  [[ -d "$root" ]] || { echo 0; return; }
  find "$root" -name '*.pt' 2>/dev/null | wc -l
}

tracker_stage_total() {
  local model="$1"
  local root
  root="$(model_root "$model")/RQ2Tracker/09_stage_tracing/01_stage_manifest.jsonl"
  [[ -f "$root" ]] || { echo 0; return; }
  wc -l < "$root"
}

tracker_stage_done() {
  local model="$1"
  local base
  base="$(model_root "$model")/RQ2Tracker/09_stage_tracing/activations"
  [[ -d "$base" ]] || { echo 0; return; }
  local i p e
  i="$(find "$base/01_interpretation" -name '*.pt' 2>/dev/null | wc -l)"
  p="$(find "$base/02_planning" -name '*.pt' 2>/dev/null | wc -l)"
  e="$(find "$base/03_execution" -name '*.pt' 2>/dev/null | wc -l)"
  printf '%s\n' "$i" "$p" "$e" | sort -n | head -1
}

tracker_complete() {
  local model="$1"
  local root
  root="$(model_root "$model")/RQ2Tracker"
  [[ -f "$root/08_logs/tracker_complete.ok" ]] && \
  [[ -f "$root/04_metrics/01_temporal_metrics.parquet" ]] && \
  [[ -f "$root/09_stage_tracing/metrics/01_artifact_carryover.parquet" ]] && \
  [[ -f "$root/09_stage_tracing/metrics/03_execution_representation.parquet" ]]
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

submit_role() {
  local role="$1"
  local model
  model="$(role_model "$role")"
  local root
  root="$(model_root "$model")"
  local job_id
  if [[ "$role" == "ReRunOLMo" ]]; then
    local e1 e3
    e1="$(exp1_count OLMo | tr -d ' ')"
    e3="$(exp3_count OLMo | tr -d ' ')"
    if [[ "$e1" -lt 540 || "$e3" -lt 540 ]]; then
      job_id="$(sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="$role" "$HERE/olmo_exp1_exp3_job.sbatch" "$root")"
      echo "[$(date -Is)] SUBMIT role=$role phase=olmo_exp1_exp3 root=$root id=$job_id" | tee -a "$LOG_FILE"
      return
    fi
  fi
  job_id="$(sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="$role" "$HERE/rq2_tracker_job.sbatch" "$model" "$root")"
  echo "[$(date -Is)] SUBMIT role=$role phase=tracker model=$model root=$root id=$job_id" | tee -a "$LOG_FILE"
}

status_line() {
  local role="$1"
  local active="$2"
  local model
  model="$(role_model "$role")"
  local e1 e3 tt td st sd tracker_state phase
  e1="$(exp1_count "$model" | tr -d ' ')"
  e3="$(exp3_count "$model" | tr -d ' ')"
  tt="$(tracker_temporal_total "$model" | tr -d ' ')"
  td="$(tracker_temporal_done "$model" | tr -d ' ')"
  st="$(tracker_stage_total "$model" | tr -d ' ')"
  sd="$(tracker_stage_done "$model" | tr -d ' ')"
  tracker_state="incomplete"
  phase="tracker"
  if tracker_complete "$model"; then
    tracker_state="complete"
    phase="complete"
  elif [[ "$model" == "OLMo" && ( "$e1" -lt 540 || "$e3" -lt 540 ) ]]; then
    phase="olmo_exp1_exp3"
  elif [[ "$active" -gt 0 ]]; then
    phase="tracker_running"
  fi
  echo "[$(date -Is)] STATUS role=$role model=$model phase=$phase exp1=$e1/540 exp3=$e3/540 temporal=$td/$tt stage=$sd/$st tracker=$tracker_state active_jobs=$active" | tee -a "$LOG_FILE"
  local rows
  rows="$(active_job_rows "$role")"
  if [[ -z "$rows" ]]; then
    echo "[$(date -Is)] ACTIVE role=$role none" | tee -a "$LOG_FILE"
  else
    while IFS= read -r row; do
      echo "[$(date -Is)] ACTIVE role=$role $row" | tee -a "$LOG_FILE"
    done <<< "$rows"
  fi
}

role_complete() {
  local role="$1"
  local model
  model="$(role_model "$role")"
  if [[ "$model" == "OLMo" ]]; then
    local e1 e3
    e1="$(exp1_count OLMo | tr -d ' ')"
    e3="$(exp3_count OLMo | tr -d ' ')"
    [[ "$e1" -ge 540 && "$e3" -ge 540 ]] || return 1
  fi
  tracker_complete "$model"
}

echo "[$(date -Is)] MONITOR_START sleep=${SLEEP_SECONDS}s account=$SLURM_ACCOUNT gemma_root=$GEMMA_ROOT olmo_root=$OLMO_ROOT" | tee -a "$LOG_FILE"

while true; do
  all_done=1
  for role in ReRunGemma ReRunOLMo; do
    active="$(active_job_count "$role" | tr -d ' ')"
    status_line "$role" "$active"
    if ! role_complete "$role"; then
      all_done=0
      if [[ "$active" -eq 0 ]]; then
        submit_role "$role"
      fi
    fi
  done
  if [[ "$all_done" -eq 1 ]]; then
    echo "[$(date -Is)] MONITOR_DONE ReRunGemma and ReRunOLMo complete" | tee -a "$LOG_FILE"
    exit 0
  fi
  sleep "$SLEEP_SECONDS"
done
