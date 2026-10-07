#!/usr/bin/env bash
set -euo pipefail

root="/scratch3/che489/FC-W4/Tracing-Reproduction/W3"
cd "$root"

printf "== running jobs ==\n"
pgrep -af 'archive_rq2tracker_package|[z]ip -b .+ -r -1 XLLMs_RQ2Tracker|[z]ip -T XLLMs_RQ2Tracker' || true
printf "\n"

printf "== progress by archived entries ==\n"
printf "%-16s %-10s %-18s %-8s %-12s %-12s %-s\n" \
  "package" "state" "entries" "pct" "source" "zip/temp" "last_log"

show_pkg() {
  local pkg="$1"
  local zip_name="$2"
  local log="archive_logs/${pkg}_rq2tracker_zip_20261001.log"
  local progress="archive_logs/${pkg}_rq2tracker_zip_20261001.progress"
  local tmpdir="archive_logs/tmp_${pkg}"

  local state="not-started"
  local total_entries=0
  local source_bytes=0
  if [ -f "$progress" ]; then
    state=$(awk -F= '/^state=/{s=$2} END{print s}' "$progress")
    total_entries=$(awk -F= '/^total_entries=/{v=$2} END{print v+0}' "$progress")
    source_bytes=$(awk -F= '/^source_bytes=/{v=$2} END{print v+0}' "$progress")
  fi

  local done_entries=0
  if [ -f "$log" ]; then
    done_entries=$(rg -c '^[[:space:]]*adding:' "$log" 2>/dev/null || true)
    done_entries=${done_entries:-0}
  fi

  local pct="n/a"
  if [ "$total_entries" -gt 0 ]; then
    pct=$(awk -v a="$done_entries" -v b="$total_entries" 'BEGIN{printf "%.1f%%", (100*a/b)}')
  fi

  local zip_bytes=0
  if [ -f "$zip_name" ]; then
    zip_bytes=$(stat -c '%s' "$zip_name")
  elif [ -d "$tmpdir" ]; then
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      b=$(stat -c '%s' "$f" 2>/dev/null || echo 0)
      zip_bytes=$((zip_bytes + b))
    done < <(find "$tmpdir" -maxdepth 1 -type f -name 'zi*' -print 2>/dev/null)
  fi

  local source_h zip_h
  source_h=$(numfmt --to=iec --suffix=B "$source_bytes" 2>/dev/null || echo "${source_bytes}B")
  zip_h=$(numfmt --to=iec --suffix=B "$zip_bytes" 2>/dev/null || echo "${zip_bytes}B")

  local last_log=""
  if [ -f "$log" ]; then
    last_log=$(tail -1 "$log" | tr -d '\r')
  fi

  printf "%-16s %-10s %-18s %-8s %-12s %-12s %-s\n" \
    "$pkg" "$state" "${done_entries}/${total_entries}" "$pct" "$source_h" "$zip_h" "$last_log"
}

show_pkg "DeepSeek_Gemma" "XLLMs_RQ2Tracker_DeepSeek_Gemma_20261001.zip"
show_pkg "Llama3.1" "XLLMs_RQ2Tracker_Llama3.1_20261001.zip"
show_pkg "Mistral" "XLLMs_RQ2Tracker_Mistral_20261001.zip"
show_pkg "Qwen" "XLLMs_RQ2Tracker_Qwen_20261001.zip"

printf "\n== zip files ==\n"
ls -lh XLLMs_RQ2Tracker_*_20261001.zip 2>/dev/null || true

printf "\n== active temp files ==\n"
find archive_logs -maxdepth 2 -type f -path '*/tmp_*/*' -name 'zi*' -exec ls -lh {} + 2>/dev/null || true

printf "\n== source dirs ==\n"
for d in \
  XLLMs/DeepSeek/RQ2Tracker \
  XLLMs/Gemma/RQ2Tracker \
  XLLMs/Llama3.1/RQ2Tracker \
  XLLMs/Mistral/RQ2Tracker \
  XLLMs/Qwen/RQ2Tracker
do
  if [ -e "$d" ]; then
    printf "exists\t%s\n" "$d"
  else
    printf "deleted\t%s\n" "$d"
  fi
done
