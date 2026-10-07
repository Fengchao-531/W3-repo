#!/usr/bin/env python3
"""AgentDojo adapter for DeepSeek-R1-Distill-Qwen and Qwen Instruct models."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer


DEEPSEEK_MODEL_PATH = Path(
    "/scratch3/che489/FC-W2-SoK/model_cache/hub/"
    "models--deepseek-ai--DeepSeek-R1-Distill-Qwen-7B/snapshots/"
    "916b56a44061fd5cd7d6a8fb632557ed4f724f60"
)


def plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return plain(value.model_dump())
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(str(item.get("content", item.get("text", ""))) if isinstance(item, dict) else str(item) for item in content)
    return str(content)


def agentdojo_tools_to_hf(tools: Any) -> list[dict[str, Any]]:
    return [{"type": "function", "function": {"name": tool.name, "description": tool.description, "parameters": tool.parameters.model_json_schema()}} for tool in tools]


def _tool_instruction(tools: list[dict[str, Any]]) -> str:
    schemas = json.dumps(tools, ensure_ascii=False)
    return (
        "\n\nYou have access to these tools:\n" + schemas +
        "\nWhen calling a tool, emit exactly one call using the model's tool-call format. "
        "Use the function name and a JSON arguments object. Do not describe a plan before the tool call. "
        "If you need a tool, the assistant message should contain only the tool call. "
        "Do not output chain-of-thought; close any thinking block immediately before the tool call."
    )


def _deepseek_style(tokenizer: Any) -> bool:
    return "<｜tool▁call▁begin｜>" in (tokenizer.chat_template or "")


def _suppress_deepseek_thinking(prompt: str) -> str:
    suffixes = (
        "<｜Assistant｜><think>\n",
        "<｜Assistant｜><think>",
    )
    for suffix in suffixes:
        if prompt.endswith(suffix):
            return prompt[: -len(suffix)] + "<｜Assistant｜><think>\n</think>\n\n"
    return prompt


def agentdojo_messages_to_hf(messages: Any, stringify_arguments: bool) -> list[dict[str, Any]]:
    converted = []
    for message in plain(messages):
        role = message["role"]
        calls = message.get("tool_calls") or []
        if role == "assistant" and calls:
            tool_calls = []
            for call in calls:
                arguments = call.get("args", {})
                tool_calls.append({"type": "function", "function": {"name": call["function"], "arguments": json.dumps(arguments, ensure_ascii=False) if stringify_arguments else arguments}})
            converted.append({"role": "assistant", "content": None, "tool_calls": tool_calls})
        elif role == "tool":
            converted.append({"role": "tool", "content": json.dumps({"result": content_to_text(message.get("content"))}, ensure_ascii=False)})
        else:
            converted.append({"role": role, "content": content_to_text(message.get("content"))})
    return converted


def render_agentdojo_prompt(tokenizer: Any, messages: Any, tools: Any) -> tuple[list[dict[str, Any]], str]:
    schemas = agentdojo_tools_to_hf(tools)
    deepseek = _deepseek_style(tokenizer)
    converted = agentdojo_messages_to_hf(messages, stringify_arguments=deepseek)
    native_tools = False
    if not deepseek:
        probe_messages = json.loads(json.dumps(converted))
        try:
            probe = tokenizer.apply_chat_template(probe_messages, tools=schemas, add_generation_prompt=True, tokenize=False)
            native_tools = bool(schemas and schemas[0]["function"]["name"] in probe)
        except Exception:
            native_tools = False
    if not native_tools and schemas:
        converted = json.loads(json.dumps(converted))
        if converted and converted[0]["role"] == "system":
            converted[0]["content"] += _tool_instruction(schemas)
        else:
            converted.insert(0, {"role": "system", "content": _tool_instruction(schemas).strip()})
    kwargs = {"tools": schemas} if native_tools else {}
    prompt = tokenizer.apply_chat_template(converted, add_generation_prompt=True, tokenize=False, **kwargs)
    if deepseek:
        prompt = _suppress_deepseek_thinking(prompt)
    return converted, prompt


def _json_objects(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    result = []
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text


def _normalize_tool_payload(payload: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    for key in ("tool_call", "function_call"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            normalized = _normalize_tool_payload(nested)
            if normalized:
                return normalized
    nested_function = payload.get("function")
    if isinstance(nested_function, dict):
        normalized = _normalize_tool_payload(nested_function)
        if normalized:
            return normalized

    name = (
        payload.get("name")
        or payload.get("function")
        or payload.get("tool")
        or payload.get("tool_name")
        or payload.get("function_name")
    )
    arguments = (
        payload.get("arguments")
        if "arguments" in payload
        else payload.get("parameters", payload.get("args", payload.get("input")))
    )
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            arguments = None
    if isinstance(name, str) and isinstance(arguments, dict):
        return name, arguments
    return None


def _normalized_marker_text(text: str) -> str:
    return (
        text.replace("｜", "|")
        .replace("▁", "_")
        .replace("<|tool|sep|>", "<|tool_sep|>")
        .replace("<|tool|call|>", "<|tool_call|>")
        .replace("<|tool|call|begin|>", "<|tool_call_begin|>")
        .replace("<|tool|call|end|>", "<|tool_call_end|>")
        .replace("<|tool|>", "<|tool|>")
        .replace("<|tool|end|>", "<|tool_end|>")
        .replace("<|tool|output|>", "<|tool_output|>")
        .replace("<|tool_call|begin|>", "<|tool_call_begin|>")
        .replace("<|tool_call|end|>", "<|tool_call_end|>")
    )


def _parse_marker_tool_call(text: str) -> tuple[str, dict[str, Any]] | None:
    text = _normalized_marker_text(text)
    flexible_patterns = (
        r"(?:<\|tool_call_begin\|>|<\|tool_call\|>)(?:\s*<\|tool_call_end\|>)*\s*function\s*(?:<\|tool_sep\|>|<\|tool\|>)\s*([A-Za-z_]\w*)\s*(?:<\|tool_sep\|>|<\|tool\|>)?\s*",
        r"(?:<\|tool_call_begin\|>|<\|tool_call\|>)(?:\s*<\|tool_call_end\|>)*\s*([A-Za-z_]\w*)\s*(?:<\|tool_sep\|>|<\|tool\|>)\s*",
    )
    for pattern in flexible_patterns:
        for match in re.finditer(pattern, text):
            tail = text[match.end() :]
            next_call = re.search(r"<\|tool_call(?:_begin)?\|>", tail)
            if next_call:
                tail = tail[: next_call.start()]
            for payload in _json_objects(tail):
                return match.group(1), payload

    for marker in ("<|tool_call_begin|>", "<|tool_call|>"):
        start = text.find(marker)
        while start != -1:
            chunk = text[start + len(marker) :]
            next_match = re.search(r"<\|tool_call(?:_begin)?\|>", chunk)
            if next_match:
                chunk = chunk[: next_match.start()]
            parts = [part.strip() for part in chunk.split("<|tool_sep|>") if part.strip()]
            if parts and parts[0] == "function":
                parts = parts[1:]
            if len(parts) >= 2:
                name = parts[0].splitlines()[0].strip()
                for payload in _json_objects(parts[1]):
                    if name:
                        return name, payload
            elif len(parts) == 1:
                head = parts[0]
                lines = head.splitlines()
                name = lines[0].strip()
                json_tail = "\n".join(lines[1:])
                for payload in _json_objects(json_tail):
                    if name:
                        return name, payload
            start = text.find(marker, start + len(marker))
    return None


def parse_llama_tool_call(completion: str) -> tuple[str, dict[str, Any]] | None:
    completion = completion.strip()
    marker_call = _parse_marker_tool_call(completion)
    if marker_call:
        return marker_call
    json_text = _strip_fences(completion.split("</think>")[-1])
    json_payloads = _json_objects(json_text)
    if (
        len(json_payloads) == 1
        and set(json_payloads[0]) == {"offer_id"}
        and isinstance(json_payloads[0]["offer_id"], str)
        and json_text.lstrip().startswith("{")
    ):
        return "apply_offer", {"offer_id": json_payloads[0]["offer_id"]}
    for payload in _json_objects(completion):
        normalized = _normalize_tool_payload(payload)
        if normalized:
            return normalized
    return None


def resolve_dtype(name: str, device: str) -> torch.dtype:
    if device == "cpu" and name != "float32":
        return torch.float32
    return {"float32": torch.float32, "float16": torch.float16, "bfloat16": torch.bfloat16}[name]


def load_local_llama31(model_path: Path, device: str, dtype: str):
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    kwargs: dict[str, Any] = {"local_files_only": True, "dtype": resolve_dtype(dtype, device), "low_cpu_mem_usage": True}
    if device == "auto": kwargs["device_map"] = "auto"
    elif device.startswith("cuda"): kwargs["device_map"] = {"": int(device.split(":", 1)[1]) if ":" in device else 0}
    elif device == "cpu": kwargs["device_map"] = "cpu"
    else: raise ValueError(f"Unsupported device: {device}")
    model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs)
    model.eval()
    return tokenizer, model, model.get_input_embeddings().weight.device


def smoke(model_path: Path) -> None:
    config = AutoConfig.from_pretrained(model_path, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    deepseek_call = '<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>function<｜tool▁sep｜>search_hotels\n```json\n{"city":"Paris"}\n```<｜tool▁call▁end｜>'
    if parse_llama_tool_call(deepseek_call) != ("search_hotels", {"city": "Paris"}):
        raise RuntimeError("Qwen-family tool parser smoke test failed")
    repeated_sep_call = '<｜tool▁call｜>function<｜tool▁sep｜>get_all_car_rental_companies_in_city<｜tool▁sep｜>{"city":"Los Angeles"}<｜tool▁sep｜>'
    if parse_llama_tool_call(repeated_sep_call) != ("get_all_car_rental_companies_in_city", {"city": "Los Angeles"}):
        raise RuntimeError("Qwen-family repeated-separator parser smoke test failed")
    nested = '```json\n{"function":{"name":"apply_offer","arguments":"{\\"offer_id\\":\\"OF-TEST\\"}"}}\n```'
    if parse_llama_tool_call(nested) != ("apply_offer", {"offer_id": "OF-TEST"}):
        raise RuntimeError("Qwen-family nested parser smoke test failed")
    bare_offer = '```json\n{"offer_id":"OF-TEST"}\n```'
    if parse_llama_tool_call(bare_offer) != ("apply_offer", {"offer_id": "OF-TEST"}):
        raise RuntimeError("Qwen-family bare offer parser smoke test failed")
    print(json.dumps({"model_type": config.model_type, "layers": config.num_hidden_layers, "hidden_size": config.hidden_size, "deepseek_template": _deepseek_style(tokenizer), "tool_parser": "passed"}, indent=2))
