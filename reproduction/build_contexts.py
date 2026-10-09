import argparse
import json
from pathlib import Path
from source_relocation.manifest import load_manifest
from source_relocation.cli import save_jsonl


def before_action(path: Path) -> str:
    messages = json.loads(path.read_text(encoding="utf-8"))
    selected = []
    for message in messages:
        calls = message.get("tool_calls") or []
        if message.get("role") == "assistant" and any("apply_offer" in str(call) for call in calls):
            break
        selected.append(message)
    return json.dumps(selected, ensure_ascii=False)


def build(manifest: str, runs: str, model: str, output: str, limit_per_type: int = 31):
    rows = load_manifest(manifest)
    base = Path(runs) / "rq1" / "relocation"
    units = []
    for row in rows:
        pair_id = row["pair_id"]
        for kind, condition in (("M", "UC_M"), ("BM", "UC_BM")):
            prefix = base / row["domain"] / model / "none"
            e_file = prefix / "E" / pair_id / "trajectory.json"
            uc_file = prefix / condition / pair_id / "trajectory.json"
            if not e_file.is_file() or not uc_file.is_file():
                continue
            external = before_action(e_file)
            user = before_action(uc_file)
            code = row["artifacts"][kind].code
            url = row["artifacts"][kind].url
            if url not in external or url not in user:
                continue
            units.append({"unit_id": f"{pair_id}_{kind}", "base_task_id": row["base_task_id"], "artifact_type": kind, "code": code, "user_task": row["task"], "E": external, "UC": user})
    selected = []
    for kind in ("M", "BM"):
        subset = [unit for unit in units if unit["artifact_type"] == kind]
        selected.extend(subset[:limit_per_type])
    units = selected
    save_jsonl(units, output)
    return units


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="outputs/manifests/travel.jsonl")
    parser.add_argument("--runs", default="outputs/runs")
    parser.add_argument("--model", default="gpt4o")
    parser.add_argument("--out", default="outputs/internal/contexts.jsonl")
    parser.add_argument("--limit-per-type", type=int, default=31)
    args = parser.parse_args()
    rows = build(args.manifest, args.runs, args.model, args.out, args.limit_per_type)
    print(json.dumps({"matched_units": len(rows), "path": args.out}))


if __name__ == "__main__":
    main()
