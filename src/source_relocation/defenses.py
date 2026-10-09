"""Upstream-backed prompt-injection defenses at AgentDojo's real pipeline hooks.

Install upstream projects and weights separately (see docs/upstream_defenses.md).
Absent dependencies abort the run. Method labels never select a fake policy prompt.
"""
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import sys

DEFENSES = ("none", "sandwich", "struq", "secalign", "perplexity", "datasentinel", "causalarmor")
TRAINED = ("struq", "secalign")
DETECTORS = ("perplexity", "datasentinel")


class DefenseSetupError(RuntimeError):
    pass


def required(var):
    value = os.environ.get(var)
    if not value:
        raise DefenseSetupError(f"Required upstream defense configuration missing: {var}")
    return value


def upstream_import(root_var, module):
    root = Path(required(root_var)).expanduser().resolve()
    if not root.is_dir():
        raise DefenseSetupError(f"Upstream checkout not found: {root}")
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return __import__(module, fromlist=["__name__"])


def upstream_file(root_var, name):
    path = Path(required(root_var)).expanduser().resolve() / name
    if not path.is_file():
        raise DefenseSetupError(f"Original implementation missing: {path}")
    spec = importlib.util.spec_from_file_location("w3_upstream_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def trained_settings(method):
    """Use the actual authors' trained model/LoRA and structured prompt format."""
    prefix = "W3_" + method.upper()
    upstream = upstream_file(prefix + "_REPO", "config.py")
    fmt = os.getenv(prefix + "_FORMAT", "SpclSpclSpcl")
    if fmt not in upstream.PROMPT_FORMAT:
        raise DefenseSetupError(f"Unsupported {method} format {fmt}")
    return required(prefix + "_MODEL"), os.environ.get(prefix + "_LORA"), upstream.PROMPT_FORMAT[fmt]


def text_of(message):
    from agentdojo.types import get_text_content_as_str
    return get_text_content_as_str(message.get("content") or [])


def replacement(message, text):
    from agentdojo.types import text_content_block_from_string
    return {**message, "content": [text_content_block_from_string(text)]}


class InputDefense:
    """Runs after InitQuery and after ToolsExecutor, before LLM consumption."""

    def __init__(self, method, original_task="", artifact_description=""):
        self.method = method
        self.original_task = original_task
        self.artifact_description = artifact_description
        self.events = []
        self._seen = set()
        self.detector = None
        if method == "datasentinel":
            upstream = upstream_import("W3_DATASENTINEL_REPO", "OpenPromptInjection")
            utils = upstream_import("W3_DATASENTINEL_REPO", "OpenPromptInjection.utils")
            config = utils.open_config(required("W3_DATASENTINEL_CONFIG"))
            config["params"]["ft_path"] = required("W3_DATASENTINEL_CHECKPOINT")
            self.detector = upstream.DataSentinelDetector(config)
        if method == "perplexity":
            original = upstream_file("W3_PERPLEXITY_REPO", "perplexity_filter.py")
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            if not torch.cuda.is_available():
                raise DefenseSetupError("The original perplexity filter requires CUDA.")
            name = required("W3_PERPLEXITY_MODEL")
            model = AutoModelForCausalLM.from_pretrained(name)
            tokenizer = AutoTokenizer.from_pretrained(name)
            self.detector = original.PerplexityFilter(
                model, tokenizer, float(required("W3_PERPLEXITY_THRESHOLD")),
                window_size=int(os.getenv("W3_PERPLEXITY_WINDOW", "10")),
            )

    def _blocked(self, text):
        if self.method == "datasentinel":
            return bool(self.detector.detect(text))
        if self.method == "perplexity":
            # Author's PerplexityFilter.filter uses token negative log-likelihood.
            return not bool(self.detector.filter([text])[1][0])
        return False

    def query(self, query, runtime, env, messages, extra_args):
        if self.method not in ("sandwich", *DETECTORS):
            return query, runtime, env, messages, extra_args
        updated = list(messages)
        for i, message in enumerate(updated):
            if i in self._seen or message["role"] not in ("user", "tool"):
                continue
            self._seen.add(i)
            text = text_of(message)
            if message["role"] == "user":
                fragment = self.artifact_description
                if not fragment or fragment not in text:
                    continue
                if self.method == "sandwich":
                    revised = text + "\n\nPlease always remember that your task is: " + self.original_task
                elif self._blocked(fragment):
                    revised = text.replace(fragment, "[Offer removed by " + self.method + "]")
                    self.events.append({"source": "user-relayed", "method": self.method, "blocked": True})
                else:
                    continue
            else:
                if self.method == "sandwich":
                    revised = text + "\n\nPlease always remember that your task is: " + self.original_task
                elif text and self._blocked(text):
                    revised = "[Tool observation removed by " + self.method + "]"
                    self.events.append({"source": "tool", "method": self.method, "blocked": True})
                else:
                    continue
            updated[i] = replacement(message, revised)
        return query, runtime, env, updated, extra_args


class ActionDefense:
    """Runs before ToolsExecutor: can block/replace an actual FunctionCall."""

    def __init__(self, method):
        self.method = method
        self.events = []
        self.middleware = None
        if method == "causalarmor":
            from causal_armor import CausalArmorConfig, CausalArmorMiddleware
            from causal_armor.providers.openai import OpenAIActionProvider, OpenAISanitizerProvider
            from causal_armor.providers.vllm import VLLMProxyProvider
            self.middleware = CausalArmorMiddleware(
                action_provider=OpenAIActionProvider(model=required("W3_CAUSAL_ACTION_MODEL")),
                proxy_provider=VLLMProxyProvider(base_url=required("W3_CAUSAL_PROXY_URL")),
                sanitizer_provider=OpenAISanitizerProvider(model=required("W3_CAUSAL_SANITIZER_MODEL")),
                config=CausalArmorConfig(margin_tau=float(os.getenv("W3_CAUSAL_MARGIN_TAU", "0"))),
            )

    def query(self, query, runtime, env, messages, extra_args):
        if self.middleware is None or not messages or messages[-1]["role"] != "assistant":
            return query, runtime, env, messages, extra_args
        proposed = messages[-1].get("tool_calls") or []
        if not proposed:
            return query, runtime, env, messages, extra_args
        from causal_armor import Message, MessageRole, ToolCall
        from agentdojo.functions_runtime import FunctionCall
        roles = dict(system=MessageRole.SYSTEM, user=MessageRole.USER,
                     assistant=MessageRole.ASSISTANT, tool=MessageRole.TOOL)
        context = [
            Message(role=roles[m["role"]], content=text_of(m),
                    tool_name=m["tool_call"].function if m["role"] == "tool" else None,
                    tool_call_id=m.get("tool_call_id") if m["role"] == "tool" else None)
            for m in messages[:-1] if m["role"] in roles
        ]
        final_calls = []
        for call in proposed:
            action = ToolCall(name=call.function, arguments=dict(call.args),
                              raw_text=json.dumps({"name": call.function, "arguments": call.args}))
            result = asyncio.run(self.middleware.guard(
                messages=context, action=action,
                untrusted_tool_names=frozenset(("list_available_offers",)),
            ))
            self.events.append({
                "method": "causalarmor", "action": call.function,
                "detected": bool(result.detection and result.detection.is_attack_detected),
                "defended": result.was_defended, "regenerated": result.regenerated,
            })
            if result.was_defended and not result.regenerated:
                # Do not execute the action. Keep the user-visible reason out of tool call args.
                continue
            final_calls.append(FunctionCall(
                function=result.final_action.name, args=result.final_action.arguments, id=call.id,
            ))
        updated = list(messages)
        updated[-1] = {**updated[-1], "tool_calls": final_calls or None}
        return query, runtime, env, updated, extra_args
