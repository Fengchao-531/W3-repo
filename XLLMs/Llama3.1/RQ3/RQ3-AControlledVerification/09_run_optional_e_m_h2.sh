#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export RQ3_INCLUDE_E_M_H2=1
./01_build_dataset.sh
./02_validate_dataset.sh
./03_make_run_queue.sh
./04_run_rq3.sh --condition E_M_H2 "$@"
./05_process_results.sh
./06_statistics.sh
./08_aggregate_analysis.sh
