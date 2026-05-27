#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from time import perf_counter

import torch
from huggingface_hub.utils import HFValidationError, validate_repo_id


ROOT = Path(__file__).resolve().parent
OPEN_PROMPT_INJECTION_DIR = ROOT / "Detection-based" / "Open-Prompt-Injection"
PREDICTION_RESULTS_DIR = ROOT / "prediction result"
DEFAULT_DATASET_FILES = [
    "agentdojo_travel_1540_combined.jsonl",
    "agentdojo_travel_1540_context_ignoring.jsonl",
    "agentdojo_travel_1540_escape_characters.jsonl",
    "agentdojo_travel_1540_fake_completion.jsonl",
    "agentdojo_travel_1540_naive.jsonl",
]
DEFAULT_MODEL_CONFIG = OPEN_PROMPT_INJECTION_DIR / "configs" / "model_configs" / "mistral_config.json"
VERDICT_COLUMN = "datasentinel_verdict"
ROW_KEY_ORDER = [
    "row_id",
    "user_instruction",
    "injection_goal",
    "injection_content",
    "causal_armor_verdict",
    "perplexity_filter_verdict",
    "datasentinel_verdict",
    "sandwich_verdict",
    "struq_verdict",
    "secalign_verdict",
]

sys.path.insert(0, str(OPEN_PROMPT_INJECTION_DIR))

from OpenPromptInjection import DataSentinelDetector  # type: ignore  # noqa: E402
from OpenPromptInjection.utils import open_config  # type: ignore  # noqa: E402


def load_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            try:
                rows.append(normalize_row(json.loads(line)))
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Malformed JSONL in {path} at line {lineno}: {exc}") from exc
    return rows


def write_rows(path: Path, rows: list[dict]) -> None:
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        for row in rows:
            tmp.write(json.dumps(normalize_row(row), ensure_ascii=False) + "\n")
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def normalize_row(row: dict) -> dict:
    existing = dict(row)
    datasentinel_verdict = row.get("datasentinel_verdict", row.get("paraphrase_verdict", ""))
    normalized = {
        "row_id": row["row_id"],
        "user_instruction": row.get("user_instruction", ""),
        "injection_goal": row.get("injection_goal", ""),
        "injection_content": row["injection_content"],
        "causal_armor_verdict": row.get("causal_armor_verdict", ""),
        "perplexity_filter_verdict": row.get("perplexity_filter_verdict", ""),
        "datasentinel_verdict": datasentinel_verdict,
        "sandwich_verdict": row.get("sandwich_verdict", row.get("jatmo_verdict", "")),
        "struq_verdict": row.get("struq_verdict", ""),
        "secalign_verdict": row.get("secalign_verdict", ""),
    }
    ordered = {key: normalized[key] for key in ROW_KEY_ORDER}
    for key, value in existing.items():
        if key in ordered or key in {"paraphrase_verdict", "jatmo_verdict"}:
            continue
        ordered[key] = value
    return ordered


def build_detector(config_path: Path, ft_path: str) -> DataSentinelDetector:
    config = open_config(str(config_path))
    config["params"]["ft_path"] = ft_path
    return DataSentinelDetector(config)


def validate_ft_path(ft_path: str) -> None:
    if ft_path in {"", "base"}:
        return

    path = Path(ft_path).expanduser()
    if path.is_absolute() or "/" in ft_path:
        adapter_config = path / "adapter_config.json"
        if not path.exists():
            raise FileNotFoundError(
                f"DATASENTINEL_FT_PATH does not exist: {path}. "
                "Set it to the real DataSentinel LoRA checkpoint directory."
            )
        if not adapter_config.exists():
            raise FileNotFoundError(
                f"DATASENTINEL_FT_PATH must contain adapter_config.json: {adapter_config}. "
                "Set it to the adapter checkpoint directory, not a placeholder or parent folder."
            )
        return

    try:
        validate_repo_id(ft_path)
    except HFValidationError as exc:
        raise ValueError(
            f"DATASENTINEL_FT_PATH is neither a valid local adapter path nor a Hugging Face repo id: {ft_path}"
        ) from exc


def map_verdict(detector_output: int) -> str:
    # Upstream DataSentinel returns 1 when contamination is detected and 0 otherwise.
    return "BLOCKED" if detector_output == 1 else "ALLOWED"


def run_file(path: Path, detector: DataSentinelDetector, limit: int | None) -> dict:
    rows = load_rows(path)
    start = perf_counter()
    total_rows = len(rows)
    existing_done = sum(1 for row in rows if row.get(VERDICT_COLUMN))
    pending_rows = total_rows - existing_done
    blocked = 0
    allowed = 0
    processed = 0
    resumed = 0

    print(f"[START] {path.name}")
    print(
        f"  total_rows={total_rows}  existing_done={existing_done}  pending_rows={pending_rows}"
    )

    for row in rows:
        if row.get(VERDICT_COLUMN):
            verdict = row[VERDICT_COLUMN]
            blocked += verdict == "BLOCKED"
            allowed += verdict == "ALLOWED"
            resumed += 1
            continue

        if limit is not None and processed >= limit:
            break

        verdict = map_verdict(detector.detect(row["injection_content"]))
        row[VERDICT_COLUMN] = verdict
        blocked += verdict == "BLOCKED"
        allowed += verdict == "ALLOWED"
        processed += 1
        write_rows(path, rows)
        print(
            f"  [{path.name}] row_id={row['row_id']} verdict={verdict} "
            f"processed_now={processed} resumed={resumed}"
        )

    write_rows(path, rows)
    elapsed = perf_counter() - start
    print(
        f"[DONE] {path.name} total_rows={total_rows} resumed={resumed} "
        f"processed_now={processed} blocked={blocked} allowed={allowed} "
        f"elapsed_sec={elapsed:.1f}"
    )
    return {
        "file": path.name,
        "total_rows": total_rows,
        "resumed": resumed,
        "processed": processed,
        "blocked": blocked,
        "allowed": allowed,
        "elapsed_sec": round(elapsed, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run DataSentinel over prediction result datasets and write datasentinel_verdict."
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Optional single JSONL file inside prediction result/ to process.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional row limit for smoke testing.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(os.environ.get("DATASENTINEL_MODEL_CONFIG", DEFAULT_MODEL_CONFIG)),
        help="Model config JSON path for Open-Prompt-Injection.",
    )
    parser.add_argument(
        "--ft-path",
        default=os.environ.get("DATASENTINEL_FT_PATH", ""),
        help="Fine-tuned checkpoint path for DataSentinel.",
    )
    args = parser.parse_args()

    if not args.ft_path:
        raise RuntimeError("DATASENTINEL_FT_PATH is not set.")
    if not args.config.exists():
        raise FileNotFoundError(f"DataSentinel config not found: {args.config}")
    validate_ft_path(args.ft_path)

    detector = build_detector(args.config, args.ft_path)
    paths = [args.input] if args.input else [PREDICTION_RESULTS_DIR / name for name in DEFAULT_DATASET_FILES]

    try:
        summaries = []
        for path in paths:
            if not path.exists():
                raise FileNotFoundError(f"Prediction result dataset not found: {path}")
            summaries.append(run_file(path, detector, args.limit))
    finally:
        del detector
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    print(json.dumps({"results": summaries}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
