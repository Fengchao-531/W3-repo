#!/usr/bin/env python3
import os
from pathlib import Path

from qwen_runner_factory import run


raw_path = os.environ.get("GEMMA_MODEL_PATH")
if not raw_path:
    raise SystemExit("GEMMA_MODEL_PATH is required; set it to a local Gemma instruct snapshot.")
run("gemma_instruct", Path(raw_path), "Gemma", "local_open_instruct.py")
