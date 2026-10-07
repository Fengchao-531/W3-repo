#!/usr/bin/env python3
"""Run W3 behavior experiments with the TaskTracer Llama 3.1 backend.

This launcher keeps the existing W3 Exp1/Exp2/RQ2 pipelines intact and swaps
their OpenAI LLM element for the same local Llama-3.1-8B-Instruct adapter used
by W3_TaskTracer/Demo.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any


W3_ROOT = Path(__file__).resolve().parents[1]
EXP1_ROOT = W3_ROOT / "Exp1_User_Context_Embedding"
EXP2_ROOT = W3_ROOT / "Exp2_Task_Binding"
RQ2_EXP2_ROOT = W3_ROOT / "RQ2" / "Exp2_SafetyIntent"
RQ2_EXP3_ROOT = W3_ROOT / "RQ2" / "Exp3_ Controlled_Source-Provenance_Intervention"
DEMO_ROOT = W3_ROOT.parent / "Demo"
AGENTDOJO_SRC = W3_ROOT.parent / "2-AgentDojo" / "agentdojo" / "src"

DEFAULT_MODEL_NAME = "local-llama-3.1-8b-instruct"
DEFAULT_CACHE_DIR = Path("/scratch3/che489/FC-W2-SoK/model_cache/hub")
DEFAULT_MODEL_PATH = (
    DEFAULT_CACHE_DIR
    / "models--meta-llama--Llama-3.1-8B-Instruct"
    / "snapshots"
    / "0e9e39f249a16976918f6564b8830bc894c89659"
)


for path in [str(AGENTDOJO_SRC), str(EXP1_ROOT), str(DEMO_ROOT)]:
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault("TRANSFORMERS_CACHE", str(DEFAULT_CACHE_DIR))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("OPENAI_API_KEY", "not-used-local-llama31")

import torch  # noqa: E402
from agentdojo.functions_runtime import EmptyEnv, Env, FunctionCall, FunctionsRuntime  # noqa: E402
from agentdojo.types import ChatAssistantMessage, ChatMessage, text_content_block_from_string  # noqa: E402

local_llama31 = importlib.import_module("01_local_llama31")
import exp1_pipeline as e1  # noqa: E402


def import_module_from_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class LocalLlama31LLM:
    """AgentDojo pipeline element compatible with e1.LoggingOpenAILLM outputs."""

    name = DEFAULT_MODEL_NAME
    _cache: dict[tuple[str, str, str], tuple[Any, torch.nn.Module, torch.device]] = {}

    model_path: Path = DEFAULT_MODEL_PATH
    device: str = "auto"
    dtype: str = "bfloat16"
    max_new_tokens: int = 512
    max_input_tokens: int = 8192

    def __init__(
        self,
        model: str,
        run_id: str,
        model_feature_dir: Path,
        temperature: float | None = 0.0,
    ) -> None:
        self.model = model
        self.run_id = run_id
        self.model_feature_dir = model_feature_dir
        self.temperature = temperature
        self.call_index = 0
        self.call_ids: list[str] = []
        self.tokenizer, self.llama_model, self.input_device = self._load()

    @classmethod
    def configure(
        cls,
        model_path: Path,
        device: str,
        dtype: str,
        max_new_tokens: int,
        max_input_tokens: int,
    ) -> None:
        cls.model_path = model_path.expanduser().resolve()
        cls.device = device
        cls.dtype = dtype
        cls.max_new_tokens = max_new_tokens
        cls.max_input_tokens = max_input_tokens

    @classmethod
    def _load(cls):
        key = (str(cls.model_path), cls.device, cls.dtype)
        if key not in cls._cache:
            cls._cache[key] = local_llama31.load_local_llama31(cls.model_path, cls.device, cls.dtype)
        return cls._cache[key]

    def _write_feature_record(
        self,
        call_dir: Path,
        call_id: str,
        messages: Sequence[ChatMessage],
        rendered_prompt: str,
        hf_messages: list[dict[str, Any]],
        completion: str | None = None,
        assistant_message: ChatAssistantMessage | None = None,
    ) -> None:
        call_dir.mkdir(parents=True, exist_ok=True)
        e1.write_json(call_dir / "01_messages.json", e1.plain(messages))
        (call_dir / "02_serialized_prompt.txt").write_text(rendered_prompt, encoding="utf-8")
        e1.write_json(
            call_dir / "03_prompt_metadata.json",
            {
                "call_id": call_id,
                "run_id": self.run_id,
                "model": self.model,
                "backend": "local_llama31_transformers",
                "model_path": str(self.model_path),
                "temperature": self.temperature,
                "max_new_tokens": self.max_new_tokens,
                "max_input_tokens": self.max_input_tokens,
                "hf_messages": e1.plain(hf_messages),
            },
        )
        e1.write_json(call_dir / "04_tokens.npz.metadata.json", {"status": "not_saved"})
        e1.write_json(call_dir / "05_span_map.json", e1.build_span_map_from_messages(messages))
        if completion is not None:
            e1.write_json(
                call_dir / "06_generation.json",
                {
                    "raw_completion": completion,
                    "assistant_message": e1.plain(assistant_message),
                },
            )
        for rel in ["07_logits", "08_hidden_states", "09_attention"]:
            (call_dir / rel).mkdir(exist_ok=True)
            e1.write_json(call_dir / rel / "README.json", {"status": "not_saved_by_behavior_launcher"})
        e1.write_json(call_dir / "10_feature_summary.json", {"status": "local_llama31_behavior_only", "call_id": call_id})

    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env = EmptyEnv(),
        messages: Sequence[ChatMessage] = (),
        extra_args: dict | None = None,
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict]:
        self.call_index += 1
        call_id = f"{self.run_id}_CALL{self.call_index:02d}"
        self.call_ids.append(call_id)
        call_dir = self.model_feature_dir / call_id
        hf_messages, rendered_prompt = local_llama31.render_agentdojo_prompt(
            self.tokenizer,
            messages,
            runtime.functions.values(),
        )
        inputs = self.tokenizer(
            rendered_prompt,
            return_tensors="pt",
            truncation=False,
            add_special_tokens=False,
        )
        input_tokens = int(inputs["input_ids"].shape[1])
        if input_tokens > self.max_input_tokens:
            self._write_feature_record(call_dir, call_id, messages, rendered_prompt, hf_messages)
            raise ValueError(
                f"{call_id} has {input_tokens} prompt tokens, above --max-input-tokens={self.max_input_tokens}; "
                "refusing to truncate the W3 experiment prompt."
            )
        inputs = {key: value.to(self.input_device) for key, value in inputs.items()}
        attention_mask = torch.ones_like(inputs["input_ids"])
        generate_kwargs: dict[str, Any] = {
            "input_ids": inputs["input_ids"],
            "attention_mask": attention_mask,
            "max_new_tokens": self.max_new_tokens,
            "pad_token_id": self.tokenizer.eos_token_id,
        }
        if self.temperature is not None and self.temperature > 0:
            generate_kwargs.update({"do_sample": True, "temperature": self.temperature})
        else:
            generate_kwargs.update({"do_sample": False})
        with torch.inference_mode():
            generated = self.llama_model.generate(**generate_kwargs)
        completion = self.tokenizer.decode(
            generated[0][inputs["input_ids"].shape[-1] :],
            skip_special_tokens=True,
        )
        parsed_call = local_llama31.parse_llama_tool_call(completion)
        if parsed_call is None:
            assistant_message = ChatAssistantMessage(
                role="assistant",
                content=[text_content_block_from_string(completion.strip())],
                tool_calls=[],
            )
        else:
            function_name, arguments = parsed_call
            assistant_message = ChatAssistantMessage(
                role="assistant",
                content=[text_content_block_from_string(completion.strip())],
                tool_calls=[FunctionCall(function=function_name, args=arguments)],
            )
        self._write_feature_record(call_dir, call_id, messages, rendered_prompt, hf_messages, completion, assistant_message)
        return query, runtime, env, [*messages, assistant_message], extra_args or {}


def patch_pipelines(args: argparse.Namespace) -> None:
    LocalLlama31LLM.configure(
        model_path=args.model_path,
        device=args.device,
        dtype=args.dtype,
        max_new_tokens=args.max_new_tokens,
        max_input_tokens=args.max_input_tokens,
    )
    e1.LoggingOpenAILLM = LocalLlama31LLM
    e1.DEFAULT_MODEL = args.model
    os.environ["AGENTDOJO_OPENAI_MODEL"] = args.model


def run_exp1(args: argparse.Namespace) -> None:
    if args.prepare:
        e1.build_dataset()
        e1.validate_dataset()
    e1.run_selected(
        SimpleNamespace(
            condition=args.condition,
            model=args.model,
            temperature=args.temperature,
            limit=args.limit,
            pair_id=args.pair_id,
            force=args.force,
        )
    )
    if args.analyze:
        e1.process_results()
        e1.analyze()
        e1.figures()
        e1.manual_inspection()


def run_exp2(args: argparse.Namespace) -> None:
    exp2 = import_module_from_path("w3_exp2_pipeline_llama31", EXP2_ROOT / "exp2_pipeline.py")
    if args.prepare or not (EXP2_ROOT / "01_manifest/02_exp2_run_manifest.jsonl").exists():
        exp2.build_manifest()
        exp2.validate_manifest()
        exp2.make_run_queue()
    exp2.run_selected(
        SimpleNamespace(
            condition=args.condition if args.condition in {"all", "UC", "UB"} else "all",
            model=args.model,
            temperature=args.temperature,
            limit=args.limit,
            pair_id=args.pair_id,
            force=args.force,
        )
    )
    if args.analyze:
        exp2.process_results()
        exp2.statistics()
        exp2.figures()


def run_rq2_exp2(args: argparse.Namespace) -> None:
    rq2_exp2 = import_module_from_path("w3_rq2_exp2_pipeline_llama31", RQ2_EXP2_ROOT / "rq2_exp2_pipeline.py")
    if args.prepare or not (RQ2_EXP2_ROOT / "01_dataset/02_h2_h3_manifest.jsonl").exists():
        rq2_exp2.build_dataset()
        rq2_exp2.validate_dataset()
        rq2_exp2.make_run_queue()
    rq2_exp2.run_selected(
        SimpleNamespace(
            condition=args.condition if args.condition in {"all", "H2", "H3"} else "all",
            arm=args.arm,
            analysis_group_id=args.analysis_group_id,
            model=args.model,
            temperature=args.temperature,
            limit=args.limit,
            force=args.force,
        )
    )
    if args.analyze:
        rq2_exp2.process_results()
        rq2_exp2.statistics()
        rq2_exp2.figures()


def run_rq2_exp3(args: argparse.Namespace) -> None:
    rq2_exp3 = import_module_from_path("w3_rq2_exp3_pipeline_llama31", RQ2_EXP3_ROOT / "rq2_exp3_pipeline.py")
    if args.prepare or not (RQ2_EXP3_ROOT / "01_manifest/01_exp3_runs.jsonl").exists():
        rq2_exp3.build_dataset()
        rq2_exp3.validate_dataset()
        rq2_exp3.make_run_queue()
    rq2_exp3.run_selected(
        SimpleNamespace(
            condition=args.condition if args.condition in {"all", "C0", "C1", "C2"} else "all",
            pair_id=args.pair_id,
            model=args.model,
            temperature=args.temperature,
            limit=args.limit,
            force=args.force,
        )
    )
    if args.analyze:
        rq2_exp3.process_results()
        rq2_exp3.statistics()
        rq2_exp3.figures()


def smoke(args: argparse.Namespace) -> None:
    patch_pipelines(args)
    local_llama31.smoke(args.model_path)
    args.limit = 1
    args.analyze = False
    args.prepare = False
    print("[smoke] Exp1 one run")
    run_exp1(args)


def write_manifest(args: argparse.Namespace) -> None:
    out = W3_ROOT / "XLLMs" / "llama31_run_manifest.json"
    e1.write_json(
        out,
        {
            "backend": "local_llama31_transformers",
            "model_name": args.model,
            "model_path": str(args.model_path),
            "device": args.device,
            "dtype": args.dtype,
            "max_new_tokens": args.max_new_tokens,
            "max_input_tokens": args.max_input_tokens,
            "experiments": args.experiment,
            "limit": args.limit,
            "force": args.force,
            "analyze": args.analyze,
        },
    )
    print(f"manifest_written={out}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--experiment",
        choices=["all", "exp1", "exp2", "rq2-exp2", "rq2-exp3"],
        default="all",
        help="Which W3 experiment family to run.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL_NAME, help="Output-directory model slug/name.")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--device", default="auto", help="auto, cpu, cuda, or cuda:N.")
    parser.add_argument("--dtype", choices=["float32", "float16", "bfloat16"], default="bfloat16")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--max-input-tokens", type=int, default=8192)
    parser.add_argument("--limit", type=int, default=None, help="Limit queued behavior runs per experiment.")
    parser.add_argument("--condition", default="all", help="Condition filter, interpreted per experiment.")
    parser.add_argument("--pair-id", default=None, help="Exp1/Exp2/Exp3 pair id filter.")
    parser.add_argument("--analysis-group-id", default=None, help="RQ2 Exp2 analysis group filter.")
    parser.add_argument("--arm", choices=["all", "malicious", "benign"], default="all", help="RQ2 Exp2 arm filter.")
    parser.add_argument("--prepare", action="store_true", help="Rebuild/validate manifests before running.")
    parser.add_argument("--no-analyze", dest="analyze", action="store_false", help="Skip process/statistics/figures after runs.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing Llama output runs.")
    parser.add_argument("--smoke", action="store_true", help="Load Llama and run one Exp1 job.")
    parser.set_defaults(analyze=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.model_path = args.model_path.expanduser().resolve()
    if args.smoke:
        smoke(args)
        write_manifest(args)
        return
    patch_pipelines(args)
    selected = ["exp1", "exp2", "rq2-exp2", "rq2-exp3"] if args.experiment == "all" else [args.experiment]
    for experiment in selected:
        print(f"=== {experiment} :: {args.model} ===")
        if experiment == "exp1":
            run_exp1(args)
        elif experiment == "exp2":
            run_exp2(args)
        elif experiment == "rq2-exp2":
            run_rq2_exp2(args)
        elif experiment == "rq2-exp3":
            run_rq2_exp3(args)
        else:
            raise AssertionError(experiment)
    write_manifest(args)


if __name__ == "__main__":
    main()
