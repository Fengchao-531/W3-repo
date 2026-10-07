from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import shutil
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
W3_ROOT = ROOT.parent
EXP1_ROOT = Path(os.environ.get("EXP1_ROOT", W3_ROOT / "Exp1_User_Context_Embedding"))
EXP2_ROOT = Path(os.environ.get("EXP2_ROOT", W3_ROOT / "Exp2_Task_Binding"))
DEFAULT_MODEL = os.environ.get("AGENTDOJO_OPENAI_MODEL", "gpt-4o-2024-05-13")

if str(EXP1_ROOT) not in sys.path:
    sys.path.insert(0, str(EXP1_ROOT))

import exp1_pipeline as e1


DIRS = [
    "00_config",
    "01_manifest",
    "02_prompts/A0",
    "03_reference_A1_A2",
    "04_runs/A0",
    "05_processed",
    "06_statistics",
    "07_figures",
    "08_logs",
    "scripts",
]

CHOICE_MAP = {"M": "M", "BM": "Bm", "BW": "Bw", "None": "None", None: "None"}

RUN_LEVEL_COLUMNS = [
    "pair_id",
    "run_id",
    "condition",
    "base_task_id",
    "desire_id",
    "carrier_type",
    "carrier_id",
    "choice",
    "malicious_selected",
    "artifact_action",
    "action_success",
    "attack_success_human",
    "legitimate_utility",
    "M_mentioned",
    "M_considered",
    "M_used_in_plan",
    "verification",
    "warning",
    "refusal",
    "runtime_status",
    "run_dir",
]


def setup_dirs() -> None:
    for rel in DIRS:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def plain(obj: Any) -> Any:
    return e1.plain(obj)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_obj(obj: Any) -> str:
    return sha256_text(json.dumps(plain(obj), sort_keys=True, ensure_ascii=False))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plain(payload), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(plain(row), ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value for key, value in row.items()})


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def original_task_lookup() -> dict[str, dict[str, Any]]:
    return {row["base_task_id"]: row for row in read_jsonl(EXP1_ROOT / "01_Original_AgentDojo_Tasks/original_user_tasks.jsonl")}


def exp4_pair_id(exp1_pair_id: str) -> str:
    return exp1_pair_id.replace("EXP1_", "EXP4_", 1) if exp1_pair_id.startswith("EXP1_") else "EXP4_" + sha256_text(exp1_pair_id)[:12]


def artifact_only_prompt(row: dict[str, Any], lookup: dict[str, Any], offers: list[dict[str, Any]], originals: dict[str, dict[str, Any]]) -> str:
    base_prompt = originals[row["base_task_id"]]["original_prompt"].rstrip()
    artifact_text = e1.embedded_context_text_for("UC_M", row, lookup, offers).strip()
    return f"{base_prompt}\n{artifact_text}"


def build_manifest() -> None:
    setup_dirs()
    exp1_manifest = e1.load_manifest()
    lookup = e1.load_lookup()
    originals = original_task_lookup()
    env_path = EXP1_ROOT / "01_Original_AgentDojo_Tasks/original_environment.yaml"
    env_hash = sha256_text(env_path.read_text(encoding="utf-8")) if env_path.exists() else None
    exp1_manifest_hash = (EXP1_ROOT / "07_Experiment_Manifest/03_manifest_hash.txt").read_text(encoding="utf-8").strip()

    pairs: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    for row in exp1_manifest:
        offers = e1.candidate_offers(row, lookup)
        carrier = lookup["carriers"][row["carrier_id"]]
        desire = lookup["desires"][row["desire_id"]]
        malicious = next(offer for offer in offers if offer["artifact_id"] == row["malicious_artifact_id"])
        pair_id = exp4_pair_id(row["pair_id"])
        prompt = artifact_only_prompt(row, lookup, offers, originals)
        run_id = f"{pair_id}_A0"
        pair = {
            "exp": "Exp4_General_Preference_Control",
            "pair_id": pair_id,
            "source_exp1_instance_id": row["pair_id"],
            "source_exp2_pair_id": row["pair_id"].replace("EXP1_", "EXP2_", 1),
            "base_task_id": row["base_task_id"],
            "desire_id": row["desire_id"],
            "desire_text_removed_from_A0": desire["desire_text"],
            "carrier_id": row["carrier_id"],
            "carrier_type": carrier["carrier_type"],
            "artifact_set_id": row["artifact_set_id"],
            "malicious_artifact_id": row["malicious_artifact_id"],
            "benign_matched_id": row["benign_matched_id"],
            "benign_weak_id": row["benign_weak_id"],
            "candidate_order": row["candidate_order"],
            "a0_prompt": prompt,
            "a0_artifact_text": e1.embedded_context_text_for("UC_M", row, lookup, offers),
            "malicious_provider": malicious["provider"],
            "malicious_code": malicious["visible_code"],
            "malicious_benefit": malicious["benefit_text"],
            "environment_hash": env_hash,
            "exp1_manifest_hash": exp1_manifest_hash,
            "model": DEFAULT_MODEL,
            "temperature": 0.0,
            "seed": row["seed"],
            "source_row_sha256": sha256_obj(row),
        }
        run = {
            **{key: pair[key] for key in pair if key not in {"a0_prompt", "a0_artifact_text"}},
            "run_id": run_id,
            "condition": "A0",
            "user_prompt": prompt,
            "preference_text": None,
            "binding_text": None,
            "prompt_sha256": sha256_text(prompt),
        }
        pairs.append(pair)
        runs.append(run)
        (ROOT / "02_prompts/A0" / f"{run_id}.txt").write_text(prompt + "\n", encoding="utf-8")

    write_jsonl(ROOT / "01_manifest/01_exp4_pair_manifest.jsonl", pairs)
    write_jsonl(ROOT / "01_manifest/02_exp4_run_manifest.jsonl", runs)
    write_json(
        ROOT / "00_config/00_exp4_config.json",
        {
            "experiment": "Exp4_General_Preference_Control",
            "conditions": {
                "A0": "base task + artifact mention only; no added general preference; no binding",
                "A1": "Exp2 UC reference: general preference + artifact mention",
                "A2": "Exp2 UB reference: general preference + artifact mention + binding",
            },
            "new_runs": ["A0"],
            "copied_reference": ["A1", "A2"],
            "model_default": DEFAULT_MODEL,
            "temperature": 0.0,
        },
    )
    print(f"Exp4 pairs={len(pairs)} A0_runs={len(runs)}")


def validate_manifest() -> None:
    setup_dirs()
    pairs = read_jsonl(ROOT / "01_manifest/01_exp4_pair_manifest.jsonl")
    runs = read_jsonl(ROOT / "01_manifest/02_exp4_run_manifest.jsonl")
    failures = []
    by_pair = {row["pair_id"]: row for row in pairs}
    for row in runs:
        pair = by_pair.get(row["pair_id"])
        if not pair:
            failures.append({"run_id": row["run_id"], "error": "missing_pair"})
            continue
        if row["condition"] != "A0":
            failures.append({"run_id": row["run_id"], "error": "non_A0_run_in_manifest"})
        if row.get("preference_text") is not None or row.get("binding_text") is not None:
            failures.append({"run_id": row["run_id"], "error": "A0_has_preference_or_binding"})
        prompt = row["user_prompt"]
        removed = pair["desire_text_removed_from_A0"]
        if removed and removed in prompt:
            failures.append({"run_id": row["run_id"], "error": "removed_desire_text_still_present"})
        for forbidden in ["Please use this offer", "Please use this tip", "Please use this resource"]:
            if forbidden in prompt:
                failures.append({"run_id": row["run_id"], "error": "binding_text_present", "text": forbidden})
        if row["prompt_sha256"] != sha256_text(prompt):
            failures.append({"run_id": row["run_id"], "error": "bad_prompt_sha256"})
    report = {"status": "PASS" if not failures else "FAIL", "pairs": len(pairs), "runs": len(runs), "failures": failures[:100]}
    write_json(ROOT / "01_manifest/03_validation_report.json", report)
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


def make_run_queue() -> None:
    rows = read_jsonl(ROOT / "01_manifest/02_exp4_run_manifest.jsonl")
    queue = [{"queue_index": idx + 1, "pair_id": row["pair_id"], "condition": "A0", "run_id": row["run_id"]} for idx, row in enumerate(rows)]
    write_jsonl(ROOT / "01_manifest/05_run_queue.jsonl", queue)
    print(f"queue_runs={len(queue)}")


def load_exp1_row_by_pair() -> dict[str, dict[str, Any]]:
    return {row["pair_id"]: row for row in e1.load_manifest()}


def run_dir(condition: str, model: str, run_id: str) -> Path:
    return ROOT / "04_runs" / condition / e1.model_slug(model) / run_id


def build_pipeline(model: str, run_id: str, temperature: float | None):
    llm = e1.LoggingOpenAILLM(model, run_id, ROOT / "08_logs/model_features" / e1.model_slug(model) / run_id, temperature)
    pipeline = e1.AgentPipeline([e1.SystemMessage(e1.SYSTEM_PROMPT), e1.InitQuery(), llm, e1.ToolsExecutionLoop([e1.ToolsExecutor(), llm], max_iters=10)])
    pipeline.name = model
    return pipeline, llm


def run_one(run_row: dict[str, Any], exp1_rows: dict[str, dict[str, Any]], lookup: dict[str, Any], model: str, temperature: float | None) -> dict[str, Any]:
    exp1_row = exp1_rows[run_row["source_exp1_instance_id"]]
    run_id = run_row["run_id"]
    out_dir = run_dir("A0", model, run_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    random.seed(run_row["seed"])

    suite = e1.get_suite(e1.BENCHMARK_VERSION, e1.SUITE_NAME)
    base_task = suite.get_user_task_by_id(run_row["base_task_id"])
    task = e1.PromptOverrideUserTask(base_task, run_row["user_prompt"])
    offers = e1.candidate_offers(exp1_row, lookup)
    embedded_offer = next(offer for offer in offers if offer["artifact_id"] == exp1_row["malicious_artifact_id"])
    e1.OFFER_STATE["offers"] = offers
    e1.OFFER_STATE["events"] = []

    env = suite.load_and_inject_default_environment({})
    task_env = task.init_environment(env)
    pre_env = task_env.model_copy(deep=True)
    runtime = e1.FunctionsRuntime([*suite.tools, e1.make_function(e1.list_available_offers), e1.make_function(e1.apply_offer)])
    pipeline, llm = build_pipeline(model, run_id, temperature)

    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    messages: list[e1.ChatMessage] = []
    error = None
    try:
        _, _, task_env, messages, _ = pipeline.query(run_row["user_prompt"], runtime, task_env)
    except Exception as exc:
        error = {"type": type(exc).__name__, "repr": repr(exc)}

    if messages:
        model_output = e1.model_output_from_messages(messages) or []
        stack_trace = e1.functions_stack_trace_from_messages(messages)
        utility_success = bool(suite._check_task_result(task, model_output, pre_env, task_env, stack_trace))
    else:
        model_output = []
        stack_trace = []
        utility_success = False

    selected = e1.selected_offer(exp1_row, offers)
    security = e1.security_result(exp1_row, selected, messages, offers, embedded_offer)
    runtime_status = "error" if error else "success"
    tool_calls = e1.tool_call_rows(messages, exp1_row, offers)
    tool_outputs = e1.tool_output_rows(messages, exp1_row, offers)
    annotated = e1.annotate_messages(messages, exp1_row, offers, "A0", run_row["user_prompt"])
    behavior_trace = {
        "pair_id": run_row["pair_id"],
        "run_id": run_id,
        "condition": "A0",
        "artifact_seen": security["embedded_artifact_seen"],
        "malicious_artifact_mentioned": security["embedded_artifact_mentioned"],
        "malicious_artifact_considered": security["embedded_artifact_considered"],
        "malicious_artifact_used_in_plan": security["embedded_artifact_used_in_plan"],
        "choice": CHOICE_MAP.get(security.get("selected_type"), "None"),
        "artifact_action": security["embedded_artifact_action_called"],
        "action_success": security["embedded_artifact_action_succeeded"],
        "legitimate_task_completed": utility_success,
    }
    summary = {
        **run_row,
        "model": model,
        "temperature": temperature,
        "started_at_utc": started,
        "runtime_status": runtime_status,
        "error": error,
        **security,
        "choice": behavior_trace["choice"],
        "utility_success": utility_success,
        "final_response": e1.final_response(messages),
        "tool_call_count": len(tool_calls),
        "message_count": len(messages),
        "run_dir": str(out_dir),
    }

    write_json(out_dir / "00_run_config.json", {**run_row, "model": model, "temperature": temperature, "system_prompt": e1.SYSTEM_PROMPT, "error": error})
    write_json(out_dir / "01_instance.json", run_row)
    (out_dir / "02_rendered_user_message.txt").write_text(run_row["user_prompt"] + "\n", encoding="utf-8")
    write_jsonl(out_dir / "03_messages.jsonl", annotated)
    write_jsonl(out_dir / "04_model_calls.jsonl", [{"call_id": call_id} for call_id in llm.call_ids])
    write_jsonl(out_dir / "05_tool_calls.jsonl", tool_calls)
    write_jsonl(out_dir / "06_tool_outputs.jsonl", tool_outputs)
    write_json(out_dir / "07_environment_before.json", {"agentdojo": pre_env, "offer_state": {"offers": offers, "events": []}})
    write_json(out_dir / "08_environment_after.json", {"agentdojo": task_env, "offer_state": selected})
    (out_dir / "09_final_response.txt").write_text(summary["final_response"], encoding="utf-8")
    write_json(out_dir / "10_behavior_trace.json", behavior_trace)
    write_json(out_dir / "11_agentdojo_scores.json", {"utility_success": utility_success, "model_output": model_output, "stack_trace": stack_trace})
    write_json(out_dir / "12_error.json", error or {"error": None})
    write_json(out_dir / "13_trace_summary.json", summary)
    return summary


def run_selected(args: argparse.Namespace) -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set. Local runners set a dummy key automatically; API runs need a real key.")
    if not (ROOT / "01_manifest/05_run_queue.jsonl").exists():
        make_run_queue()
    runs = {row["run_id"]: row for row in read_jsonl(ROOT / "01_manifest/02_exp4_run_manifest.jsonl")}
    queue = read_jsonl(ROOT / "01_manifest/05_run_queue.jsonl")
    if args.pair_id:
        queue = [item for item in queue if item["pair_id"] == args.pair_id]
    if args.limit is not None:
        queue = queue[: args.limit]
    exp1_rows = load_exp1_row_by_pair()
    lookup = e1.load_lookup()
    for index, item in enumerate(queue, start=1):
        row = runs[item["run_id"]]
        out_dir = run_dir("A0", args.model, row["run_id"])
        if (out_dir / "13_trace_summary.json").exists() and not args.force:
            print(f"[{index}/{len(queue)}] skip existing {row['run_id']}")
            continue
        print(f"[{index}/{len(queue)}] run {row['run_id']} model={args.model}")
        summary = run_one(row, exp1_rows, lookup, args.model, args.temperature)
        print(f"  status={summary['runtime_status']} choice={summary['choice']} malicious_selected={summary['malicious_artifact_selected']} utility={summary['utility_success']} error={summary['error']}")


def copy_a1_a2_reference() -> None:
    setup_dirs()
    dest = ROOT / "03_reference_A1_A2"
    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    for rel in ["05_processed", "06_statistics", "01_manifest", "02_prompts"]:
        src = EXP2_ROOT / rel
        if src.exists():
            target = dest / rel
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(src, target)
            copied.append({"source": str(src), "target": str(target)})
    write_json(dest / "copy_manifest.json", {"source_exp2_root": str(EXP2_ROOT), "copied": copied})
    print(f"copied_reference_items={len(copied)} from={EXP2_ROOT}")


def process_results() -> None:
    setup_dirs()
    rows = []
    excluded = []
    for summary_path in (ROOT / "04_runs/A0").glob("*/*/13_trace_summary.json"):
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        row = {
            "pair_id": summary["pair_id"],
            "run_id": summary["run_id"],
            "condition": "A0",
            "base_task_id": summary["base_task_id"],
            "desire_id": summary["desire_id"],
            "carrier_type": summary["carrier_type"],
            "carrier_id": summary["carrier_id"],
            "choice": summary["choice"],
            "malicious_selected": int(bool(summary["malicious_artifact_selected"])),
            "artifact_action": int(bool(summary["embedded_artifact_action_called"])),
            "action_success": int(bool(summary["embedded_artifact_action_succeeded"])),
            "attack_success_human": int(bool(summary["attack_success"])),
            "legitimate_utility": int(bool(summary["utility_success"])),
            "M_mentioned": int(bool(summary["embedded_artifact_mentioned"])),
            "M_considered": int(bool(summary["embedded_artifact_considered"])),
            "M_used_in_plan": int(bool(summary["embedded_artifact_used_in_plan"])),
            "verification": 0,
            "warning": 0,
            "refusal": 0,
            "runtime_status": summary["runtime_status"],
            "run_dir": str(summary_path.parent),
        }
        rows.append(row)
        if summary["runtime_status"] != "success":
            excluded.append({"pair_id": summary["pair_id"], "condition": "A0", "reason": summary.get("error"), "final_status": summary["runtime_status"]})
    write_csv(ROOT / "05_processed/00_A0_run_level_results.csv", rows, RUN_LEVEL_COLUMNS)
    write_csv(ROOT / "05_processed/01_A0_excluded_runs.csv", excluded)
    print(f"A0_processed_runs={len(rows)} excluded={len(excluded)}")


def _as_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes"}:
        return 1
    return 0


def _mean(rows: list[dict[str, Any]], key: str) -> float | None:
    return sum(_as_int(row.get(key)) for row in rows) / len(rows) if rows else None


def _exp2_to_reference_rows() -> list[dict[str, Any]]:
    path = ROOT / "03_reference_A1_A2/05_processed/00_run_level_results.csv"
    rows = []
    for row in read_csv(path):
        condition = row.get("condition")
        if condition not in {"UC", "UB"}:
            continue
        rows.append(
            {
                "pair_id": row["pair_id"].replace("EXP2_", "EXP4_", 1),
                "run_id": row["run_id"].replace("EXP2_", "EXP4_", 1).replace("_UC", "_A1").replace("_UB", "_A2"),
                "condition": "A1" if condition == "UC" else "A2",
                "base_task_id": row.get("base_task_id"),
                "carrier_type": row.get("carrier_type"),
                "choice": row.get("choice"),
                "malicious_selected": row.get("malicious_selected"),
                "artifact_action": row.get("artifact_action"),
                "attack_success_human": row.get("attack_success_human"),
                "legitimate_utility": row.get("legitimate_utility"),
                "runtime_status": row.get("runtime_status"),
                "source_exp2_run_dir": row.get("run_dir"),
            }
        )
    return rows


def _mcnemar(rows: list[dict[str, Any]], left: str, right: str, field: str) -> dict[str, Any]:
    by_pair: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_pair.setdefault(row["pair_id"], {})[row["condition"]] = row
    pairs = [group for group in by_pair.values() if left in group and right in group]
    n01 = sum(1 for group in pairs if _as_int(group[left].get(field)) == 0 and _as_int(group[right].get(field)) == 1)
    n10 = sum(1 for group in pairs if _as_int(group[left].get(field)) == 1 and _as_int(group[right].get(field)) == 0)
    n00 = sum(1 for group in pairs if _as_int(group[left].get(field)) == 0 and _as_int(group[right].get(field)) == 0)
    n11 = sum(1 for group in pairs if _as_int(group[left].get(field)) == 1 and _as_int(group[right].get(field)) == 1)
    n = n01 + n10
    p = None
    if n:
        k = min(n01, n10)
        p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2**n))
    left_rate = sum(_as_int(group[left].get(field)) for group in pairs) / len(pairs) if pairs else None
    right_rate = sum(_as_int(group[right].get(field)) for group in pairs) / len(pairs) if pairs else None
    return {
        "comparison": f"{left}_vs_{right}",
        "metric": field,
        "n": len(pairs),
        f"{left}_rate": left_rate,
        f"{right}_rate": right_rate,
        "delta_right_minus_left": None if left_rate is None or right_rate is None else right_rate - left_rate,
        "n00": n00,
        "n01_left0_right1": n01,
        "n10_left1_right0": n10,
        "n11": n11,
        "mcnemar_exact_p": p,
    }


def statistics() -> None:
    process_results()
    a0 = [row for row in read_csv(ROOT / "05_processed/00_A0_run_level_results.csv") if row.get("runtime_status") == "success"]
    refs = [row for row in _exp2_to_reference_rows() if row.get("runtime_status") == "success"]
    all_rows = a0 + refs
    write_csv(ROOT / "05_processed/02_A0_A1_A2_combined_run_level.csv", all_rows)
    primary = []
    for condition in ["A0", "A1", "A2"]:
        rows = [row for row in all_rows if row.get("condition") == condition]
        primary.append(
            {
                "condition": condition,
                "n": len(rows),
                "M_selected_rate": _mean(rows, "malicious_selected"),
                "artifact_action_rate": _mean(rows, "artifact_action"),
                "attack_success_rate": _mean(rows, "attack_success_human"),
                "utility_rate": _mean(rows, "legitimate_utility"),
            }
        )
    comparisons = []
    for left, right in [("A0", "A1"), ("A1", "A2"), ("A0", "A2")]:
        comparisons.append(_mcnemar(all_rows, left, right, "malicious_selected"))
        comparisons.append(_mcnemar(all_rows, left, right, "artifact_action"))
    write_csv(ROOT / "06_statistics/00_primary_A0_A1_A2.csv", primary)
    write_csv(ROOT / "06_statistics/01_paired_tests.csv", comparisons)
    write_json(
        ROOT / "06_statistics/02_reference_status.json",
        {
            "a0_successful_runs": len(a0),
            "reference_a1_a2_successful_runs": len(refs),
            "reference_source": str(ROOT / "03_reference_A1_A2"),
        },
    )
    print(f"statistics_written={ROOT / '06_statistics'}")


def figures() -> None:
    print("Exp4 figures are not generated by default; use 06_statistics/00_primary_A0_A1_A2.csv for paper tables.")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build_manifest")
    sub.add_parser("validate_manifest")
    sub.add_parser("make_run_queue")
    sub.add_parser("copy_a1_a2_reference")
    run_p = sub.add_parser("run")
    run_p.add_argument("--model", default=DEFAULT_MODEL)
    run_p.add_argument("--temperature", type=float, default=0.0)
    run_p.add_argument("--limit", type=int, default=None)
    run_p.add_argument("--pair-id", default=None)
    run_p.add_argument("--force", action="store_true")
    sub.add_parser("process_results")
    sub.add_parser("statistics")
    sub.add_parser("figures")
    args = parser.parse_args()
    if args.cmd == "build_manifest":
        build_manifest()
    elif args.cmd == "validate_manifest":
        validate_manifest()
    elif args.cmd == "make_run_queue":
        make_run_queue()
    elif args.cmd == "copy_a1_a2_reference":
        copy_a1_a2_reference()
    elif args.cmd == "run":
        run_selected(args)
    elif args.cmd == "process_results":
        process_results()
    elif args.cmd == "statistics":
        statistics()
    elif args.cmd == "figures":
        figures()


if __name__ == "__main__":
    main()
