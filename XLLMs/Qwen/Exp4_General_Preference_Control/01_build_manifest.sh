#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
cd "$HERE"
"$PY" exp4_pipeline.py build_manifest

