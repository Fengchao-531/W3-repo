#!/usr/bin/env bash
set -euo pipefail
cd /scratch3/che489/FC-W4/Tracing-Reproduction/W3/Exp1_User_Context_Embedding
./06_process_results.sh
./07_run_statistics.sh
./08_generate_figures.sh
./09_manual_inspection.sh
