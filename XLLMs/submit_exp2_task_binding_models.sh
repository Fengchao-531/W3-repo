#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLURM_ACCOUNT="${SLURM_ACCOUNT:-OD-237777}"
mkdir -p "$HERE/logs/exp2_task_binding_slurm"

MODELS=("$@")
if [[ ${#MODELS[@]} -eq 0 ]]; then
  MODELS=(llama mistral deepseek qwen gemma)
fi

for model in "${MODELS[@]}"; do
  job_name="Exp2TB-${model}"
  echo "submit $job_name"
  sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="$job_name" "$HERE/exp2_task_binding_model_job.sbatch" "$model"
done
