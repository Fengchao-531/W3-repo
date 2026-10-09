import argparse
import json
from pathlib import Path
from statistics import mean
from source_relocation.tracing import selected_heads


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", default="outputs/internal/selected_heads.json")
    args = parser.parse_args()
    units = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
    effects = {}
    for unit in units:
        for row in unit["head_effects"]:
            key = row["layer"], row["head"]
            effects.setdefault(key, []).append(row["bidirectional_mean"])
    table = [{"layer": index[0], "head": index[1], "mean_effect": mean(values), "n": len(values)} for index, values in effects.items()]
    chosen = selected_heads(table, count=3)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"selected": chosen, "heads": table}, indent=2), encoding="utf-8")
    print(json.dumps({"selected": chosen, "candidate_heads": len(table)}))


if __name__ == "__main__":
    main()
