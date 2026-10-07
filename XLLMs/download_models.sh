#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/model_paths.sh"
PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"

MODELS=("$@")
if [[ ${#MODELS[@]} -eq 0 || "${MODELS[0]}" == all ]]; then
  MODELS=(qwen olmo gemma)
fi

for model in "${MODELS[@]}"; do
  case "${model,,}" in
    qwen) repo="Qwen/Qwen2.5-7B-Instruct"; target="$QWEN_MODEL_PATH" ;;
    olmo) repo="allenai/OLMo-2-1124-7B-Instruct"; target="$OLMO_MODEL_PATH" ;;
    gemma) repo="google/gemma-2-9b-it"; target="$GEMMA_MODEL_PATH" ;;
    *) echo "Unknown model: $model (choose qwen, olmo, gemma, or all)" >&2; exit 2 ;;
  esac
  echo "===== Downloading $repo -> $target ====="
  "$PYTHON_BIN" - "$repo" "$target" <<'PY'
import sys
from huggingface_hub import snapshot_download

repo, target = sys.argv[1:]
print(snapshot_download(repo, local_dir=target))
PY
done
