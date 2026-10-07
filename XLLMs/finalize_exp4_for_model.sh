#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL="${1:?Usage: $0 <llama|mistral|deepseek|qwen|gemma>}"
PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"

case "${MODEL,,}" in
  llama|llama3|llama3.1) ROOT="$HERE/Llama3.1/Exp4_General_Preference_Control" ;;
  mistral|ministral) ROOT="$HERE/Mistral/Exp4_General_Preference_Control" ;;
  deepseek) ROOT="$HERE/DeepSeek/Exp4_General_Preference_Control" ;;
  qwen) ROOT="$HERE/Qwen/Exp4_General_Preference_Control" ;;
  gemma) ROOT="$HERE/Gemma/Exp4_General_Preference_Control" ;;
  *) echo "Unknown model: $MODEL" >&2; exit 2 ;;
esac

"$PYTHON_BIN" - "$ROOT" <<'PY'
import importlib.util
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("exp4_pipeline_finalize", root / "exp4_pipeline.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
module.process_results()
module.statistics()
module.figures()
print(f"finalized {root}")
PY
