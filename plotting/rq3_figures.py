import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from style import apply, save


def figure(data, filename):
    apply()
    relevant = data[data["condition"] == "UC_M"].copy()
    if relevant.empty:
        raise ValueError("No UC_M defense records in summary")
    relevant["attack"] *= 100
    labels = list(relevant["defense"].unique())
    vals = [relevant[relevant["defense"] == x]["attack"].mean() for x in labels]
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(np.arange(len(labels)), vals)
    ax.set_xticks(np.arange(len(labels)), labels, rotation=35, ha="right")
    ax.set_ylabel("Malicious-action execution (%)")
    save(fig, filename)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default="outputs/analysis/summary.csv")
    parser.add_argument("--out", default="outputs/figures/rq3.pdf")
    args = parser.parse_args()
    figure(pd.read_csv(args.summary), args.out)


if __name__ == "__main__":
    main()
