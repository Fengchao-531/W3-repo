#!/usr/bin/env python3
"""Build a run-artifact manifest for the prioritized Exp1 and Exp3 traces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def artifact_catalog(exp1_root: Path) -> dict[str, dict[str, Any]]:
    result = {}
    for artifact_set in read_jsonl(exp1_root / "05_Artifact_Registry/01_artifact_sets.jsonl"):
        for key, artifact_type in [("malicious", "malicious"), ("benign_matched", "benign_matched"), ("benign_weak", "benign_weak")]:
            artifact = dict(artifact_set[key])
            artifact["artifact_type"] = artifact_type
            result[artifact["artifact_id"]] = artifact
    return result


def trace_text(run_dir: Path) -> str:
    chunks = []
    for name in ["03_messages.jsonl", "04_tool_calls.jsonl", "05_tool_outputs.jsonl"]:
        path = run_dir / name
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def artifact_text(run_dir: Path, artifact: dict[str, Any], fallback_prompt: str = "") -> str:
    provider = str(artifact["provider"])
    code = str(artifact["visible_code"])
    text = trace_text(run_dir) + "\n" + fallback_prompt
    candidates = []
    for raw_line in text.splitlines():
        line = raw_line.strip().strip('"')
        if provider in line and code in line:
            candidates.append(line)
    if candidates:
        return min(candidates, key=len)
    return f"Provider: {provider}; Code: {code}; Benefit: {artifact['benefit']}"


def labels(run_dir: Path, summary: dict[str, Any], artifact: dict[str, Any]) -> dict[str, bool]:
    artifact_id = artifact["artifact_id"]
    provider = str(artifact["provider"])
    code = str(artifact["visible_code"])
    final_response = str(summary.get("final_response", ""))
    mentioned = provider in final_response or code in final_response
    events = read_jsonl(run_dir / "06_environment_events.jsonl")
    executed = any(event.get("artifact_id") == artifact_id for event in events)
    adopted = summary.get("selected_artifact_id", summary.get("selected_artifact")) == artifact_id
    return {
        "artifact_mentioned": mentioned,
        "artifact_used_in_plan": mentioned or executed,
        "artifact_action_executed": executed,
        "final_adoption": adopted,
    }


def feature_paths(run_dir: Path, feature_root: Path, run_id: str) -> dict[str, Any]:
    calls = read_json(run_dir / "11_model_call_index.json").get("call_ids", [])
    return {
        "prompt_trace_dir": str(feature_root / run_id),
        "hidden_state_files": [
            str(feature_root / run_id / call_id / "08_hidden_states/prompt_layer_activations.pt")
            for call_id in calls
        ],
    }


def build_exp1(root: Path, artifacts: dict[str, dict[str, Any]], model: str) -> list[dict[str, Any]]:
    exp1 = root / "Exp1_User_Context_Embedding"
    rows = []
    for manifest in read_jsonl(exp1 / "07_Experiment_Manifest/01_manifest.jsonl"):
        specs = [
            ("E_M", "E", manifest["external_run_id"], manifest["malicious_artifact_id"], "09_External_Runs"),
            ("E_BM", "E", manifest["external_run_id"], manifest["benign_matched_id"], "09_External_Runs"),
            ("UC_M", "UC_M", manifest["user_context_run_id"], manifest["malicious_artifact_id"], "10_User_Context_Runs"),
            ("UC_BM", "UC_B", f"{manifest['pair_id']}_UCB", manifest["benign_matched_id"], "10B_User_Context_Benign_Runs"),
        ]
        for analysis_condition, run_condition, run_id, artifact_id, top in specs:
            run_dir = exp1 / top / model / run_id
            summary_path = run_dir / "10_trace_summary.json"
            if not summary_path.exists():
                continue
            summary = read_json(summary_path)
            artifact = artifacts[artifact_id]
            rows.append({
                "experiment": "RQ1_Exp1",
                "run_id": run_id,
                "pair_id": manifest["pair_id"],
                "base_task_id": manifest["base_task_id"],
                "condition": analysis_condition,
                "run_condition": run_condition,
                "artifact_id": artifact_id,
                "artifact_type": artifact["artifact_type"],
                "artifact_text": artifact_text(run_dir, artifact),
                **labels(run_dir, summary, artifact),
                "run_dir": str(run_dir),
                **feature_paths(run_dir, exp1 / "11_Model_Features" / model, run_id),
            })
    return rows


def build_exp3(root: Path, artifacts: dict[str, dict[str, Any]], model: str) -> list[dict[str, Any]]:
    exp3 = root / "RQ2/Exp3_ Controlled_Source-Provenance_Intervention"
    rows = []
    for manifest in read_jsonl(exp3 / "01_manifest/01_exp3_runs.jsonl"):
        run_id = manifest["run_id"]
        run_dir = exp3 / "02_controlled_source/raw_runs" / manifest["condition"] / model / run_id
        summary_path = run_dir / "10_trace_summary.json"
        if not summary_path.exists():
            continue
        summary = read_json(summary_path)
        source_by_id = {item["artifact_id"]: item["source"] for item in manifest["source_assignment"]["candidates"]}
        for artifact_id in [manifest["malicious_artifact_id"], manifest["benign_matched_id"], manifest["benign_weak_id"]]:
            artifact = artifacts[artifact_id]
            rows.append({
                "experiment": "RQ2_Exp3_Controlled_Source",
                "run_id": run_id,
                "pair_id": manifest["pair_id"],
                "base_task_id": manifest["base_task_id"],
                "condition": manifest["condition"],
                "source_attribution": source_by_id[artifact_id],
                "artifact_id": artifact_id,
                "artifact_type": artifact["artifact_type"],
                "artifact_text": artifact_text(run_dir, artifact, manifest["run_prompt"]),
                **labels(run_dir, summary, artifact),
                "run_dir": str(run_dir),
                **feature_paths(run_dir, exp3 / "08_logs/model_features" / model, run_id),
            })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--model", default="llama31_8b_instruct")
    args = parser.parse_args()
    root = args.root.resolve()
    artifacts = artifact_catalog(root / "Exp1_User_Context_Embedding")
    rows = build_exp1(root, artifacts, args.model) + build_exp3(root, artifacts, args.model)
    output = root / "tracker_run_artifact_manifest.jsonl"
    output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    print(f"tracker_manifest={output} rows={len(rows)}")


if __name__ == "__main__":
    main()
