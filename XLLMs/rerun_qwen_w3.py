#!/usr/bin/env python3
import os
from pathlib import Path
from qwen_runner_factory import run

raw_path = os.environ.get("QWEN_MODEL_PATH")
if not raw_path:
    raise SystemExit("QWEN_MODEL_PATH is required because no standalone Qwen snapshot is installed locally.")
run("qwen_instruct", Path(raw_path), "Qwen")
