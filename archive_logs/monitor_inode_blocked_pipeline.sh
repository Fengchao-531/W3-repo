#!/usr/bin/env bash
set -euo pipefail

ROOT="/scratch3/che489/FC-W4/Tracing-Reproduction/W3"
cd "$ROOT"

echo "============================================================"
date -Is
echo

echo "== inode / disk =="
df -ih /scratch3/che489
df -h /scratch3/che489
echo

echo "== RQ2Tracker zip progress =="
archive_logs/check_rq2_zip_progress.sh
echo

echo "== watcher =="
ps -eo pid,etime,cmd | grep -E 'restart_inode_blocked_jobs_after_quota.sh' | grep -v grep || echo "watcher not running"
latest_watcher="$(ls -t archive_logs/restart_inode_blocked_jobs_after_quota_*.log 2>/dev/null | head -1 || true)"
if [[ -n "$latest_watcher" ]]; then
  echo "--- latest watcher log: $latest_watcher ---"
  tail -25 "$latest_watcher"
fi
echo

echo "== slurm queue =="
squeue -u "${USER:-che489}" -o "%.18i %.10P %.32j %.8T %.10M %.6D %R" || true
echo

echo "== Exp4b E0 progress =="
XLLMs/progress_exp4b_e0.sh || true
echo

echo "== RQ2 v3/xllms progress summary =="
RQ2_Internal_Visualization/v3_artifact_gate_sanity/xllms/scripts/check_xllms_progress.sh | sed -n '1,160p' || true
