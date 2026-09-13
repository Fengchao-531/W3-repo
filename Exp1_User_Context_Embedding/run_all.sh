#!/usr/bin/env bash
set -euo pipefail
./01_build_dataset.sh
./02_validate_dataset.sh
./03_run_clean.sh
./04_run_external.sh
./05_run_user_context.sh
./05B_run_user_context_benign.sh
./06_process_results.sh
./07_run_statistics.sh
./08_generate_figures.sh
./09_manual_inspection.sh
