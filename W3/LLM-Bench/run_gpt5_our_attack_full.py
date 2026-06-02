#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter
from typing import Any

from openai import OpenAI

import run_llm_bench as bench


ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT / "datasets" / "our_attack_full.jsonl"
LEGACY_DATASET_PATH = ROOT.parent / "Attack-Methods" / "generated" / "our_attack_full.jsonl"
RESULT_BASENAME = "gpt5_our_attack_full.jsonl"


def default_dataset_path() -> Path:
    if DATASET_PATH.exists():
        return DATASET_PATH
    if LEGACY_DATASET_PATH.exists():
        return LEGACY_DATASET_PATH
    return DATASET_PATH


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run GPT-5 only on our_attack_full.jsonl, print each row's input/verdict/output, "
            "and save results incrementally to a dedicated JSONL file."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=default_dataset_path(),
        help="Optional input JSONL. Defaults to LLM-Bench/datasets/our_attack_full.jsonl.",
    )
    parser.add_argument(
        "--runtime",
        default=None,
        help="Optional runtime override. Defaults to auto-detect.",
    )
    parser.add_argument(
        "--model",
        default="gpt-5",
        help="OpenAI model id to use. Defaults to gpt-5 or the GPT_5_MODEL env override.",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=4096,
        help="Maximum output tokens for GPT-5 (includes reasoning tokens, so needs to be large).",
    )
    parser.add_argument(
        "--limit-rows",
        type=int,
        default=None,
        help="Optional row limit for smoke testing.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Recompute rows even if the dedicated result file already contains GPT-5 output/verdict.",
    )
    return parser.parse_args()


def result_path_for_runtime(runtime: str) -> Path:
    return ROOT / "result" / runtime / RESULT_BASENAME


def normalize_result_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        current = dict(row)
        current.setdefault("gpt_5_runner", "")
        current.setdefault("gpt_5_output", "")
        current.setdefault("gpt_5_verdict", "")
        current.setdefault("gpt_5_matched_anchor", "")
        normalized.append(current)
    return normalized


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_or_initialize_rows(input_path: Path, result_path: Path) -> list[dict[str, Any]]:
    if result_path.exists():
        return normalize_result_rows(bench.load_rows(result_path))
    return normalize_result_rows(bench.load_rows(input_path))


def extract_chat_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text", "")
            else:
                text = getattr(item, "text", "")
            if text:
                parts.append(text)
        return "".join(parts).strip()
    return str(content).strip()


def extract_responses_text(response: Any) -> str:
    text = getattr(response, "output_text", "")
    if text:
        return text.strip()

    parts: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            if isinstance(content, dict):
                value = content.get("text", "")
            else:
                value = getattr(content, "text", "")
            if value:
                parts.append(value)
    if parts:
        return "".join(parts).strip()

    return ""


def is_reasoning_only_incomplete(response: Any) -> bool:
    status = getattr(response, "status", None)
    incomplete = getattr(response, "incomplete_details", None)
    reason = None
    if incomplete is not None:
        if isinstance(incomplete, dict):
            reason = incomplete.get("reason")
        else:
            reason = getattr(incomplete, "reason", None)
    return status == "incomplete" and reason == "max_output_tokens"


def generate_with_gpt5(client: OpenAI, model_id: str, prompt: str, max_new_tokens: int) -> str:
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=max_new_tokens,
        )
        text = extract_chat_text(response.choices[0].message.content)
        if text:
            return text
    except Exception as exc:
        print(f"[WARN] chat.completions fallback failed: {exc}")

    retry_budget = [max_new_tokens, max(max_new_tokens * 2, 8192), max(max_new_tokens * 4, 16384)]
    last_response = None
    for token_budget in retry_budget:
        response = client.responses.create(
            model=model_id,
            input=prompt,
            max_output_tokens=token_budget,
            reasoning={"effort": "low"},
        )
        last_response = response
        text = extract_responses_text(response)
        if text:
            return text
        if is_reasoning_only_incomplete(response):
            print(
                f"[WARN] responses API returned reasoning-only output at max_output_tokens={token_budget}; retrying"
            )
            continue

    print("[WARN] GPT-5 produced no final text after all retries; saving empty output and continuing.")
    return ""


def main() -> None:
    args = parse_args()
    runtime = bench.detect_runtime(args.runtime)
    model_id = args.model.strip() or bench.resolve_model_id(bench.MODEL_SPEC_BY_SLUG["gpt_5"])
    if args.model == parser_default_model():
        model_id = bench.resolve_model_id(bench.MODEL_SPEC_BY_SLUG["gpt_5"])

    input_path = args.input.resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input dataset not found: {input_path}")

    result_path = result_path_for_runtime(runtime)
    rows = load_or_initialize_rows(input_path, result_path)
    active_rows = rows
    if args.limit_rows is not None:
        active_rows = rows[: args.limit_rows]

    client = OpenAI()
    start = perf_counter()
    processed = 0
    resumed = 0

    print(f"[GPT5_OUR_ATTACK] runtime={runtime} model={model_id}")
    print(f"[GPT5_OUR_ATTACK] input={input_path}")
    print(f"[GPT5_OUR_ATTACK] result={result_path}")
    print(f"[GPT5_OUR_ATTACK] rows={len(active_rows)}")

    for index, row in enumerate(active_rows, 1):
        already_done = row.get("gpt_5_output", "") != "" and row.get("gpt_5_verdict", "") != ""
        prompt = bench.build_prompt(row, bench.OUR_ATTACK_FULL_DATASET)

        if already_done and not args.overwrite:
            resumed += 1
            print(f"\n=== ROW {index}/{len(active_rows)} row_id={row.get('row_id')} RESUME ===")
            print("INPUT:")
            print(prompt)
            print("VERDICT:")
            print(row.get("gpt_5_verdict", ""))
            print("OUTPUT:")
            print(row.get("gpt_5_output", ""))
            continue

        output_text = generate_with_gpt5(client, model_id=model_id, prompt=prompt, max_new_tokens=args.max_new_tokens)
        verdict, matched_anchor = bench.classify_output(
            output_text=output_text,
            injection_goal=row.get("injection_goal", ""),
            injection_content=row.get("injection_content", ""),
        )

        row["gpt_5_runner"] = runtime
        row["gpt_5_output"] = output_text
        row["gpt_5_verdict"] = verdict
        row["gpt_5_matched_anchor"] = matched_anchor

        write_rows(result_path, rows)
        processed += 1

        print(f"\n=== ROW {index}/{len(active_rows)} row_id={row.get('row_id')} ===")
        print("INPUT:")
        print(prompt)
        print("VERDICT:")
        print(verdict)
        print("OUTPUT:")
        print(output_text)

    blocked = sum(1 for row in active_rows if row.get("gpt_5_verdict", "") == "BLOCKED")
    allowed = sum(1 for row in active_rows if row.get("gpt_5_verdict", "") == "ALLOWED")
    elapsed = perf_counter() - start
    print(
        f"\n[GPT5_OUR_ATTACK_DONE] processed={processed} resumed={resumed} "
        f"blocked={blocked} allowed={allowed} elapsed_sec={elapsed:.1f}"
    )


def parser_default_model() -> str:
    return "gpt-5"


if __name__ == "__main__":
    main()
