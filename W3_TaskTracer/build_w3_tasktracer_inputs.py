#!/usr/bin/env python3
"""Build W3 AgentDojo samples in the strict TaskTracer input shape.

The output rows intentionally match the fields consumed by
Demo/OriginalTaskTracer/run_original_tasktracker.py::run_dataset:
sample_id, primary_task, clean_text, poisoned_text, injection_text, and metadata.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
W3_DIR = SCRIPT_DIR.parent
EXP1_DIR = W3_DIR / "Exp1_User_Context_Embedding"
DEFAULT_MANIFEST = EXP1_DIR / "07_Experiment_Manifest" / "01_manifest.jsonl"
DEFAULT_CLEAN_ROOT = EXP1_DIR / "08_Clean_Runs" / "gpt-4o-2024-05-13"
DEFAULT_EXTERNAL_ROOT = EXP1_DIR / "09_External_Runs" / "gpt-4o-2024-05-13"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(value: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def first_message_content(messages_path: Path, role: str) -> str:
    with messages_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("role") == role and row.get("content"):
                return str(row["content"])
    raise ValueError(f"No {role!r} content found in {messages_path}")


def artifact_tool_output(messages_path: Path) -> dict[str, Any]:
    with messages_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("role") == "tool" and row.get("contains_artifact"):
                return row
    raise ValueError(f"No artifact-bearing tool output found in {messages_path}")


def tool_output_at_step(messages_path: Path, step: int) -> dict[str, Any] | None:
    with messages_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("role") == "tool" and int(row.get("step", -1)) == step:
                return row
    return None


def tool_name(row: dict[str, Any]) -> str | None:
    raw = row.get("raw_message") or {}
    call = raw.get("tool_call") or {}
    return call.get("function")


def tool_output_by_name(messages_path: Path, name: str) -> dict[str, Any] | None:
    with messages_path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("role") == "tool" and tool_name(row) == name:
                return row
    return None


def first_divergence(left_words: list[str], right_words: list[str]) -> int | None:
    shared = min(len(left_words), len(right_words))
    for index in range(shared):
        if left_words[index] != right_words[index]:
            return index
    if len(left_words) != len(right_words):
        return shared
    return None


def build_samples(
    manifest_path: Path,
    clean_root: Path,
    external_root: Path,
    limit: int,
) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for row in read_jsonl(manifest_path):
        clean_dir = clean_root / row["clean_run_id"]
        external_dir = external_root / row["external_run_id"]
        clean_messages = clean_dir / "03_messages.jsonl"
        external_messages = external_dir / "03_messages.jsonl"
        if not clean_messages.exists() or not external_messages.exists():
            continue

        poisoned_tool = artifact_tool_output(external_messages)
        poisoned_tool_name = tool_name(poisoned_tool)
        clean_tool = (
            tool_output_by_name(clean_messages, poisoned_tool_name)
            if poisoned_tool_name is not None
            else None
        )
        if clean_tool is None:
            clean_tool = tool_output_at_step(clean_messages, int(poisoned_tool["step"]))
        if clean_tool is None:
            # Same task/tool trajectory can shift after injection; use the first clean
            # tool output as a conservative clean external context.
            clean_tool = next(
                json.loads(line)
                for line in clean_messages.read_text(encoding="utf-8").splitlines()
                if json.loads(line).get("role") == "tool"
            )

        primary_task = first_message_content(clean_messages, "user").strip()
        clean_text = str(clean_tool.get("content", "")).strip()
        poisoned_text = str(poisoned_tool.get("content", "")).strip()
        if not primary_task or not poisoned_text:
            continue

        onset = first_divergence(poisoned_text.split(), clean_text.split())
        if onset is None:
            continue

        sample = {
            "sample_id": row["pair_id"],
            "source_dataset": "W3 Exp1 AgentDojo extended external/tool-context run",
            "primary_task": primary_task,
            "clean_text": clean_text,
            "poisoned_text": poisoned_text,
            "injection_text": poisoned_text,
            "injection_location": "tool_result",
            "injection_onset_word": onset,
            "injection_onset_method": "first_clean_poisoned_word_divergence",
            "base_task_id": row["base_task_id"],
            "desire_id": row["desire_id"],
            "carrier_id": row["carrier_id"],
            "clean_run_id": row["clean_run_id"],
            "external_run_id": row["external_run_id"],
            "artifact_ids": poisoned_tool.get("artifact_ids", []),
            "carrier_ids": poisoned_tool.get("carrier_ids", []),
            "artifact_tool_step": poisoned_tool.get("step"),
            "artifact_tool_name": poisoned_tool_name,
            "clean_tool_step": clean_tool.get("step"),
            "clean_tool_name": tool_name(clean_tool),
        }
        samples.append(sample)
        if limit and len(samples) >= limit:
            break
    return samples


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--clean-root", type=Path, default=DEFAULT_CLEAN_ROOT)
    parser.add_argument("--external-root", type=Path, default=DEFAULT_EXTERNAL_ROOT)
    parser.add_argument("--output", type=Path, default=SCRIPT_DIR / "01_source_data" / "w3_exp1_tasktracer_samples.json")
    parser.add_argument("--limit", type=int, default=8)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    samples = build_samples(args.manifest, args.clean_root, args.external_root, args.limit)
    if not samples:
        raise RuntimeError("No W3 TaskTracer samples were built")
    write_json(samples, args.output)
    print(f"Wrote {len(samples)} W3 TaskTracer samples to {args.output}")


if __name__ == "__main__":
    main()
