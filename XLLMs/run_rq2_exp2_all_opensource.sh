#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/model_paths.sh"

PYTHON_BIN="${PYTHON_BIN:-/scratch3/che489/.conda/envs/W4/bin/python}"
DEVICE="${DEVICE:-auto}"
DTYPE="${DTYPE:-bfloat16}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-512}"
export PYTHONUNBUFFERED=1

run_python() {
  env \
    -u SLURM_HOME \
    -u SLURM_CONF \
    -u SLURM_STEP_ID \
    -u SLURM_STEPID \
    -u SLURM_STEP_NODELIST \
    -u SLURM_NTASKS \
    -u SLURM_NPROCS \
    -u SLURM_PROCID \
    -u SLURM_LOCALID \
    -u SLURM_TASK_PID \
    -u PMI_FD \
    -u PMI_RANK \
    -u PMI_SIZE \
    -u PMIX_RANK \
    -u PMIX_NAMESPACE \
    "$PYTHON_BIN" "$@"
}

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
fi

model_root() {
  case "$1" in
    llama|llama3|llama3.1) echo "$HERE/Llama3.1" ;;
    mistral|ministral) echo "$HERE/Mistral" ;;
    deepseek) echo "$HERE/DeepSeek" ;;
    qwen) echo "$HERE/Qwen" ;;
    gemma) echo "$HERE/Gemma" ;;
    olmo) echo "$HERE/OLMo" ;;
    *) return 1 ;;
  esac
}

runner_for_model() {
  case "$1" in
    llama|llama3|llama3.1) echo "$HERE/rerun_llama31_w3.py" ;;
    mistral|ministral) echo "$HERE/rerun_mistral_w3.py" ;;
    deepseek) echo "$HERE/rerun_deepseek_w3.py" ;;
    qwen) echo "$HERE/rerun_qwen_w3.py" ;;
    gemma) echo "$HERE/rerun_gemma_w3.py" ;;
    olmo) echo "$HERE/rerun_olmo_w3.py" ;;
    *) return 1 ;;
  esac
}

tracker_model_name() {
  case "$1" in
    llama|llama3|llama3.1) echo "" ;;
    mistral|ministral) echo "ministral_8b_instruct_2410" ;;
    deepseek) echo "deepseek_r1_distill_qwen_7b" ;;
    qwen) echo "qwen_instruct" ;;
    gemma) echo "gemma_instruct" ;;
    olmo) echo "olmo_instruct" ;;
    *) return 1 ;;
  esac
}

require_model_path() {
  case "$1" in
    qwen) : "${QWEN_MODEL_PATH:?Set QWEN_MODEL_PATH or keep model_paths.sh defaults valid.}" ;;
    gemma) : "${GEMMA_MODEL_PATH:?Set GEMMA_MODEL_PATH or keep model_paths.sh defaults valid.}" ;;
    olmo) : "${OLMO_MODEL_PATH:?Set OLMO_MODEL_PATH or keep model_paths.sh defaults valid.}" ;;
  esac
}

valid_exp1_ucm_count() {
  local root="$1"
  local csv="$root/Exp1_User_Context_Embedding/12_Processed_Data/01_run_level.csv"
  [[ -f "$csv" ]] || { echo 0; return; }
  run_python - "$csv" <<'PY'
import csv
import sys
path = sys.argv[1]
with open(path, encoding="utf-8", newline="") as handle:
    rows = list(csv.DictReader(handle))
print(sum(1 for row in rows if row.get("condition") == "UC_M"))
PY
}

completed_rq2_exp2_count() {
  local root="$1"
  if [[ ! -d "$root/RQ2/Exp2_SafetyIntent/02_runs" ]]; then
    echo 0
    return
  fi
  find "$root/RQ2/Exp2_SafetyIntent/02_runs" -name 15_trace_summary.json 2>/dev/null | wc -l
}

failures=()
for model in "${MODELS[@]}"; do
  if ! root="$(model_root "$model")"; then
    echo "Unknown model: $model" >&2
    failures+=("$model:unknown")
    continue
  fi
  runner="$(runner_for_model "$model")"
  require_model_path "$model"

  exp1_ucm="$(valid_exp1_ucm_count "$root")"
  if [[ "$exp1_ucm" -lt 180 ]]; then
    echo "FAIL [$model] Exp1 UC_M has $exp1_ucm/180 rows. Run/fix Exp1 before RQ2 Exp2." >&2
    failures+=("$model:missing-exp1-ucm")
    continue
  fi

  before="$(completed_rq2_exp2_count "$root")"
  echo
  echo "===== $model :: RQ2 Exp2 SafetyIntent ====="
  echo "Existing completed summaries: $before/360"

  if run_python "$runner" \
      --output-root "$root" \
      --device "$DEVICE" \
      --dtype "$DTYPE" \
      --max-new-tokens "$MAX_NEW_TOKENS" \
      --stages rq2_exp2 \
      "${EXTRA_ARGS[@]}"; then
    after="$(completed_rq2_exp2_count "$root")"
    echo "DONE [$model] completed summaries: $after/360"
    tracker_model="$(tracker_model_name "$model")"
    if [[ -n "$tracker_model" ]]; then
      run_python "$HERE/build_tracker_manifest.py" --root "$root" --model "$tracker_model"
    else
      run_python "$HERE/build_tracker_manifest.py" --root "$root"
    fi
  else
    status=$?
    echo "FAIL [$model] exit=$status" >&2
    failures+=("$model:$status")
  fi
done

if [[ ${#failures[@]} -gt 0 ]]; then
  printf 'Failures: %s\n' "${failures[*]}" >&2
  exit 1
fi
