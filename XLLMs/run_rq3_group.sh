#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GROUP="${1:?Usage: $0 <1|2|3|A|B|C> [extra run_rq3_model.py args...]}"
shift || true

case "${GROUP,,}" in
  1|a) MODELS=(gemma qwen) ;;
  2|b) MODELS=(mistral) ;;
  3|c) MODELS=(llama deepseek) ;;
  *)
    echo "Usage: $0 <1|2|3|A|B|C> [extra run_rq3_model.py args...]" >&2
    echo "  group 1/A: gemma qwen" >&2
    echo "  group 2/B: mistral" >&2
    echo "  group 3/C: llama deepseek" >&2
    exit 2
    ;;
esac

source "$HERE/model_paths.sh"

PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"
LOG_DIR="${LOG_DIR:-$HERE/logs/rq3_groups}"
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

choose_device() {
  run_python - <<'PY'
import os, subprocess
visible = os.environ.get("CUDA_VISIBLE_DEVICES")
if visible:
    physical_ids = [x.strip() for x in visible.split(",") if x.strip() and x.strip() != "-1"]
    logical_for_physical = {physical: str(i) for i, physical in enumerate(physical_ids)}
else:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=index,memory.used,memory.total", "--format=csv,noheader,nounits"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        physical_ids = [line.split(",")[0].strip() for line in out.splitlines() if line.strip()]
        logical_for_physical = {physical: physical for physical in physical_ids}
    except Exception:
        physical_ids = ["0"]
        logical_for_physical = {"0": "0"}
best = None
try:
    out = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=index,memory.used,memory.total", "--format=csv,noheader,nounits"],
        text=True,
        stderr=subprocess.DEVNULL,
    )
    allowed = set(physical_ids)
    for line in out.splitlines():
        parts = [x.strip() for x in line.split(",")]
        if len(parts) < 3 or parts[0] not in allowed:
            continue
        idx, used, total = parts[0], int(parts[1]), int(parts[2])
        free = total - used
        if best is None or free > best[1]:
            best = (idx, free)
except Exception:
    pass
chosen_physical = best[0] if best else (physical_ids[0] if physical_ids else "0")
print(f"cuda:{logical_for_physical.get(chosen_physical, '0')}")
PY
}

run_model() {
  local model="$1"
  local device="$2"
  shift 2
  local log="$LOG_DIR/group${GROUP}_${model}.log"
  echo "[$(date -Is)] START group=$GROUP model=$model device=$device log=$log"
  DEVICE="$device" run_python "$HERE/run_rq3_model.py" "$model" \
    --device "$device" \
    --dtype "${DTYPE:-bfloat16}" \
    --max-new-tokens "${MAX_NEW_TOKENS:-2048}" \
    --no-hidden-states \
    "$@" > "$log" 2>&1
  echo "[$(date -Is)] DONE  group=$GROUP model=$model device=$device"
}

echo "group=$GROUP models=${MODELS[*]}"
for model in "${MODELS[@]}"; do
  device="$(choose_device)"
  run_model "$model" "$device" "$@"
done
