#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
"$PY" rq2_exp3_pipeline.py validate
