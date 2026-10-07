#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLURM_ACCOUNT="${SLURM_ACCOUNT:-OD-237777}"
mkdir -p "$HERE/logs/exp4_a0_slurm"

for group in 1 2 3; do
  job_name="Exp4A0-$group"
  echo "submit $job_name"
  sbatch --parsable -A "$SLURM_ACCOUNT" --job-name="$job_name" "$HERE/exp4_a0_group_job.sbatch" "$group"
done
