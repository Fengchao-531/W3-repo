#!/usr/bin/env bash
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/model_paths.sh"
MODE="${1:-all}"
if [[ $# -gt 0 ]]; then shift; fi
case "$MODE" in
  all|exp1|exp1_core|exp2|exp3|rq2_exp3|rq2_exp2|exp4|exp4_a0|exp4b_e0|exp4_a1a2) ;;
  *) echo "Usage: $0 [all|exp1|exp2|exp3|rq2_exp2|exp4|exp4_a0|exp4b_e0|exp4_a1a2] [model ...] [-- extra arguments]" >&2; exit 2 ;;
esac

MODELS=()
EXTRA_ARGS=()
after_separator=0
for arg in "$@"; do
  if [[ "$arg" == "--" && $after_separator -eq 0 ]]; then
    after_separator=1
  elif [[ $after_separator -eq 1 ]]; then
    EXTRA_ARGS+=("$arg")
  else
    MODELS+=("${arg,,}")
  fi
done
if [[ ${#MODELS[@]} -eq 0 ]]; then
  MODELS=(llama mistral deepseek qwen gemma olmo)
  explicit_models=0
else
  explicit_models=1
fi

script_for_model() {
  case "$1" in
    llama|llama3|llama3.1) echo "$HERE/run_llama31_experiments.sh" ;;
    mistral|ministral) echo "$HERE/run_mistral_experiments.sh" ;;
    deepseek) echo "$HERE/run_deepseek_experiments.sh" ;;
    qwen) echo "$HERE/run_qwen_experiments.sh" ;;
    gemma) echo "$HERE/run_gemma_experiments.sh" ;;
    olmo) echo "$HERE/run_olmo_experiments.sh" ;;
    *) return 1 ;;
  esac
}

missing_path_var() {
  case "$1" in
    qwen) [[ -z "${QWEN_MODEL_PATH:-}" ]] && echo QWEN_MODEL_PATH ;;
    gemma) [[ -z "${GEMMA_MODEL_PATH:-}" ]] && echo GEMMA_MODEL_PATH ;;
    olmo) [[ -z "${OLMO_MODEL_PATH:-}" ]] && echo OLMO_MODEL_PATH ;;
  esac
}

path_value_for_model() {
  case "$1" in
    qwen) echo "${QWEN_MODEL_PATH:-}" ;;
    gemma) echo "${GEMMA_MODEL_PATH:-}" ;;
    olmo) echo "${OLMO_MODEL_PATH:-}" ;;
  esac
}

valid_model_snapshot() {
  local path="$1"
  [[ -f "$path/config.json" ]] || return 1
  compgen -G "$path/*.safetensors" >/dev/null || \
    compgen -G "$path/*.bin" >/dev/null || \
    [[ -f "$path/model.safetensors.index.json" ]] || \
    [[ -f "$path/pytorch_model.bin.index.json" ]]
}

failures=()
ran=0
for model in "${MODELS[@]}"; do
  if ! script="$(script_for_model "$model")"; then
    echo "Unknown model: $model" >&2
    failures+=("$model:unknown")
    continue
  fi
  required="$(missing_path_var "$model")"
  if [[ -n "$required" ]]; then
    if [[ $explicit_models -eq 1 || "${STRICT_MODELS:-0}" == 1 ]]; then
      echo "ERROR [$model] $required is not set." >&2
      failures+=("$model:missing-$required")
    else
      echo "SKIP  [$model] set $required to include this model."
    fi
    continue
  fi
  configured_path="$(path_value_for_model "$model")"
  if [[ -n "$configured_path" ]] && ! valid_model_snapshot "$configured_path"; then
    echo "ERROR [$model] model snapshot is missing or incomplete: $configured_path" >&2
    echo "      Resume it with: bash $HERE/download_models.sh $model" >&2
    failures+=("$model:invalid-model-path")
    continue
  fi

  echo
  echo "===== $model :: $MODE ====="
  if bash "$script" "$MODE" "${EXTRA_ARGS[@]}"; then
    echo "DONE  [$model]"
    ran=$((ran + 1))
  else
    status=$?
    echo "FAIL  [$model] exit=$status" >&2
    failures+=("$model:$status")
  fi
done

echo
echo "Completed models: $ran"
if [[ ${#failures[@]} -gt 0 ]]; then
  printf 'Failures: %s\n' "${failures[*]}" >&2
  exit 1
fi
