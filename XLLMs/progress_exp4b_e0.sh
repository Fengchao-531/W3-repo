#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

count_files() {
  local root="$1"
  local pattern="$2"
  [[ -d "$root" ]] || { echo 0; return; }
  find "$root" -name "$pattern" 2>/dev/null | wc -l
}

printf '%-9s %9s %10s %12s\n' model E0/180 E0_csv paired_csv
for model in DeepSeek Gemma Llama3.1 Mistral Qwen; do
  base="$HERE/$model/Exp4b_Preference_Controlled_External_Baseline"
  runs=$(count_files "$base/03_runs/E0" "13_trace_summary.json")
  e0_csv=no
  paired_csv=no
  [[ -s "$base/04_processed/00_E0_run_level_results.csv" ]] && e0_csv=yes
  [[ -s "$base/05_statistics/01_paired_E0_vs_A0.csv" ]] && paired_csv=yes
  printf '%-9s %3s/180 %10s %12s\n' "$model" "$runs" "$e0_csv" "$paired_csv"
done

echo
squeue -u "$USER" -o "%.18i %.20j %.8T %.10M %.9P %.30R" | grep -E 'JOBID|Exp4bE0|interact' || true
