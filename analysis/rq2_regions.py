import argparse
import json
from pathlib import Path

import pandas as pd


def summarize(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        unit = json.loads(line)
        for source in ("E", "UC"):
            for reg in unit[source]:
                rows.append({
                    "unit_id": unit["unit_id"],
                    "artifact_type": unit["artifact_type"],
                    "source": source,
                    **reg,
                })
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    by = ["unit_id", "artifact_type", "layer", "head", "region"]
    pivot = frame.pivot_table(index=by, columns="source", values=["mass", "density"], aggfunc="first")
    pivot.columns = [f"{measure}_{source}" for measure, source in pivot.columns]
    pivot = pivot.reset_index()
    pivot["delta_mass"] = pivot["mass_UC"] - pivot["mass_E"]
    pivot["delta_density"] = pivot["density_UC"] - pivot["density_E"]
    shares = []
    group_keys = ["unit_id", "artifact_type", "layer", "head"]
    for key, group in frame.groupby(group_keys):
        values = {}
        for source in ("E", "UC"):
            sub = group[group["source"] == source].set_index("region")
            artifact = float(sub["mass"].get("target_artifact", 0))
            surrounding = float(sub["mass"].get("surrounding_context", 0))
            denominator = artifact + surrounding
            values[f"artifact_share_{source}"] = artifact / denominator if denominator else float("nan")
        shares.append(dict(zip(group_keys, key), **values))
    shares = pd.DataFrame(shares)
    shares["delta_artifact_share"] = shares["artifact_share_UC"] - shares["artifact_share_E"]
    return pivot.merge(shares, on=group_keys, how="left")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", default="outputs/analysis/rq2_regions.csv")
    args = parser.parse_args()
    output = summarize(args.input)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(path, index=False)
    print(f"RQ2 region rows: {len(output)}, output: {path}")


if __name__ == "__main__":
    main()
