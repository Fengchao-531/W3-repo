#!/usr/bin/env bash
set -euo pipefail
./01_build_exp2_manifest.sh
./02_validate_exp2_manifest.sh
./03_make_run_queue.sh
./04_run_exp2.sh
./05_extract_results.sh
./06_exp2_statistics.sh
./07_generate_figures.sh
