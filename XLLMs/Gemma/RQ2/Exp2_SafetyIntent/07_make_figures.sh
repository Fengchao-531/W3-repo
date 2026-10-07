#!/usr/bin/env bash
set -euo pipefail
EXP_DIR="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/RQ2/Exp2_SafetyIntent"
EXP1_ROOT="${EXP1_ROOT:-/scratch3/che489/FC-W4/Tracing-Reproduction/W3/Exp1_User_Context_Embedding}"
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
export EXP1_ROOT
export PYTHONPATH="$EXP1_ROOT:${PYTHONPATH:-}"
cd "$EXP_DIR"
"$PY" rq2_exp2_pipeline.py figures
