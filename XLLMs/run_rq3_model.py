#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
SOURCE_W3 = HERE.parent
TRACING_ROOT = SOURCE_W3.parent
DEMO_ROOT = TRACING_ROOT / "Demo"


@dataclass(frozen=True)
class ModelConfig:
    key: str
    label: str
    output_name: str
    model_path: Path
    adapter_path: Path


def env_path(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default)).expanduser()


MODEL_CONFIGS = {
    "llama": ModelConfig(
        key="llama",
        label="llama31_8b_instruct",
        output_name="Llama3.1",
        model_path=Path("/scratch3/che489/FC-W2-SoK/model_cache/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659"),
        adapter_path=DEMO_ROOT / "01_local_llama31.py",
    ),
    "mistral": ModelConfig(
        key="mistral",
        label="ministral_8b_instruct_2410",
        output_name="Mistral",
        model_path=Path("/scratch3/che489/FC-W2-SoK/model_cache/hub/models--mistralai--Ministral-8B-Instruct-2410/snapshots/2f494a194c5b980dfb9772cb92d26cbb671fce5a"),
        adapter_path=HERE / "local_ministral8b.py",
    ),
    "deepseek": ModelConfig(
        key="deepseek",
        label="deepseek_r1_distill_qwen_7b",
        output_name="DeepSeek",
        model_path=Path("/scratch3/che489/FC-W2-SoK/model_cache/hub/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-7B/snapshots/916b56a44061fd5cd7d6a8fb632557ed4f724f60"),
        adapter_path=HERE / "local_qwen_family.py",
    ),
    "qwen": ModelConfig(
        key="qwen",
        label="qwen_instruct",
        output_name="Qwen",
        model_path=env_path("QWEN_MODEL_PATH", "/scratch3/che489/hf_home/models/w3_models/Qwen2.5-7B-Instruct"),
        adapter_path=HERE / "local_qwen_family.py",
    ),
    "gemma": ModelConfig(
        key="gemma",
        label="gemma_instruct",
        output_name="Gemma",
        model_path=env_path("GEMMA_MODEL_PATH", "/scratch3/che489/hf_home/models/w3_models/gemma-2-9b-it"),
        adapter_path=HERE / "local_open_instruct.py",
    ),
    "olmo": ModelConfig(
        key="olmo",
        label="olmo_instruct",
        output_name="OLMo",
        model_path=env_path("OLMO_MODEL_PATH", "/scratch3/che489/hf_home/models/w3_models/OLMo-2-1124-7B-Instruct"),
        adapter_path=HERE / "local_open_instruct.py",
    ),
}

ALIASES = {
    "llama3": "llama",
    "llama3.1": "llama",
    "llama31": "llama",
    "ministral": "mistral",
}


@dataclass
class RunArgs:
    model: str
    temperature: float = 0.0
    limit: int | None = None
    force: bool = False
    run_id: str | None = None
    pair_id: str | None = None
    condition: str = "all"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def prepare_rq3_workspace(target_w3: Path) -> None:
    source = SOURCE_W3 / "RQ3"
    target = target_w3 / "RQ3"
    if not source.is_dir():
        raise SystemExit(f"Missing source RQ3 folder: {source}")
    shutil.copytree(
        source,
        target,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "02_runs", "03_annotations", "04_processed", "05_statistics", "06_figures", "07_logs"),
    )


def import_rq3_modules(config: ModelConfig, target_w3: Path):
    exp1_root = target_w3 / "Exp1_User_Context_Embedding"
    rq3a_root = target_w3 / "RQ3" / "RQ3-AControlledVerification"
    rq3b_root = target_w3 / "RQ3" / "RQ3-BDefenseCoverage"
    rq3c_root = target_w3 / "RQ3" / "RQ3-CDeployedAgentVerification"
    for path in [HERE, DEMO_ROOT, exp1_root, rq3a_root, rq3b_root, rq3c_root]:
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    adapter = load_module(f"rq3_adapter_{config.label}", config.adapter_path)
    exp1 = load_module("exp1_pipeline", exp1_root / "exp1_pipeline.py")
    exp1.AGENTDOJO_REPO = TRACING_ROOT / "2-AgentDojo" / "agentdojo"
    exp1.AGENTDOJO_SRC = exp1.AGENTDOJO_REPO / "src"
    exp1.DEFAULT_MODEL = config.label
    rq3a = load_module(f"rq3a_run_{config.label}", rq3a_root / "rq3_controlled_verification.py")
    rq3a_agg = load_module(f"rq3a_agg_{config.label}", rq3a_root / "rq3a_aggregate_analysis.py")
    rq3b = load_module(f"rq3b_{config.label}", rq3b_root / "rq3b_defense_coverage.py")
    rq3c = load_module(f"rq3c_{config.label}", rq3c_root / "rq3c_deployed_agent_verification.py")
    rq3a.DEFAULT_MODEL = config.label
    rq3a.EXP1_ROOT = target_w3 / "Exp1_User_Context_Embedding"
    rq3a_agg.EXP1_ROOT = target_w3 / "Exp1_User_Context_Embedding"
    rq3a_agg.RQ2_EXP2_ROOT = target_w3 / "RQ2" / "Exp2_SafetyIntent"
    return adapter, exp1, rq3a, rq3a_agg, rq3b, rq3c


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run all implemented RQ3 local-model components for one XLLM model.")
    parser.add_argument("model", choices=sorted(set(MODEL_CONFIGS) | set(ALIASES)))
    parser.add_argument("--device", default="auto")
    parser.add_argument("--dtype", default="bfloat16", choices=["float32", "float16", "bfloat16"])
    parser.add_argument("--max-new-tokens", type=int, default=2048)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--pair-id", default=None)
    parser.add_argument("--condition", choices=["all", "E_M_H2", "E_M_H3"], default="all")
    parser.add_argument("--h3-only", action="store_true")
    parser.add_argument("--no-hidden-states", dest="save_hidden_states", action="store_false")
    parser.set_defaults(save_hidden_states=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    key = ALIASES.get(args.model, args.model)
    config = MODEL_CONFIGS[key]
    model_path = config.model_path.expanduser().resolve()
    if not model_path.is_dir():
        raise SystemExit(f"Missing local model snapshot for {config.key}: {model_path}")

    base_runner = load_module(f"rq3_base_runner_{config.label}", HERE / "rerun_llama31_w3.py")
    base_runner.MODEL_LABEL = config.label
    base_runner.DEFAULT_MODEL_PATH = model_path
    base_runner.DEFAULT_OUTPUT_ROOT = HERE / config.output_name
    base_runner.prepare_environment(model_path)

    target_w3 = (HERE / config.output_name).resolve()
    base_runner.prepare_workspace(target_w3, reset=False)
    prepare_rq3_workspace(target_w3)

    os.environ["EXP1_ROOT"] = str(target_w3 / "Exp1_User_Context_Embedding")
    os.environ["RQ2_EXP2_ROOT"] = str(target_w3 / "RQ2" / "Exp2_SafetyIntent")
    os.environ["RQ3_INCLUDE_E_M_H2"] = "0" if args.h3_only else "1"
    os.environ.setdefault("OPENAI_API_KEY", f"local-{config.label}-no-openai-call")

    write_json(
        target_w3 / f"00_{config.label}_rq3_manifest.json",
        {
            "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source_w3": str(SOURCE_W3),
            "target_w3": str(target_w3),
            "model_label": config.label,
            "model_path": str(model_path),
            "stages": ["rq3a_controlled_verification", "rq3b_defense_coverage_analysis", "rq3c_deployed_agent_analysis"],
            "limit": args.limit,
            "force": args.force,
            "device": args.device,
            "dtype": args.dtype,
            "max_new_tokens": args.max_new_tokens,
            "save_hidden_states": args.save_hidden_states,
        },
    )

    adapter, exp1, rq3a, rq3a_agg, rq3b, rq3c = import_rq3_modules(config, target_w3)
    random.seed(0)
    base_runner.LocalLlama31LLM.install(
        exp1,
        local_llama31=adapter,
        model_path=model_path,
        device=args.device,
        dtype=args.dtype,
        max_new_tokens=args.max_new_tokens,
        save_hidden_states=args.save_hidden_states,
    )

    rq3a.setup_dirs()
    rq3a.build_dataset()
    rq3a.validate_dataset()
    rq3a.make_run_queue()
    rq3a.run_selected(
        RunArgs(
            model=config.label,
            limit=args.limit,
            force=args.force,
            run_id=args.run_id,
            pair_id=args.pair_id,
            condition=args.condition,
        )
    )
    rq3a.process_results()
    rq3a.statistics()
    rq3a.figures()
    rq3a_agg.main()

    rq3b.main()
    rq3c.main()

    write_json(
        target_w3 / f"01_{config.label}_rq3_done.json",
        {
            "finished_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "target_w3": str(target_w3),
            "model_label": config.label,
        },
    )
    print(f"\nRQ3 workspace: {target_w3 / 'RQ3'}")


if __name__ == "__main__":
    main()
