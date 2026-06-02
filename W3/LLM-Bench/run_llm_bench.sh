#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Python not found: ${PYTHON_BIN}" >&2
  exit 1
fi

RUNTIME="$(${PYTHON_BIN} "${ROOT}/run_llm_bench.py" --print-runtime | tr -d '\r\n')"
echo "[llm-bench] runtime=${RUNTIME}"
echo "[llm-bench] result_dir=${ROOT}/result/${RUNTIME}"
echo "[llm-bench] summary_file=${ROOT}/result/${RUNTIME}/summary.json"

exec "${PYTHON_BIN}" "${ROOT}/run_llm_bench.py" "$@"
