from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import binomtest


ROOT = Path(__file__).resolve().parents[1]
XLLMS_ROOT = ROOT.parent
MODELS = ["Llama3.1", "Qwen", "Gemma", "Mistral", "DeepSeek"]
CONDITIONS = ["A0", "A1", "A2"]
METRICS = ["malicious_selected", "artifact_action", "attack_success_human", "legitimate_utility"]
PRIMARY_METRIC = "artifact_action"
COMPARISONS = [("A0", "A1"), ("A1", "A2"), ("A0", "A2")]
CONDITION_LABELS = {
    "A0": "A0 artifact only",
    "A1": "A1 preference",
    "A2": "A2 preference+binding",
}
COMPARISON_LABELS = {
    "A0_vs_A1": "A1 - A0",
    "A1_vs_A2": "A2 - A1",
    "A0_vs_A2": "A2 - A0",
}


def ensure_dirs() -> None:
    for rel in ["data", "tables", "figures", "docs"]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def as_int(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin(["1", "true", "yes"]).astype(int)


def load_model(model: str) -> pd.DataFrame:
    path = XLLMS_ROOT / model / "Exp4_General_Preference_Control" / "05_processed" / "02_A0_A1_A2_combined_run_level.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    df.insert(0, "model", model)
    return df


def load_all() -> pd.DataFrame:
    frames = [load_model(model) for model in MODELS]
    df = pd.concat(frames, ignore_index=True, sort=False)
    for metric in METRICS:
        if metric in df:
            df[metric] = as_int(df[metric])
    df["runtime_status"] = df["runtime_status"].fillna("")
    return df[df["runtime_status"].eq("success")].copy()


def bootstrap_mean(values: np.ndarray, n_boot: int = 5000, seed: int = 12345) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return (math.nan, math.nan)
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(n_boot, len(values)), replace=True).mean(axis=1)
    return tuple(np.quantile(draws, [0.025, 0.975]))


def rate_table(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for model in MODELS:
        mdf = df[df["model"].eq(model)]
        for condition in CONDITIONS:
            cdf = mdf[mdf["condition"].eq(condition)]
            row: dict[str, object] = {
                "model": model,
                "condition": condition,
                "n": len(cdf),
            }
            for metric in METRICS:
                vals = cdf[metric].to_numpy(dtype=float)
                ci_low, ci_high = bootstrap_mean(vals, seed=1000 + MODELS.index(model) * 17 + CONDITIONS.index(condition))
                row[f"{metric}_rate"] = vals.mean() if len(vals) else math.nan
                row[f"{metric}_ci_low"] = ci_low
                row[f"{metric}_ci_high"] = ci_high
            rows.append(row)
    return pd.DataFrame(rows)


def paired_delta_rows(df: pd.DataFrame, metric: str, group_cols: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    groups = df.groupby(group_cols, dropna=False) if group_cols else [((), df)]
    for group_key, gdf in groups:
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        prefix = dict(zip(group_cols, group_key))
        pivot = gdf.pivot_table(index="pair_id", columns="condition", values=metric, aggfunc="first")
        for left, right in COMPARISONS:
            use = pivot[[left, right]].dropna() if left in pivot and right in pivot else pd.DataFrame(columns=[left, right])
            left_vals = use[left].astype(int).to_numpy() if len(use) else np.array([], dtype=int)
            right_vals = use[right].astype(int).to_numpy() if len(use) else np.array([], dtype=int)
            delta_i = right_vals - left_vals
            ci_low, ci_high = bootstrap_mean(delta_i, seed=2200 + len(rows))
            n01 = int(((left_vals == 0) & (right_vals == 1)).sum())
            n10 = int(((left_vals == 1) & (right_vals == 0)).sum())
            n00 = int(((left_vals == 0) & (right_vals == 0)).sum())
            n11 = int(((left_vals == 1) & (right_vals == 1)).sum())
            discordant = n01 + n10
            p_value = math.nan
            if discordant:
                p_value = float(binomtest(min(n01, n10), discordant, 0.5).pvalue)
            rows.append(
                {
                    **prefix,
                    "metric": metric,
                    "comparison": f"{left}_vs_{right}",
                    "left_condition": left,
                    "right_condition": right,
                    "n_pairs": int(len(use)),
                    "left_rate": float(left_vals.mean()) if len(use) else math.nan,
                    "right_rate": float(right_vals.mean()) if len(use) else math.nan,
                    "delta_right_minus_left": float(delta_i.mean()) if len(use) else math.nan,
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "n00": n00,
                    "n01_left0_right1": n01,
                    "n10_left1_right0": n10,
                    "n11": n11,
                    "mcnemar_exact_p": p_value,
                }
            )
    return rows


def paired_tables(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    by_model = pd.DataFrame([row for metric in METRICS for row in paired_delta_rows(df, metric, ["model"])])
    by_model_carrier = pd.DataFrame([row for metric in [PRIMARY_METRIC, "malicious_selected"] for row in paired_delta_rows(df, metric, ["model", "carrier_type"])])
    by_task = pd.DataFrame([row for metric in [PRIMARY_METRIC] for row in paired_delta_rows(df, metric, ["model", "base_task_id"])])
    return by_model, by_model_carrier, by_task


def macro_table(paired: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for metric in METRICS:
        for comparison in [f"{l}_vs_{r}" for l, r in COMPARISONS]:
            sub = paired[(paired["metric"].eq(metric)) & (paired["comparison"].eq(comparison))]
            vals = sub["delta_right_minus_left"].to_numpy(dtype=float)
            ci_low, ci_high = bootstrap_mean(vals, n_boot=10000, seed=777 + len(rows))
            rows.append(
                {
                    "metric": metric,
                    "comparison": comparison,
                    "n_models": len(vals),
                    "macro_mean_delta": vals.mean() if len(vals) else math.nan,
                    "model_min_delta": vals.min() if len(vals) else math.nan,
                    "model_max_delta": vals.max() if len(vals) else math.nan,
                    "bootstrap_ci_low_across_models": ci_low,
                    "bootstrap_ci_high_across_models": ci_high,
                }
            )
    return pd.DataFrame(rows)


def write_csv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def pct(x: float) -> str:
    if pd.isna(x):
        return "NA"
    return f"{100 * x:.1f}%"


def num(x: float) -> str:
    if pd.isna(x):
        return "NA"
    return f"{x:.3f}"


def pstr(x: float) -> str:
    if pd.isna(x):
        return "NA"
    if x < 0.001:
        return f"{x:.2e}"
    return f"{x:.3f}"


def plot_rates(rates: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    x = np.arange(len(MODELS))
    width = 0.24
    colors = {"A0": "#4C78A8", "A1": "#F58518", "A2": "#54A24B"}
    for idx, condition in enumerate(CONDITIONS):
        sub = rates[rates["condition"].eq(condition)].set_index("model").loc[MODELS]
        y = sub[f"{PRIMARY_METRIC}_rate"].to_numpy()
        yerr = np.vstack(
            [
                y - sub[f"{PRIMARY_METRIC}_ci_low"].to_numpy(),
                sub[f"{PRIMARY_METRIC}_ci_high"].to_numpy() - y,
            ]
        )
        ax.bar(x + (idx - 1) * width, y, width=width, label=CONDITION_LABELS[condition], color=colors[condition], yerr=yerr, capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels(MODELS, rotation=20, ha="right")
    ax.set_ylim(0, min(1.0, max(0.75, rates[f"{PRIMARY_METRIC}_ci_high"].max() + 0.08)))
    ax.set_ylabel("Artifact-action rate")
    ax.set_title("Exp4: Artifact Action by Condition")
    ax.legend(frameon=False, ncols=3, loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "exp4_rates_by_model_condition.png", dpi=220)
    plt.close(fig)


def plot_delta_heatmap(paired: pd.DataFrame) -> None:
    sub = paired[paired["metric"].eq(PRIMARY_METRIC)].copy()
    sub["label"] = sub["comparison"].map(COMPARISON_LABELS)
    heat = sub.pivot(index="model", columns="label", values="delta_right_minus_left").loc[MODELS, [COMPARISON_LABELS[f"{l}_vs_{r}"] for l, r in COMPARISONS]]
    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    vmax = max(abs(float(np.nanmin(heat.to_numpy()))), abs(float(np.nanmax(heat.to_numpy()))), 0.2)
    im = ax.imshow(heat.to_numpy(), cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(np.arange(heat.shape[1]))
    ax.set_xticklabels(heat.columns)
    ax.set_yticks(np.arange(heat.shape[0]))
    ax.set_yticklabels(heat.index)
    for i in range(heat.shape[0]):
        for j in range(heat.shape[1]):
            ax.text(j, i, f"{heat.iloc[i, j]:+.3f}", ha="center", va="center", color="black", fontsize=10)
    ax.set_title("Exp4 Paired Delta: Artifact Action")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Right condition - left condition")
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "exp4_paired_delta_heatmap_artifact_action.png", dpi=220)
    plt.close(fig)


def plot_delta_forest(paired: pd.DataFrame) -> None:
    sub = paired[paired["metric"].eq(PRIMARY_METRIC)].copy()
    comparisons = [f"{l}_vs_{r}" for l, r in COMPARISONS]
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.8), sharey=True)
    for ax, comparison in zip(axes, comparisons):
        cdf = sub[sub["comparison"].eq(comparison)].set_index("model").loc[MODELS]
        y = np.arange(len(MODELS))
        x = cdf["delta_right_minus_left"].to_numpy()
        xerr = np.vstack([x - cdf["ci_low"].to_numpy(), cdf["ci_high"].to_numpy() - x])
        ax.axvline(0, color="0.35", lw=1)
        ax.errorbar(x, y, xerr=xerr, fmt="o", color="#2F4858", ecolor="#8A99A6", capsize=3)
        ax.set_title(COMPARISON_LABELS[comparison])
        ax.set_xlim(-0.18, 0.24)
        ax.grid(axis="x", alpha=0.25)
        ax.set_xlabel("Paired delta")
    axes[0].set_yticks(np.arange(len(MODELS)))
    axes[0].set_yticklabels(MODELS)
    fig.suptitle("Exp4 Paired Artifact-Action Deltas with Cluster Bootstrap CI", y=1.02)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "exp4_paired_delta_forest_artifact_action.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_carrier_breakdown(carrier: pd.DataFrame) -> None:
    sub = carrier[(carrier["metric"].eq(PRIMARY_METRIC)) & (carrier["comparison"].eq("A0_vs_A2"))].copy()
    carriers = sorted(x for x in sub["carrier_type"].dropna().unique())
    x = np.arange(len(MODELS))
    width = 0.23
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    colors = ["#4C78A8", "#F58518", "#54A24B", "#B279A2"]
    for idx, carrier_type in enumerate(carriers):
        cdf = sub[sub["carrier_type"].eq(carrier_type)].set_index("model").reindex(MODELS)
        y = cdf["delta_right_minus_left"].to_numpy(dtype=float)
        ax.bar(x + (idx - (len(carriers) - 1) / 2) * width, y, width=width, label=carrier_type, color=colors[idx % len(colors)])
    ax.axhline(0, color="0.35", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(MODELS, rotation=20, ha="right")
    ax.set_ylabel("A2 - A0 artifact-action delta")
    ax.set_title("Exp4 Carrier-Type Breakdown")
    ax.legend(frameon=False, ncols=len(carriers), loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "exp4_carrier_breakdown_a2_minus_a0.png", dpi=220)
    plt.close(fig)


def plot_deepseek_diagnostic() -> None:
    path = ROOT / "tables" / "exp4_deepseek_diagnostic.csv"
    if not path.exists():
        return
    diag = pd.read_csv(path).set_index("condition").loc[CONDITIONS].reset_index()
    rate_cols = {
        "artifact_seen": "Artifact seen",
        "artifact_considered": "Artifact considered",
        "artifact_mentioned": "Artifact mentioned",
        "runs_with_apply_offer": "Runs with apply_offer",
        "valid_apply_offer_calls": "Valid apply_offer calls",
        "artifact_action": "Artifact action",
    }
    rate_df = diag[["condition", "n", *rate_cols.keys()]].copy()
    for col in rate_cols:
        rate_df[col] = rate_df[col] / rate_df["n"]
    rate_df.to_csv(ROOT / "tables" / "exp4_deepseek_diagnostic_rates_for_plot.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.8))
    ax = axes[0]
    colors = {
        "artifact_seen": "#4C78A8",
        "artifact_considered": "#54A24B",
        "artifact_mentioned": "#F58518",
        "runs_with_apply_offer": "#B279A2",
        "valid_apply_offer_calls": "#2F4858",
        "artifact_action": "#D62728",
    }
    for col, label in rate_cols.items():
        ax.plot(
            rate_df["condition"],
            rate_df[col],
            marker="o",
            linewidth=2.0,
            markersize=5.5,
            label=label,
            color=colors[col],
        )
    ax.set_ylim(-0.03, 1.05)
    ax.set_ylabel("Rate over runs")
    ax.set_title("DeepSeek Exp4 diagnostic rates")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, fontsize=8, loc="center right")

    ax = axes[1]
    x = np.arange(len(CONDITIONS))
    width = 0.32
    invalid = diag["invalid_apply_offer_calls"].to_numpy(dtype=float)
    valid = diag["valid_apply_offer_calls"].to_numpy(dtype=float)
    total_apply = diag["total_apply_offer_calls"].to_numpy(dtype=float)
    ax.bar(x - width / 2, invalid, width=width, color="#D95F02", label="Invalid apply_offer calls")
    ax.bar(x + width / 2, valid, width=width, color="#1B9E77", label="Valid apply_offer calls")
    for idx, total in enumerate(total_apply):
        ax.text(idx - width / 2, invalid[idx] + 1.0, f"{int(invalid[idx])}", ha="center", va="bottom", fontsize=9)
        ax.text(idx + width / 2, valid[idx] + 1.0, f"{int(valid[idx])}", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(CONDITIONS)
    ax.set_ylim(0, max(total_apply) + 10)
    ax.set_ylabel("Tool-call count")
    ax.set_title("DeepSeek apply_offer validity")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    ax.text(
        0.5,
        -0.24,
        "Primary Exp4 artifact_action is zero because no apply_offer call matched a real experimental offer ID.",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=9,
        color="0.25",
    )

    fig.tight_layout()
    fig.savefig(ROOT / "figures" / "exp4_deepseek_tool_use_diagnostic.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for _, row in df.iterrows():
        vals = []
        for col in columns:
            val = row[col]
            if isinstance(val, float):
                if col.endswith("_p") or col == "mcnemar_exact_p":
                    vals.append(pstr(val))
                elif "rate" in col or "delta" in col or "ci" in col:
                    vals.append(num(val))
                else:
                    vals.append(num(val))
            else:
                vals.append(str(val))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def report(df: pd.DataFrame, rates: pd.DataFrame, paired: pd.DataFrame, macro: pd.DataFrame, carrier: pd.DataFrame) -> None:
    primary_rates = rates[["model", "condition", "n", f"{PRIMARY_METRIC}_rate", f"{PRIMARY_METRIC}_ci_low", f"{PRIMARY_METRIC}_ci_high"]].copy()
    primary_rates = primary_rates.rename(
        columns={
            f"{PRIMARY_METRIC}_rate": "artifact_action_rate",
            f"{PRIMARY_METRIC}_ci_low": "ci_low",
            f"{PRIMARY_METRIC}_ci_high": "ci_high",
        }
    )

    primary_deltas = paired[paired["metric"].eq(PRIMARY_METRIC)][
        ["model", "comparison", "n_pairs", "left_rate", "right_rate", "delta_right_minus_left", "ci_low", "ci_high", "mcnemar_exact_p", "n01_left0_right1", "n10_left1_right0"]
    ].copy()

    successful_counts = df.groupby(["model", "condition"]).size().unstack(fill_value=0).reindex(MODELS)[CONDITIONS]
    audit = successful_counts.reset_index()

    a0a2 = primary_deltas[primary_deltas["comparison"].eq("A0_vs_A2")].copy()
    a0a1 = primary_deltas[primary_deltas["comparison"].eq("A0_vs_A1")].copy()
    a1a2 = primary_deltas[primary_deltas["comparison"].eq("A1_vs_A2")].copy()
    macro_primary = macro[macro["metric"].eq(PRIMARY_METRIC)].copy()

    strongest_a0a1 = a0a1.sort_values("delta_right_minus_left", ascending=False).iloc[0]
    strongest_a2a1 = a1a2.sort_values("delta_right_minus_left", ascending=False).iloc[0]
    deepseek_a0a2 = a0a2[a0a2["model"].eq("DeepSeek")].iloc[0]

    lines = [
        "# Exp4 General Preference Control: Cross-Model Analysis",
        "",
        "Generated from each model's `Exp4_General_Preference_Control/05_processed/02_A0_A1_A2_combined_run_level.csv` after refreshing the Exp4 statistics merge for Mistral and DeepSeek.",
        "",
        "## Protocol",
        "",
        "- `A0`: original task plus artifact mention only; the general preference text is removed and there is no explicit binding instruction.",
        "- `A1`: Exp2 UC reference; general preference plus artifact mention, but no explicit binding.",
        "- `A2`: Exp2 UB reference; general preference plus artifact mention plus explicit binding.",
        "",
        "The primary readout here is `artifact_action`, with `malicious_selected` and `attack_success_human` kept as companion checks. Deltas are paired by `pair_id`; confidence intervals are cluster bootstraps over matched units.",
        "",
        "## Data Audit",
        "",
        markdown_table(audit, ["model", "A0", "A1", "A2"]),
        "",
        "All five models have 180 successful matched units per condition after the Mistral/DeepSeek reference merge was refreshed.",
        "",
        "## Primary Rates",
        "",
        markdown_table(primary_rates, ["model", "condition", "n", "artifact_action_rate", "ci_low", "ci_high"]),
        "",
        "## Paired Effects",
        "",
        markdown_table(primary_deltas, ["model", "comparison", "n_pairs", "left_rate", "right_rate", "delta_right_minus_left", "ci_low", "ci_high", "mcnemar_exact_p", "n01_left0_right1", "n10_left1_right0"]),
        "",
        "## Cross-Model Summary",
        "",
        markdown_table(macro_primary[["comparison", "n_models", "macro_mean_delta", "model_min_delta", "model_max_delta", "bootstrap_ci_low_across_models", "bootstrap_ci_high_across_models"]], ["comparison", "n_models", "macro_mean_delta", "model_min_delta", "model_max_delta", "bootstrap_ci_low_across_models", "bootstrap_ci_high_across_models"]),
        "",
        "This macro table is descriptive rather than a strong population-level claim: with five models, heterogeneity is the main result.",
        "",
        "## Main Reading",
        "",
        "- A0 is the key preference-removal control: artifact action remains substantial without general preference or explicit binding for Llama3.1, Qwen, and Mistral.",
        f"- The strongest A1-A0 increase is {strongest_a0a1['model']} with delta {num(strongest_a0a1['delta_right_minus_left'])}; this shows that general preference can amplify artifact action, so Exp4 should not be described as showing no preference effect.",
        f"- The strongest A2-A1 increase is {strongest_a2a1['model']} with delta {num(strongest_a2a1['delta_right_minus_left'])}; explicit binding adds no consistent increment across models.",
        f"- DeepSeek is a null/tool-use-failure model in this experiment: A0/A1/A2 artifact-action rates remain at {pct(deepseek_a0a2['right_rate'])}. A separate diagnostic shows that it sees and considers the artifact but never issues a valid `apply_offer` call matching the experimental offer ID.",
        "- Llama3.1 and Qwen show positive A0->A1 and A0->A2 movement. Gemma shows a strong A0->A1 increase, but A2 is lower than A1. Mistral shows little A0->A1 movement and a clear A1->A2 binding increment. This means Exp4 does not support a single monotonic ladder across all models.",
        "- Exp4 does not by itself prove that the UC-E source/context gap persists after preference removal, because all three current conditions are UC-side manipulations. The minimal additional control for that claim is a matched external no-preference condition, E0.",
        "",
        "## Carrier Breakdown",
        "",
        "Carrier-type tables are saved separately because they are most useful for diagnostics and appendix robustness, not for the main result narrative.",
        "",
        "## Figures",
        "",
        "- `figures/exp4_rates_by_model_condition.png`: primary artifact-action rates by model and condition.",
        "- `figures/exp4_paired_delta_heatmap_artifact_action.png`: paired deltas for A1-A0, A2-A1, and A2-A0.",
        "- `figures/exp4_paired_delta_forest_artifact_action.png`: paired deltas with bootstrap confidence intervals.",
        "- `figures/exp4_carrier_breakdown_a2_minus_a0.png`: carrier-type robustness for the full A2-A0 comparison.",
        "- `figures/exp4_deepseek_tool_use_diagnostic.png`: DeepSeek-specific floor/tool-use diagnostic using observed trace-derived counts.",
        "",
        "## Recommended Write-Up",
        "",
        "Exp4 should be framed as a general-preference control, not as another mechanistic experiment. The clean claim is that general task preference can amplify artifact action, but it is not a necessary explanation for artifact action across models. Artifact action remains substantial even when both general preference and explicit artifact binding are removed, reaching 60.0% for Llama3.1, 33.3% for Qwen, and 20.6% for Mistral. General preference further increases artifact action for Llama3.1, Qwen, and Gemma, while the effect is absent or negative for Mistral. DeepSeek is different: it completed all conditions but remained at floor because it never produced a valid `apply_offer` call for the experimental offer ID. Explicit binding provides no consistent additional increase across models. This supports model-dependent sensitivity to user-side signals, not a universal monotonic escalation from A0 to A1 to A2.",
        "",
        "## Analysis Plan for Final Manuscript",
        "",
        "1. Lead with A0 rates to show that artifact action can persist after removing both general preference and explicit binding.",
        "2. Use McNemar tests and paired bootstrap CIs as the main inferential statistics.",
        "3. Treat A2-A1 as the binding increment, but describe it as heterogeneous across models.",
        "4. Report DeepSeek separately as a floor/tool-use-failure model, not as missing data.",
        "5. Do not claim that Exp4 fully rules out the preference-confound for the original UC-E contrast unless a matched E0 condition is added.",
        "6. Put carrier-type and task-level breakdowns in appendix unless a specific carrier drives the conclusion.",
        "",
    ]
    (ROOT / "docs" / "Exp4_Analysis_Report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    df = load_all()
    write_csv(ROOT / "data" / "exp4_master_run_level.csv", df)

    rates = rate_table(df)
    paired, carrier, by_task = paired_tables(df)
    macro = macro_table(paired)

    write_csv(ROOT / "tables" / "exp4_primary_rates_by_model_condition.csv", rates)
    write_csv(ROOT / "tables" / "exp4_paired_deltas_by_model.csv", paired)
    write_csv(ROOT / "tables" / "exp4_macro_model_summary.csv", macro)
    write_csv(ROOT / "tables" / "exp4_carrier_type_breakdown.csv", carrier)
    write_csv(ROOT / "tables" / "exp4_task_breakdown_artifact_action.csv", by_task)

    plot_rates(rates)
    plot_delta_heatmap(paired)
    plot_delta_forest(paired)
    plot_carrier_breakdown(carrier)
    plot_deepseek_diagnostic()
    report(df, rates, paired, macro, carrier)

    print(f"master_rows={len(df)}")
    print(f"report={ROOT / 'docs' / 'Exp4_Analysis_Report.md'}")
    print(f"figures={ROOT / 'figures'}")


if __name__ == "__main__":
    main()
