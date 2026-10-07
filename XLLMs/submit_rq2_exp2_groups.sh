#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLURM_ACCOUNT="${SLURM_ACCOUNT:-OD-237777}"
mkdir -p "$HERE/logs/rq2_exp2_slurm"

for group in 1 2 3; do
  job_name="RQ2Exp2-$group"
  echo "submit $job_name"
  sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="$job_name" "$HERE/rq2_exp2_group_job.sbatch" "$group"
done
