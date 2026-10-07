#!/usr/bin/env bash
set -euo pipefail

package="$1"
out="$2"
shift 2

root="/scratch3/che489/FC-W4/Tracing-Reproduction/W3"
log="$root/archive_logs/${package}_rq2tracker_zip_20261001.log"
progress="$root/archive_logs/${package}_rq2tracker_zip_20261001.progress"
tmpdir="$root/archive_logs/tmp_${package}"

cd "$root"
: > "$log"
mkdir -p "$tmpdir"
printf "state=STARTING\npackage=%s\nout=%s\nstart_time=%s\n" "$package" "$out" "$(date)" > "$progress"
echo "[START] $(date) $package" >> "$log"

for src in "$@"; do
  if [ ! -d "$src" ]; then
    echo "[SKIP] missing source: $src" >> "$log"
    printf "state=SKIP\nreason=missing_source\nmissing=%s\n" "$src" >> "$progress"
    exit 0
  fi
done

printf "state=COUNTING\n" >> "$progress"
total_entries=0
source_bytes=0
for src in "$@"; do
  entries=$(find "$src" -print 2>/dev/null | wc -l)
  bytes=$(du -sb "$src" 2>/dev/null | awk '{print $1}')
  total_entries=$((total_entries + entries))
  source_bytes=$((source_bytes + bytes))
done
printf "state=ZIPPING\ntotal_entries=%s\nsource_bytes=%s\n" "$total_entries" "$source_bytes" >> "$progress"

find . -maxdepth 1 -type f -name "$out" -print -delete >> "$log" 2>&1
zip -b "$tmpdir" -r -1 "$out" "$@" >> "$log" 2>&1
printf "state=TESTING\n" >> "$progress"
zip -T "$out" >> "$log" 2>&1

printf "state=DELETING\n" >> "$progress"
for src in "$@"; do
  find "$src" -depth -type f -delete
  find "$src" -depth -type l -delete
  find "$src" -depth -type d -empty -delete
done

echo "[DONE] $(date) $package" >> "$log"
printf "state=DONE\nend_time=%s\n" "$(date)" >> "$progress"
