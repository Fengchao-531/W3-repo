#!/usr/bin/env python3
from pathlib import Path
from qwen_runner_factory import run

run(
    "deepseek_r1_distill_qwen_7b",
    Path("/scratch3/che489/FC-W2-SoK/model_cache/hub/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-7B/snapshots/916b56a44061fd5cd7d6a8fb632557ed4f724f60"),
    "DeepSeek",
)
