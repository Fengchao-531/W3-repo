#!/usr/bin/env bash
set -euo pipefail
EXP_DIR="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/RQ2/Exp2_SafetyIntent"
EXP1_ROOT="${EXP1_ROOT:-/scratch3/che489/FC-W4/Tracing-Reproduction/W3/Exp1_User_Context_Embedding}"
REPO="/scratch3/che489/FC-W4/Tracing-Reproduction/2-AgentDojo/agentdojo"
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
export EXP1_ROOT
export PYTHONPATH="$EXP1_ROOT:$REPO/src:${PYTHONPATH:-}"
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy || true
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "ERROR: OPENAI_API_KEY is not set for AgentDojo/OpenAI model calls." >&2
    exit 1
fi
cd "$EXP_DIR"
"$PY" rq2_exp2_pipeline.py run "$@"
