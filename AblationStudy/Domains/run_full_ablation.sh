#!/usr/bin/env bash
set -euo pipefail
./07_build_all.sh
./10_run_exp1.sh "$@"
./11_run_exp2_safety.sh "$@"
./12_extract_results.sh
./13_statistics_results.sh
./14_make_result_figures.sh
