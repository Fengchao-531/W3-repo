#!/usr/bin/env bash
# Shared local checkpoints for the W3 multi-model experiments.
W3_MODEL_DIR="${W3_MODEL_DIR:-/scratch3/che489/hf_home/models/w3_models}"

set_default_model_path() {
  local variable="$1"
  local default_path="$2"
  local current="${!variable:-}"
  if [[ -z "$current" || "$current" == /path/to/* ]]; then
    printf -v "$variable" '%s' "$default_path"
    export "$variable"
  fi
}

set_default_model_path QWEN_MODEL_PATH "$W3_MODEL_DIR/Qwen2.5-7B-Instruct"
set_default_model_path GEMMA_MODEL_PATH "$W3_MODEL_DIR/gemma-2-9b-it"
set_default_model_path OLMO_MODEL_PATH "$W3_MODEL_DIR/OLMo-2-1124-7B-Instruct"
unset -f set_default_model_path
