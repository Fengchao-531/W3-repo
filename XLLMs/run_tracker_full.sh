#!/usr/bin/env bash
set -euo pipefail

TRACKER_DIR="${1:?Usage: $0 /path/to/Model/RQ2Tracker}"
DEVICE="${DEVICE:-cuda:0}"
PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"
LOG_FILE="$TRACKER_DIR/08_logs/full_resume.log"
COMPLETE_FILE="$TRACKER_DIR/08_logs/tracker_complete.ok"

mkdir -p "$TRACKER_DIR/08_logs"
cd "$TRACKER_DIR"
rm -f "$COMPLETE_FILE"

run_step() {
  local name="$1"
  shift
  echo "[$(date -Is)] START $name" | tee -a "$LOG_FILE"
  "$@" 2>&1 | tee -a "$LOG_FILE"
  local status="${PIPESTATUS[0]}"
  if [[ "$status" -ne 0 ]]; then
    echo "[$(date -Is)] FAIL  $name status=$status" | tee -a "$LOG_FILE"
    return "$status"
  fi
  echo "[$(date -Is)] DONE  $name" | tee -a "$LOG_FILE"
}

run_python() {
  env \
    -u SLURM_HOME \
    -u SLURM_CONF \
    -u SLURM_STEP_ID \
    -u SLURM_STEP_NODELIST \
    -u SLURM_NTASKS \
    -u SLURM_PROCID \
    -u SLURM_LOCALID \
    -u PMI_FD \
    -u PMI_RANK \
    -u PMI_SIZE \
    "$PYTHON_BIN" "$@"
}

run_step spans run_python tracker_pipeline.py spans
run_step prefixes run_python tracker_pipeline.py prefixes
run_step temporal_extract run_python tracker_pipeline.py extract --device "$DEVICE"
run_step temporal_metrics run_python tracker_pipeline.py metrics
run_step stages_manifest run_python tracker_pipeline.py stages
run_step stages_extract run_python tracker_pipeline.py stages-extract --device "$DEVICE"
run_step stages_metrics run_python tracker_pipeline.py stages-metrics

date -Is > "$COMPLETE_FILE"
echo "[$(date -Is)] TRACKER_FULL_COMPLETE tracker=$TRACKER_DIR" | tee -a "$LOG_FILE"
