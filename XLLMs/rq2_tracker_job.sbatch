#!/usr/bin/env bash
#SBATCH --partition=h2gpu
#SBATCH --account=OD-237777
#SBATCH --time=02:00:00
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --output=/scratch3/che489/FC-W4/Tracing-Reproduction/W3/XLLMs/logs/rq2_tracker_slurm/%x-%j.out
#SBATCH --error=/scratch3/che489/FC-W4/Tracing-Reproduction/W3/XLLMs/logs/rq2_tracker_slurm/%x-%j.err

set -euo pipefail

HERE="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/XLLMs"
MODEL="${1:?Usage: sbatch rq2_tracker_job.sbatch <Gemma|OLMo>}"
ROOT_OVERRIDE="${2:-}"
if [[ -n "$ROOT_OVERRIDE" ]]; then
  MODEL_ROOT="$ROOT_OVERRIDE"
else
  MODEL_ROOT="$HERE/$MODEL"
fi
TRACKER_DIR="$MODEL_ROOT/RQ2Tracker"

mkdir -p "$HERE/logs/rq2_tracker_slurm"
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

prepare_tracker_dir() {
  mkdir -p "$TRACKER_DIR"
  TEMPLATE_DIR="$HERE/$MODEL/RQ2Tracker"
  if [[ "$MODEL" == "Gemma" ]]; then
    TEMPLATE_DIR="$HERE/Gemma/RQ2Tracker"
  elif [[ "$MODEL" == "OLMo" ]]; then
    TEMPLATE_DIR="$HERE/OLMo/RQ2Tracker"
  else
    echo "Unknown tracker model: $MODEL" >&2
    exit 2
  fi
  if [[ "$TRACKER_DIR" != "$TEMPLATE_DIR" ]]; then
    cp "$TEMPLATE_DIR/tracker_pipeline.py" "$TRACKER_DIR/tracker_pipeline.py"
    cp "$TEMPLATE_DIR/run_demo.sh" "$TRACKER_DIR/run_demo.sh"
  elif [[ ! -f "$TRACKER_DIR/tracker_pipeline.py" || ! -f "$TRACKER_DIR/run_demo.sh" ]]; then
    echo "Missing tracker files in template directory: $TRACKER_DIR" >&2
    exit 2
  fi
  chmod +x "$TRACKER_DIR/run_demo.sh"
}

echo "[$(date -Is)] tracker_job_start model=$MODEL job=${SLURM_JOB_NAME:-unknown} id=${SLURM_JOB_ID:-unknown} node=${SLURMD_NODENAME:-unknown}"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"
echo "MODEL_ROOT=$MODEL_ROOT"
echo "TRACKER_DIR=$TRACKER_DIR"

prepare_tracker_dir
DEVICE=cuda:0 "$HERE/run_tracker_full.sh" "$TRACKER_DIR"

echo "[$(date -Is)] tracker_job_done model=$MODEL job=${SLURM_JOB_NAME:-unknown} id=${SLURM_JOB_ID:-unknown}"
