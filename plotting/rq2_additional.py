import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def save(fig, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output, dpi=200, bbox_inches="tight")
    plt.close(fig)


def matched_unit_distribution(path, output):
    rows = read_jsonl(path)
    vals = [
        (row["artifact_type"], float(row.get("late_mean", 0)))
        for row in rows
    ]
    frame = pd.DataFrame(vals, columns=["type", "late_gap"])
    fig, ax = plt.subplots(figsize=(5, 3.2))
    for i, kind in enumerate(("M", "BM")):
        data = frame.loc[frame["type"] == kind, "late_gap"].to_numpy()
        if len(data):
            ax.scatter(np.full(len(data), i), data, alpha=0.65, s=16)
            ax.plot([i - .15, i + .15], [data.mean()] * 2, color="black")
    ax.set_xticks([0, 1], ["M", "BM"])
    ax.set_ylabel("Late-layer UC − E artifact score")
    ax.axhline(0, lw=0.6)
    save(fig, output)


def head_set_effects(path, output):
    rows = read_jsonl(path)
    order = ["Top3", "Top3_counteracting", "FullWindow", "Random3"]
    vals = {
        key: [float(row["bidirectional_mean"]) for row in rows if row["set"] == key]
        for key in order
    }
    fig, ax = plt.subplots(figsize=(6, 3.4))
    means = [np.mean(vals[key]) if vals[key] else np.nan for key in order]
    ax.bar(range(len(order)), means, color="0.65")
    ax.set_xticks(range(len(order)), order, rotation=12)
    ax.axhline(0, lw=0.7, color="black")
    ax.set_ylabel("Bidirectional intervention effect")
    save(fig, output)


def semantic_region_effects(path, output):
    frame = pd.read_csv(path)
    mean = frame.groupby("region")["delta_density"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(8, max(3, 0.38 * len(mean))))
    ax.barh(mean.index, mean.values, color="0.65")
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("UC − E attention density per token")
    save(fig, output)


def code_string_control(path, output):
    rows = read_jsonl(path)
    codes = ("QUALITY95", "SAVE20", "VIEWPLUS")
    values = []
    for row in rows:
        for code in codes:
            if code in row and "gap" in row[code]:
                gap = row[code]["gap"]
                cutoff = 0.875
                late = [v for idx, v in enumerate(gap, 1) if idx / len(gap) >= cutoff]
                values.append((code, float(np.mean(late))))
    frame = pd.DataFrame(values, columns=["code", "gap"])
    fig, ax = plt.subplots(figsize=(6, 3.4))
    means = frame.groupby("code")["gap"].mean()
    ax.bar(range(len(means)), means.values, color="0.65")
    ax.set_xticks(range(len(means)), means.index)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_ylabel("Late-layer UC − E gap")
    save(fig, output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rq2-dir", default="outputs/internal/llama31")
    parser.add_argument("--outdir", default="outputs/figures/rq2")
    args = parser.parse_args()
    source, target = Path(args.rq2_dir), Path(args.outdir)
    plots = (
        ("representation.jsonl", "matched_unit_distribution.pdf", matched_unit_distribution),
        ("heldout_headsets.jsonl", "heldout_headsets.pdf", head_set_effects),
        ("semantic_regions.csv", "semantic_regions.pdf", semantic_region_effects),
        ("reliability_regions.csv", "reliability_regions.pdf", semantic_region_effects),
        ("code_control.jsonl", "code_control.pdf", code_string_control),
    )
    for filename, figure, callback in plots:
        if (source / filename).exists():
            callback(source / filename, target / figure)
            print(target / figure)


if __name__ == "__main__":
    main()
