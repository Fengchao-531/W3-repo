#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

count_files() {
  local root="$1"
  local pattern="$2"
  [[ -d "$root" ]] || { echo 0; return; }
  find "$root" -name "$pattern" 2>/dev/null | wc -l
}

printf '%-9s %9s %13s %12s %12s\n' model A0/180 A1A2/360 A0_csv combined_csv
for model in DeepSeek Gemma Llama3.1 Mistral Qwen; do
  base="$HERE/$model"
  a0="$(count_files "$base/Exp4_General_Preference_Control/04_runs/A0" 13_trace_summary.json)"
  a1a2="$(count_files "$base/Exp4_General_Preference_Control/03_reference_A1_A2/03_runs" 16_trace_summary.json)"
  a0_csv="-"
  combined_csv="-"
  [[ -f "$base/Exp4_General_Preference_Control/05_processed/00_A0_run_level_results.csv" ]] && a0_csv="yes"
  [[ -f "$base/Exp4_General_Preference_Control/05_processed/02_A0_A1_A2_combined_run_level.csv" ]] && combined_csv="yes"
  printf '%-9s %4s/180 %8s/360 %12s %12s\n' "$model" "$a0" "$a1a2" "$a0_csv" "$combined_csv"
done

echo
squeue -u "$USER" -o '%.18i %.20j %.8T %.10M %.9P %.30R' | rg 'Exp4A0|Exp4A12|JOBID' || true
