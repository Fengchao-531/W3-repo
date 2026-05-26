#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parent
SAMPLES_PATH = ROOT / "sample_attack_inputs_5.json"
RESULTS_DIR = ROOT / "probe-results"

BASELINE_DEFENSES_DIR = ROOT / "Detection-based" / "baseline-defenses"
CAUSAL_ARMOR_DIR = ROOT / "Detection-based" / "causal-armor"
OPEN_PROMPT_INJECTION_DIR = ROOT / "Detection-based" / "Open-Prompt-Injection"

import sys

sys.path.insert(0, str(BASELINE_DEFENSES_DIR))

from perplexity_filter import PerplexityFilter  # type: ignore  # noqa: E402


def load_samples(samples_path: Path) -> list[dict]:
    return json.loads(samples_path.read_text(encoding="utf-8"))


def get_sample_input(sample: dict) -> str:
    if "injection_content" in sample:
        return sample["injection_content"]
    if "raw_injection_content" in sample:
        return sample["raw_injection_content"]
    return sample["input"]


def run_perplexity_probe(samples: list[dict], model_name: str) -> dict:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    probe = PerplexityFilter(model=model, tokenizer=tokenizer, threshold=3.1, window_size=10)
    sequences = [get_sample_input(sample) for sample in samples]
    mean_scores, mean_pass = probe.filter(sequences)
    window_scores, window_pass, passed_all = probe.filter_window(sequences)

    results = []
    for sample, mean_score, mean_ok, per_window_scores, per_window_pass, passed in zip(
        samples,
        mean_scores,
        mean_pass,
        window_scores,
        window_pass,
        passed_all,
    ):
        results.append(
            {
                "sample_id": sample["id"],
                "attack_method": sample["attack_method"],
                "row_id": sample["row_id"],
                "mean_neg_log_ppl": mean_score,
                "mean_filter_pass": mean_ok,
                "window_neg_log_ppl": per_window_scores,
                "window_filter_pass": per_window_pass,
                "all_windows_pass": passed,
            }
        )

    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return {
        "method": "baseline-defenses/perplexity_filter",
        "model_name": model_name,
        "threshold": 3.1,
        "window_size": 10,
        "results": results,
    }


def run_causal_armor_probe(samples: list[dict]) -> dict:
    return {
        "method": "causal-armor/middleware",
        "status": "not_run",
        "reason": (
            "CausalArmor guards agent actions using full conversation state, "
            "untrusted tool spans, a proposed action, and proxy/sanitizer providers. "
            "The current probe dataset only contains standalone injection_content strings."
        ),
        "sample_input_mode": "injection_content_only",
        "sample_count": len(samples),
        "repo_path": str(CAUSAL_ARMOR_DIR),
        "runtime_requirements": {
            "python": ">=3.11 (upstream package metadata)",
            "proxy_model": "vLLM-compatible logprob model, e.g. google/gemma-3-12b-it",
            "sanitizer_and_action_provider": "OpenAI/Anthropic/Gemini/LiteLLM-compatible provider",
        },
    }


def run_datasentinel_probe(samples: list[dict]) -> dict:
    ft_path = os.environ.get("DATASENTINEL_FT_PATH", "")
    return {
        "method": "open-prompt-injection/datasentinel",
        "status": "not_run",
        "reason": (
            "DataSentinel needs a local fine-tuned checkpoint path via DATASENTINEL_FT_PATH. "
            "The upstream README points to a downloadable checkpoint, but it is not available in the current environment."
        ),
        "sample_input_mode": "injection_content_only",
        "sample_count": len(samples),
        "repo_path": str(OPEN_PROMPT_INJECTION_DIR),
        "runtime_requirements": {
            "python": "3.9+ (repo environment.yml uses 3.9.19)",
            "base_model_config": "configs/model_configs/mistral_config.json by default",
            "fine_tuned_checkpoint": ft_path or "required",
        },
    }


def save_result(name: str, payload: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe 5 prompt-injection samples with directly runnable defenses.")
    parser.add_argument("--samples", type=Path, default=SAMPLES_PATH)
    parser.add_argument("--perplexity-model", default="facebook/opt-125m")
    args = parser.parse_args()

    samples = load_samples(args.samples)

    outputs: list[str] = []

    try:
        perplexity_payload = run_perplexity_probe(samples, args.perplexity_model)
    except Exception as exc:
        perplexity_payload = {
            "method": "baseline-defenses/perplexity_filter",
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    perplexity_path = save_result("baseline_perplexity_probe", perplexity_payload)
    outputs.append(str(perplexity_path))

    try:
        detector_payload = run_causal_armor_probe(samples)
    except Exception as exc:
        detector_payload = {
            "method": "causal-armor/middleware",
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    detector_path = save_result("causal_armor_probe", detector_payload)
    outputs.append(str(detector_path))

    try:
        datasentinel_payload = run_datasentinel_probe(samples)
    except Exception as exc:
        datasentinel_payload = {
            "method": "open-prompt-injection/datasentinel",
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    datasentinel_path = save_result("datasentinel_probe", datasentinel_payload)
    outputs.append(str(datasentinel_path))

    print(
        json.dumps(
            {
                "samples": str(args.samples),
                "outputs": outputs,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
