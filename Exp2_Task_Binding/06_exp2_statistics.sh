#!/usr/bin/env bash
set -euo pipefail
EXP2_DIR="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/Exp2_Task_Binding"
EXP1_ROOT="${EXP1_ROOT:-/scratch3/che489/FC-W4/Tracing-Reproduction/W3/Exp1_User_Context_Embedding}"
REPO="/scratch3/che489/FC-W4/Tracing-Reproduction/2-AgentDojo/agentdojo"
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
export EXP1_ROOT
export PYTHONPATH="$EXP1_ROOT:$REPO/src:${PYTHONPATH:-}"
cd "$EXP2_DIR"
"$PY" exp2_pipeline.py statistics
