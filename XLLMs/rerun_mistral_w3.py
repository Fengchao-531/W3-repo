#!/usr/bin/env python3
"""Run the isolated W3 priority experiments with Ministral-8B-Instruct-2410."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("shared_w3_runner", HERE / "rerun_llama31_w3.py")
if spec is None or spec.loader is None:
    raise ImportError("Cannot load shared W3 runner")
runner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = runner
spec.loader.exec_module(runner)

MODEL_LABEL = "ministral_8b_instruct_2410"
MODEL_PATH = Path(
    "/scratch3/che489/FC-W2-SoK/model_cache/hub/"
    "models--mistralai--Ministral-8B-Instruct-2410/snapshots/"
    "2f494a194c5b980dfb9772cb92d26cbb671fce5a"
)

runner.MODEL_LABEL = MODEL_LABEL
runner.DEFAULT_MODEL_PATH = MODEL_PATH
runner.DEFAULT_OUTPUT_ROOT = HERE / "Mistral"
runner.__doc__ = "Rerun W3 Exp1 core and RQ2 Exp3 with Ministral-8B-Instruct-2410."


def import_mistral_modules(target_w3: Path):
    exp1_root = target_w3 / "Exp1_User_Context_Embedding"
    exp2_root = target_w3 / "Exp2_Task_Binding"
    exp4_root = target_w3 / "Exp4_General_Preference_Control"
    exp4b_root = target_w3 / "Exp4b_Preference_Controlled_External_Baseline"
    exp4_a1a2_root = runner.sync_exp4_a1a2_reference(target_w3)
    rq2_exp2_root = target_w3 / "RQ2/Exp2_SafetyIntent"
    rq2_exp3_root = target_w3 / "RQ2/Exp3_ Controlled_Source-Provenance_Intervention"
    for path in [HERE, exp1_root, exp2_root, exp4_root, exp4b_root, exp4_a1a2_root, rq2_exp2_root, rq2_exp3_root]:
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    adapter = runner.load_module("local_ministral8b_xllms", HERE / "local_ministral8b.py")
    exp1 = runner.load_module("exp1_pipeline", exp1_root / "exp1_pipeline.py")
    exp1.AGENTDOJO_REPO = runner.TRACING_ROOT / "2-AgentDojo/agentdojo"
    exp1.AGENTDOJO_SRC = exp1.AGENTDOJO_REPO / "src"
    exp1.DEFAULT_MODEL = MODEL_LABEL
    exp2 = runner.load_module("exp2_pipeline_mistral", exp2_root / "exp2_pipeline.py")
    exp4 = runner.load_module("exp4_pipeline_mistral", exp4_root / "exp4_pipeline.py")
    exp4b = runner.load_module("exp4b_pipeline_mistral", exp4b_root / "exp4b_pipeline.py")
    import os
    old_exp1_root = os.environ.get("EXP1_ROOT")
    os.environ["EXP1_ROOT"] = str(exp1_root)
    exp4_a1a2 = runner.load_module("exp4_a1a2_pipeline_mistral", exp4_a1a2_root / "exp2_pipeline.py")
    if old_exp1_root is None:
        os.environ.pop("EXP1_ROOT", None)
    else:
        os.environ["EXP1_ROOT"] = old_exp1_root
    rq2_exp2 = runner.load_module("rq2_exp2_pipeline_mistral", rq2_exp2_root / "rq2_exp2_pipeline.py")
    rq2_exp3 = runner.load_module("rq2_exp3_pipeline_mistral", rq2_exp3_root / "rq2_exp3_pipeline.py")
    return adapter, exp1, exp2, exp4, exp4b, exp4_a1a2, rq2_exp2, rq2_exp3


runner.import_w3_modules = import_mistral_modules


if __name__ == "__main__":
    runner.main()
