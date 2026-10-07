#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/model_paths.sh"
PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"
: "${QWEN_MODEL_PATH:?Set QWEN_MODEL_PATH to a local Qwen Instruct snapshot}"
MODE="${1:-all}"; shift || true
case "$MODE" in all) STAGES=(exp1_core rq2_exp3);; exp1|exp1_core) STAGES=(exp1_core);; exp2) STAGES=(exp2);; exp3|rq2_exp3) STAGES=(rq2_exp3);; rq2_exp2) STAGES=(rq2_exp2);; exp4|exp4_a0) STAGES=(exp4_a0);; exp4b_e0) STAGES=(exp4b_e0);; exp4_a1a2) STAGES=(exp4_a1a2);; *) echo "Usage: $0 [all|exp1|exp2|exp3|rq2_exp2|exp4|exp4_a0|exp4b_e0|exp4_a1a2] [extra arguments]" >&2; exit 2;; esac
export PYTHONUNBUFFERED=1
"$PYTHON_BIN" "$HERE/rerun_qwen_w3.py" --output-root "$HERE/Qwen" --device "${DEVICE:-auto}" --dtype bfloat16 --stages "${STAGES[@]}" "$@"
"$PYTHON_BIN" "$HERE/build_tracker_manifest.py" --root "$HERE/Qwen" --model qwen_instruct
