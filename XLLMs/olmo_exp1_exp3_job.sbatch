#!/usr/bin/env bash
#SBATCH --partition=h2gpu
#SBATCH --account=OD-237777
#SBATCH --time=02:00:00
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --output=/scratch3/che489/FC-W4/Tracing-Reproduction/W3/XLLMs/logs/olmo_exp1_exp3_slurm/%x-%j.out
#SBATCH --error=/scratch3/che489/FC-W4/Tracing-Reproduction/W3/XLLMs/logs/olmo_exp1_exp3_slurm/%x-%j.err

set -euo pipefail

HERE="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/XLLMs"
OLMO_ROOT="${1:-$HERE/OLMo}"
mkdir -p "$HERE/logs/olmo_exp1_exp3_slurm"
cd "$HERE"

if [[ -f /scratch3/che489/anaconda3_new/etc/profile.d/conda.sh ]]; then
  source /scratch3/che489/anaconda3_new/etc/profile.d/conda.sh
  conda activate W4 || true
fi

export PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"
export PYTHONUNBUFFERED=1

heartbeat() {
  while true; do
    echo "[$(date -Is)] NODE_STATUS job=${SLURM_JOB_NAME:-unknown} id=${SLURM_JOB_ID:-unknown} node=${SLURMD_NODENAME:-unknown}"
    squeue -j "${SLURM_JOB_ID:-0}" -o "%.18i %.24j %.10T %.12M %.10l %.9P %.12N %.35R" || true
    nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv,noheader || true
    nvidia-smi || true
    ps -u "$USER" -o pid,ppid,stat,etime,pcpu,pmem,args --sort=-pcpu | head -40 || true
    sleep 300
  done
}
heartbeat &
HEARTBEAT_PID=$!
trap 'kill "$HEARTBEAT_PID" 2>/dev/null || true' EXIT

echo "[$(date -Is)] olmo_exp1_exp3_start job=${SLURM_JOB_NAME:-unknown} id=${SLURM_JOB_ID:-unknown} node=${SLURMD_NODENAME:-unknown}"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"

DEVICE=cuda:0 "$PYTHON_BIN" "$HERE/rerun_olmo_w3.py" \
  --output-root "$OLMO_ROOT" \
  --device cuda:0 \
  --dtype bfloat16 \
  --stages exp1_core rq2_exp3 \
  --no-hidden-states

echo "[$(date -Is)] olmo_exp1_exp3_done job=${SLURM_JOB_NAME:-unknown} id=${SLURM_JOB_ID:-unknown}"
