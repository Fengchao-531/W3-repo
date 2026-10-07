#!/usr/bin/env python3
"""Rerun W3 Exp1, Exp2, and RQ2 with the local Llama-3.1-8B-Instruct model."""

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


THIS_FILE = Path(__file__).resolve()
XLLMS_ROOT = THIS_FILE.parent
SOURCE_W3 = XLLMS_ROOT.parent
TRACING_ROOT = SOURCE_W3.parent
DEMO_ROOT = TRACING_ROOT / "Demo"
DEFAULT_PYTHON = Path("/scratch3/che489/.conda/envs/W4/bin/python")
DEFAULT_CACHE_DIR = Path("/scratch3/che489/FC-W2-SoK/model_cache/hub")
DEFAULT_MODEL_PATH = (
    DEFAULT_CACHE_DIR
    / "models--meta-llama--Llama-3.1-8B-Instruct"
    / "snapshots"
    / "0e9e39f249a16976918f6564b8830bc894c89659"
)
MODEL_LABEL = "llama31_8b_instruct"
DEFAULT_OUTPUT_ROOT = XLLMS_ROOT / "Llama3.1"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return plain(value.model_dump())
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


TOOL_ALIASES = {
    "get_car_rental_companies_in_city": "get_all_car_rental_companies_in_city",
    "get_car_rental_companies": "get_all_car_rental_companies_in_city",
    "get_hotels_in_city": "get_all_hotels_in_city",
    "get_restaurants_in_city": "get_all_restaurants_in_city",
    "get_restaurants_in_paris": "get_all_restaurants_in_city",
    "get_hotel_address": "get_hotels_address",
    "get_hotel_addresses": "get_hotels_address",
    "get_hotels_rating_reviews": "get_rating_reviews_for_hotels",
    "get_hotel_rating_reviews": "get_rating_reviews_for_hotels",
    "get_price_for_hotels": "get_hotels_prices",
    "get_hotel_price": "get_hotels_prices",
    "get_hotel_prices": "get_hotels_prices",
    "get_restaurant_address": "get_restaurants_address",
    "get_restaurant_addresses": "get_restaurants_address",
    "get_restaurant_cuisine_type": "get_cuisine_type_for_restaurants",
    "get_restaurant_price": "get_price_for_restaurants",
    "get_restaurant_opening_hours": "check_restaurant_opening_hours",
    "get_car_rental_rating_reviews": "get_rating_reviews_for_car_rental",
    "get_car_rental_fuel_options": "get_car_fuel_options",
    "get_car_rental_price": "get_car_price_per_day",
    "get_car_rental_prices": "get_car_price_per_day",
    "get_price_for_car_rental": "get_car_price_per_day",
    "get_prices_for_car_rental": "get_car_price_per_day",
}

ARG_ALIASES = {
    "hotel_name": ["hotel_name", "hotel", "name", "hotel_names"],
    "hotel_names": ["hotel_names", "hotel_name", "hotels", "hotel", "name"],
    "restaurant_names": ["restaurant_names", "restaurant_name", "restaurants", "restaurant", "name"],
    "company_name": ["company_name", "company_names", "company", "car_rental_company", "name"],
    "offer_id": ["offer_id", "id", "offer", "coupon_id", "code"],
}

LIST_ARGS = {"hotel_names", "restaurant_names", "company_name", "recipients", "participants", "attachments", "cc", "bcc"}


def _tool_schema(function: Any) -> dict[str, Any]:
    try:
        return function.parameters.model_json_schema()
    except Exception:
        return {}


def _first_arg(arguments: dict[str, Any], key: str) -> Any:
    for candidate in ARG_ALIASES.get(key, [key]):
        if candidate in arguments and arguments[candidate] not in (None, ""):
            value = arguments[candidate]
            if isinstance(value, list) and key not in LIST_ARGS:
                return value[0] if value else None
            if key in LIST_ARGS and not isinstance(value, list):
                return [value]
            return value
    return None


def normalize_tool_call(
    function_name: str,
    arguments: dict[str, Any],
    available_functions: dict[str, Any],
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """Map obvious local-model tool aliases to AgentDojo tool names.

    Ambiguous invented tools are rejected instead of being forced into a nearby
    schema, because that would make behavioral outcomes look cleaner than the
    model actually earned.
    """
    target = function_name if function_name in available_functions else TOOL_ALIASES.get(function_name)
    audit = {"original_function": function_name, "mapped_function": target, "status": "accepted"}
    if target not in available_functions:
        audit["status"] = "rejected_unknown_tool"
        return function_name, arguments, audit

    schema = _tool_schema(available_functions[target])
    properties = schema.get("properties", {}) or {}
    required = set(schema.get("required", []) or [])
    normalized: dict[str, Any] = {}
    for key in properties:
        value = _first_arg(arguments, key)
        if value is not None:
            normalized[key] = value
    for key, value in arguments.items():
        if key in properties and key not in normalized:
            normalized[key] = value

    missing = [key for key in required if key not in normalized]
    if missing:
        audit["status"] = "rejected_missing_required_args"
        audit["missing_required_args"] = missing
        return function_name, arguments, audit
    audit["normalized_arguments"] = normalized
    return target, normalized, audit


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def prepare_environment(model_path: Path) -> None:
    os.environ.setdefault("TRANSFORMERS_CACHE", str(DEFAULT_CACHE_DIR))
    os.environ.setdefault("HF_HOME", str(DEFAULT_CACHE_DIR.parent))
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("OPENAI_API_KEY", "local-llama31-no-openai-call")
    os.environ["AGENTDOJO_OPENAI_MODEL"] = MODEL_LABEL
    os.environ["LLAMA31_MODEL_PATH"] = str(model_path)
    os.environ["AGENTDOJO_REPO"] = str(TRACING_ROOT / "2-AgentDojo" / "agentdojo")


def ignore_for_copy(source_dir: str, names: list[str]) -> set[str]:
    ignored = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
    ignored.update(name for name in names if name.endswith(".pyc"))
    source_path = Path(source_dir).resolve()
    relative = source_path.relative_to(SOURCE_W3)

    if relative == Path("."):
        ignored.update({"XLLMs", "AblationStudy", "RQ2_results_analysis", "RQ2Tracker", "W3_TaskTracer"})
        ignored.update(name for name in names if not (source_path / name).is_dir() and name not in {"RQ1_Results_Analysis.md"})
    elif relative == Path("Exp1_User_Context_Embedding"):
        ignored.update(
            {
                "08_Clean_Runs",
                "09_External_Runs",
                "10_User_Context_Runs",
                "10B_User_Context_Benign_Runs",
                "11_Model_Features",
                "12_Processed_Data",
                "13_Statistical_Analysis",
                "14_Figures",
                "15_Tables",
                "16_Manual_Inspection",
                "17_QC_and_Validation",
                "18_Reproducibility",
            }
        )
    elif relative == Path("Exp2_Task_Binding"):
        ignored.update({"03_runs", "04_annotations", "05_processed", "06_statistics", "07_figures", "08_logs"})
    elif relative == Path("Exp4_General_Preference_Control"):
        ignored.update({"01_manifest", "02_prompts", "03_reference_A1_A2", "04_runs", "05_processed", "06_statistics", "07_figures", "08_logs"})
    elif relative == Path("Exp4b_Preference_Controlled_External_Baseline"):
        ignored.update({"01_manifest", "02_prompts", "03_runs", "04_processed", "05_statistics", "06_figures", "07_logs"})
    elif relative == Path("RQ2/Exp2_SafetyIntent"):
        ignored.update({"00_exp1_reference", "01_dataset", "02_runs", "03_annotations", "04_processed", "05_statistics", "06_figures", "07_logs"})
    elif relative == Path("RQ2/Exp3_ Controlled_Source-Provenance_Intervention"):
        ignored.update({"00_config", "01_manifest", "02_controlled_source", "04_processed", "05_statistics", "06_figures", "07_validation", "08_logs"})
    return ignored.intersection(names)


def prepare_workspace(target_w3: Path, reset: bool) -> None:
    required_files = (
        target_w3 / "Exp1_User_Context_Embedding/exp1_pipeline.py",
        target_w3 / "RQ2/Exp3_ Controlled_Source-Provenance_Intervention/rq2_exp3_pipeline.py",
    )
    if target_w3.exists() and not reset and all(path.is_file() for path in required_files):
        exp4_src = SOURCE_W3 / "Exp4_General_Preference_Control"
        exp4_dst = target_w3 / "Exp4_General_Preference_Control"
        if exp4_src.exists():
            shutil.copytree(exp4_src, exp4_dst, ignore=ignore_for_copy, dirs_exist_ok=True)
        exp4b_src = SOURCE_W3 / "Exp4b_Preference_Controlled_External_Baseline"
        exp4b_dst = target_w3 / "Exp4b_Preference_Controlled_External_Baseline"
        if exp4b_src.exists():
            shutil.copytree(exp4b_src, exp4b_dst, ignore=ignore_for_copy, dirs_exist_ok=True)
        return
    if target_w3.exists() and reset:
        shutil.rmtree(target_w3)
    target_w3.parent.mkdir(parents=True, exist_ok=True)
    # Output roots also contain their launcher and README. Merge the clean W3
    # skeleton into a pre-created directory without removing those files.
    shutil.copytree(SOURCE_W3, target_w3, ignore=ignore_for_copy, dirs_exist_ok=True)


def sync_exp4_a1a2_reference(target_w3: Path) -> Path:
    exp2_src = target_w3 / "Exp2_Task_Binding"
    ref_root = target_w3 / "Exp4_General_Preference_Control" / "03_reference_A1_A2"
    ref_root.mkdir(parents=True, exist_ok=True)
    for filename in [
        "exp2_pipeline.py",
        "01_build_exp2_manifest.sh",
        "02_validate_manifest.sh",
        "03_run_exp2.sh",
        "04_process_results.sh",
        "05_statistics.sh",
    ]:
        src = exp2_src / filename
        if src.exists():
            shutil.copy2(src, ref_root / filename)
    return ref_root


@dataclass
class RunArgs:
    model: str = MODEL_LABEL
    temperature: float = 0.0
    limit: int | None = None
    force: bool = False
    condition: str = "all"
    pair_id: str | None = None
    arm: str = "all"
    analysis_group_id: str | None = None


class LocalLlama31LLM:
    """AgentDojo pipeline element that mimics the W3 LoggingOpenAILLM contract."""

    name = MODEL_LABEL

    def __init__(
        self,
        model: str,
        run_id: str,
        model_feature_dir: Path,
        temperature: float | None = 0.0,
    ) -> None:
        if not hasattr(type(self), "_shared"):
            raise RuntimeError("LocalLlama31LLM.install() must be called before use")
        shared = type(self)._shared
        self.model = model
        self.run_id = run_id
        self.model_feature_dir = model_feature_dir
        self.temperature = temperature
        self.call_index = 0
        self.call_ids: list[str] = []
        self.local_llama31 = shared["local_llama31"]
        self.tokenizer = shared["tokenizer"]
        self.hf_model = shared["hf_model"]
        self.input_device = shared["input_device"]
        self.max_new_tokens = shared["max_new_tokens"]
        self.save_hidden_states = shared["save_hidden_states"]

    @classmethod
    def install(
        cls,
        exp1_module: Any,
        local_llama31: Any,
        model_path: Path,
        device: str,
        dtype: str,
        max_new_tokens: int,
        save_hidden_states: bool,
    ) -> None:
        tokenizer, hf_model, input_device = local_llama31.load_local_llama31(model_path, device, dtype)
        cls._shared = {
            "local_llama31": local_llama31,
            "tokenizer": tokenizer,
            "hf_model": hf_model,
            "input_device": input_device,
            "max_new_tokens": max_new_tokens,
            "save_hidden_states": save_hidden_states,
        }
        exp1_module.LoggingOpenAILLM = cls

    @staticmethod
    def _token_occurrences(input_ids: torch.Tensor, needle: list[int]) -> list[tuple[int, int]]:
        if not needle:
            return []
        values = input_ids.tolist()
        width = len(needle)
        return [(i, i + width) for i in range(len(values) - width + 1) if values[i : i + width] == needle]

    def _save_prompt_hidden_states(self, call_dir: Path, inputs: dict[str, torch.Tensor]) -> None:
        import torch

        with torch.inference_mode():
            output = self.hf_model(
                **inputs,
                output_hidden_states=True,
                use_cache=False,
                return_dict=True,
            )
        layers = torch.stack([state[0] for state in output.hidden_states[1:]]).detach()
        payload: dict[str, Any] = {
            "definition": "Llama decoder hidden_states[1:] before generation",
            "shape": list(layers.shape),
            "final_prompt_token": layers[:, -1, :].to("cpu", dtype=torch.bfloat16),
            "marker_spans": {},
        }
        markers = ["DealHub", "TravelOfficial", "SAVE20", "SAVE15", "QUALITY95", "QUALITY90", "VIEWPLUS", "VIEWSTD"]
        for marker in markers:
            marker_ids = self.tokenizer(marker, add_special_tokens=False)["input_ids"]
            occurrences = self._token_occurrences(inputs["input_ids"][0], marker_ids)
            if occurrences:
                payload["marker_spans"][marker] = [
                    {
                        "token_start": start,
                        "token_end": end,
                        "layer_mean": layers[:, start:end, :].mean(dim=1).to("cpu", dtype=torch.bfloat16),
                    }
                    for start, end in occurrences
                ]
        hidden_dir = call_dir / "08_hidden_states"
        hidden_dir.mkdir(exist_ok=True)
        torch.save(payload, hidden_dir / "prompt_layer_activations.pt")
        write_json(
            hidden_dir / "metadata.json",
            {
                "status": "saved",
                "layers": int(layers.shape[0]),
                "prompt_tokens": int(layers.shape[1]),
                "hidden_size": int(layers.shape[2]),
                "markers": {key: len(value) for key, value in payload["marker_spans"].items()},
            },
        )
        del output, layers, payload

    def query(self, query, runtime, env=None, messages=(), extra_args=None):
        import torch
        from agentdojo.functions_runtime import FunctionCall
        from agentdojo.types import ChatAssistantMessage, text_content_block_from_string

        self.call_index += 1
        call_id = f"{self.run_id}_CALL{self.call_index:02d}"
        self.call_ids.append(call_id)
        call_dir = self.model_feature_dir / call_id
        call_dir.mkdir(parents=True, exist_ok=True)

        converted, prompt = self.local_llama31.render_agentdojo_prompt(
            self.tokenizer, messages, runtime.functions.values()
        )
        write_json(call_dir / "01_messages.json", plain(messages))
        (call_dir / "02_serialized_prompt.txt").write_text(prompt, encoding="utf-8")
        write_json(
            call_dir / "03_prompt_metadata.json",
            {
                "call_id": call_id,
                "run_id": self.run_id,
                "model": self.model,
                "model_path": str(os.environ["LLAMA31_MODEL_PATH"]),
                "temperature": self.temperature,
                "adapter": "W3/XLLMs/rerun_llama31_w3.py::LocalLlama31LLM",
                "message_count": len(messages),
                "converted_messages": plain(converted),
            },
        )
        write_json(call_dir / "04_tokens.npz.metadata.json", {"status": "not_saved_for_behavior_rerun"})
        write_json(call_dir / "05_span_map.json", {"status": "not_available_for_local_wrapper"})

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=False,
            add_special_tokens=False,
        )
        inputs = {key: value.to(self.input_device) for key, value in inputs.items()}
        attention_mask = torch.ones_like(inputs["input_ids"])
        if self.save_hidden_states:
            self._save_prompt_hidden_states(call_dir, {**inputs, "attention_mask": attention_mask})
        with torch.inference_mode():
            generated = self.hf_model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=attention_mask,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        completion = self.tokenizer.decode(
            generated[0][inputs["input_ids"].shape[-1] :],
            skip_special_tokens=True,
        )
        parsed = self.local_llama31.parse_llama_tool_call(completion)
        tool_normalization = None
        if parsed is None:
            assistant = ChatAssistantMessage(
                role="assistant",
                content=[text_content_block_from_string(completion.strip())],
                tool_calls=[],
            )
        else:
            function_name, arguments = parsed
            function_name, arguments, tool_normalization = normalize_tool_call(
                function_name, arguments, runtime.functions
            )
            if tool_normalization["status"] == "accepted":
                assistant = ChatAssistantMessage(
                    role="assistant",
                    content=[text_content_block_from_string(completion.strip())],
                    tool_calls=[FunctionCall(function=function_name, args=arguments)],
                )
            else:
                assistant = ChatAssistantMessage(
                    role="assistant",
                    content=[text_content_block_from_string(completion.strip())],
                    tool_calls=[],
                )
        final_messages = [*messages, assistant]
        write_json(
            call_dir / "06_generation.json",
            {
                "raw_completion": completion,
                "parsed_assistant_message": plain(assistant),
                "tool_call_normalization": plain(tool_normalization),
                "input_tokens": int(inputs["input_ids"].shape[-1]),
                "generated_tokens": int(generated.shape[-1] - inputs["input_ids"].shape[-1]),
            },
        )
        for rel in ["07_logits", "09_attention"]:
            (call_dir / rel).mkdir(exist_ok=True)
            write_json(call_dir / rel / "README.json", {"status": "not_saved_for_behavior_rerun"})
        write_json(
            call_dir / "10_feature_summary.json",
            {
                "status": "local_llama31_behavior_and_prompt_hidden_states" if self.save_hidden_states else "local_llama31_behavior_only",
                "call_id": call_id,
            },
        )
        return query, runtime, env, final_messages, extra_args or {}


def import_w3_modules(target_w3: Path):
    exp1_root = target_w3 / "Exp1_User_Context_Embedding"
    exp2_root = target_w3 / "Exp2_Task_Binding"
    exp4_root = target_w3 / "Exp4_General_Preference_Control"
    exp4b_root = target_w3 / "Exp4b_Preference_Controlled_External_Baseline"
    exp4_a1a2_root = sync_exp4_a1a2_reference(target_w3)
    rq2_exp2_root = target_w3 / "RQ2" / "Exp2_SafetyIntent"
    rq2_exp3_root = target_w3 / "RQ2" / "Exp3_ Controlled_Source-Provenance_Intervention"
    for path in [str(DEMO_ROOT), str(exp1_root), str(exp2_root), str(exp4_root), str(exp4b_root), str(exp4_a1a2_root), str(rq2_exp2_root), str(rq2_exp3_root)]:
        if path not in sys.path:
            sys.path.insert(0, path)

    local_llama31 = load_module("local_llama31_xllms", DEMO_ROOT / "01_local_llama31.py")
    exp1 = load_module("exp1_pipeline", exp1_root / "exp1_pipeline.py")
    exp1.AGENTDOJO_REPO = TRACING_ROOT / "2-AgentDojo" / "agentdojo"
    exp1.AGENTDOJO_SRC = exp1.AGENTDOJO_REPO / "src"
    exp1.DEFAULT_MODEL = MODEL_LABEL
    exp2 = load_module("exp2_pipeline_xllms", exp2_root / "exp2_pipeline.py")
    exp4 = load_module("exp4_pipeline_xllms", exp4_root / "exp4_pipeline.py")
    exp4b = load_module("exp4b_pipeline_xllms", exp4b_root / "exp4b_pipeline.py")
    old_exp1_root = os.environ.get("EXP1_ROOT")
    os.environ["EXP1_ROOT"] = str(exp1_root)
    exp4_a1a2 = load_module("exp4_a1a2_pipeline_xllms", exp4_a1a2_root / "exp2_pipeline.py")
    if old_exp1_root is None:
        os.environ.pop("EXP1_ROOT", None)
    else:
        os.environ["EXP1_ROOT"] = old_exp1_root
    rq2_exp2 = load_module("rq2_exp2_pipeline_xllms", rq2_exp2_root / "rq2_exp2_pipeline.py")
    rq2_exp3 = load_module("rq2_exp3_pipeline_xllms", rq2_exp3_root / "rq2_exp3_pipeline.py")
    return local_llama31, exp1, exp2, exp4, exp4b, exp4_a1a2, rq2_exp2, rq2_exp3


def run_exp1_core(exp1: Any, args: argparse.Namespace) -> None:
    exp1.build_dataset()
    exp1.validate_dataset()
    for condition in ["E", "UC_M", "UC_B"]:
        exp1.run_selected(
            RunArgs(model=MODEL_LABEL, limit=args.limit, force=args.force, condition=condition)
        )
    exp1.process_results()
    exp1.analyze()
    exp1.figures()
    exp1.manual_inspection()


def run_exp2(exp2: Any, args: argparse.Namespace) -> None:
    exp2.build_manifest()
    exp2.validate_manifest()
    exp2.make_run_queue()
    exp2.run_selected(RunArgs(model=MODEL_LABEL, limit=args.limit, force=args.force))
    exp2.process_results()
    exp2.statistics()
    exp2.figures()


def run_exp4_a0(exp4: Any, args: argparse.Namespace) -> None:
    exp4.build_manifest()
    exp4.validate_manifest()
    exp4.make_run_queue()
    exp4.run_selected(RunArgs(model=MODEL_LABEL, limit=args.limit, force=args.force))
    exp4.process_results()
    exp4.statistics()
    exp4.figures()


def run_exp4_a1a2(exp4_a1a2: Any, args: argparse.Namespace) -> None:
    exp4_a1a2.build_manifest()
    exp4_a1a2.validate_manifest()
    exp4_a1a2.make_run_queue()
    exp4_a1a2.run_selected(RunArgs(model=MODEL_LABEL, limit=args.limit, force=args.force))
    exp4_a1a2.process_results()
    exp4_a1a2.statistics()
    exp4_a1a2.figures()


def run_exp4b_e0(exp4b: Any, args: argparse.Namespace) -> None:
    exp4b.build_manifest()
    exp4b.validate_manifest()
    exp4b.make_run_queue()
    exp4b.run_selected(RunArgs(model=MODEL_LABEL, limit=args.limit, force=args.force))
    exp4b.process_results()
    exp4b.statistics()
    exp4b.figures()


def run_rq2_exp2(rq2_exp2: Any, args: argparse.Namespace) -> None:
    rq2_exp2.setup_dirs()
    rq2_exp2.freeze_exp1_reference()
    rq2_exp2.build_dataset()
    rq2_exp2.validate_dataset()
    rq2_exp2.make_run_queue()
    rq2_exp2.run_selected(RunArgs(model=MODEL_LABEL, limit=args.limit, force=args.force))
    rq2_exp2.process_results()
    rq2_exp2.statistics()
    rq2_exp2.figures()


def run_rq2_exp3(rq2_exp3: Any, args: argparse.Namespace) -> None:
    rq2_exp3.build_dataset()
    rq2_exp3.validate_dataset()
    rq2_exp3.make_run_queue()
    rq2_exp3.run_selected(RunArgs(model=MODEL_LABEL, limit=args.limit, force=args.force))
    rq2_exp3.process_results()
    rq2_exp3.statistics()
    rq2_exp3.figures()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--device", default="cuda:0", help="cuda:0, cuda, auto, or cpu")
    parser.add_argument("--dtype", default="bfloat16", choices=["float32", "float16", "bfloat16"])
    parser.add_argument("--max-new-tokens", type=int, default=2048)
    parser.add_argument("--no-hidden-states", dest="save_hidden_states", action="store_false")
    parser.add_argument("--limit", type=int, default=None, help="Limit each run queue for smoke testing.")
    parser.add_argument("--force", action="store_true", help="Rerun existing completed run directories.")
    parser.add_argument("--reset-workspace", action="store_true", help="Delete and recreate the isolated W3 copy.")
    parser.add_argument(
        "--stages",
        nargs="+",
        default=["exp1_core", "rq2_exp3"],
        choices=["exp1_core", "exp2", "exp4_a0", "exp4b_e0", "exp4_a1a2", "rq2_exp2", "rq2_exp3"],
    )
    parser.set_defaults(save_hidden_states=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = args.model_path.expanduser().resolve()
    if not model_path.is_dir():
        raise SystemExit(f"Missing local model snapshot: {model_path}")

    prepare_environment(model_path)
    target_w3 = args.output_root.expanduser().resolve()
    prepare_workspace(target_w3, reset=args.reset_workspace)

    manifest_path = target_w3 / f"00_{MODEL_LABEL}_rerun_manifest.json"
    write_json(
        manifest_path,
        {
            "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source_w3": str(SOURCE_W3),
            "target_w3": str(target_w3),
            "model_label": MODEL_LABEL,
            "model_path": str(model_path),
            "stages": args.stages,
            "limit": args.limit,
            "force": args.force,
            "device": args.device,
            "dtype": args.dtype,
            "max_new_tokens": args.max_new_tokens,
            "save_hidden_states": args.save_hidden_states,
        },
    )

    local_llama31, exp1, exp2, exp4, exp4b, exp4_a1a2, rq2_exp2, rq2_exp3 = import_w3_modules(target_w3)
    random.seed(0)
    LocalLlama31LLM.install(
        exp1,
        local_llama31=local_llama31,
        model_path=model_path,
        device=args.device,
        dtype=args.dtype,
        max_new_tokens=args.max_new_tokens,
        save_hidden_states=args.save_hidden_states,
    )

    stage_fns = {
        "exp1_core": lambda: run_exp1_core(exp1, args),
        "exp2": lambda: run_exp2(exp2, args),
        "exp4_a0": lambda: run_exp4_a0(exp4, args),
        "exp4b_e0": lambda: run_exp4b_e0(exp4b, args),
        "exp4_a1a2": lambda: run_exp4_a1a2(exp4_a1a2, args),
        "rq2_exp2": lambda: run_rq2_exp2(rq2_exp2, args),
        "rq2_exp3": lambda: run_rq2_exp3(rq2_exp3, args),
    }
    for stage in args.stages:
        print(f"\n=== {stage} :: start ===", flush=True)
        stage_fns[stage]()
        print(f"=== {stage} :: done ===", flush=True)

    write_json(
        target_w3 / f"01_{MODEL_LABEL}_rerun_done.json",
        {
            "finished_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "target_w3": str(target_w3),
            "stages": args.stages,
        },
    )
    print(f"\nRerun workspace: {target_w3}")


if __name__ == "__main__":
    main()
