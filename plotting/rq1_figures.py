import argparse
import pandas as pd
import matplotlib.pyplot as plt
from style import apply, save


def adoption_chart(data, filename):
    apply()
    fig, ax = plt.subplots(figsize=(8, 3.6))
    domains = [d for d in ("travel", "workspace", "banking", "slack") if d in set(data["domain"])]
    conditions = [c for c in ("E", "UC_M", "UC_BM") if c in set(data["condition"])]
    for i, condition in enumerate(conditions):
        subset = data.loc[data["condition"] == condition]
        vals = [float(subset.loc[subset["domain"] == domain, "adoption"].mean()) * 100 for domain in domains]
        ax.bar([n + (i - (len(conditions) - 1) / 2) * 0.23 for n in range(len(domains))], vals, 0.22, label=condition)
    ax.set_xticks(range(len(domains)), [domain.capitalize() for domain in domains])
    ax.set_ylabel("Artifact adoption (%)")
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, ncol=len(conditions))
    save(fig, filename)


def position_chart(data, filename):
    apply()
    fig, ax = plt.subplots(figsize=(8, 4))
    groups = [("M", "UC_M_"), ("BM", "UC_BM_")]
    domains = [d for d in ("travel", "workspace", "banking", "slack") if d in set(data["domain"])]
    for i, (kind, prefix) in enumerate(groups):
        for j, position in enumerate(("beginning", "middle", "end")):
            sub = data[data["condition"] == prefix + position]
            vals = [float(sub[sub["domain"] == domain]["adoption"].mean()) * 100 for domain in domains]
            loc = [x + (i * 3 + j - 2.5) * 0.13 for x in range(len(domains))]
            ax.bar(loc, vals, 0.12, label=f"{kind} {position[0].upper()}", hatch="///" if kind == "BM" else None, color="0.78" if kind == "BM" else None)
    ax.set_xticks(range(len(domains)), [domain.capitalize() for domain in domains])
    ax.set_ylabel("Adoption (%)")
    ax.set_ylim(0, 100)
    ax.legend(frameon=False, ncol=3, fontsize=8)
    save(fig, filename)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default="outputs/analysis/summary.csv")
    parser.add_argument("--figure", choices=("adoption", "position"), default="adoption")
    parser.add_argument("--out", default="outputs/figures/rq1.pdf")
    args = parser.parse_args()
    data = pd.read_csv(args.summary)
    (adoption_chart if args.figure == "adoption" else position_chart)(data, args.out)


if __name__ == "__main__":
    main()
