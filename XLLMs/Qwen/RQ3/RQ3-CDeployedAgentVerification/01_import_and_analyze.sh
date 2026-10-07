#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
if [[ ! -x "$PY" ]]; then
  PY="${PYTHON:-python3}"
fi

"$PY" rq3c_deployed_agent_verification.py
