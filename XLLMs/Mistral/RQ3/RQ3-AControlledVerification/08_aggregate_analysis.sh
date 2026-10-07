#!/usr/bin/env bash
set -euo pipefail
EXP_DIR="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/RQ3/RQ3-AControlledVerification"
EXP1_ROOT="${EXP1_ROOT:-/scratch3/che489/FC-W4/Tracing-Reproduction/W3/Exp1_User_Context_Embedding}"
RQ2_EXP2_ROOT="${RQ2_EXP2_ROOT:-/scratch3/che489/FC-W4/Tracing-Reproduction/W3/RQ2/Exp2_SafetyIntent}"
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
export EXP1_ROOT RQ2_EXP2_ROOT
cd "$EXP_DIR"
"$PY" rq3a_aggregate_analysis.py
