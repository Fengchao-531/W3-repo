#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"
DEVICE="${DEVICE:-auto}"
DTYPE="${DTYPE:-bfloat16}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-512}"
MODE="${1:-all}"

case "$MODE" in
  all) STAGES=(exp1_core rq2_exp3) ;;
  exp1|exp1_core) STAGES=(exp1_core) ;;
  exp2) STAGES=(exp2) ;;
  exp3|rq2_exp3) STAGES=(rq2_exp3) ;;
  rq2_exp2) STAGES=(rq2_exp2) ;;
  exp4|exp4_a0) STAGES=(exp4_a0) ;;
  exp4b_e0) STAGES=(exp4b_e0) ;;
  exp4_a1a2) STAGES=(exp4_a1a2) ;;
  *)
    echo "Usage: $0 [all|exp1|exp1_core|exp2|exp3|rq2_exp3|rq2_exp2|exp4|exp4_a0|exp4b_e0|exp4_a1a2] [extra launcher arguments...]" >&2
    exit 2
    ;;
esac
shift || true

export PYTHONUNBUFFERED=1
"$PYTHON_BIN" "$SCRIPT_DIR/rerun_llama31_w3.py" \
  --output-root "$SCRIPT_DIR/Llama3.1" \
  --device "$DEVICE" \
  --dtype "$DTYPE" \
  --max-new-tokens "$MAX_NEW_TOKENS" \
  --stages "${STAGES[@]}" \
  "$@"

"$PYTHON_BIN" "$SCRIPT_DIR/build_tracker_manifest.py" \
  --root "$SCRIPT_DIR/Llama3.1"
