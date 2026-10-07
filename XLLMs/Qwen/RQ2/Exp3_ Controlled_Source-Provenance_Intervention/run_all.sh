#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
./01_build_dataset.sh
./02_validate_dataset.sh
./03_make_run_queue.sh
./04_run_exp3.sh
./run_analysis.sh
