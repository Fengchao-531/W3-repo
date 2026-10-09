import argparse
from collections import defaultdict
from pathlib import Path

import pandas as pd

from source_relocation.evaluation import load_results


def joint_outcomes(runs):
    groups = defaultdict(dict)
    for row in load_results(runs):
        groups[(row["model"], row["domain"], row["pair_id"])][row["condition"]] = row
    summary = defaultdict(lambda: defaultdict(int))
    for (model, domain, _), cases in groups.items():
        counts = summary[(model, domain)]
        for condition in ("E", "UC_M", "UC_BM"):
            if condition not in cases:
                continue
            row = cases[condition]
            key = condition + "_"
            counts[key + "n"] += 1
            counts[key + "utility"] += int(bool(row["task_success"]))
            preferred = "BM" if condition == "UC_BM" else "M"
            chosen = row["selected"] == preferred
            counts[key + "adopted"] += int(chosen)
            counts[key + "adopted_and_success"] += int(chosen and bool(row["task_success"]))
        if all(condition in cases for condition in ("E", "UC_M", "UC_BM")):
            counts["matched_triples"] += 1
            counts["E_BM_to_UC_M_M"] += int(
                cases["E"]["selected"] == "BM" and
                cases["UC_M"]["selected"] == "M"
            )
            counts["E_M_to_UC_BM_BM"] += int(
                cases["E"]["selected"] == "M" and
                cases["UC_BM"]["selected"] == "BM"
            )
    return pd.DataFrame([
        {"model": model, "domain": domain, **dict(counts)}
        for (model, domain), counts in sorted(summary.items())
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", default="outputs/runs/rq1/relocation")
    parser.add_argument("--out", default="outputs/analysis/rq1_joint_utility.csv")
    args = parser.parse_args()
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    outcome = joint_outcomes(args.runs)
    outcome.to_csv(path, index=False)
    print(f"RQ1 joint outcome groups: {len(outcome)}")


if __name__ == "__main__":
    main()
