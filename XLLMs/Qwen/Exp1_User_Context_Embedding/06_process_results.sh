#!/usr/bin/env bash
set -euo pipefail
EXP_DIR="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/Exp1_User_Context_Embedding"
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
cd "$EXP_DIR"
"$PY" exp1_pipeline.py process_results
