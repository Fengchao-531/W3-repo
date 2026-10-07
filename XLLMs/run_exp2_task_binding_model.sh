#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL="${1:?Usage: $0 <llama|mistral|deepseek|qwen|gemma> [extra launcher args...]}"
shift || true

DEVICE="${DEVICE:-cuda:0}"
LOG_DIR="${LOG_DIR:-$HERE/logs/exp2_task_binding_models}"
mkdir -p "$LOG_DIR"

log="$LOG_DIR/${MODEL}.log"
echo "[$(date -Is)] START stage=exp2 model=$MODEL device=$DEVICE log=$log"
DEVICE="$DEVICE" "$HERE/run_all_models.sh" exp2 "$MODEL" -- --no-hidden-states "$@" \
  > "$log" 2>&1
echo "[$(date -Is)] DONE  stage=exp2 model=$MODEL device=$DEVICE"
