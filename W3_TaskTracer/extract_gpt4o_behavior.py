#!/usr/bin/env python3
"""Extract GPT-4o behavior using RQ2Tracker's canonical RQ2 schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


HERE = Path(__file__).resolve().parent
W3 = HERE.parent
RQ2_TRACKER = W3 / "RQ2Tracker"
sys.path.insert(0, str(RQ2_TRACKER))

from behavioral_trace import (  # noqa: E402
    BEHAVIORAL_FIELDS,
    SCHEMA_VERSION,
    extract_behavior,
    read_jsonl,
    summarize,
    write_csv,
    write_schema,
)

EXP1 = W3 / "Exp1_User_Context_Embedding"
MODEL = "gpt-4o-2024-05-13"


def artifact_catalog() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for aset in read_jsonl(EXP1 / "05_Artifact_Registry/01_artifact_sets.jsonl"):
        for key, kind in [("malicious", "M"), ("benign_matched", "BM"), ("benign_weak", "BW")]:
            item = dict(aset[key])
            item["artifact_type"] = kind
            result[item["artifact_id"]] = item
    return result


def build(limit: int | None = None) -> list[dict[str, Any]]:
    artifacts = artifact_catalog()
    rows: list[dict[str, Any]] = []
    for manifest in read_jsonl(EXP1 / "07_Experiment_Manifest/01_manifest.jsonl"):
        candidates = [
            ("E_M", "09_External_Runs", manifest["external_run_id"], manifest["malicious_artifact_id"]),
            ("E_BM", "09_External_Runs", manifest["external_run_id"], manifest["benign_matched_id"]),
            ("UC_M", "10_User_Context_Runs", manifest["user_context_run_id"], manifest["malicious_artifact_id"]),
            ("UC_BM", "10B_User_Context_Benign_Runs", f"{manifest['pair_id']}_UCB", manifest["benign_matched_id"]),
        ]
        for condition, run_group, run_id, artifact_id in candidates:
            run_dir = EXP1 / run_group / MODEL / run_id
            if not (run_dir / "03_messages.jsonl").exists():
                continue
            metadata = {**manifest, "run_id": run_id, "model": MODEL, "condition": condition}
            rows.append(extract_behavior(
                run_dir=run_dir, metadata=metadata, artifact=artifacts[artifact_id],
                model_family="gpt4o", internal_trace_ref=None,
            ))
            if limit is not None and len(rows) >= limit:
                break
        if limit is not None and len(rows) >= limit:
            break

    output = HERE / "03_behavioral_traces"
    metrics = HERE / "04_metrics"
    output.mkdir(parents=True, exist_ok=True)
    metrics.mkdir(parents=True, exist_ok=True)
    write_schema(output / "00_behavioral_trace_schema.json")
    write_csv(output / "01_gpt4o_behavioral_trace.csv", rows)
    pd.DataFrame(summarize(rows)).to_csv(
        metrics / "01_reliance_calibration_summary.csv", index=False
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "scope": "gpt4o_behavioral_only",
        "row_count": len(rows),
        "internal_trace_available": False,
        "fields": BEHAVIORAL_FIELDS,
        "canonical_schema_source": str(RQ2_TRACKER / "behavioral_trace.py"),
    }
    (output / "02_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"gpt4o_behavioral_rows={len(rows)}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    build(args.limit)


if __name__ == "__main__":
    main()
