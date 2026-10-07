#!/usr/bin/env bash
set -euo pipefail
EXP_DIR="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/RQ3/RQ3-AControlledVerification"
EXP1_ROOT="${EXP1_ROOT:-/scratch3/che489/FC-W4/Tracing-Reproduction/W3/Exp1_User_Context_Embedding}"
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
export EXP1_ROOT
export PYTHONPATH="$EXP1_ROOT:${PYTHONPATH:-}"
cd "$EXP_DIR"
"$PY" rq3_controlled_verification.py build_dataset
