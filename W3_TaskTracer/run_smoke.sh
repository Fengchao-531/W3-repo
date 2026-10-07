#!/usr/bin/env bash
set -euo pipefail

TASKTRACER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"
SMOKE_LIMIT="${SMOKE_LIMIT:-3}"

mkdir -p "$TASKTRACER_DIR/06_logs"

"$PYTHON_BIN" "$TASKTRACER_DIR/smoke_tasktracer_inputs.py" \
  --output-dir "$TASKTRACER_DIR" \
  --limit "$SMOKE_LIMIT" \
  2>&1 | tee "$TASKTRACER_DIR/06_logs/smoke.log"
