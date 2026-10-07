#!/usr/bin/env python3
"""Portable AgentDojo adapter for Gemma and OLMo instruct checkpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch
from jinja2.exceptions import TemplateError
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer


TEMPLATE_EXCEPTIONS = (TypeError, ValueError, RuntimeError, IndexError, TemplateError)


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
        return "\n".join(
            str(item.get("content", item.get("text", "")))
            if isinstance(item, dict) else str(item)
            for item in content
        )
    return str(content)


def agentdojo_tools_to_hf(tools: Any) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters.model_json_schema(),
            },
        }
        for tool in tools
    ]


def tool_instruction(schemas: list[dict[str, Any]]) -> str:
    return (
        "Available tools (JSON schema):\n"
        + json.dumps(schemas, ensure_ascii=False)
        + "\nTo call a tool, output exactly one JSON object in this form: "
        '{"name":"tool_name","arguments":{...}}. Otherwise answer normally.'
    )


def compact_tool_instruction(schemas: list[dict[str, Any]]) -> str:
    lines = [
        "You can use tools when needed.",
        'To call a tool, reply with exactly one JSON object and no markdown: {"name":"tool_name","arguments":{...}}',
        "Available tools:",
    ]
    for schema in schemas:
        function = schema.get("function", {})
        params = function.get("parameters", {}) or {}
        properties = params.get("properties", {}) or {}
        required = set(params.get("required", []) or [])
        args = []
        for name, spec in properties.items():
            arg_type = spec.get("type") or "value"
            marker = "" if name in required else " optional"
            args.append(f"{name}: {arg_type}{marker}")
        signature = ", ".join(args)
        if signature:
            signature = f"({signature})"
        description = str(function.get("description") or "").replace("\n", " ")
        lines.append(f"- {function.get('name')}{signature}: {description}")
    return "\n".join(lines)


def is_olmo_tokenizer(tokenizer: Any) -> bool:
    name = str(getattr(tokenizer, "name_or_path", "")).lower()
    template = str(getattr(tokenizer, "chat_template", "") or "")
    return "olmo" in name or "<|system|>" in template and "<|user|>" in template


def convert_messages(messages: Any, native_tool_roles: bool) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for message in plain(messages):
        role = message["role"]
        calls = message.get("tool_calls") or []
        if role == "assistant" and calls:
            calls_text = "\n".join(
                json.dumps(
                    {"name": call["function"], "arguments": call.get("args", {})},
                    ensure_ascii=False,
                )
                for call in calls
            )
            converted.append({"role": "assistant", "content": calls_text})
        elif role == "tool":
            text = "[TOOL RESULT]\n" + content_to_text(message.get("content"))
            converted.append({"role": "tool" if native_tool_roles else "user", "content": text})
        else:
            converted.append({"role": role, "content": content_to_text(message.get("content"))})
    return converted


def _render(tokenizer: Any, messages: list[dict[str, Any]], **kwargs: Any) -> str:
    return tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=False, **kwargs
    )


def render_agentdojo_prompt(
    tokenizer: Any, messages: Any, tools: Any
) -> tuple[list[dict[str, Any]], str]:
    schemas = agentdojo_tools_to_hf(tools)

    # OLMo's simple ChatML-style template has no native tool syntax. The full
    # JSON schema tends to make it copy schema fragments instead of answering, so
    # use a compact instruction while preserving the normal system prompt first.
    if is_olmo_tokenizer(tokenizer):
        converted = convert_messages(messages, native_tool_roles=False)
        instruction = compact_tool_instruction(schemas)
        if converted and converted[0]["role"] == "system":
            converted[0]["content"] = converted[0]["content"] + "\n\n" + instruction
        elif converted and converted[0]["role"] == "user":
            converted[0]["content"] = instruction + "\n\n" + converted[0]["content"]
        else:
            converted.insert(0, {"role": "system", "content": instruction})
        return converted, _render(tokenizer, converted)

    # First preserve native roles and native tool schema whenever the checkpoint supports them.
    native = convert_messages(messages, native_tool_roles=True)
    try:
        prompt = _render(tokenizer, native, tools=schemas)
        if not schemas or schemas[0]["function"]["name"] in prompt:
            return native, prompt
    except TEMPLATE_EXCEPTIONS:
        pass

    converted = convert_messages(messages, native_tool_roles=False)
    instruction = tool_instruction(schemas)
    if converted and converted[0]["role"] == "system":
        converted[0]["content"] = instruction + "\n\n" + converted[0]["content"]
        try:
            return converted, _render(tokenizer, converted)
        except TEMPLATE_EXCEPTIONS:
            system_text = converted.pop(0)["content"]
    else:
        system_text = instruction

    # Gemma templates commonly reject system/tool roles. Fold the system text into
    # the first user turn while retaining the complete transcript in the saved trace.
    if converted and converted[0]["role"] == "user":
        converted[0]["content"] = system_text + "\n\n" + converted[0]["content"]
    else:
        converted.insert(0, {"role": "user", "content": system_text})
    return converted, _render(tokenizer, converted)


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


def _normalize_tool_payload(payload: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    if "tool_call" in payload and isinstance(payload["tool_call"], dict):
        nested = _normalize_tool_payload(payload["tool_call"])
        if nested:
            return nested
    if "function_call" in payload and isinstance(payload["function_call"], dict):
        nested = _normalize_tool_payload(payload["function_call"])
        if nested:
            return nested
    if "function" in payload and isinstance(payload["function"], dict):
        nested = _normalize_tool_payload(payload["function"])
        if nested:
            return nested

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


def parse_llama_tool_call(completion: str) -> tuple[str, dict[str, Any]] | None:
    completion = completion.strip()
    if completion.startswith("```"):
        completion = completion.strip("`").strip()
        if completion.lower().startswith("json"):
            completion = completion[4:].strip()
    for payload in _json_objects(completion):
        normalized = _normalize_tool_payload(payload)
        if normalized:
            return normalized
    return None


def resolve_dtype(name: str, device: str) -> torch.dtype:
    if device == "cpu" and name != "float32":
        return torch.float32
    return {
        "float32": torch.float32,
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
    }[name]


def load_local_llama31(model_path: Path, device: str, dtype: str):
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, local_files_only=True, trust_remote_code=True
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    kwargs: dict[str, Any] = {
        "local_files_only": True,
        "trust_remote_code": True,
        "dtype": resolve_dtype(dtype, device),
        "low_cpu_mem_usage": True,
    }
    if device == "auto":
        kwargs["device_map"] = "auto"
    elif device.startswith("cuda"):
        kwargs["device_map"] = {"": int(device.split(":", 1)[1]) if ":" in device else 0}
    elif device == "cpu":
        kwargs["device_map"] = "cpu"
    else:
        raise ValueError(f"Unsupported device: {device}")
    model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs)
    model.eval()
    return tokenizer, model, model.get_input_embeddings().weight.device


def smoke(model_path: Path) -> None:
    config = AutoConfig.from_pretrained(
        model_path, local_files_only=True, trust_remote_code=True
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, local_files_only=True, trust_remote_code=True
    )
    sample = '<tool_call>{"name":"search_hotels","arguments":{"city":"Paris"}}</tool_call>'
    if parse_llama_tool_call(sample) != ("search_hotels", {"city": "Paris"}):
        raise RuntimeError("Open-instruct tool parser smoke test failed")
    fenced = '```json\n{"tool_call":{"name":"search_hotels","arguments":"{\\"city\\":\\"Paris\\"}"}}\n```'
    if parse_llama_tool_call(fenced) != ("search_hotels", {"city": "Paris"}):
        raise RuntimeError("Open-instruct fenced tool parser smoke test failed")
    print(
        json.dumps(
            {
                "model_type": config.model_type,
                "layers": config.num_hidden_layers,
                "hidden_size": config.hidden_size,
                "chat_template": bool(tokenizer.chat_template),
                "tool_parser": "passed",
            },
            indent=2,
        )
    )
