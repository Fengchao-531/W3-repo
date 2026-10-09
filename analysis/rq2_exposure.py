import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

import pandas as pd

from source_relocation.manifest import load_manifest


def first_exposure_step(messages, code):
    step = 0
    for item in messages:
        if item.get("role") == "system":
            continue
        step += 1
        if item.get("role") not in ("user", "tool"):
            continue
        if code in json.dumps(item.get("content", ""), ensure_ascii=False):
            return step
    return None


def calculate(manifest, runs):
    references = {
        row["pair_id"]: row for row in load_manifest(manifest)
    }
    grouped = defaultdict(list)
    for result_path in Path(runs).rglob("result.json"):
        row = json.loads(result_path.read_text(encoding="utf-8"))
        if row.get("condition") not in ("E", "UC_M", "UC_BM"):
            continue
        pair = references[row["pair_id"]]
        code = pair["artifacts"][row["artifact_type"]].code
        trace_path = result_path.with_name("trajectory.json")
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        first = first_exposure_step(trace, code)
        grouped[(row["model"], row["domain"], row["condition"], row["artifact_type"])].append({
            "first_step": first,
            "mentioned": bool(row["artifact_mentioned"]),
            "planned": bool(row["artifact_used_in_plan"]),
            "action": bool(row["artifact_action_executed"]),
        })
    outputs = []
    for (model, domain, condition, kind), values in sorted(grouped.items()):
        exposed = [x["first_step"] for x in values if x["first_step"] is not None]
        outputs.append({
            "model": model, "domain": domain, "condition": condition,
            "artifact_type": kind, "n": len(values),
            "exposure_rate": len(exposed) / len(values),
            "median_first_step": statistics.median(exposed) if exposed else float("nan"),
            "mention_rate": sum(x["mentioned"] for x in values) / len(values),
            "plan_rate": sum(x["planned"] for x in values) / len(values),
            "action_rate": sum(x["action"] for x in values) / len(values),
        })
    return pd.DataFrame(outputs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="outputs/manifests/travel.jsonl")
    parser.add_argument("--runs", default="outputs/runs/rq1/relocation")
    parser.add_argument("--out", default="outputs/analysis/rq2_exposure.csv")
    args = parser.parse_args()
    table = calculate(args.manifest, args.runs)
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output, index=False)
    print(f"RQ2 exposure records: {len(table)}")


if __name__ == "__main__":
    main()
