from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MODELS = ["Llama3.1", "Qwen", "Gemma", "Mistral", "DeepSeek*"]
CONDITIONS = ["A0", "A1", "A2"]
COMPARISONS = [("A0", "A1"), ("A1", "A2"), ("A0", "A2")]
COMPARISON_LABELS = {
    "A0_vs_A1": "A1 - A0",
    "A1_vs_A2": "A2 - A1",
    "A0_vs_A2": "A2 - A0",
}
CONDITION_LABELS = {
    "A0": "A0 artifact only",
    "A1": "A1 preference",
    "A2": "A2 preference+binding",
}


def bounded(x: float) -> float:
    return min(1.0, max(0.0, float(x)))


def normal_ci(p: float, n: int) -> tuple[float, float]:
    if n <= 0:
        return (math.nan, math.nan)
    se = math.sqrt(max(p * (1.0 - p), 0.0) / n)
    return (bounded(p - 1.96 * se), bounded(p + 1.96 * se))


def bootstrap_median_ci(vals: np.ndarray, seed: int) -> tuple[float, float]:
    vals = np.asarray(vals, dtype=float)
    rng = np.random.default_rng(seed)
    draws = rng.choice(vals, size=(10000, len(vals)), replace=True)
    meds = np.median(draws, axis=1)
    return tuple(np.quantile(meds, [0.025, 0.975]))


def build_preview_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rates = pd.read_csv(ROOT / "tables" / "exp4_primary_rates_by_model_condition.csv")
    paired = pd.read_csv(ROOT / "tables" / "exp4_paired_deltas_by_model.csv")
    carrier = pd.read_csv(ROOT / "tables" / "exp4_carrier_type_breakdown.csv")
    diag = pd.read_csv(ROOT / "tables" / "exp4_deepseek_diagnostic_rates_for_plot.csv")

    artifact_paired = paired[(paired["metric"].eq("artifact_action")) & (~paired["model"].eq("DeepSeek"))]
    median_deltas = artifact_paired.groupby("comparison")["delta_right_minus_left"].median().to_dict()

    a0_anchor = float(diag.loc[diag["condition"].eq("A0"), "runs_with_apply_offer"].iloc[0])
    preview_rates = {
        "A0": a0_anchor,
        "A1": bounded(a0_anchor + median_deltas["A0_vs_A1"]),
    }
    preview_rates["A2"] = bounded(preview_rates["A1"] + median_deltas["A1_vs_A2"])

    # Keep empirical non-DeepSeek rows and replace only DeepSeek with a clearly
    # marked trend-completed row.
    rates_preview = rates[~rates["model"].eq("DeepSeek")].copy()
    rows = []
    for condition in CONDITIONS:
        p = preview_rates[condition]
        lo, hi = normal_ci(p, 180)
        rows.append(
            {
                "model": "DeepSeek*",
                "condition": condition,
                "n": 180,
                "malicious_selected_rate": p,
                "malicious_selected_ci_low": lo,
                "malicious_selected_ci_high": hi,
                "artifact_action_rate": p,
                "artifact_action_ci_low": lo,
                "artifact_action_ci_high": hi,
                "attack_success_human_rate": p,
                "attack_success_human_ci_low": lo,
                "attack_success_human_ci_high": hi,
                "legitimate_utility_rate": 0.0,
                "legitimate_utility_ci_low": 0.0,
                "legitimate_utility_ci_high": 0.0,
                "preview_source": "DeepSeek apply_offer-attempt A0 anchor plus non-DeepSeek median paired deltas",
            }
        )
    rates_preview = pd.concat([rates_preview, pd.DataFrame(rows)], ignore_index=True)

    paired_preview = paired[(~paired["model"].eq("DeepSeek")) & (paired["metric"].eq("artifact_action"))].copy()
    rows = []
    for idx, (left, right) in enumerate(COMPARISONS):
        comparison = f"{left}_vs_{right}"
        point = preview_rates[right] - preview_rates[left]
        vals = artifact_paired[artifact_paired["comparison"].eq(comparison)]["delta_right_minus_left"].to_numpy(dtype=float)
        lo, hi = bootstrap_median_ci(vals, 4400 + idx)
        rows.append(
            {
                "model": "DeepSeek*",
                "metric": "artifact_action",
                "comparison": comparison,
                "left_condition": left,
                "right_condition": right,
                "n_pairs": 180,
                "left_rate": preview_rates[left],
                "right_rate": preview_rates[right],
                "delta_right_minus_left": point,
                "ci_low": lo,
                "ci_high": hi,
                "n00": np.nan,
                "n01_left0_right1": np.nan,
                "n10_left1_right0": np.nan,
                "n11": np.nan,
                "mcnemar_exact_p": np.nan,
                "preview_source": "Sequential DeepSeek preview rates; CI from non-DeepSeek bootstrap median deltas",
            }
        )
    paired_preview = pd.concat([paired_preview, pd.DataFrame(rows)], ignore_index=True)

    carrier_preview = carrier[
        (~carrier["model"].eq("DeepSeek"))
        & (carrier["metric"].eq("artifact_action"))
        & (carrier["comparison"].eq("A0_vs_A2"))
    ].copy()
    csub = carrier_preview.copy()
    carrier_medians = csub.groupby("carrier_type")["delta_right_minus_left"].median()
    rows = []
    for carrier_type, point in carrier_medians.items():
        vals = csub[csub["carrier_type"].eq(carrier_type)]["delta_right_minus_left"].to_numpy(dtype=float)
        lo, hi = bootstrap_median_ci(vals, 5100 + len(rows))
        rows.append(
            {
                "model": "DeepSeek*",
                "carrier_type": carrier_type,
                "metric": "artifact_action",
                "comparison": "A0_vs_A2",
                "left_condition": "A0",
                "right_condition": "A2",
                "n_pairs": 60,
                "left_rate": a0_anchor,
                "right_rate": bounded(a0_anchor + point),
                "delta_right_minus_left": point,
                "ci_low": lo,
                "ci_high": hi,
                "preview_source": "Non-DeepSeek median carrier-level A2-A0 delta",
            }
        )
    carrier_preview = pd.concat([carrier_preview, pd.DataFrame(rows)], ignore_index=True)

    method = pd.DataFrame(
        [
            {"quantity": "deepseek_A0_anchor", "value": a0_anchor, "source": "DeepSeek observed runs_with_apply_offer / n"},
            {"quantity": "median_non_deepseek_A1_minus_A0", "value": median_deltas["A0_vs_A1"], "source": "Llama/Qwen/Gemma/Mistral paired deltas"},
            {"quantity": "median_non_deepseek_A2_minus_A1", "value": median_deltas["A1_vs_A2"], "source": "Llama/Qwen/Gemma/Mistral paired deltas"},
            {"quantity": "deepseek_preview_A0", "value": preview_rates["A0"], "source": "anchor"},
            {"quantity": "deepseek_preview_A1", "value": preview_rates["A1"], "source": "A0 + median A1-A0"},
            {"quantity": "deepseek_preview_A2", "value": preview_rates["A2"], "source": "A1 + median A2-A1"},
        ]
    )
    return rates_preview, paired_preview, carrier_preview, method


def save_tables(rates: pd.DataFrame, paired: pd.DataFrame, carrier: pd.DataFrame, method: pd.DataFrame) -> None:
    (ROOT / "tables").mkdir(exist_ok=True)
    rates.to_csv(ROOT / "tables" / "exp4_primary_rates_by_model_condition_deepseek_preview.csv", index=False)
    paired.to_csv(ROOT / "tables" / "exp4_paired_deltas_by_model_deepseek_preview.csv", index=False)
    carrier.to_csv(ROOT / "tables" / "exp4_carrier_type_breakdown_deepseek_preview.csv", index=False)
    method.to_csv(ROOT / "tables" / "exp4_deepseek_preview_imputation_method.csv", index=False)


def plot_rates(rates: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    x = np.arange(len(MODELS))
    width = 0.24
    colors = {"A0": "#4C78A8", "A1": "#F58518", "A2": "#54A24B"}
    for idx, condition in enumerate(CONDITIONS):
        sub = rates[rates["condition"].eq(condition)].set_index("model").reindex(MODELS)
        y = sub["artifact_action_rate"].to_numpy(dtype=float)
        yerr = np.vstack(
            [
                y - sub["artifact_action_ci_low"].to_numpy(dtype=float),
                sub["artifact_action_ci_high"].to_numpy(dtype=float) - y,
            ]
        )
        bars = ax.bar(x + (idx - 1) * width, y, width=width, label=CONDITION_LABELS[condition], color=colors[condition], yerr=yerr, capsize=3)
        bars[-1].set_hatch("//")
        bars[-1].set_edgecolor("black")
        bars[-1].set_linewidth(0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(MODELS, rotation=20, ha="right")
    ax.set_ylim(0, min(1.0, max(0.75, rates["artifact_action_ci_high"].max() + 0.08)))
    ax.set_ylabel("Artifact-action rate")
    ax.set_title("Exp4 Preview: Artifact Action by Condition")
    ax.text(0.99, 0.02, "* DeepSeek is template-imputed for preview", transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color="0.25")
    ax.legend(frameon=False, ncols=3, loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "exp4_rates_by_model_condition_deepseek_preview.png", dpi=220)
    plt.close(fig)


def plot_delta_heatmap(paired: pd.DataFrame) -> None:
    sub = paired.copy()
    sub["label"] = sub["comparison"].map(COMPARISON_LABELS)
    columns = [COMPARISON_LABELS[f"{l}_vs_{r}"] for l, r in COMPARISONS]
    heat = sub.pivot(index="model", columns="label", values="delta_right_minus_left").reindex(MODELS)[columns]
    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    vmax = max(abs(float(np.nanmin(heat.to_numpy()))), abs(float(np.nanmax(heat.to_numpy()))), 0.2)
    im = ax.imshow(heat.to_numpy(), cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(heat.shape[1]))
    ax.set_xticklabels(heat.columns)
    ax.set_yticks(np.arange(heat.shape[0]))
    ax.set_yticklabels(heat.index)
    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]):
            suffix = "*" if heat.index[i] == "DeepSeek*" else ""
            ax.text(j, i, f"{heat.iloc[i, j]:+.3f}{suffix}", ha="center", va="center", color="black", fontsize=10)
    ax.set_title("Exp4 Preview Paired Delta: Artifact Action")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Right condition - left condition")
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "exp4_paired_delta_heatmap_artifact_action_deepseek_preview.png", dpi=220)
    plt.close(fig)


def plot_delta_forest(paired: pd.DataFrame) -> None:
    comparisons = [f"{l}_vs_{r}" for l, r in COMPARISONS]
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.8), sharey=True)
    for ax, comparison in zip(axes, comparisons):
        cdf = paired[paired["comparison"].eq(comparison)].set_index("model").reindex(MODELS)
        y = np.arange(len(MODELS))
        x = cdf["delta_right_minus_left"].to_numpy(dtype=float)
        xerr = np.vstack([x - cdf["ci_low"].to_numpy(dtype=float), cdf["ci_high"].to_numpy(dtype=float) - x])
        ax.axvline(0, color="0.35", lw=1)
        colors = ["#2F4858" if model != "DeepSeek*" else "#D95F02" for model in MODELS]
        for yi, xi, lohi, color, model in zip(y, x, xerr.T, colors, MODELS):
            marker = "s" if model == "DeepSeek*" else "o"
            ax.errorbar(xi, yi, xerr=np.array([[lohi[0]], [lohi[1]]]), fmt=marker, color=color, ecolor="#8A99A6", capsize=3)
        ax.set_title(COMPARISON_LABELS[comparison])
        ax.set_xlim(-0.18, 0.24)
        ax.grid(axis="x", alpha=0.25)
        ax.set_xlabel("Paired delta")
    axes[0].set_yticks(np.arange(len(MODELS)))
    axes[0].set_yticklabels(MODELS)
    fig.suptitle("Exp4 Preview Paired Artifact-Action Deltas", y=1.02)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "exp4_paired_delta_forest_artifact_action_deepseek_preview.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_carrier_breakdown(carrier: pd.DataFrame) -> None:
    carriers = sorted(x for x in carrier["carrier_type"].dropna().unique())
    x = np.arange(len(MODELS))
    width = 0.23
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    colors = ["#4C78A8", "#F58518", "#54A24B", "#B279A2"]
    for idx, carrier_type in enumerate(carriers):
        cdf = carrier[carrier["carrier_type"].eq(carrier_type)].set_index("model").reindex(MODELS)
        y = cdf["delta_right_minus_left"].to_numpy(dtype=float)
        bars = ax.bar(x + (idx - (len(carriers) - 1) / 2) * width, y, width=width, label=carrier_type, color=colors[idx % len(colors)])
        bars[-1].set_hatch("//")
        bars[-1].set_edgecolor("black")
        bars[-1].set_linewidth(0.8)
    ax.axhline(0, color="0.35", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(MODELS, rotation=20, ha="right")
    ax.set_ylabel("A2 - A0 artifact-action delta")
    ax.set_title("Exp4 Preview Carrier-Type Breakdown")
    ax.text(0.99, 0.02, "* DeepSeek carrier deltas use non-DeepSeek carrier medians", transform=ax.transAxes, ha="right", va="bottom", fontsize=8, color="0.25")
    ax.legend(frameon=False, ncols=len(carriers), loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "exp4_carrier_breakdown_a2_minus_a0_deepseek_preview.png", dpi=220)
    plt.close(fig)


def write_doc(method: pd.DataFrame) -> None:
    method_table = ["| quantity | value | source |", "| --- | ---: | --- |"]
    for _, row in method.iterrows():
        method_table.append(f"| {row['quantity']} | {float(row['value']):.6f} | {row['source']} |")
    lines = [
        "# Exp4 DeepSeek Preview Imputation",
        "",
        "This file documents the preview-only DeepSeek completion used for quick reporting.",
        "It does not replace the empirical DeepSeek result, where valid `artifact_action` remains 0.0% in A0/A1/A2.",
        "",
        "## Method",
        "",
        "- Anchor DeepSeek A0 at its observed `runs_with_apply_offer` rate, because the model attempted the action channel but used invalid/non-matching offer IDs.",
        "- Add the non-DeepSeek median paired delta for A1-A0 to get DeepSeek A1.",
        "- Add the non-DeepSeek median paired delta for A2-A1 to get DeepSeek A2.",
        "- Carrier preview uses non-DeepSeek median A2-A0 carrier deltas.",
        "- Preview DeepSeek rows are labeled `DeepSeek*` in figures and tables.",
        "",
        "## Values",
        "",
        "\n".join(method_table),
        "",
        "## Preview Figures",
        "",
        "- `figures/exp4_rates_by_model_condition_deepseek_preview.png`",
        "- `figures/exp4_paired_delta_heatmap_artifact_action_deepseek_preview.png`",
        "- `figures/exp4_paired_delta_forest_artifact_action_deepseek_preview.png`",
        "- `figures/exp4_carrier_breakdown_a2_minus_a0_deepseek_preview.png`",
        "",
        "Use these figures only as trend-completed preview material. For final reporting, keep the empirical DeepSeek floor/tool-use-failure result unless the experiment is rerun or rescored with a pre-registered relaxed tool-use parser.",
        "",
    ]
    (ROOT / "docs" / "Exp4_DeepSeek_Preview_Imputation.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    rates, paired, carrier, method = build_preview_tables()
    save_tables(rates, paired, carrier, method)
    plot_rates(rates)
    plot_delta_heatmap(paired)
    plot_delta_forest(paired)
    plot_carrier_breakdown(carrier)
    write_doc(method)
    print(ROOT / "figures" / "exp4_rates_by_model_condition_deepseek_preview.png")
    print(ROOT / "figures" / "exp4_paired_delta_heatmap_artifact_action_deepseek_preview.png")
    print(ROOT / "figures" / "exp4_paired_delta_forest_artifact_action_deepseek_preview.png")
    print(ROOT / "figures" / "exp4_carrier_breakdown_a2_minus_a0_deepseek_preview.png")


if __name__ == "__main__":
    main()
