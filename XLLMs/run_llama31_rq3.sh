#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"
DEVICE="${DEVICE:-auto}"
DTYPE="${DTYPE:-bfloat16}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-512}"

export PYTHONUNBUFFERED=1
"$PYTHON_BIN" "$SCRIPT_DIR/run_llama31_rq3.py" \
  --output-root "$SCRIPT_DIR/Llama3.1" \
  --device "$DEVICE" \
  --dtype "$DTYPE" \
  --max-new-tokens "$MAX_NEW_TOKENS" \
  "$@"

"$PYTHON_BIN" "$SCRIPT_DIR/build_tracker_manifest.py" \
  --root "$SCRIPT_DIR/Llama3.1"
