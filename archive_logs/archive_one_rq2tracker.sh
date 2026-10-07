#!/usr/bin/env bash
set -euo pipefail
model="$1"
src="$2"
out="$3"
root="/scratch3/che489/FC-W4/Tracing-Reproduction/W3"
log="$root/archive_logs/${model}_rq2tracker_zip_20261001.log"
cd "$root"
echo "[START] $(date) $model" >> "$log"
if [ ! -d "$src" ]; then
  echo "[SKIP] missing source $src" >> "$log"
  exit 0
fi
find . -maxdepth 1 -type f -name "$out" -print -delete >> "$log" 2>&1
zip -r -1 -q "$out" "$src"
zip -T "$out" >> "$log" 2>&1
find "$src" -depth -type f -delete
find "$src" -depth -type l -delete
find "$src" -depth -type d -empty -delete
echo "[DONE] $(date) $model" >> "$log"
