#!/usr/bin/env bash
set -euo pipefail
ROOT="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/AblationStudy/Domains"
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
REPO="${AGENTDOJO_REPO:-/scratch3/che489/FC-W4/Tracing-Reproduction/2-AgentDojo/agentdojo}"
EXP1_ROOT="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/Exp1_User_Context_Embedding"
export PYTHONPATH="$ROOT:$EXP1_ROOT:$REPO/src:${PYTHONPATH:-}"
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy || true
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "ERROR: OPENAI_API_KEY is not set." >&2
    exit 1
fi
cd "$ROOT"
"$PY" domain_ablation_pipeline.py run_exp1 "$@"
