#!/usr/bin/env bash
set -euo pipefail

ROOT="/scratch3/che489/FC-W4/Tracing-Reproduction/W3"
MIN_FREE_INODES="${MIN_FREE_INODES:-35000}"
CHECK_INTERVAL="${CHECK_INTERVAL:-60}"
SCRATCH_PATH="${SCRATCH_PATH:-/scratch3/che489}"
SUBMIT_LOCK="$ROOT/archive_logs/inode_blocked_jobs_submitted.lock"

free_inodes() {
  df -Pi "$SCRATCH_PATH" | awk 'NR==2 {print $4}'
}

queued_or_running() {
  local job_name="$1"
  squeue -h -u "${USER:-che489}" -n "$job_name" 2>/dev/null | grep -q .
}

submit_once() {
  local job_name="$1"
  shift
  if queued_or_running "$job_name"; then
    echo "[$(date -Is)] skip already queued/running: $job_name"
  else
    echo "[$(date -Is)] submit $job_name"
    sbatch --parsable --job-name="$job_name" "$@" | sed "s/^/[jobid] $job_name /"
  fi
}

echo "[$(date -Is)] watcher_start min_free_inodes=$MIN_FREE_INODES scratch=$SCRATCH_PATH"
if [[ -e "$SUBMIT_LOCK" ]]; then
  echo "[$(date -Is)] found existing submit lock: $SUBMIT_LOCK"
  echo "[$(date -Is)] exiting to avoid duplicate submissions"
  exit 0
fi

while true; do
  free="$(free_inodes)"
  dg_state="$(
    awk -F= '$1=="state"{state=$2} END{print state}' \
      "$ROOT/archive_logs/DeepSeek_Gemma_rq2tracker_zip_20261001.progress" 2>/dev/null || true
  )"
  dg_line="$(
    { "$ROOT/archive_logs/check_rq2_zip_progress.sh" 2>/dev/null | awk '$1=="DeepSeek_Gemma"{print; exit}'; } || true
  )"
  echo "[$(date -Is)] free_inodes=$free DeepSeek_Gemma_state=${dg_state:-unknown} progress=${dg_line:-unknown}"
  if [[ "$free" =~ ^[0-9]+$ ]] && (( free >= MIN_FREE_INODES )); then
    break
  fi
  sleep "$CHECK_INTERVAL"
done

if ! mkdir "$SUBMIT_LOCK" 2>/dev/null; then
  echo "[$(date -Is)] another watcher created submit lock; exiting"
  exit 0
fi

mkdir -p "$ROOT/XLLMs/logs/exp4b_e0_slurm" "$ROOT/RQ2_Internal_Visualization/v3_artifact_gate_sanity/xllms/logs"

echo "[$(date -Is)] submitting Exp4b E0 groups"
for group in 1 2 3; do
  submit_once "Exp4bE0-$group" "$ROOT/XLLMs/exp4b_e0_group_job.sbatch" "$group"
done

echo "[$(date -Is)] submitting RQ2 v3 xllms Fig.3-6 jobs"
submit_once "RQ2X-ministral_8b_instruct_2410" \
  "$ROOT/RQ2_Internal_Visualization/v3_artifact_gate_sanity/xllms/scripts/xllms_fig3_6_model_job.sbatch" \
  "ministral_8b_instruct_2410" \
  "/scratch3/che489/FC-W2-SoK/model_cache/hub/models--mistralai--Ministral-8B-Instruct-2410/snapshots/2f494a194c5b980dfb9772cb92d26cbb671fce5a" \
  "28,29,30,31,32"

submit_once "RQ2X-deepseek_r1_distill_qwen_7b" \
  "$ROOT/RQ2_Internal_Visualization/v3_artifact_gate_sanity/xllms/scripts/xllms_fig3_6_model_job.sbatch" \
  "deepseek_r1_distill_qwen_7b" \
  "/scratch3/che489/FC-W2-SoK/model_cache/hub/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-7B/snapshots/916b56a44061fd5cd7d6a8fb632557ed4f724f60" \
  "22,23,24,25"

submit_once "RQ2X-qwen25_7b_instruct" \
  "$ROOT/RQ2_Internal_Visualization/v3_artifact_gate_sanity/xllms/scripts/xllms_fig3_6_model_job.sbatch" \
  "qwen25_7b_instruct" \
  "/scratch3/che489/hf_home/models/w3_models/Qwen2.5-7B-Instruct" \
  "22,23,24,25"

submit_once "RQ2X-gemma2_9b_it" \
  "$ROOT/RQ2_Internal_Visualization/v3_artifact_gate_sanity/xllms/scripts/xllms_fig3_6_model_job.sbatch" \
  "gemma2_9b_it" \
  "/scratch3/che489/hf_home/models/w3_models/gemma-2-9b-it" \
  "33,34,35,36"

echo "[$(date -Is)] watcher_done"
