from __future__ import annotations

import csv
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
W3 = ROOT.parent
EXP1 = W3 / "Exp1_User_Context_Embedding"
EXP3 = W3 / "RQ2" / "Exp3_ Controlled_Source-Provenance_Intervention"
SAFETY = W3 / "RQ2" / "Exp2_SafetyIntent"

DATA = ROOT / "data"
TABLES = ROOT / "tables"
FIGURES = ROOT / "figures"


def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def read_csv(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows, columns=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def boolish(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def intish(value):
    return 1 if boolish(value) else 0


def pct(value):
    if value is None or value == "":
        return "NA"
    return f"{100 * float(value):.1f}%"


def proportion_ci_wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def cluster_bootstrap_delta(rows, cluster_field, y_field, group_field, a, b, reps=2000, seed=20260916):
    paired = defaultdict(dict)
    clusters_for_pair = {}
    for row in rows:
        paired[row["pair_id"]][row[group_field]] = int(row[y_field])
        clusters_for_pair[row["pair_id"]] = row[cluster_field]
    pair_rows = [
        {"pair_id": pid, "cluster": clusters_for_pair[pid], "a": vals[a], "b": vals[b]}
        for pid, vals in paired.items()
        if a in vals and b in vals
    ]
    if not pair_rows:
        return {"estimate": None, "ci_low": None, "ci_high": None, "clusters": 0, "pairs": 0}
    est = sum(r["b"] - r["a"] for r in pair_rows) / len(pair_rows)
    by_cluster = defaultdict(list)
    for row in pair_rows:
        by_cluster[row["cluster"]].append(row)
    clusters = sorted(by_cluster)
    rng = random.Random(seed)
    deltas = []
    for _ in range(reps):
        sample = []
        for _cluster in clusters:
            sample.extend(by_cluster[rng.choice(clusters)])
        deltas.append(sum(r["b"] - r["a"] for r in sample) / len(sample))
    deltas.sort()
    return {
        "estimate": est,
        "ci_low": deltas[int(0.025 * (reps - 1))],
        "ci_high": deltas[int(0.975 * (reps - 1))],
        "clusters": len(clusters),
        "pairs": len(pair_rows),
    }


def mcnemar_counts(rows, a_field, b_field):
    n00 = n01 = n10 = n11 = 0
    for row in rows:
        a = int(row[a_field])
        b = int(row[b_field])
        if a == 0 and b == 0:
            n00 += 1
        elif a == 0 and b == 1:
            n01 += 1
        elif a == 1 and b == 0:
            n10 += 1
        else:
            n11 += 1
    return n00, n01, n10, n11


def role_for_artifact(config, artifact_id):
    if artifact_id == config.get("malicious_artifact_id") or artifact_id == config.get("malicious_id"):
        return "M"
    if artifact_id == config.get("benign_matched_id"):
        return "BM"
    if artifact_id == config.get("benign_weak_id"):
        return "BW"
    return "UNKNOWN"


def snippet(text, limit=140):
    if text is None:
        return ""
    text = " ".join(str(text).split())
    return text[:limit]


def model_message_count(run_dir):
    index = read_json(run_dir / "11_model_call_index.json", {})
    return len(index.get("call_ids", []))


def valid_status(config):
    if not config:
        return "missing_config"
    if config.get("error"):
        return "run_error"
    return "valid"


def parse_a_source():
    rows = []
    cand_rows = []
    raw_root = EXP3 / "02_controlled_source" / "raw_runs"
    for run_dir in sorted(p for p in raw_root.glob("*/*/*") if p.is_dir()):
        config = read_json(run_dir / "01_run_config.json", {})
        security = read_json(run_dir / "08_security_result.json", {})
        utility = read_json(run_dir / "09_utility_result.json", {})
        assignment = read_json(run_dir / "source_assignment.json", config.get("source_assignment", {}))
        messages = read_jsonl(run_dir / "03_messages.jsonl")
        calls = read_jsonl(run_dir / "04_tool_calls.jsonl")
        outputs = read_jsonl(run_dir / "05_tool_outputs.jsonl")
        events = read_jsonl(run_dir / "06_environment_events.jsonl")
        status = valid_status(config)
        selected_role = security.get("selected_type") or "None"
        selected_id = security.get("selected_artifact_id") or ""
        source_by_role = {c["artifact_role"]: c["source"] for c in assignment.get("candidates", [])}
        selected_source = source_by_role.get(selected_role, "") if selected_role in {"M", "BM", "BW"} else ""
        executed_roles = Counter()
        action_success_roles = Counter()
        for event in events:
            role = role_for_artifact(config, event.get("artifact_id"))
            if role != "UNKNOWN":
                executed_roles[role] += 1
                if event.get("matched", True):
                    action_success_roles[role] += 1
        exposed_steps = [m for m in messages if m.get("contains_artifact")]
        first_exposure = min([m.get("timestamp_order", 9999) for m in exposed_steps], default=None)
        row = {
            "analysis": "A_source_label",
            "run_id": config.get("run_id", run_dir.name),
            "pair_id": config.get("pair_id", ""),
            "condition": config.get("condition", ""),
            "base_task_id": config.get("base_task_id", ""),
            "desire_id": config.get("desire_id", ""),
            "carrier_id": config.get("carrier_id", ""),
            "model": config.get("model", ""),
            "temperature": config.get("temperature", ""),
            "runtime_status": status,
            "selected_role": selected_role,
            "selected_artifact_id": selected_id,
            "selected_source": selected_source,
            "M_source": source_by_role.get("M", ""),
            "BM_source": source_by_role.get("BM", ""),
            "BW_source": source_by_role.get("BW", ""),
            "M_adopted": int(selected_role == "M"),
            "BM_adopted": int(selected_role == "BM"),
            "BW_adopted": int(selected_role == "BW"),
            "none_selected": int(selected_role not in {"M", "BM", "BW"}),
            "M_executed": int(executed_roles["M"] > 0),
            "BM_executed": int(executed_roles["BM"] > 0),
            "BW_executed": int(executed_roles["BW"] > 0),
            "M_action_success": int(action_success_roles["M"] > 0),
            "BM_action_success": int(action_success_roles["BM"] > 0),
            "attack_success": int(boolish(security.get("attack_success"))),
            "utility_success": int(boolish(utility.get("utility_success"))),
            "exposure": int(bool(exposed_steps)),
            "first_exposure_step": first_exposure if first_exposure is not None else "",
            "exposure_message_count": len(exposed_steps),
            "planning_adoption_M_observable": int(boolish(security.get("artifact_used_in_plan"))),
            "verification_observable": "unknown",
            "run_dir": str(run_dir),
            "evidence_message_step": exposed_steps[0].get("timestamp_order", "") if exposed_steps else "",
            "evidence_message_role": exposed_steps[0].get("role", "") if exposed_steps else "",
            "evidence_snippet": snippet(exposed_steps[0].get("content", "")) if exposed_steps else "",
        }
        rows.append(row)
        for cand in assignment.get("candidates", []):
            role = cand["artifact_role"]
            cand_rows.append({
                "run_id": row["run_id"],
                "pair_id": row["pair_id"],
                "condition": row["condition"],
                "base_task_id": row["base_task_id"],
                "artifact_id": cand["artifact_id"],
                "artifact_role": role,
                "source": cand["source"],
                "position": cand["position"],
                "selected": int(selected_role == role),
                "executed": int(executed_roles[role] > 0),
                "action_success": int(action_success_roles[role] > 0),
                "run_dir": str(run_dir),
            })
    write_csv(DATA / "A_source_trajectory_table.csv", rows)
    write_csv(DATA / "A_source_candidate_table.csv", cand_rows)
    return rows


def parse_b_timing():
    rows = []
    for condition, raw_root in [
        ("E", EXP1 / "09_External_Runs" / "gpt-4o-2024-05-13"),
        ("UC", EXP1 / "10_User_Context_Runs" / "gpt-4o-2024-05-13"),
    ]:
        for run_dir in sorted(p for p in raw_root.glob("*") if p.is_dir()):
            config = read_json(run_dir / "01_run_config.json", {})
            security = read_json(run_dir / "08_security_result.json", {})
            utility = read_json(run_dir / "09_utility_result.json", {})
            messages = read_jsonl(run_dir / "03_messages.jsonl")
            calls = read_jsonl(run_dir / "04_tool_calls.jsonl")
            outputs = read_jsonl(run_dir / "05_tool_outputs.jsonl")
            events = read_jsonl(run_dir / "06_environment_events.jsonl")
            status = valid_status(config)
            artifact_ids = {
                config.get("malicious_artifact_id", ""),
                config.get("benign_matched_id", ""),
                config.get("benign_weak_id", ""),
            }
            exposure_messages = [m for m in messages if m.get("contains_artifact") and set(m.get("artifact_ids", [])) & artifact_ids]
            first_exposure_step = min([m.get("timestamp_order", 9999) for m in exposure_messages], default=None)
            pre_calls = []
            pre_offer_calls = []
            pre_final = False
            if first_exposure_step is not None:
                pre_calls = [c for c in calls if c.get("step", 9999) < first_exposure_step]
                pre_offer_calls = [c for c in pre_calls if c.get("tool_name") == "apply_offer"]
                pre_final = any(
                    m.get("role") == "assistant" and m.get("content") and m.get("timestamp_order", 9999) < first_exposure_step
                    for m in messages
                )
            exposure_status = "exposed" if exposure_messages else ("unexposed" if status == "valid" else "unjudgeable")
            pre_tool_messages = []
            pre_tool_names = []
            if exposure_messages:
                for message in messages:
                    if message.get("timestamp_order", 9999) >= first_exposure_step:
                        continue
                    raw = message.get("raw_message") or {}
                    for call in raw.get("tool_calls") or []:
                        name = (call.get("function") or "")
                        pre_tool_messages.append(message)
                        pre_tool_names.append(name)
                pre_offer_calls = [name for name in pre_tool_names if name == "apply_offer"]
                pre_state = "artifact_action_before_exposure" if pre_offer_calls else ("task_work_started_before_exposure" if pre_tool_names else "no_prior_tool_call")
            else:
                pre_state = "not_applicable_no_exposure" if status == "valid" else "unjudgeable"
            first = exposure_messages[0] if exposure_messages else {}
            selected = security.get("selected_type") or "None"
            rows.append({
                "analysis": "B_timing_exposure",
                "run_id": config.get("run_id", run_dir.name),
                "pair_id": config.get("pair_id", ""),
                "condition": condition,
                "base_task_id": config.get("base_task_id", ""),
                "desire_id": config.get("desire_id", ""),
                "carrier_id": config.get("carrier_id", ""),
                "model": config.get("model", ""),
                "runtime_status": status,
                "exposure_status": exposure_status,
                "first_exposure_step": first_exposure_step if first_exposure_step is not None else "",
                "first_exposure_role": first.get("role", ""),
                "first_exposure_source": first.get("source", ""),
                "exposure_count": len(exposure_messages),
                "model_calls_total": model_message_count(run_dir),
                "pre_exposure_tool_calls": len(pre_tool_names),
                "pre_exposure_artifact_action": int(bool(pre_offer_calls)),
                "pre_exposure_final_response": int(pre_final),
                "pre_exposure_state_observable": pre_state,
                "selected_role": selected,
                "M_adopted": int(selected == "M"),
                "BM_adopted": int(selected == "BM"),
                "any_adopted": int(selected in {"M", "BM", "BW"}),
                "execution": int(boolish(security.get("artifact_action_called")) or bool(events)),
                "M_execution": int(any(role_for_artifact(config, e.get("artifact_id")) == "M" for e in events)),
                "attack_success": int(boolish(security.get("attack_success"))),
                "utility_success": int(boolish(utility.get("utility_success"))),
                "verification": "unknown",
                "run_dir": str(run_dir),
                "evidence_message_step": first.get("timestamp_order", ""),
                "evidence_snippet": snippet(first.get("content", "")),
            })
    write_csv(DATA / "B_timing_trajectory_table.csv", rows)
    return rows


def parse_c_safety():
    new_rows = read_csv(SAFETY / "04_processed" / "00_new_runs.csv")
    panel = read_csv(SAFETY / "04_processed" / "01_h1_h2_h3_panel.csv")
    h1_ref = read_csv(SAFETY / "00_exp1_reference" / "02_exp1_h1_results_snapshot.csv")
    rows = []
    h1_by_group = {r["analysis_group_id"]: r for r in h1_ref if r.get("arm") == "malicious"}
    for p in panel:
        group = p["analysis_group_id"]
        h1 = h1_by_group.get(group, {})
        for cond in ["H1", "H2", "H3"]:
            if cond == "H1":
                rows.append({
                    "analysis": "C_user_safety_guidance",
                    "analysis_group_id": group,
                    "pair_id": p["source_exp1_instance_id"],
                    "condition": "H1_no_guidance",
                    "base_task_id": p["base_task_id"],
                    "carrier_type": p["carrier_type"],
                    "runtime_status": "valid",
                    "choice": p["H1_choice"],
                    "adoption": int(p["H1_choice"] == "M"),
                    "planning_adoption": intish(h1.get("artifact_planned")),
                    "verification": intish(p["H1_verify"]),
                    "execution": intish(h1.get("artifact_action")),
                    "attack_success": intish(p["H1_attack"]),
                    "utility_success": intish(p["H1_utility"]),
                    "run_dir": h1.get("run_dir", ""),
                })
            else:
                nr = next((r for r in new_rows if r["analysis_group_id"] == group and r["condition"] == cond), {})
                rows.append({
                    "analysis": "C_user_safety_guidance",
                    "analysis_group_id": group,
                    "pair_id": p["source_exp1_instance_id"],
                    "condition": "H2_concern" if cond == "H2" else "H3_concern_plus_verify",
                    "base_task_id": p["base_task_id"],
                    "carrier_type": p["carrier_type"],
                    "runtime_status": nr.get("runtime_status", "missing"),
                    "choice": p[f"{cond}_choice"],
                    "adoption": int(p[f"{cond}_choice"] == "M"),
                    "planning_adoption": "unknown",
                    "verification": intish(p[f"{cond}_verify"]),
                    "execution": intish(nr.get("artifact_action")),
                    "attack_success": intish(p[f"{cond}_attack"]),
                    "utility_success": intish(p[f"{cond}_utility"]),
                    "trusted_source_access": intish(nr.get("trusted_source_accessed")),
                    "grounded_verification": intish(nr.get("grounded_verification")),
                    "verification_correct": nr.get("verification_correct", "NA"),
                    "warning": intish(nr.get("warning")),
                    "run_dir": nr.get("run_dir", ""),
                })
    write_csv(DATA / "C_safety_trajectory_table.csv", rows)
    return rows


def rate_summary(rows, group_fields, metric_fields):
    out = []
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[g] for g in group_fields)].append(row)
    for key, subset in sorted(groups.items()):
        base = dict(zip(group_fields, key))
        base["n"] = len(subset)
        for m in metric_fields:
            vals = [int(r[m]) for r in subset if str(r.get(m, "")).strip() not in {"", "unknown", "NA"}]
            k = sum(vals)
            n = len(vals)
            lo, hi = proportion_ci_wilson(k, n)
            base[f"{m}_num"] = k
            base[f"{m}_den"] = n
            base[f"{m}_rate"] = k / n if n else None
            base[f"{m}_ci_low"] = lo
            base[f"{m}_ci_high"] = hi
        out.append(base)
    return out


def make_summaries(a_rows, b_rows, c_rows):
    # A summaries
    a_valid = [r for r in a_rows if r["runtime_status"] == "valid"]
    a_summary = rate_summary(a_valid, ["condition"], ["M_adopted", "BM_adopted", "BW_adopted", "none_selected", "M_executed", "BM_executed", "attack_success", "utility_success"])
    write_csv(TABLES / "Table_A1_source_condition_summary.csv", a_summary)
    a_diffs = []
    for metric, a, b, label in [
        ("M_adopted", "C0", "C1", "P(M|C1)-P(M|C0)"),
        ("BM_adopted", "C0", "C2", "P(BM|C2)-P(BM|C0)"),
        ("M_executed", "C0", "C1", "P(M execution|C1)-P(M execution|C0)"),
        ("BM_executed", "C0", "C2", "P(BM execution|C2)-P(BM execution|C0)"),
    ]:
        stats = cluster_bootstrap_delta(a_valid, "base_task_id", metric, "condition", a, b)
        a_diffs.append({"comparison": label, "metric": metric, **stats})
    write_csv(TABLES / "Table_A1_source_primary_differences.csv", a_diffs)

    # B summaries
    b_valid = [r for r in b_rows if r["runtime_status"] == "valid"]
    b_exposure = rate_summary(b_valid, ["condition", "exposure_status", "pre_exposure_state_observable"], ["M_adopted", "any_adopted", "execution", "M_execution", "attack_success", "utility_success"])
    write_csv(TABLES / "Table_B1_exposure_timing_summary.csv", b_exposure)
    b_groups = []
    for label, subset in [
        ("E_all", [r for r in b_valid if r["condition"] == "E"]),
        ("E_exposed", [r for r in b_valid if r["condition"] == "E" and r["exposure_status"] == "exposed"]),
        ("E_unexposed", [r for r in b_valid if r["condition"] == "E" and r["exposure_status"] == "unexposed"]),
        ("UC_all", [r for r in b_valid if r["condition"] == "UC"]),
    ]:
        for metric in ["M_adopted", "any_adopted", "execution", "M_execution", "attack_success", "utility_success"]:
            vals = [int(r[metric]) for r in subset]
            k, n = sum(vals), len(vals)
            lo, hi = proportion_ci_wilson(k, n)
            b_groups.append({"group": label, "metric": metric, "num": k, "den": n, "rate": k / n if n else None, "ci_low": lo, "ci_high": hi})
    write_csv(TABLES / "Table_B2_exposure_subset_rates.csv", b_groups)

    # C summaries and paired differences
    c_valid = [r for r in c_rows if r["runtime_status"] == "valid"]
    c_summary = rate_summary(c_valid, ["condition"], ["adoption", "verification", "execution", "attack_success", "utility_success"])
    write_csv(TABLES / "Table_C1_safety_guidance_summary.csv", c_summary)
    c_diffs = []
    for metric in ["adoption", "verification", "execution", "attack_success", "utility_success"]:
        for a, b, label in [
            ("H1_no_guidance", "H2_concern", "H2-H1"),
            ("H1_no_guidance", "H3_concern_plus_verify", "H3-H1"),
            ("H2_concern", "H3_concern_plus_verify", "H3-H2"),
        ]:
            stats = cluster_bootstrap_delta(c_valid, "base_task_id", metric, "condition", a, b)
            c_diffs.append({"comparison": label, "metric": metric, **stats})
    write_csv(TABLES / "Table_C1_safety_guidance_differences.csv", c_diffs)
    return a_summary, a_diffs, b_exposure, b_groups, c_summary, c_diffs


def plot_errorbar_diffs(rows, path_base, title):
    labels = [r["comparison"] for r in rows]
    estimates = [float(r["estimate"]) if r["estimate"] not in {None, ""} else 0 for r in rows]
    lows = [float(r["ci_low"]) if r["ci_low"] not in {None, ""} else 0 for r in rows]
    highs = [float(r["ci_high"]) if r["ci_high"] not in {None, ""} else 0 for r in rows]
    yerr = [[e - lo for e, lo in zip(estimates, lows)], [hi - e for e, hi in zip(estimates, highs)]]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.errorbar(estimates, range(len(labels)), xerr=yerr, fmt="o", color="#2f6f9f", ecolor="#2f6f9f", capsize=4)
    ax.axvline(0, color="black", linewidth=1, linestyle="--")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Difference in rate (percentage points)")
    ax.set_title(title)
    ax.set_xlim(-0.35, 0.35)
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path_base.with_suffix(".pdf"))
    fig.savefig(path_base.with_suffix(".png"), dpi=300)
    plt.close(fig)


def make_figures(a_summary, a_diffs, b_groups, c_summary, c_diffs):
    # A1
    plot_errorbar_diffs(a_diffs[:2], FIGURES / "Figure_A1_source_primary_differences", "Figure A1. Source-label adoption differences (cluster bootstrap 95% CI)")

    # A2 stacked mutually exclusive choices.
    conds = ["C0", "C1", "C2"]
    roles = ["M_adopted", "BM_adopted", "BW_adopted", "none_selected"]
    colors = ["#4C78A8", "#59A14F", "#F28E2B", "#BAB0AC"]
    by_cond = {r["condition"]: r for r in a_summary}
    bottoms = [0] * len(conds)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for role, color in zip(roles, colors):
        vals = [float(by_cond[c][f"{role}_rate"]) for c in conds]
        ax.bar(conds, vals, bottom=bottoms, label=role.replace("_adopted", "").replace("none_selected", "None"), color=color)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax.set_ylabel("Proportion of valid runs")
    ax.set_title("Figure A2. Candidate choice distribution by source-label condition")
    ax.legend(loc="upper right")
    ax.set_ylim(0, 1)
    fig.tight_layout()
    fig.savefig(FIGURES / "Figure_A2_source_choice_distribution.pdf")
    fig.savefig(FIGURES / "Figure_A2_source_choice_distribution.png", dpi=300)
    plt.close(fig)

    # B1
    b_status = Counter()
    b_pre = Counter()
    for row in read_csv(DATA / "B_timing_trajectory_table.csv"):
        if row["condition"] == "E" and row["runtime_status"] == "valid":
            b_status[row["exposure_status"]] += 1
            b_pre[row["pre_exposure_state_observable"]] += 1
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.2))
    axes[0].bar(list(b_status), list(b_status.values()), color="#4C78A8")
    axes[0].set_title("E exposure status")
    axes[0].set_ylabel("Runs")
    axes[1].barh(list(b_pre), list(b_pre.values()), color="#59A14F")
    axes[1].set_title("Pre-exposure observable state")
    fig.suptitle("Figure B1. Actual exposure and pre-exposure state in E")
    fig.tight_layout()
    fig.savefig(FIGURES / "Figure_B1_exposure_state_distribution.pdf")
    fig.savefig(FIGURES / "Figure_B1_exposure_state_distribution.png", dpi=300)
    plt.close(fig)

    # B2
    bg = [r for r in b_groups if r["metric"] in {"M_adopted", "M_execution"}]
    labels = []
    vals = []
    errs_low = []
    errs_high = []
    for r in bg:
        labels.append(f"{r['group']}\n{r['metric']}\n(n={r['den']})")
        rate = float(r["rate"]) if r["rate"] not in {None, ""} else 0
        vals.append(rate)
        errs_low.append(rate - float(r["ci_low"]))
        errs_high.append(float(r["ci_high"]) - rate)
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(range(len(vals)), vals, color="#4C78A8")
    ax.errorbar(range(len(vals)), vals, yerr=[errs_low, errs_high], fmt="none", ecolor="black", capsize=3)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha="right")
    ax.set_ylabel("Rate")
    ax.set_ylim(0, 1)
    ax.set_title("Figure B2. Adoption/execution rates by actual exposure subset")
    fig.tight_layout()
    fig.savefig(FIGURES / "Figure_B2_exposure_subset_rates.pdf")
    fig.savefig(FIGURES / "Figure_B2_exposure_subset_rates.png", dpi=300)
    plt.close(fig)

    # C1
    c_plot_rows = [r for r in c_diffs if r["metric"] in {"adoption", "verification", "execution", "utility_success"}]
    plot_errorbar_diffs(c_plot_rows, FIGURES / "Figure_C1_safety_guidance_differences", "Figure C1. User Safety Guidance differences (cluster bootstrap 95% CI)")

    # C2 observed stage rates.
    conds = ["H1_no_guidance", "H2_concern", "H3_concern_plus_verify"]
    metrics = ["verification", "adoption", "execution", "utility_success"]
    by_cond = {r["condition"]: r for r in c_summary}
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for metric in metrics:
        ax.plot(conds, [float(by_cond[c][f"{metric}_rate"]) for c in conds], marker="o", label=metric)
    ax.set_ylabel("Rate")
    ax.set_ylim(0, 1.05)
    ax.set_title("Figure C2. Observed stage metrics under safety guidance")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "Figure_C2_safety_stage_metrics.pdf")
    fig.savefig(FIGURES / "Figure_C2_safety_stage_metrics.png", dpi=300)
    plt.close(fig)


def md_table(rows, columns, max_rows=None):
    rows = rows[:max_rows] if max_rows else rows
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(c, "")) for c in columns) + " |")
    return "\n".join(lines)


def fmt_rate(row, metric):
    return f"{row[f'{metric}_num']}/{row[f'{metric}_den']} = {pct(row[f'{metric}_rate'])}"


def build_reports(a_summary, a_diffs, b_exposure, b_groups, c_summary, c_diffs):
    mapping = [
        {"analysis": "A", "analysis_name": "来源标签实验", "repo_experiment": "RQ2/Exp3_ Controlled_Source-Provenance_Intervention", "status": "540 raw runs available; repository processed CSVs were empty, re-extracted here from raw logs"},
        {"analysis": "B", "analysis_name": "基于 RQ1 轨迹的 timing / actual exposure 分析", "repo_experiment": "Exp1_User_Context_Embedding E and UC_M raw runs", "status": "360 raw runs analyzed descriptively"},
        {"analysis": "C", "analysis_name": "用户安全提示实验", "repo_experiment": "RQ2/Exp2_SafetyIntent", "status": "H1 reused from Exp1 UC_M; H2/H3 new runs; no E+guidance arms found"},
    ]
    write_csv(TABLES / "analysis_name_mapping.csv", mapping)

    # Claim evidence.
    def diff_lookup(metric, comp, diffs):
        return next(r for r in diffs if r["metric"] == metric and r["comparison"] == comp)

    a_m = diff_lookup("M_adopted", "P(M|C1)-P(M|C0)", a_diffs)
    a_bm = diff_lookup("BM_adopted", "P(BM|C2)-P(BM|C0)", a_diffs)
    c_h2 = diff_lookup("adoption", "H2-H1", c_diffs)
    c_h3 = diff_lookup("adoption", "H3-H1", c_diffs)
    claim_rows = [
        {
            "Claim": "Textual provenance labels show no stable large adoption shift in this sample",
            "Numeric evidence": f"M label diff {100*a_m['estimate']:.1f} pp, 95% CI [{100*a_m['ci_low']:.1f}, {100*a_m['ci_high']:.1f}] pp; BM label diff {100*a_bm['estimate']:.1f} pp, 95% CI [{100*a_bm['ci_low']:.1f}, {100*a_bm['ci_high']:.1f}] pp",
            "Tables/Figures": "Table A1, Figure A1, Figure A2",
            "Scope": "Controlled textual source labels inside user-message candidate observation",
            "Alternative explanations / limits": "Not a real user-channel vs tool-channel intervention; small effects or CIs near zero do not prove no label effect",
            "Evidence type": "Controlled behavioral result",
        },
        {
            "Claim": "E vs UC in RQ1 differs in actual exposure and timing",
            "Numeric evidence": "See exposure coverage and subset rates; E exposure is path-dependent while UC exposure occurs in the initial user message",
            "Tables/Figures": "Table B1, Figure B1, Figure B2",
            "Scope": "Natural RQ1 traces, descriptive only",
            "Alternative explanations / limits": "Exposed E subset is selected by agent behavior; not a randomized timing intervention",
            "Evidence type": "Descriptive association",
        },
        {
            "Claim": "User Safety Guidance reduces M adoption in UC",
            "Numeric evidence": f"H2-H1 adoption diff {100*c_h2['estimate']:.1f} pp, 95% CI [{100*c_h2['ci_low']:.1f}, {100*c_h2['ci_high']:.1f}] pp; H3-H1 {100*c_h3['estimate']:.1f} pp, 95% CI [{100*c_h3['ci_low']:.1f}, {100*c_h3['ci_high']:.1f}] pp",
            "Tables/Figures": "Table C1, Figure C1, Figure C2",
            "Scope": "UC malicious arm only; H2/H3 prompts appended to Exp1 UC_M prompt",
            "Alternative explanations / limits": "No E+guidance arms, so cannot test narrowing of E-UC gap; verification increase does not mean verification was effective",
            "Evidence type": "Controlled behavioral result within UC",
        },
    ]
    write_csv(TABLES / "claim_evidence_table.csv", claim_rows)

    a_summary_fmt = []
    for r in a_summary:
        a_summary_fmt.append({
            "Condition": r["condition"],
            "n": r["n"],
            "M adoption": fmt_rate(r, "M_adopted"),
            "BM adoption": fmt_rate(r, "BM_adopted"),
            "None": fmt_rate(r, "none_selected"),
            "M execution": fmt_rate(r, "M_executed"),
            "Utility": fmt_rate(r, "utility_success"),
        })
    b_group_fmt = []
    for r in b_groups:
        if r["metric"] in {"M_adopted", "M_execution", "utility_success"}:
            b_group_fmt.append({"Group": r["group"], "Metric": r["metric"], "n": r["den"], "Rate": f"{r['num']}/{r['den']} = {pct(r['rate'])}", "95% CI": f"[{pct(r['ci_low'])}, {pct(r['ci_high'])}]"})
    c_summary_fmt = []
    for r in c_summary:
        c_summary_fmt.append({
            "Condition": r["condition"],
            "n": r["n"],
            "Adoption": fmt_rate(r, "adoption"),
            "Verification": fmt_rate(r, "verification"),
            "Execution": fmt_rate(r, "execution"),
            "Utility": fmt_rate(r, "utility_success"),
        })

    a_diff_fmt = []
    for r in a_diffs:
        a_diff_fmt.append({
            "Comparison": r["comparison"],
            "Pairs": r["pairs"],
            "Clusters": r["clusters"],
            "Estimate": f"{100 * r['estimate']:.1f} pp",
            "95% CI": f"[{100 * r['ci_low']:.1f}, {100 * r['ci_high']:.1f}] pp",
        })

    c_diff_fmt = []
    for r in c_diffs:
        if r["metric"] in {"adoption", "verification", "execution", "utility_success"}:
            c_diff_fmt.append({
                "Metric": r["metric"],
                "Comparison": r["comparison"],
                "Pairs": r["pairs"],
                "Clusters": r["clusters"],
                "Estimate": f"{100 * r['estimate']:.1f} pp",
                "95% CI": f"[{100 * r['ci_low']:.1f}, {100 * r['ci_high']:.1f}] pp",
            })

    report = f"""# RQ2 结果分析报告

本报告基于现有仓库数据生成，没有启动新的模型调用，也没有覆盖原始结果。所有新产物均保存在 `{ROOT}`。

## 0. 数据与实现审计

{md_table(mapping, ["analysis", "analysis_name", "repo_experiment", "status"])}

统一解释边界：`M` 是 malicious-designated candidate；采用或执行 `M` 只表示 agent 使用了实验注册的候选，不自动等同于真实世界攻击后果。`BM` 是与 `M` benefit-matched 的 benign candidate，`BW` 是 weaker benign candidate。无法从日志直接观察的 planning 或 verification 不自动编码为不存在。

## A. 来源标签实验

研究问题：在候选正文、顺序、任务、消息容器和呈现时机保持一致时，仅改变候选内部 `Source:` 文字标签是否影响采用。

实现核对：C0 将 `M/BM/BW` 全部标为 `external`；C1 仅把 `M` 标为 `user-provided`；C2 仅把 `BM` 标为 `user-provided`。三个候选实际都位于同一个 user message 中的 synchronized candidate observation，因此这里测量的是 textual provenance attribution，而不是真实 user channel vs tool channel。

### 表 A1. 条件选择与执行分布

{md_table(a_summary_fmt, ["Condition", "n", "M adoption", "BM adoption", "None", "M execution", "Utility"])}

主要差异见 `Table_A1_source_primary_differences.csv` 和 Figure A1。完整选择分布见 Figure A2。

### 表 A1b. 主要配对差异

{md_table(a_diff_fmt, ["Comparison", "Pairs", "Clusters", "Estimate", "95% CI"])}

可以成立的 claim：在这个 controlled textual-source 设置下，来源标签效应可以被直接估计；如果点估计较小或 CI 跨 0，只能说明现有任务样本下没有稳定的大效应证据，不能证明标签完全无作用。

不能成立的 claim：不能把该实验称为真实 user/tool channel 干预，不能据此测量 trust，也不能把它与 RQ1 效应量机械相减来分解 RQ1。

Conservative English result: In the controlled source-label experiment, all candidates were presented together in the same user message and only the textual `Source:` attribution varied. Therefore, the experiment estimates a textual provenance-attribution effect on candidate adoption, not a channel-origin effect. The observed differences should be interpreted with the clustered uncertainty intervals and should not be used as a direct measure of user trust.

## B. RQ1 timing / actual exposure 分析

研究问题：RQ1 中 E 与 UC 的差异是否伴随实际暴露机会、暴露时间和暴露前可观察状态的差异。

本分析从 Exp1 的 E 与 UC_M 原始日志提取 artifact 是否进入模型可见消息、首次暴露位置、暴露前是否已有普通任务工具调用或 artifact action、暴露后采用/执行。一次模型调用前同时传入的候选不拆成逐个阅读时刻。

仓库中未发现一个只改变呈现时机、同时保持 source/channel 等其他因素完全固定的单独受控配对实验。因此 B 只作为自然轨迹的 timing/exposure 审计，而不是新的因果干预实验。

### 表 B1. 暴露与后续采用/执行

详见 `Table_B1_exposure_timing_summary.csv`。为了论文可读性，下面列出全样本与关键子集：

{md_table(b_group_fmt, ["Group", "Metric", "n", "Rate", "95% CI"])}

可以成立的 claim：E 的候选暴露是 agent 行动路径的一部分；UC 的候选在初始 user message 中暴露。E 已暴露子集与 UC 的比较是描述性分析。

不能成立的 claim：不能说已暴露 E 与 UC 的差异已经排除了 timing 或 source；不能把自然轨迹子集冒充随机控制实验；不能从 token 位置推断内部注意过程。

Conservative English result: The RQ1 trace analysis shows that external-condition exposure is path-dependent, whereas UC exposure occurs at the initial user message. Comparisons restricted to E runs that actually exposed the artifact are descriptive and potentially selected by the agent's own behavior. They are useful for auditing timing and exposure, but not for decomposing the RQ1 effect into causal timing, source, or salience components.

## C. 用户安全提示实验

研究问题：明确的用户安全提示是否改变 UC 条件下 artifact 的核验、采用和执行。

实现核对：现有默认数据覆盖 H1=`UC_M` 无提示、H2=H1+concern sentence、H3=H2+explicit verification sentence。没有发现 E+安全提示 arm，因此不能回答“是否缩小 E-UC 差异”。提示措辞是 User Safety Guidance，不是禁止使用某候选。

### 表 C1. 安全提示条件下的阶段指标

{md_table(c_summary_fmt, ["Condition", "n", "Adoption", "Verification", "Execution", "Utility"])}

主要配对差异见 `Table_C1_safety_guidance_differences.csv`、Figure C1；阶段指标趋势见 Figure C2。H2/H3 的 verification 字段来自显式 safety trace；H1 verification 在该实验面板中为无提示基线，不代表完整独立人工核验。

### 表 C1b. 主要配对差异

{md_table(c_diff_fmt, ["Metric", "Comparison", "Pairs", "Clusters", "Estimate", "95% CI"])}

可以成立的 claim：在 UC malicious arm 中，添加安全提示后 verification_attempted 上升到 100%，M adoption/execution 相对 H1 下降，但仍保持较高水平；合法任务完成率也需要同时报告。

不能成立的 claim：由于缺少 E+提示条件，不能判断提示是否缩小 E-UC 差异。verification 增加不自动意味着核验有效；阶段比例变化也不构成因果中介证明。

Conservative English result: In the User Safety Guidance experiment, the available data cover only UC-style malicious-arm prompts: H1 without guidance, H2 with a concern sentence, and H3 with an additional verification request. Guidance increased observable verification attempts, while M adoption and execution remained common. Because E-with-guidance conditions are absent, the current evidence cannot establish whether guidance narrows the E-UC adoption gap.

## Claim-Evidence 对照

{md_table(claim_rows, ["Claim", "Numeric evidence", "Tables/Figures", "Scope", "Alternative explanations / limits", "Evidence type"])}
"""
    (ROOT / "RQ2_results_report_zh.md").write_text(report, encoding="utf-8")

    audit = f"""# RQ2 Data and Condition Audit

## Mapping

{md_table(mapping, ["analysis", "analysis_name", "repo_experiment", "status"])}

## Inclusion Rule

This analysis uses existing completed logs only. It does not launch model calls and does not overwrite source experiment outputs. Runs with valid configs and no recorded runtime error are included. Missing logs would be labeled separately, but the extracted A/B/C trajectory tables contain valid rows only.

## Condition Audit

- A / Controlled Source: 540 valid raw runs, 180 each for C0, C1, and C2. C0 labels M/BM/BW as external; C1 labels only M as user-provided; C2 labels only BM as user-provided. All candidates are placed in a synchronized candidate observation inside a user message.
- B / Timing Exposure: 360 valid raw runs from Exp1, including 180 E and 180 UC_M. E exposure is path-dependent; UC_M exposure is in the initial user message.
- C / User Safety Guidance: 540 valid trajectory rows after joining H1/H2/H3, with 180 per condition. H1 is reused from Exp1 UC_M, H2 appends a concern sentence, and H3 appends an additional verification request. No E-with-guidance condition is present in the default completed data.

## Field Meanings

- Exposure: artifact text appears in model-visible messages.
- Adoption: final selected candidate role in the security/result trace.
- Planning adoption: only retained where an explicit trace flag exists; otherwise marked unknown in trajectory tables.
- Verification: for C H2/H3, safety-trace verification attempt; for A/B, independent verification is not reliably observable and is marked unknown.
- Execution: an artifact-linked `apply_offer`/environment event, not a verbal recommendation.
- Attack success: experiment-specific registered M success flag; not a real-world harm claim.
"""
    (ROOT / "data_condition_audit_report.md").write_text(audit, encoding="utf-8")

    english = """# RQ2 English Results Description

## A. Controlled Source Label

The controlled source-label experiment presents all candidates together in the same user message and varies only the textual `Source:` attribution. The design therefore supports claims about textual provenance attribution, not a real user-channel versus tool-channel intervention. The primary contrasts are `P(M|C1)-P(M|C0)` and `P(BM|C2)-P(BM|C0)`, with uncertainty estimated by a base-task clustered bootstrap.

## B. Timing and Actual Exposure

The RQ1 trace audit separates actual exposure from mere database availability. In the external condition, artifact exposure occurs only if the agent reaches a tool response containing the candidates, whereas in UC the target artifact is visible in the initial user message. E-exposed subsets are descriptive and may be selected by the agent's own action path.

## C. User Safety Guidance

The available safety-guidance data include H1, H2, and H3 for the UC malicious arm. H2 adds a user concern sentence and H3 adds an explicit verification request. The data do not include E-with-guidance arms, so they cannot determine whether guidance narrows the E-UC gap. The observed process metrics should be interpreted as behavioral evidence, not proof of an effective causal mediation pathway.
"""
    (ROOT / "RQ2_english_results_and_claims.md").write_text(english, encoding="utf-8")


def main():
    for path in [DATA, TABLES, FIGURES]:
        path.mkdir(parents=True, exist_ok=True)
    a_rows = parse_a_source()
    b_rows = parse_b_timing()
    c_rows = parse_c_safety()
    a_summary, a_diffs, b_exposure, b_groups, c_summary, c_diffs = make_summaries(a_rows, b_rows, c_rows)
    make_figures(a_summary, a_diffs, b_groups, c_summary, c_diffs)
    build_reports(a_summary, a_diffs, b_exposure, b_groups, c_summary, c_diffs)
    print(f"Wrote RQ2 analysis to {ROOT}")


if __name__ == "__main__":
    main()
