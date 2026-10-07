"""Configure the shared isolated W3 runner for a Qwen-family adapter."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def run(
    model_label: str,
    model_path: Path,
    output_name: str,
    adapter_filename: str = "local_qwen_family.py",
) -> None:
    spec = importlib.util.spec_from_file_location(f"shared_w3_runner_{model_label}", HERE / "rerun_llama31_w3.py")
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load shared W3 runner")
    runner = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = runner
    spec.loader.exec_module(runner)
    runner.MODEL_LABEL = model_label
    runner.DEFAULT_MODEL_PATH = model_path
    runner.DEFAULT_OUTPUT_ROOT = HERE / output_name
    runner.__doc__ = f"Rerun W3 Exp1 core and RQ2 Exp3 with {model_label}."

    def import_modules(target_w3: Path):
        exp1_root = target_w3 / "Exp1_User_Context_Embedding"
        exp2_root = target_w3 / "Exp2_Task_Binding"
        exp4_root = target_w3 / "Exp4_General_Preference_Control"
        exp4b_root = target_w3 / "Exp4b_Preference_Controlled_External_Baseline"
        exp4_a1a2_root = runner.sync_exp4_a1a2_reference(target_w3)
        rq2_exp2_root = target_w3 / "RQ2/Exp2_SafetyIntent"
        rq2_exp3_root = target_w3 / "RQ2/Exp3_ Controlled_Source-Provenance_Intervention"
        for path in [HERE, exp1_root, exp2_root, exp4_root, exp4b_root, exp4_a1a2_root, rq2_exp2_root, rq2_exp3_root]:
            if str(path) not in sys.path: sys.path.insert(0, str(path))
        adapter = runner.load_module(f"local_adapter_{model_label}", HERE / adapter_filename)
        exp1 = runner.load_module("exp1_pipeline", exp1_root / "exp1_pipeline.py")
        exp1.AGENTDOJO_REPO = runner.TRACING_ROOT / "2-AgentDojo/agentdojo"
        exp1.AGENTDOJO_SRC = exp1.AGENTDOJO_REPO / "src"
        exp1.DEFAULT_MODEL = model_label
        exp2 = runner.load_module(f"exp2_pipeline_{model_label}", exp2_root / "exp2_pipeline.py")
        exp4 = runner.load_module(f"exp4_pipeline_{model_label}", exp4_root / "exp4_pipeline.py")
        exp4b = runner.load_module(f"exp4b_pipeline_{model_label}", exp4b_root / "exp4b_pipeline.py")
        import os
        old_exp1_root = os.environ.get("EXP1_ROOT")
        os.environ["EXP1_ROOT"] = str(exp1_root)
        exp4_a1a2 = runner.load_module(f"exp4_a1a2_pipeline_{model_label}", exp4_a1a2_root / "exp2_pipeline.py")
        if old_exp1_root is None:
            os.environ.pop("EXP1_ROOT", None)
        else:
            os.environ["EXP1_ROOT"] = old_exp1_root
        rq2_exp2 = runner.load_module(f"rq2_exp2_{model_label}", rq2_exp2_root / "rq2_exp2_pipeline.py")
        rq2_exp3 = runner.load_module(f"rq2_exp3_{model_label}", rq2_exp3_root / "rq2_exp3_pipeline.py")
        return adapter, exp1, exp2, exp4, exp4b, exp4_a1a2, rq2_exp2, rq2_exp3

    runner.import_w3_modules = import_modules
    runner.main()
