import argparse
import pandas as pd
from source_relocation.evaluation import load_results
from source_relocation.statistics import cluster_bootstrap


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", default="outputs/runs/rq1/relocation")
    parser.add_argument("--out", default="outputs/analysis/rq1_effects.csv")
    args = parser.parse_args()
    rows = load_results(args.runs)
    output = []
    for model in sorted({row["model"] for row in rows}):
        for domain in sorted({row["domain"] for row in rows}):
            subset = [row for row in rows if row["model"] == model and row["domain"] == domain]
            for reference, target, field in (("E", "UC_M", "M_adopted"), ("E", "UC_BM", "BM_adopted")):
                paired = [row for row in subset if row["condition"] in (reference, target)]
                for item in paired:
                    item["M_adopted"] = item["selected"] == "M"
                    item["BM_adopted"] = item["selected"] == "BM"
                stats = cluster_bootstrap(paired, reference, target, field)
                output.append({"model": model, "domain": domain, "contrast": target + "-" + reference, **stats})
    from pathlib import Path
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(output).to_csv(args.out, index=False)


if __name__ == "__main__":
    main()
