#!/usr/bin/env bash
set -euo pipefail
ROOT="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/AblationStudy/Domains"
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
REPO="${AGENTDOJO_REPO:-/scratch3/che489/FC-W4/Tracing-Reproduction/2-AgentDojo/agentdojo}"
EXP1_ROOT="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/Exp1_User_Context_Embedding"
export PYTHONPATH="$ROOT:$EXP1_ROOT:$REPO/src:${PYTHONPATH:-}"
cd "$ROOT"
"$PY" domain_ablation_pipeline.py statistics
