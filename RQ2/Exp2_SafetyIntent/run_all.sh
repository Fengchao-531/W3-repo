#!/usr/bin/env bash
set -euo pipefail
./01_build_dataset.sh
./02_validate_dataset.sh
./03_make_run_queue.sh
./04_run_exp2.sh "$@"
./05_process_results.sh
./06_statistics.sh
./07_make_figures.sh
