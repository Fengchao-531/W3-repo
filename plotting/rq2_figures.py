import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from style import apply, save


def plot_layer_gap(rows, filename):
    apply()
    fig, ax = plt.subplots(figsize=(7, 3.5))
    all_gaps = [row["gap"] for row in rows]
    length = min(map(len, all_gaps))
    arr = np.asarray([gap[:length] for gap in all_gaps], dtype=float)
    x = np.arange(1, length + 1) / length * 100
    mean = arr.mean(axis=0)
    rng = np.random.default_rng(1234)
    sampled = np.stack([arr[rng.integers(0, len(arr), len(arr))].mean(axis=0) for _ in range(2000)])
    low, high = np.percentile(sampled, [2.5, 97.5], axis=0)
    ax.plot(x, mean, linewidth=1.8)
    ax.fill_between(x, low, high, alpha=0.2)
    ax.axhline(0, color="0.4", linewidth=0.7)
    ax.axvspan(87.5, 100, color="0.85", alpha=0.5)
    ax.set_xlabel("Relative layer depth (%)")
    ax.set_ylabel("UC − E log-probability gap")
    save(fig, filename)


def plot_patching(rows, filename):
    apply()
    fig, ax = plt.subplots(figsize=(7, 3.5))
    sets = {}
    for row in rows:
        name = str(row["component"]) + " L" + str(row["layer"])
        sets.setdefault(name, []).append(row["bidirectional_mean"])
    labels = list(sets)
    means = [np.mean(sets[key]) for key in labels]
    ax.bar(range(len(means)), means)
    ax.set_xticks(range(len(labels)), labels, rotation=40, ha="right")
    ax.axhline(0, color="0.5", linewidth=0.8)
    ax.set_ylabel("Bidirectional patch effect")
    save(fig, filename)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--figure", choices=("gap", "patching"), default="gap")
    parser.add_argument("--out", default="outputs/figures/rq2.pdf")
    args = parser.parse_args()
    rows = [json.loads(line) for line in open(args.input, encoding="utf-8") if line.strip()]
    (plot_layer_gap if args.figure == "gap" else plot_patching)(rows, args.out)


if __name__ == "__main__":
    main()
