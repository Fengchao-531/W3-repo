#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ATTACK_GENERATED_DIR = ROOT.parent / "Attack-Methods" / "generated"
AGENTDOJO_DATASET_PATH = ROOT.parent / "Datasets" / "agentdojo_travel_1540.jsonl"
PREDICTION_RESULTS_DIR = ROOT / "prediction result"

DETECTOR_COLUMNS = [
    "causal_armor_verdict",
    "perplexity_filter_verdict",
    "datasentinel_verdict",
    "sandwich_verdict",
    "struq_verdict",
    "secalign_verdict",
]


def load_dataset_metadata() -> dict[int, dict[str, str]]:
    metadata: dict[int, dict[str, str]] = {}
    if not AGENTDOJO_DATASET_PATH.exists():
        return metadata

    with AGENTDOJO_DATASET_PATH.open("r", encoding="utf-8") as src:
        for line in src:
            row = json.loads(line)
            metadata[int(row["row_id"])] = {
                "user_instruction": row.get("user_instruction", ""),
                "injection_goal": row.get("injection_goal", ""),
            }
    return metadata


def prepare_row(row: dict) -> dict:
    prepared = {
        "row_id": row["row_id"],
        "user_instruction": row.get("user_instruction", ""),
        "injection_goal": row.get("injection_goal", ""),
        "injection_content": row["injection_content"],
    }
    for column in DETECTOR_COLUMNS:
        prepared[column] = ""
    return prepared


def main() -> None:
    overwrite = "--overwrite" in sys.argv
    PREDICTION_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    dataset_metadata = load_dataset_metadata()
    skipped_existing: list[str] = []

    for input_path in sorted(ATTACK_GENERATED_DIR.glob("*.jsonl")):
        output_path = PREDICTION_RESULTS_DIR / input_path.name
        if output_path.exists() and not overwrite:
            skipped_existing.append(output_path.name)
            continue
        with input_path.open("r", encoding="utf-8") as src, output_path.open(
            "w", encoding="utf-8"
        ) as dst:
            for line in src:
                row = json.loads(line)
                metadata = dataset_metadata.get(int(row["row_id"]), {})
                if not row.get("user_instruction"):
                    row["user_instruction"] = metadata.get("user_instruction", "")
                if not row.get("injection_goal"):
                    row["injection_goal"] = metadata.get("injection_goal", "")
                dst.write(json.dumps(prepare_row(row), ensure_ascii=False) + "\n")

    print(
        json.dumps(
            {
                "input_dir": str(ATTACK_GENERATED_DIR),
                "output_dir": str(PREDICTION_RESULTS_DIR),
                "files": sorted(p.name for p in PREDICTION_RESULTS_DIR.glob("*.jsonl")),
                "detector_columns": DETECTOR_COLUMNS,
                "overwrite": overwrite,
                "skipped_existing": skipped_existing,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
