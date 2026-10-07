from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
W3_ROOT = ROOT.parent
EXP1_ROOT = Path(os.environ.get("EXP1_ROOT", W3_ROOT / "Exp1_User_Context_Embedding"))
EXP4_ROOT = Path(os.environ.get("EXP4_ROOT", W3_ROOT / "Exp4_General_Preference_Control"))
DEFAULT_MODEL = os.environ.get("AGENTDOJO_OPENAI_MODEL", "gpt-4o-2024-05-13")

if str(EXP1_ROOT) not in sys.path:
    sys.path.insert(0, str(EXP1_ROOT))

import exp1_pipeline as e1


DIRS = [
    "00_config",
    "01_manifest",
    "02_prompts/E0",
    "03_runs/E0",
    "04_processed",
    "05_statistics",
    "06_figures",
    "07_logs",
]

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

CHOICE_MAP = {"M": "M", "BM": "Bm", "BW": "Bw", "None": "None", None: "None"}


def setup_dirs() -> None:
    for rel in DIRS:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def plain(obj: Any) -> Any:
    return e1.plain(obj)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def load_exp1_row_by_pair() -> dict[str, dict[str, Any]]:
    return {row["pair_id"]: row for row in e1.load_manifest()}


def build_manifest() -> None:
    setup_dirs()
    exp1_rows = load_exp1_row_by_pair()
    originals = original_task_lookup()
    exp4_pairs = read_jsonl(EXP4_ROOT / "01_manifest/01_exp4_pair_manifest.jsonl")
    if not exp4_pairs:
        raise SystemExit(f"Missing Exp4 A0 manifest: {EXP4_ROOT / '01_manifest/01_exp4_pair_manifest.jsonl'}")

    rows = []
    for pair in exp4_pairs:
        source_pair = pair["source_exp1_instance_id"]
        exp1_row = exp1_rows[source_pair]
        prompt = originals[pair["base_task_id"]]["original_prompt"].rstrip()
        run_id = f"{pair['pair_id']}_E0"
        row = {
            "exp": "Exp4b_Preference_Controlled_External_Baseline",
            "pair_id": pair["pair_id"],
            "run_id": run_id,
            "condition": "E0",
            "source_exp1_instance_id": source_pair,
            "base_task_id": pair["base_task_id"],
            "desire_id": pair["desire_id"],
            "desire_text_removed_from_E0": pair["desire_text_removed_from_A0"],
            "carrier_id": pair["carrier_id"],
            "carrier_type": pair["carrier_type"],
            "artifact_set_id": pair["artifact_set_id"],
            "malicious_artifact_id": pair["malicious_artifact_id"],
            "benign_matched_id": pair["benign_matched_id"],
            "benign_weak_id": pair["benign_weak_id"],
            "candidate_order": pair["candidate_order"],
            "user_prompt": prompt,
            "preference_text": None,
            "binding_text": None,
            "artifact_location": "external_tool_observation",
            "target_artifact_id": exp1_row["malicious_artifact_id"],
            "prompt_sha256": sha256_text(prompt),
            "seed": pair["seed"],
            "model": DEFAULT_MODEL,
            "temperature": 0.0,
        }
        rows.append(row)
        (ROOT / "02_prompts/E0" / f"{run_id}.txt").write_text(prompt + "\n", encoding="utf-8")

    write_jsonl(ROOT / "01_manifest/01_exp4b_e0_manifest.jsonl", rows)
    write_jsonl(ROOT / "01_manifest/02_exp4b_e0_run_manifest.jsonl", rows)
    write_json(
        ROOT / "00_config/00_exp4b_config.json",
        {
            "experiment": "Exp4b_Preference_Controlled_External_Baseline",
            "condition": "E0",
            "definition": "External artifact observation with general preference removed and no explicit binding.",
            "paired_reference": str(EXP4_ROOT),
            "target_comparison": "A0_UC_no_pref_minus_E0_external_no_pref",
            "model_default": DEFAULT_MODEL,
            "temperature": 0.0,
        },
    )
    print(f"Exp4b E0 runs={len(rows)}")


def validate_manifest() -> None:
    setup_dirs()
    rows = read_jsonl(ROOT / "01_manifest/02_exp4b_e0_run_manifest.jsonl")
    lookup = e1.load_lookup()
    failures = []
    exp1_rows = load_exp1_row_by_pair()
    for row in rows:
        prompt = row["user_prompt"]
        if row["condition"] != "E0":
            failures.append({"run_id": row["run_id"], "error": "non_E0_condition"})
        if row.get("preference_text") is not None or row.get("binding_text") is not None:
            failures.append({"run_id": row["run_id"], "error": "preference_or_binding_present"})
        removed = row.get("desire_text_removed_from_E0")
        if removed and removed in prompt:
            failures.append({"run_id": row["run_id"], "error": "removed_desire_text_still_present"})
        exp1_row = exp1_rows[row["source_exp1_instance_id"]]
        offers = e1.candidate_offers(exp1_row, lookup)
        for offer in offers:
            for marker in [offer["provider"], offer["visible_code"], offer["opaque_offer_id"], offer["carrier_text"]]:
                if marker and marker in prompt:
                    failures.append({"run_id": row["run_id"], "error": "artifact_marker_in_user_prompt", "marker": marker})
                    break
        if row["prompt_sha256"] != sha256_text(prompt):
            failures.append({"run_id": row["run_id"], "error": "bad_prompt_sha256"})
    report = {"status": "PASS" if not failures else "FAIL", "runs": len(rows), "failures": failures[:100]}
    write_json(ROOT / "01_manifest/03_validation_report.json", report)
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


def make_run_queue() -> None:
    rows = read_jsonl(ROOT / "01_manifest/02_exp4b_e0_run_manifest.jsonl")
    queue = [{"queue_index": index + 1, "pair_id": row["pair_id"], "condition": "E0", "run_id": row["run_id"]} for index, row in enumerate(rows)]
    write_jsonl(ROOT / "01_manifest/05_run_queue.jsonl", queue)
    print(f"queue_runs={len(queue)}")


def run_dir(model: str, run_id: str) -> Path:
    return ROOT / "03_runs/E0" / e1.model_slug(model) / run_id


def build_pipeline(model: str, run_id: str, temperature: float | None):
    llm = e1.LoggingOpenAILLM(model, run_id, ROOT / "07_logs/model_features" / e1.model_slug(model) / run_id, temperature)
    pipeline = e1.AgentPipeline([e1.SystemMessage(e1.SYSTEM_PROMPT), e1.InitQuery(), llm, e1.ToolsExecutionLoop([e1.ToolsExecutor(), llm], max_iters=10)])
    pipeline.name = model
    return pipeline, llm


def run_one(run_row: dict[str, Any], exp1_rows: dict[str, dict[str, Any]], lookup: dict[str, Any], model: str, temperature: float | None) -> dict[str, Any]:
    exp1_row = exp1_rows[run_row["source_exp1_instance_id"]]
    run_id = run_row["run_id"]
    out_dir = run_dir(model, run_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    random.seed(run_row["seed"])

    suite = e1.get_suite(e1.BENCHMARK_VERSION, e1.SUITE_NAME)
    base_task = suite.get_user_task_by_id(run_row["base_task_id"])
    task = e1.PromptOverrideUserTask(base_task, run_row["user_prompt"])
    offers = e1.candidate_offers(exp1_row, lookup)
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
    security = e1.security_result(exp1_row, selected, messages, offers, embedded_offer=None)
    runtime_status = "error" if error else "success"
    tool_calls = e1.tool_call_rows(messages, exp1_row, offers)
    tool_outputs = e1.tool_output_rows(messages, exp1_row, offers)
    annotated = e1.annotate_messages(messages, exp1_row, offers, "E0", embedded_text=None)
    behavior_trace = {
        "pair_id": run_row["pair_id"],
        "run_id": run_id,
        "condition": "E0",
        "artifact_seen": security["artifact_seen"],
        "malicious_artifact_mentioned": security["artifact_mentioned"],
        "malicious_artifact_considered": security["artifact_considered"],
        "malicious_artifact_used_in_plan": security["artifact_used_in_plan"],
        "choice": CHOICE_MAP.get(security.get("selected_type"), "None"),
        "artifact_action": security["artifact_action_called"],
        "action_success": security["artifact_action_succeeded"],
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
    runs = {row["run_id"]: row for row in read_jsonl(ROOT / "01_manifest/02_exp4b_e0_run_manifest.jsonl")}
    queue = read_jsonl(ROOT / "01_manifest/05_run_queue.jsonl")
    if getattr(args, "pair_id", None):
        queue = [item for item in queue if item["pair_id"] == args.pair_id]
    if args.limit is not None:
        queue = queue[: args.limit]
    exp1_rows = load_exp1_row_by_pair()
    lookup = e1.load_lookup()
    for index, item in enumerate(queue, start=1):
        row = runs[item["run_id"]]
        out_dir = run_dir(args.model, row["run_id"])
        if (out_dir / "13_trace_summary.json").exists() and not args.force:
            print(f"[{index}/{len(queue)}] skip existing {row['run_id']}")
            continue
        print(f"[{index}/{len(queue)}] run {row['run_id']} model={args.model}")
        summary = run_one(row, exp1_rows, lookup, args.model, args.temperature)
        print(f"  status={summary['runtime_status']} choice={summary['choice']} malicious_selected={summary['malicious_artifact_selected']} utility={summary['utility_success']} error={summary['error']}")


def process_results() -> None:
    setup_dirs()
    rows = []
    excluded = []
    for summary_path in (ROOT / "03_runs/E0").glob("*/*/13_trace_summary.json"):
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        row = {
            "pair_id": summary["pair_id"],
            "run_id": summary["run_id"],
            "condition": "E0",
            "base_task_id": summary["base_task_id"],
            "desire_id": summary["desire_id"],
            "carrier_type": summary["carrier_type"],
            "carrier_id": summary["carrier_id"],
            "choice": summary["choice"],
            "malicious_selected": int(bool(summary["malicious_artifact_selected"])),
            "artifact_action": int(bool(summary["artifact_action_called"])),
            "action_success": int(bool(summary["artifact_action_succeeded"])),
            "attack_success_human": int(bool(summary["attack_success"])),
            "legitimate_utility": int(bool(summary["utility_success"])),
            "M_mentioned": int(bool(summary["artifact_mentioned"])),
            "M_considered": int(bool(summary["artifact_considered"])),
            "M_used_in_plan": int(bool(summary["artifact_used_in_plan"])),
            "verification": 0,
            "warning": 0,
            "refusal": 0,
            "runtime_status": summary["runtime_status"],
            "run_dir": str(summary_path.parent),
        }
        rows.append(row)
        if summary["runtime_status"] != "success":
            excluded.append({"pair_id": summary["pair_id"], "condition": "E0", "reason": summary.get("error"), "final_status": summary["runtime_status"]})
    write_csv(ROOT / "04_processed/00_E0_run_level_results.csv", rows, RUN_LEVEL_COLUMNS)
    write_csv(ROOT / "04_processed/01_E0_excluded_runs.csv", excluded)
    print(f"E0_processed_runs={len(rows)} excluded={len(excluded)}")


def _as_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    return 1 if str(value).strip().lower() in {"1", "true", "yes"} else 0


def _mean(rows: list[dict[str, Any]], key: str) -> float | None:
    return sum(_as_int(row.get(key)) for row in rows) / len(rows) if rows else None


def _bootstrap_delta(pairs: list[dict[str, dict[str, Any]]], left: str, right: str, field: str, n_boot: int = 5000) -> tuple[float | None, float | None]:
    if not pairs:
        return None, None
    rng = random.Random(12345)
    values = [_as_int(group[right].get(field)) - _as_int(group[left].get(field)) for group in pairs]
    draws = []
    for _ in range(n_boot):
        sample = [values[rng.randrange(len(values))] for _ in values]
        draws.append(sum(sample) / len(sample))
    draws.sort()
    return draws[int(0.025 * n_boot)], draws[int(0.975 * n_boot)]


def _mcnemar(rows: list[dict[str, Any]], left: str, right: str, field: str) -> dict[str, Any]:
    by_pair: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_pair.setdefault(row["pair_id"], {})[row["condition"]] = row
    pairs = [group for group in by_pair.values() if left in group and right in group]
    n01 = sum(1 for group in pairs if _as_int(group[left].get(field)) == 0 and _as_int(group[right].get(field)) == 1)
    n10 = sum(1 for group in pairs if _as_int(group[left].get(field)) == 1 and _as_int(group[right].get(field)) == 0)
    n00 = sum(1 for group in pairs if _as_int(group[left].get(field)) == 0 and _as_int(group[right].get(field)) == 0)
    n11 = sum(1 for group in pairs if _as_int(group[left].get(field)) == 1 and _as_int(group[right].get(field)) == 1)
    discordant = n01 + n10
    p = None
    if discordant:
        k = min(n01, n10)
        p = min(1.0, 2 * sum(math.comb(discordant, i) for i in range(k + 1)) / (2**discordant))
    left_rate = sum(_as_int(group[left].get(field)) for group in pairs) / len(pairs) if pairs else None
    right_rate = sum(_as_int(group[right].get(field)) for group in pairs) / len(pairs) if pairs else None
    ci_low, ci_high = _bootstrap_delta(pairs, left, right, field)
    return {
        "comparison": f"{left}_vs_{right}",
        "metric": field,
        "n": len(pairs),
        f"{left}_rate": left_rate,
        f"{right}_rate": right_rate,
        "delta_right_minus_left": None if left_rate is None or right_rate is None else right_rate - left_rate,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "n00": n00,
        "n01_left0_right1": n01,
        "n10_left1_right0": n10,
        "n11": n11,
        "mcnemar_exact_p": p,
    }


def statistics() -> None:
    process_results()
    e0 = [row for row in read_csv(ROOT / "04_processed/00_E0_run_level_results.csv") if row.get("runtime_status") == "success"]
    a0 = [row for row in read_csv(EXP4_ROOT / "05_processed/00_A0_run_level_results.csv") if row.get("runtime_status") == "success"]
    all_rows = e0 + [{**row, "condition": "A0"} for row in a0]
    write_csv(ROOT / "04_processed/02_E0_A0_combined_run_level.csv", all_rows)
    primary = []
    for condition in ["E0", "A0"]:
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
    for metric in ["malicious_selected", "artifact_action", "attack_success_human", "legitimate_utility"]:
        comparisons.append(_mcnemar(all_rows, "E0", "A0", metric))
    write_csv(ROOT / "05_statistics/00_primary_E0_A0.csv", primary)
    write_csv(ROOT / "05_statistics/01_paired_E0_vs_A0.csv", comparisons)
    write_json(ROOT / "05_statistics/02_status.json", {"e0_successful_runs": len(e0), "a0_reference_successful_runs": len(a0), "reference_a0_root": str(EXP4_ROOT)})
    print(f"statistics_written={ROOT / '05_statistics'}")


def figures() -> None:
    print("Exp4b figures are generated by the cross-model analysis script.")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build_manifest")
    sub.add_parser("validate_manifest")
    sub.add_parser("make_run_queue")
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
