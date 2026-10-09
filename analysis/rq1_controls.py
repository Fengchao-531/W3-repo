import argparse
from collections import defaultdict
from pathlib import Path

import pandas as pd

from source_relocation.statistics import cluster_bootstrap


CONTRASTS = {
    "relocation": [
        ("M", "E", "UC_M"),
        ("BM", "E", "UC_BM"),
    ],
    "position": [
        ("M", "UC_M_beginning", "UC_M_middle"),
        ("M", "UC_M_middle", "UC_M_end"),
        ("M", "UC_M_beginning", "UC_M_end"),
        ("BM", "UC_BM_beginning", "UC_BM_middle"),
        ("BM", "UC_BM_middle", "UC_BM_end"),
        ("BM", "UC_BM_beginning", "UC_BM_end"),
    ],
    "preference": [
        ("M", "UC_M_R_D", "UC_M_R_P_D"),
        ("BM", "UC_BM_R_D", "UC_BM_R_P_D"),
    ],
    "instruction": [
        ("M", "UC_P", "UC_P_I"),
    ],
    "reliability": [
        ("M", "E_base", "E_V"),
        ("M", "UC_base", "UC_V"),
    ],
    "source_label": [
        ("M", "C0", "C1"),
        ("BM", "C0", "C2"),
    ],
}


def evaluate(root, resamples=2000, seed=1234):
    by_group = defaultdict(list)
    for path in Path(root).rglob("result.json"):
        import json
        row = json.loads(path.read_text(encoding="utf-8"))
        experiment = path.relative_to(root).parts[0]
        by_group[(experiment, row["model"], row["domain"])].append(row)
    result = []
    for (experiment, model, domain), items in sorted(by_group.items()):
        for role, left, right in CONTRASTS.get(experiment, []):
            relevant = []
            for row in items:
                if row["condition"] not in (left, right):
                    continue
                relevant.append({
                    **row,
                    "_candidate": row["selected"] == role,
                })
            left_ids = {r["pair_id"] for r in relevant if r["condition"] == left}
            right_ids = {r["pair_id"] for r in relevant if r["condition"] == right}
            matched_ids = left_ids & right_ids
            relevant = [r for r in relevant if r["pair_id"] in matched_ids]
            if not matched_ids:
                continue
            stat = cluster_bootstrap(
                relevant, left, right, "_candidate",
                iterations=resamples, seed=seed,
            )
            result.append({
                "experiment": experiment, "model": model, "domain": domain,
                "candidate": role, "left": left, "right": right,
                "paired_units": len(matched_ids),
                "left_rate": sum(r["_candidate"] for r in relevant if r["condition"] == left) / len(matched_ids),
                "right_rate": sum(r["_candidate"] for r in relevant if r["condition"] == right) / len(matched_ids),
                **stat,
            })
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", default="outputs/runs/rq1")
    parser.add_argument("--out", default="outputs/analysis/rq1_all_controls.csv")
    parser.add_argument("--resamples", type=int, default=2000)
    args = parser.parse_args()
    rows = evaluate(args.runs, args.resamples)
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"RQ1 contrasts: {len(rows)}, output: {path}")


if __name__ == "__main__":
    main()
