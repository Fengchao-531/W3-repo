import argparse
from collections import defaultdict
from pathlib import Path

import pandas as pd

from source_relocation.evaluation import load_results
from source_relocation.statistics import cluster_bootstrap


MEASURES = ("malicious_action_executed", "artifact_adopted", "task_success", "safe_completion")


def aggregate(root):
    rows = load_results(root)
    groups = defaultdict(list)
    for row in rows:
        groups[(row["model"], row["domain"], row["defense"], row["condition"])].append(row)
    records = []
    for (model, domain, defense, condition), units in sorted(groups.items()):
        sample = {
            "model": model, "domain": domain, "defense": defense,
            "condition": condition, "n": len(units),
        }
        for metric in MEASURES:
            sample[metric] = sum(bool(u[metric]) for u in units) / len(units)
        records.append(sample)
    return pd.DataFrame(records), rows


def contrasts(rows, experiment, iterations=2000):
    table = defaultdict(list)
    for row in rows:
        key = (row["model"], row["domain"], row["defense"])
        table[key].append(row)
    configurations = {
        "defenses": [(f"E_{kind}", f"UC_{kind}") for kind in ("M", "BM")],
        "verification": [(f"{src}_H1", f"{src}_H2") for src in ("E", "UC")] +
                        [(f"{src}_H1", f"{src}_H3") for src in ("E", "UC")] +
                        [(f"{src}_H2", f"{src}_H3") for src in ("E", "UC")],
    }
    output = []
    for (model, domain, defense), subset in sorted(table.items()):
        for left, right in configurations[experiment]:
            for metric in MEASURES:
                l = {r["pair_id"] for r in subset if r["condition"] == left}
                r = {r["pair_id"] for r in subset if r["condition"] == right}
                matched = l & r
                if not matched:
                    continue
                chosen = [x for x in subset if x["pair_id"] in matched and x["condition"] in (left, right)]
                result = cluster_bootstrap(chosen, left, right, metric, iterations=iterations)
                output.append({
                    "experiment": experiment, "model": model,
                    "domain": domain, "defense": defense,
                    "left": left, "right": right, "metric": metric,
                    "paired_units": len(matched), **result,
                })
    return pd.DataFrame(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", default="outputs/runs/rq3")
    parser.add_argument("--outdir", default="outputs/analysis/rq3")
    parser.add_argument("--resamples", type=int, default=2000)
    args = parser.parse_args()
    output = Path(args.outdir)
    output.mkdir(parents=True, exist_ok=True)
    for experiment in ("defenses", "verification"):
        directory = Path(args.runs) / experiment
        if not directory.exists():
            continue
        summary, rows = aggregate(directory)
        summary.to_csv(output / f"{experiment}_rates.csv", index=False)
        contrasts(rows, experiment, args.resamples).to_csv(
            output / f"{experiment}_contrasts.csv", index=False
        )
        print(f"{experiment}: {len(rows)} executions")


if __name__ == "__main__":
    main()
