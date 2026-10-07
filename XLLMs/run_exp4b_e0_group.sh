#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GROUP="${1:?Usage: $0 <1|2|3|A|B|C> [extra launcher args...]}"
shift || true

case "${GROUP,,}" in
  1|a) MODELS=(gemma qwen) ;;
  2|b) MODELS=(mistral) ;;
  3|c) MODELS=(llama deepseek) ;;
  *)
    echo "Usage: $0 <1|2|3|A|B|C> [extra launcher args...]" >&2
    echo "  group 1/A: gemma qwen" >&2
    echo "  group 2/B: mistral" >&2
    echo "  group 3/C: llama deepseek" >&2
    exit 2
    ;;
esac

PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"
LOG_DIR="${LOG_DIR:-$HERE/logs/exp4b_e0_groups}"
mkdir -p "$LOG_DIR"

unset SLURM_HOME SLURM_CONF SLURM_STEP_ID SLURM_STEPID SLURM_STEP_NODELIST
unset SLURM_NTASKS SLURM_NPROCS SLURM_PROCID SLURM_LOCALID SLURM_TASK_PID
unset PMI_FD PMI_RANK PMI_SIZE PMIX_RANK PMIX_NAMESPACE

run_python() {
  env \
    -u SLURM_HOME \
    -u SLURM_CONF \
    -u SLURM_STEP_ID \
    -u SLURM_STEPID \
    -u SLURM_STEP_NODELIST \
    -u SLURM_NTASKS \
    -u SLURM_NPROCS \
    -u SLURM_PROCID \
    -u SLURM_LOCALID \
    -u SLURM_TASK_PID \
    -u PMI_FD \
    -u PMI_RANK \
    -u PMI_SIZE \
    -u PMIX_RANK \
    -u PMIX_NAMESPACE \
    "$PYTHON_BIN" "$@"
}

visible_gpu_count() {
  run_python - <<'PY'
import os
value = os.environ.get("CUDA_VISIBLE_DEVICES")
if value:
    devices = [item for item in value.split(",") if item.strip() and item.strip() != "-1"]
    print(len(devices))
else:
    try:
        import torch
        print(torch.cuda.device_count())
    except Exception:
        print(1)
PY
}

run_model() {
  local model="$1"
  local device="$2"
  shift 2
  local log="$LOG_DIR/group${GROUP}_${model}.log"
  echo "[$(date -Is)] START group=$GROUP model=$model device=$device log=$log"
  DEVICE="$device" "$HERE/run_all_models.sh" exp4b_e0 "$model" -- --no-hidden-states "$@" \
    > "$log" 2>&1
  echo "[$(date -Is)] DONE  group=$GROUP model=$model device=$device"
}

GPU_COUNT="$(visible_gpu_count)"
echo "exp4b_e0_group=$GROUP models=${MODELS[*]} visible_gpus=$GPU_COUNT"

if [[ ${#MODELS[@]} -ge 2 && "$GPU_COUNT" -ge 2 && "${EXP4B_E0_PARALLEL_IF_POSSIBLE:-1}" != "0" ]]; then
  run_model "${MODELS[0]}" cuda:0 "$@" &
  pid0=$!
  run_model "${MODELS[1]}" cuda:1 "$@" &
  pid1=$!
  wait "$pid0"
  wait "$pid1"
else
  for model in "${MODELS[@]}"; do
    run_model "$model" cuda:0 "$@"
  done
fi
