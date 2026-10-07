#!/usr/bin/env python3
"""Ministral-8B-Instruct-2410 adapter for AgentDojo messages and tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer


DEFAULT_MODEL_PATH = Path(
    "/scratch3/che489/FC-W2-SoK/model_cache/hub/"
    "models--mistralai--Ministral-8B-Instruct-2410/snapshots/"
    "2f494a194c5b980dfb9772cb92d26cbb671fce5a"
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


def agentdojo_messages_to_hf(messages: Any) -> list[dict[str, Any]]:
    converted = []
    pending_ids: list[str] = []
    call_number = 0
    for message in plain(messages):
        role = message["role"]
        calls = message.get("tool_calls") or []
        if role == "assistant" and calls:
            mistral_calls = []
            pending_ids = []
            for call in calls:
                call_number += 1
                call_id = f"c{call_number:08d}"
                pending_ids.append(call_id)
                mistral_calls.append(
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": call["function"],
                            "arguments": call.get("args", {}),
                        },
                    }
                )
            converted.append({"role": "assistant", "content": content_to_text(message.get("content")), "tool_calls": mistral_calls})
        elif role == "tool":
            call_id = pending_ids.pop(0) if pending_ids else f"c{call_number:08d}"
            converted.append({"role": "tool", "content": json.dumps({"result": content_to_text(message.get("content"))}, ensure_ascii=False), "tool_call_id": call_id})
        else:
            converted.append({"role": role, "content": content_to_text(message.get("content"))})
    return converted


def render_agentdojo_prompt(tokenizer: Any, messages: Any, tools: Any) -> tuple[list[dict[str, Any]], str]:
    converted = agentdojo_messages_to_hf(messages)
    prompt = tokenizer.apply_chat_template(
        converted,
        tools=agentdojo_tools_to_hf(tools),
        add_generation_prompt=True,
        tokenize=False,
    )
    return converted, prompt


def _json_objects(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    values = []
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            values.append(value)
    return values


def parse_llama_tool_call(completion: str) -> tuple[str, dict[str, Any]] | None:
    """Keep the shared runner contract while parsing Ministral tool calls."""
    for payload in _json_objects(completion):
        name = payload.get("name") or payload.get("function")
        arguments = payload.get("arguments", payload.get("parameters", payload.get("args")))
        if isinstance(name, str) and isinstance(arguments, dict):
            return name, arguments
    return None


def resolve_dtype(name: str, device: str) -> torch.dtype:
    if device == "cpu" and name != "float32":
        return torch.float32
    return {"float32": torch.float32, "float16": torch.float16, "bfloat16": torch.bfloat16}[name]


def load_local_llama31(model_path: Path, device: str, dtype: str):
    """Keep the shared runner contract while loading Ministral."""
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, fix_mistral_regex=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    kwargs: dict[str, Any] = {"local_files_only": True, "dtype": resolve_dtype(dtype, device), "low_cpu_mem_usage": True}
    if device == "auto":
        kwargs["device_map"] = "auto"
    elif device.startswith("cuda"):
        index = int(device.split(":", 1)[1]) if ":" in device else 0
        kwargs["device_map"] = {"": index}
    elif device == "cpu":
        kwargs["device_map"] = "cpu"
    else:
        raise ValueError(f"Unsupported device: {device}")
    model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs)
    model.eval()
    return tokenizer, model, model.get_input_embeddings().weight.device


def smoke(model_path: Path = DEFAULT_MODEL_PATH) -> None:
    config = AutoConfig.from_pretrained(model_path, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, fix_mistral_regex=True)
    parsed = parse_llama_tool_call('[TOOL_CALLS][{"name":"search_hotels","arguments":{"city":"Paris"},"id":"c00000001"}]')
    if parsed != ("search_hotels", {"city": "Paris"}):
        raise RuntimeError(f"Ministral parser failed: {parsed}")
    rendered = tokenizer.apply_chat_template(
        [{"role": "system", "content": "Helpful."}, {"role": "user", "content": "Search."}],
        tools=[{"type": "function", "function": {"name": "search_hotels", "description": "Search", "parameters": {"type": "object", "properties": {}}}}],
        add_generation_prompt=True,
        tokenize=False,
    )
    print(json.dumps({"model_type": config.model_type, "layers": config.num_hidden_layers, "hidden_size": config.hidden_size, "tool_parser": "passed", "tool_template": "[AVAILABLE_TOOLS]" in rendered}, indent=2))


if __name__ == "__main__":
    smoke()
