#!/usr/bin/env bash
set -euo pipefail
./05_process_results.sh
./06_statistics.sh
./07_make_figures.sh
