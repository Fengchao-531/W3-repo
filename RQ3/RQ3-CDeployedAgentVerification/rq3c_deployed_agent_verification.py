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
W3_BACKUP_ROOT = Path(os.environ.get("W3_BACKUP_ROOT", "/scratch3/che489/W3-Backup/W3-repo"))

RUN_COLUMNS = [
    "run_id",
    "agent",
    "model",
    "condition",
    "source",
    "guidance",
    "artifact_type",
    "artifact_exposed",
    "artifact_mentioned",
    "artifact_used_in_plan",
    "artifact_action_executed",
    "security_success",
    "benign_task_success",
    "runtime_status",
    "source_file",
]

SUMMARY_COLUMNS = [
    "agent",
    "model",
    "condition",
    "source",
    "guidance",
    "n",
    "exposure_rate",
    "mention_rate",
    "planning_adoption_rate",
    "execution_rate",
    "security_success_rate",
    "task_utility",
    "p_plan_given_mention",
    "p_action_given_plan",
]


def setup_dirs() -> None:
    for rel in [
        "00_config",
        "01_legacy_sources",
        "04_processed",
        "05_statistics",
        "06_figures",
        "07_tables",
        "08_analysis",
    ]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, Any]]:
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


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "success", "succeeded", "pass", "passed", "blocked"}


def maybe_bool(value: Any) -> int | None:
    if value in {None, "", "NA", "None", "null"}:
        return None
    return int(boolish(value))


def first(row: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        value = row.get(key)
        if value not in {None, "", "NA", "None", "null"}:
            return value
    return default


def infer_guidance(row: dict[str, Any]) -> str:
    text = str(first(row, "guidance", "verification", "condition", "arm", "prompt_condition", default="")).upper()
    for guidance in ["H3", "H2", "H1"]:
        if guidance in text:
            return guidance
    return text or "unknown"


def infer_source(row: dict[str, Any]) -> str:
    text = str(first(row, "source", "context_source", "condition", "arm", default="")).upper()
    if text.startswith("UC") or "USER_CONTEXT" in text:
        return "UC"
    if text.startswith("E") or "EXTERNAL" in text:
        return "E"
    return text or "unknown"


def infer_condition(row: dict[str, Any], source: str, guidance: str) -> str:
    condition = str(first(row, "condition", "arm", "prompt_condition", default="")).strip()
    if condition and guidance in condition.upper():
        return condition
    if source != "unknown" and guidance != "unknown":
        return f"{source}_M_{guidance}"
    return condition or "unknown"


def candidate_paths() -> list[Path]:
    env_paths = [Path(p.strip()) for p in os.environ.get("RQ3C_INPUTS", "").split(",") if p.strip()]
    local_paths = []
    for pattern in ["*.csv", "*.jsonl"]:
        local_paths.extend((ROOT / "01_legacy_sources").glob(pattern))
    curated = [
        W3_ROOT / "RQ3" / "RQ3-CDeployedAgentVerification" / "01_legacy_sources",
        W3_BACKUP_ROOT / "Deployed-Agent-Verification",
        W3_BACKUP_ROOT / "Commercial-Agent-Verification",
        W3_BACKUP_ROOT / "DeployedAgents",
        W3_BACKUP_ROOT / "CommercialAgents",
    ]
    for base in curated:
        if base.is_dir():
            for pattern in ["*.csv", "*.jsonl"]:
                local_paths.extend(base.glob(pattern))
    return sorted(set(env_paths + [p for p in local_paths if p.is_file()]))


def load_source_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        return read_jsonl(path)
    if path.suffix.lower() == ".csv":
        return read_csv(path)
    return []


def normalize_row(row: dict[str, Any], path: Path, idx: int) -> dict[str, Any]:
    guidance = infer_guidance(row)
    source = infer_source(row)
    attack_success = maybe_bool(first(row, "attack_success", "asr", "artifact_action", "artifact_action_executed", default=""))
    security_success = maybe_bool(first(row, "security_success", "safe", "blocked_attack", default=""))
    if security_success is None and attack_success is not None:
        security_success = 1 - attack_success
    action = maybe_bool(first(row, "artifact_action_executed", "embedded_artifact_action_called", "artifact_action_called", "attack_success", "asr", default=""))
    return {
        "run_id": first(row, "run_id", "id", "trace_id", default=f"{path.stem}_{idx:05d}"),
        "agent": first(row, "agent", "deployed_agent", "commercial_agent", "platform", "app", default="unknown"),
        "model": first(row, "model", "llm", "agent_model", default="unknown"),
        "condition": infer_condition(row, source, guidance),
        "source": source,
        "guidance": guidance,
        "artifact_type": first(row, "artifact_type", "arm_type", default="M"),
        "artifact_exposed": maybe_bool(first(row, "artifact_exposed", "artifact_seen", "embedded_artifact_seen", default="")),
        "artifact_mentioned": maybe_bool(first(row, "artifact_mentioned", "embedded_artifact_mentioned", default="")),
        "artifact_used_in_plan": maybe_bool(first(row, "artifact_used_in_plan", "artifact_planned", "embedded_artifact_used_in_plan", default="")),
        "artifact_action_executed": action,
        "security_success": security_success,
        "benign_task_success": maybe_bool(first(row, "benign_task_success", "utility_success", "utility", "task_success", default="")),
        "runtime_status": first(row, "runtime_status", "status", default="valid"),
        "source_file": str(path),
    }


def import_legacy() -> list[dict[str, Any]]:
    paths = candidate_paths()
    rows = []
    for path in paths:
        for idx, row in enumerate(load_source_rows(path), 1):
            rows.append(normalize_row(row, path, idx))
    write_csv(ROOT / "04_processed/21_rq3c_run_level.csv", rows, RUN_COLUMNS)
    write_json(
        ROOT / "00_config/00_source_manifest.json",
        {
            "status": "ok" if rows else "pending_legacy_logs",
            "input_files": [str(path) for path in paths],
            "rows": len(rows),
            "note": "Set RQ3C_INPUTS=/path/a.csv,/path/b.jsonl or place files in 01_legacy_sources/.",
        },
    )
    return rows


def ratio(numer: int, denom: int) -> float | None:
    return None if denom == 0 else numer / denom


def mean_known(rows: list[dict[str, Any]], field: str) -> float | None:
    vals = [maybe_bool(row.get(field)) for row in rows]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return sum(vals) / len(vals)


def summarize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid = [row for row in rows if str(row.get("runtime_status", "valid")).lower() in {"valid", "ok", "success", "succeeded", "completed"}]
    groups: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in valid:
        groups[(row["agent"], row["model"], row["condition"], row["source"], row["guidance"])].append(row)
    summary = []
    transitions = []
    for (agent, model, condition, source, guidance), subset in sorted(groups.items()):
        mention_rows = [row for row in subset if maybe_bool(row.get("artifact_mentioned")) is not None]
        plan_rows = [row for row in subset if maybe_bool(row.get("artifact_used_in_plan")) is not None]
        mentions = sum(maybe_bool(row.get("artifact_mentioned")) or 0 for row in mention_rows)
        plans = sum(maybe_bool(row.get("artifact_used_in_plan")) or 0 for row in plan_rows)
        plan_and_mention = sum((maybe_bool(row.get("artifact_mentioned")) or 0) and (maybe_bool(row.get("artifact_used_in_plan")) or 0) for row in mention_rows)
        action_and_plan = sum((maybe_bool(row.get("artifact_used_in_plan")) or 0) and (maybe_bool(row.get("artifact_action_executed")) or 0) for row in plan_rows)
        summary.append(
            {
                "agent": agent,
                "model": model,
                "condition": condition,
                "source": source,
                "guidance": guidance,
                "n": len(subset),
                "exposure_rate": mean_known(subset, "artifact_exposed"),
                "mention_rate": mean_known(subset, "artifact_mentioned"),
                "planning_adoption_rate": mean_known(subset, "artifact_used_in_plan"),
                "execution_rate": mean_known(subset, "artifact_action_executed"),
                "security_success_rate": mean_known(subset, "security_success"),
                "task_utility": mean_known(subset, "benign_task_success"),
                "p_plan_given_mention": ratio(plan_and_mention, mentions),
                "p_action_given_plan": ratio(action_and_plan, plans),
            }
        )
        transitions.extend(
            [
                {"agent": agent, "model": model, "condition": condition, "transition": "Mention -> Plan", "numerator": plan_and_mention, "denominator": mentions, "probability": ratio(plan_and_mention, mentions)},
                {"agent": agent, "model": model, "condition": condition, "transition": "Plan -> Action", "numerator": action_and_plan, "denominator": plans, "probability": ratio(action_and_plan, plans)},
            ]
        )
    return summary, transitions


def norm_cdf(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def two_prop(rows_a: list[dict[str, Any]], rows_b: list[dict[str, Any]], field: str) -> dict[str, Any]:
    a = [maybe_bool(row.get(field)) for row in rows_a]
    b = [maybe_bool(row.get(field)) for row in rows_b]
    a = [v for v in a if v is not None]
    b = [v for v in b if v is not None]
    if not a or not b:
        return {"delta": None, "p": None}
    pa = sum(a) / len(a)
    pb = sum(b) / len(b)
    delta = pb - pa
    se = math.sqrt(pa * (1 - pa) / len(a) + pb * (1 - pb) / len(b))
    p = 2 * (1 - norm_cdf(abs(delta / se))) if se else None
    return {"delta": delta, "p": p}


def source_effects(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid = [row for row in rows if str(row.get("runtime_status", "valid")).lower() in {"valid", "ok", "success", "succeeded", "completed"}]
    grouped: dict[tuple[str, str, str], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in valid:
        grouped[(row["agent"], row["model"], row["guidance"])][row["source"]].append(row)
    out = []
    for (agent, model, guidance), sources in sorted(grouped.items()):
        if "E" not in sources or "UC" not in sources:
            continue
        for field in ["artifact_used_in_plan", "artifact_action_executed", "security_success"]:
            effect = two_prop(sources["E"], sources["UC"], field)
            out.append(
                {
                    "agent": agent,
                    "model": model,
                    "guidance": guidance,
                    "outcome": field,
                    "delta_uc_minus_e": effect["delta"],
                    "p_value": effect["p"],
                    "n_e": len(sources["E"]),
                    "n_uc": len(sources["UC"]),
                }
            )
    return out


def figures(summary: list[dict[str, Any]]) -> None:
    import matplotlib.pyplot as plt

    rows = [row for row in summary if row.get("execution_rate") not in {None, ""}]
    if rows:
        labels = [f"{row['agent']} {row['condition']}" for row in rows[:20]]
        values = [float(row["execution_rate"]) for row in rows[:20]]
        plt.figure(figsize=(8, 3.8))
        plt.bar(range(len(values)), values)
        plt.xticks(range(len(values)), labels, rotation=35, ha="right", fontsize=7)
        plt.ylim(0, 1)
        plt.ylabel("Artifact execution rate")
        plt.tight_layout()
        plt.savefig(ROOT / "06_figures/34_fig_deployed_agent_execution.pdf")
        plt.close()
    write_json(ROOT / "06_figures/README.json", {"note": "Generated only from imported legacy deployed-agent rows."})


def analysis_md(summary: list[dict[str, Any]], effects: list[dict[str, Any]]) -> None:
    lines = ["# RQ3-C Deployed-Agent Verification\n\n"]
    if not summary:
        lines.extend(
            [
                "## Status\n\n",
                "Pending old commercial/deployed-agent H1/H2/H3 logs. No rerun is required for this RQ3 component.\n\n",
                "Place CSV/JSONL logs in `01_legacy_sources/` or run with `RQ3C_INPUTS=/path/a.csv,/path/b.jsonl`.\n",
            ]
        )
    else:
        lines.extend(["## Summary\n\n", "| Agent | Model | Condition | N | Action | Security | Utility |\n", "| --- | --- | --- | ---: | ---: | ---: | ---: |\n"])
        for row in summary:
            lines.append(f"| {row['agent']} | {row['model']} | {row['condition']} | {row['n']} | {row['execution_rate']} | {row['security_success_rate']} | {row['task_utility']} |\n")
        lines.extend(["\n## Source Effects\n\n", "| Agent | Model | Guidance | Outcome | Delta UC-E | p |\n", "| --- | --- | --- | --- | ---: | ---: |\n"])
        for row in effects:
            lines.append(f"| {row['agent']} | {row['model']} | {row['guidance']} | {row['outcome']} | {row['delta_uc_minus_e']} | {row['p_value']} |\n")
    (ROOT / "08_analysis/03_RQ3C_deployed_agent_verification_analysis.md").write_text("".join(lines), encoding="utf-8")


def main() -> None:
    setup_dirs()
    rows = import_legacy()
    summary, transitions = summarize(rows)
    effects = source_effects(rows)
    write_csv(ROOT / "05_statistics/22_rq3c_condition_summary.csv", summary, SUMMARY_COLUMNS)
    write_csv(ROOT / "05_statistics/23_rq3c_stage_transitions.csv", transitions)
    write_csv(ROOT / "05_statistics/24_rq3c_source_effect.csv", effects)
    write_csv(ROOT / "07_tables/43_table_deployed_agent_verification.csv", summary, SUMMARY_COLUMNS)
    figures(summary)
    analysis_md(summary, effects)
    print(f"rq3c_rows={len(rows)} summary_rows={len(summary)}")


if __name__ == "__main__":
    main()
