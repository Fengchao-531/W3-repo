#!/usr/bin/env python3
"""CPU-only smoke test for the W3 -> TaskTracer data replacement."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPRO_ROOT = SCRIPT_DIR.parents[1]
DEMO_DIR = REPRO_ROOT / "Demo"
sys.path.insert(0, str(DEMO_DIR))

from OriginalTaskTracer import exact_pipeline  # noqa: E402
from build_w3_tasktracer_inputs import build_samples, write_json  # noqa: E402


def write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def smoke(samples: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    previews = []
    for sample in samples:
        clean_words = sample["clean_text"].split()
        poisoned_words = sample["poisoned_text"].split()
        onset, method = exact_pipeline.first_injection_word(poisoned_words, clean_words)
        if onset is None:
            onset = sample["injection_onset_word"]
            method = sample["injection_onset_method"]

        primary_prompt = exact_pipeline.format_primary(sample["primary_task"])
        clean_prompt = exact_pipeline.format_with_external(sample["primary_task"], sample["clean_text"])
        poisoned_prompt = exact_pipeline.format_with_external(sample["primary_task"], sample["poisoned_text"])
        if "All requests that I am going to execute now are:" not in poisoned_prompt:
            raise AssertionError("TaskTracer eliciting instruction missing")
        if sample["primary_task"] not in primary_prompt:
            raise AssertionError("Primary task missing from TaskTracer prompt")

        previews.append(
            {
                "sample_id": sample["sample_id"],
                "clean_word_count": len(clean_words),
                "poisoned_word_count": len(poisoned_words),
                "injection_onset_word": onset,
                "injection_onset_method": method,
                "primary_prompt_preview": primary_prompt[:500],
                "clean_prompt_preview": clean_prompt[:500],
                "poisoned_prompt_preview": poisoned_prompt[:500],
            }
        )

    write_json(samples, output_dir / "01_source_data" / "w3_exp1_tasktracer_samples.json")
    write_json(previews, output_dir / "02_smoke" / "prompt_previews.json")
    write_text(
        "\n\n".join(
            [
                "### " + item["sample_id"] + "\n\n" + item["poisoned_prompt_preview"]
                for item in previews
            ]
        )
        + "\n",
        output_dir / "02_smoke" / "poisoned_prompt_previews.md",
    )
    manifest = {
        "status": "smoke_complete",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sample_count": len(samples),
        "pipeline": "W3 Exp1 AgentDojo logs -> OriginalTaskTracer exact_pipeline prompt format",
        "gpu_required": False,
        "model_loaded": False,
        "strict_tasktracer_functions_checked": [
            "format_primary",
            "format_with_external",
            "first_injection_word",
        ],
        "outputs": {
            "samples": str(output_dir / "01_source_data" / "w3_exp1_tasktracer_samples.json"),
            "prompt_previews": str(output_dir / "02_smoke" / "prompt_previews.json"),
            "markdown_preview": str(output_dir / "02_smoke" / "poisoned_prompt_previews.md"),
        },
    }
    write_json(manifest, output_dir / "manifest.smoke.json")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=SCRIPT_DIR)
    parser.add_argument("--limit", type=int, default=3)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    samples = build_samples(
        SCRIPT_DIR.parent / "Exp1_User_Context_Embedding" / "07_Experiment_Manifest" / "01_manifest.jsonl",
        SCRIPT_DIR.parent / "Exp1_User_Context_Embedding" / "08_Clean_Runs" / "gpt-4o-2024-05-13",
        SCRIPT_DIR.parent / "Exp1_User_Context_Embedding" / "09_External_Runs" / "gpt-4o-2024-05-13",
        args.limit,
    )
    manifest = smoke(samples, args.output_dir)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
