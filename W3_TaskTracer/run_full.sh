#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"
LIMIT="${LIMIT:-}"

mkdir -p "$HERE/06_logs"
limit_args=()
if [[ -n "$LIMIT" ]]; then
  limit_args=(--limit "$LIMIT")
fi

"$PYTHON_BIN" "$HERE/extract_gpt4o_behavior.py" "${limit_args[@]}" \
  2>&1 | tee "$HERE/06_logs/behavioral_trace.log"
