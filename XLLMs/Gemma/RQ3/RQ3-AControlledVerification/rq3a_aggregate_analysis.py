from __future__ import annotations

import csv
import json
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
RQ3_ROOT = ROOT.parent
W3_ROOT = RQ3_ROOT.parent
EXP1_ROOT = Path(os.environ.get("EXP1_ROOT", W3_ROOT / "Exp1_User_Context_Embedding"))
RQ2_EXP2_ROOT = Path(os.environ.get("RQ2_EXP2_ROOT", W3_ROOT / "RQ2" / "Exp2_SafetyIntent"))

RUN_COLUMNS = [
    "run_id",
    "pair_id",
    "base_task_id",
    "replicate_id",
    "model",
    "source",
    "guidance",
    "condition",
    "artifact_type",
    "artifact_exposed",
    "artifact_mentioned",
    "artifact_used_in_plan",
    "artifact_action_executed",
    "security_success",
    "benign_task_success",
    "runtime_status",
    "run_dir",
]

SUMMARY_COLUMNS = [
    "condition",
    "model",
    "source",
    "guidance",
    "n",
    "exposure_rate",
    "artifact_adoption_rate",
    "mention_rate",
    "planning_adoption_rate",
    "execution_rate",
    "security_success_rate",
    "task_utility",
    "p_plan_given_mention",
    "p_action_given_plan",
    "p_action_given_mention",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def intish(value: Any) -> int:
    return int(boolish(value))


def maybe_bool(value: Any) -> int | None:
    if value in {None, "", "NA", "None"}:
        return None
    return intish(value)


def mean_known(rows: list[dict[str, Any]], field: str) -> float | None:
    vals = [maybe_bool(row.get(field)) for row in rows]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def ratio(numer: int, denom: int) -> float | None:
    return None if denom == 0 else numer / denom


def norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def two_prop_effect(rows_a: list[dict[str, Any]], rows_b: list[dict[str, Any]], field: str) -> dict[str, Any]:
    a = [intish(row.get(field)) for row in rows_a]
    b = [intish(row.get(field)) for row in rows_b]
    if not a or not b:
        return {"delta": None, "ci_low": None, "ci_high": None, "p_value": None, "or": None}
    pa = sum(a) / len(a)
    pb = sum(b) / len(b)
    delta = pb - pa
    se = math.sqrt(pa * (1 - pa) / len(a) + pb * (1 - pb) / len(b))
    z = delta / se if se else 0.0
    p = 2 * (1 - norm_cdf(abs(z))) if se else None
    aa = sum(a) + 0.5
    an = len(a) - sum(a) + 0.5
    bb = sum(b) + 0.5
    bn = len(b) - sum(b) + 0.5
    odds_ratio = (bb / bn) / (aa / an)
    return {
        "delta": delta,
        "ci_low": delta - 1.96 * se,
        "ci_high": delta + 1.96 * se,
        "p_value": p,
        "or": odds_ratio,
    }


def load_summary(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def exp1_rows() -> list[dict[str, Any]]:
    out = []
    for row in read_csv(EXP1_ROOT / "12_Processed_Data/01_run_level.csv"):
        if row.get("condition") not in {"E", "UC_M"}:
            continue
        source = "E" if row["condition"] == "E" else "UC"
        summary = load_summary(Path(row.get("run_dir", "")) / "10_trace_summary.json")

        def first_metric(*keys: str) -> Any:
            for key in keys:
                value = summary.get(key, row.get(key, ""))
                if value not in {"", None, "None", "NA"}:
                    return value
            return ""

        out.append(
            {
                "run_id": row["run_id"],
                "pair_id": row["pair_id"],
                "base_task_id": row["base_task"],
                "replicate_id": "",
                "model": row["model"],
                "source": source,
                "guidance": "H1",
                "condition": f"{source}_M_H1",
                "artifact_type": "M",
                "artifact_exposed": intish(first_metric("artifact_seen", "embedded_artifact_seen")),
                "artifact_mentioned": intish(first_metric("artifact_mentioned", "embedded_artifact_mentioned")),
                "artifact_used_in_plan": intish(first_metric("artifact_used_in_plan", "artifact_planned", "embedded_artifact_used_in_plan")),
                "artifact_action_executed": intish(first_metric("artifact_action_called", "artifact_action", "embedded_artifact_action_called")),
                "security_success": 1 - intish(first_metric("attack_success")),
                "benign_task_success": intish(first_metric("utility_success")),
                "runtime_status": "valid",
                "run_dir": row.get("run_dir", ""),
            }
        )
    return out


def rq2_uc_guidance_rows() -> list[dict[str, Any]]:
    out = []
    for row in read_csv(RQ2_EXP2_ROOT / "04_processed/00_new_runs.csv"):
        if row.get("arm") != "malicious" or row.get("condition") not in {"H2", "H3"}:
            continue
        summary = load_summary(Path(row.get("run_dir", "")) / "15_trace_summary.json")
        out.append(
            {
                "run_id": row["run_id"],
                "pair_id": row["source_exp1_instance_id"],
                "base_task_id": row["base_task_id"],
                "replicate_id": "",
                "model": Path(row.get("run_dir", "")).parts[-2] if row.get("run_dir") else "",
                "source": "UC",
                "guidance": row["condition"],
                "condition": f"UC_M_{row['condition']}",
                "artifact_type": "M",
                "artifact_exposed": intish(summary.get("embedded_artifact_seen", True)),
                "artifact_mentioned": intish(summary.get("embedded_artifact_mentioned", "")),
                "artifact_used_in_plan": intish(summary.get("embedded_artifact_used_in_plan", row.get("artifact_action"))),
                "artifact_action_executed": intish(summary.get("embedded_artifact_action_called", row.get("artifact_action"))),
                "security_success": 1 - intish(row.get("attack_success")),
                "benign_task_success": intish(row.get("utility")),
                "runtime_status": row.get("runtime_status", ""),
                "run_dir": row.get("run_dir", ""),
            }
        )
    return out


def rq3_external_guidance_rows() -> list[dict[str, Any]]:
    out = []
    for row in read_csv(ROOT / "04_processed/01_run_level.csv"):
        if not row.get("run_id"):
            continue
        out.append({key: row.get(key, "") for key in RUN_COLUMNS})
    return out


def summarize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("runtime_status") != "valid":
            continue
        groups[(row["condition"], row.get("model", ""), row["source"], row["guidance"])].append(row)
    summary = []
    transitions = []
    for (condition, model, source, guidance), subset in sorted(groups.items()):
        mentioned_rows = [row for row in subset if maybe_bool(row.get("artifact_mentioned")) is not None]
        plan_rows = [row for row in subset if maybe_bool(row.get("artifact_used_in_plan")) is not None]
        mentions = sum(intish(row["artifact_mentioned"]) for row in mentioned_rows)
        plans = sum(intish(row["artifact_used_in_plan"]) for row in plan_rows)
        actions = sum(intish(row["artifact_action_executed"]) for row in subset)
        plan_and_mention = sum(intish(row["artifact_mentioned"]) and intish(row["artifact_used_in_plan"]) for row in mentioned_rows)
        action_and_plan = sum(intish(row["artifact_used_in_plan"]) and intish(row["artifact_action_executed"]) for row in plan_rows)
        action_and_mention = sum(intish(row["artifact_mentioned"]) and intish(row["artifact_action_executed"]) for row in mentioned_rows)
        summary.append(
            {
                "condition": condition,
                "model": model,
                "source": source,
                "guidance": guidance,
                "n": len(subset),
                "exposure_rate": mean_known(subset, "artifact_exposed"),
                "artifact_adoption_rate": mean_known(subset, "artifact_action_executed"),
                "mention_rate": mean_known(subset, "artifact_mentioned"),
                "planning_adoption_rate": mean_known(subset, "artifact_used_in_plan"),
                "execution_rate": mean_known(subset, "artifact_action_executed"),
                "security_success_rate": mean_known(subset, "security_success"),
                "task_utility": mean_known(subset, "benign_task_success"),
                "p_plan_given_mention": ratio(plan_and_mention, mentions),
                "p_action_given_plan": ratio(action_and_plan, plans),
                "p_action_given_mention": ratio(action_and_mention, mentions),
            }
        )
        for name, numer, denom in [
            ("Mention -> Plan", plan_and_mention, mentions),
            ("Plan -> Action", action_and_plan, plans),
            ("Mention -> Action", action_and_mention, mentions),
        ]:
            transitions.append(
                {
                    "condition": condition,
                    "model": model,
                    "source": source,
                    "guidance": guidance,
                    "transition": name,
                    "numerator": numer,
                    "denominator": denom,
                    "probability": ratio(numer, denom),
                }
            )
    return summary, transitions


def source_verification_effects(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid = [row for row in rows if row.get("runtime_status") == "valid"]
    by_condition = defaultdict(list)
    for row in valid:
        by_condition[row["condition"]].append(row)
    effects = []
    for outcome in ["artifact_used_in_plan", "artifact_action_executed", "security_success"]:
        h1 = two_prop_effect(by_condition["E_M_H1"], by_condition["UC_M_H1"], outcome)
        h3 = two_prop_effect(by_condition["E_M_H3"], by_condition["UC_M_H3"], outcome)
        effects.append(
            {
                "outcome": outcome,
                "delta_source_h1_uc_minus_e": h1["delta"],
                "delta_source_h3_uc_minus_e": h3["delta"],
                "diff_in_diff_h3_minus_h1": None if h1["delta"] is None or h3["delta"] is None else h3["delta"] - h1["delta"],
                "h1_ci_low": h1["ci_low"],
                "h1_ci_high": h1["ci_high"],
                "h3_ci_low": h3["ci_low"],
                "h3_ci_high": h3["ci_high"],
                "h1_p_value": h1["p_value"],
                "h3_p_value": h3["p_value"],
                "h1_or_uc_vs_e": h1["or"],
                "h3_or_uc_vs_e": h3["or"],
            }
        )
    for outcome in ["artifact_used_in_plan", "artifact_action_executed", "security_success"]:
        h1_h2 = two_prop_effect(by_condition["UC_M_H1"], by_condition["UC_M_H2"], outcome)
        h2_h3 = two_prop_effect(by_condition["UC_M_H2"], by_condition["UC_M_H3"], outcome)
        effects.append(
            {
                "outcome": f"uc_guidance_gradient_{outcome}",
                "delta_source_h1_uc_minus_e": h1_h2["delta"],
                "delta_source_h3_uc_minus_e": h2_h3["delta"],
                "diff_in_diff_h3_minus_h1": None,
                "h1_ci_low": h1_h2["ci_low"],
                "h1_ci_high": h1_h2["ci_high"],
                "h3_ci_low": h2_h3["ci_low"],
                "h3_ci_high": h2_h3["ci_high"],
                "h1_p_value": h1_h2["p_value"],
                "h3_p_value": h2_h3["p_value"],
                "h1_or_uc_vs_e": h1_h2["or"],
                "h3_or_uc_vs_e": h2_h3["or"],
            }
        )
    return effects


def regression(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    try:
        import pandas as pd
        import statsmodels.formula.api as smf
    except Exception as exc:
        return [{"status": "skipped", "reason": f"statsmodels unavailable: {exc}"}]
    valid = [
        {
            **row,
            "source_uc": int(row["source"] == "UC"),
            "verification_h3": int(row["guidance"] == "H3"),
            "task": row["base_task_id"],
        }
        for row in rows
        if row.get("runtime_status") == "valid" and row["condition"] in {"E_M_H1", "UC_M_H1", "E_M_H3", "UC_M_H3"}
    ]
    out = []
    for outcome in ["artifact_used_in_plan", "artifact_action_executed", "security_success"]:
        data = []
        for row in valid:
            value = maybe_bool(row.get(outcome))
            if value is not None:
                data.append({**row, "outcome": value})
        if not data:
            continue
        df = pd.DataFrame(data)
        try:
            fit = smf.logit("outcome ~ source_uc + verification_h3 + source_uc:verification_h3", data=df).fit(disp=False)
        except Exception as exc:
            out.append({"outcome": outcome, "status": "failed", "reason": str(exc)})
            continue
        for term in fit.params.index:
            beta = float(fit.params[term])
            se = float(fit.bse[term])
            out.append(
                {
                    "outcome": outcome,
                    "predictor": term,
                    "beta": beta,
                    "se": se,
                    "ci_low": beta - 1.96 * se,
                    "ci_high": beta + 1.96 * se,
                    "p": float(fit.pvalues[term]),
                    "or": math.exp(beta),
                    "status": "ok",
                }
            )
    return out


def figures(summary_rows: list[dict[str, Any]]) -> None:
    import matplotlib.pyplot as plt

    fig_dir = ROOT / "06_figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    order = ["E_M_H1", "UC_M_H1", "E_M_H3", "UC_M_H3"]
    lookup = {row["condition"]: row for row in summary_rows}
    vals = [float(lookup[c]["artifact_adoption_rate"]) if c in lookup and lookup[c]["artifact_adoption_rate"] not in {None, ""} else 0.0 for c in order]
    plt.figure(figsize=(6, 3.5))
    plt.bar(range(len(order)), vals)
    plt.xticks(range(len(order)), order)
    plt.ylim(0, 1)
    plt.ylabel("Artifact action/adoption rate")
    plt.tight_layout()
    plt.savefig(fig_dir / "31_fig_source_verification.pdf")
    plt.close()

    stage_conditions = [c for c in ["E_M_H1", "UC_M_H1", "E_M_H3", "UC_M_H3"] if c in lookup]
    stages = [("Mention", "mention_rate"), ("Plan", "planning_adoption_rate"), ("Action", "execution_rate")]
    plt.figure(figsize=(6, 3.5))
    for condition in stage_conditions:
        values = [float(lookup[condition][field]) if lookup[condition][field] not in {None, ""} else 0.0 for _, field in stages]
        plt.plot([name for name, _ in stages], values, marker="o", label=condition)
    plt.ylim(0, 1)
    plt.ylabel("Rate")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(fig_dir / "32_fig_propagation_stages.pdf")
    plt.close()


def analysis_md(summary_rows: list[dict[str, Any]], effects: list[dict[str, Any]]) -> None:
    def fmt(value: Any) -> str:
        if value in {None, ""}:
            return "NA"
        try:
            return f"{float(value):.3f}"
        except Exception:
            return str(value)

    lines = [
        "# RQ3-A Controlled Verification Intervention\n\n",
        "## Data Integrity\n\n",
        "| Condition | N | Exposure | Mention | Plan | Action | Security | Utility |\n",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['condition']} | {row['n']} | {fmt(row['exposure_rate'])} | {fmt(row['mention_rate'])} | "
            f"{fmt(row['planning_adoption_rate'])} | {fmt(row['execution_rate'])} | "
            f"{fmt(row['security_success_rate'])} | {fmt(row['task_utility'])} |\n"
        )
    lines.extend(["\n## Source x Verification\n\n", "| Outcome | Delta H1 | Delta H3 | Diff-in-Diff | H1 OR | H3 OR |\n", "| --- | ---: | ---: | ---: | ---: | ---: |\n"])
    for row in effects:
        if str(row["outcome"]).startswith("uc_guidance_gradient"):
            continue
        lines.append(
            f"| {row['outcome']} | {fmt(row['delta_source_h1_uc_minus_e'])} | {fmt(row['delta_source_h3_uc_minus_e'])} | "
            f"{fmt(row['diff_in_diff_h3_minus_h1'])} | {fmt(row['h1_or_uc_vs_e'])} | {fmt(row['h3_or_uc_vs_e'])} |\n"
        )
    lines.append("\n## Notes\n\n- E_M_H2 and E_M_H3 rows appear after the new RQ3-A runs finish.\n")
    (ROOT / "06_analysis").mkdir(parents=True, exist_ok=True)
    (ROOT / "06_analysis/01_RQ3A_controlled_verification_analysis.md").write_text("".join(lines), encoding="utf-8")


def main() -> None:
    rows = exp1_rows() + rq2_uc_guidance_rows() + rq3_external_guidance_rows()
    summary_rows, transitions = summarize(rows)
    effects = source_verification_effects(rows)
    reg = regression(rows)
    write_csv(ROOT / "04_processed/01_rq3a_run_level.csv", rows, RUN_COLUMNS)
    write_csv(ROOT / "05_statistics/02_rq3a_condition_summary.csv", summary_rows, SUMMARY_COLUMNS)
    write_csv(ROOT / "05_statistics/03_rq3a_stage_transitions.csv", transitions)
    write_csv(ROOT / "05_statistics/04_rq3a_source_verification_effect.csv", effects)
    write_csv(ROOT / "05_statistics/05_rq3a_regression.csv", reg)
    write_csv(ROOT / "05_tables/41_table_verification_propagation.csv", summary_rows, SUMMARY_COLUMNS)
    figures(summary_rows)
    analysis_md(summary_rows, effects)
    write_json(ROOT / "04_processed/00_rq3a_aggregate_manifest.json", {"rows": len(rows), "conditions": sorted({row["condition"] for row in rows})})
    print(f"rq3a_rows={len(rows)} conditions={sorted({row['condition'] for row in rows})}")


if __name__ == "__main__":
    main()
