#!/usr/bin/env bash
set -euo pipefail
EXP_DIR="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/Exp1_User_Context_Embedding"
REPO="/scratch3/che489/FC-W4/Tracing-Reproduction/2-AgentDojo/agentdojo"
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
export PYTHONPATH="$REPO/src:${PYTHONPATH:-}"
cd "$EXP_DIR"
"$PY" exp1_pipeline.py build_dataset
