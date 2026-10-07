#!/usr/bin/env bash
#SBATCH --partition=h2gpu
#SBATCH --account=OD-237777
#SBATCH --time=02:00:00
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --requeue
#SBATCH --output=/scratch3/che489/FC-W4/Tracing-Reproduction/W3/XLLMs/logs/exp4_a0_slurm/%x-%j.out
#SBATCH --error=/scratch3/che489/FC-W4/Tracing-Reproduction/W3/XLLMs/logs/exp4_a0_slurm/%x-%j.err

set -euo pipefail

HERE="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/XLLMs"
MODEL="${1:?Usage: sbatch exp4_a0_model_job.sbatch <model>}"

mkdir -p "$HERE/logs/exp4_a0_slurm"
cd "$HERE"

if [[ -f /scratch3/che489/anaconda3_new/etc/profile.d/conda.sh ]]; then
  source /scratch3/che489/anaconda3_new/etc/profile.d/conda.sh
  conda activate W4 || true
fi

export PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"
export PYTHONUNBUFFERED=1

echo "[$(date -Is)] job_start name=${SLURM_JOB_NAME:-unknown} id=${SLURM_JOB_ID:-unknown} model=$MODEL node=${SLURMD_NODENAME:-unknown}"
echo "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-unset}"

DEVICE=cuda:0 "$HERE/run_all_models.sh" exp4_a0 "$MODEL" -- --no-hidden-states

echo "[$(date -Is)] job_done name=${SLURM_JOB_NAME:-unknown} id=${SLURM_JOB_ID:-unknown} model=$MODEL"
