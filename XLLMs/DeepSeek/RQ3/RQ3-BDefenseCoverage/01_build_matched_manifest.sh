#!/usr/bin/env bash
set -euo pipefail
EXP_DIR="/scratch3/che489/FC-W4/Tracing-Reproduction/W3/RQ3/RQ3-BDefenseCoverage"
EXP1_ROOT="${EXP1_ROOT:-/scratch3/che489/FC-W4/Tracing-Reproduction/W3/Exp1_User_Context_Embedding}"
W3_BACKUP_ROOT="${W3_BACKUP_ROOT:-/scratch3/che489/W3-Backup/W3-repo}"
PY="${PY:-/scratch3/che489/.conda/envs/W4/bin/python}"
export EXP1_ROOT W3_BACKUP_ROOT
cd "$EXP_DIR"
"$PY" rq3b_defense_coverage.py
