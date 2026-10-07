#!/usr/bin/env python3
import os
from pathlib import Path

from qwen_runner_factory import run


raw_path = os.environ.get("OLMO_MODEL_PATH")
if not raw_path:
    raise SystemExit("OLMO_MODEL_PATH is required; set it to a local OLMo instruct snapshot.")
run("olmo_instruct", Path(raw_path), "OLMo", "local_open_instruct.py")
