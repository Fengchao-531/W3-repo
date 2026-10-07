#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


THIS_FILE = Path(__file__).resolve()
XLLMS_ROOT = THIS_FILE.parent
SOURCE_W3 = XLLMS_ROOT.parent
TRACING_ROOT = SOURCE_W3.parent
DEMO_ROOT = TRACING_ROOT / "Demo"
DEFAULT_MODEL_PATH = (
    Path("/scratch3/che489/FC-W2-SoK/model_cache/hub")
    / "models--meta-llama--Llama-3.1-8B-Instruct"
    / "snapshots"
    / "0e9e39f249a16976918f6564b8830bc894c89659"
)
MODEL_LABEL = "llama31_8b_instruct"
DEFAULT_OUTPUT_ROOT = XLLMS_ROOT / "Llama3.1"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


@dataclass
class RunArgs:
    model: str = MODEL_LABEL
    temperature: float = 0.0
    limit: int | None = None
    force: bool = False
    run_id: str | None = None
    pair_id: str | None = None
    condition: str = "all"


def prepare_rq3_workspace(target_w3: Path) -> None:
    source = SOURCE_W3 / "RQ3"
    target = target_w3 / "RQ3"
    if not source.is_dir():
        raise SystemExit(f"Missing source RQ3 folder: {source}")
    shutil.copytree(
        source,
        target,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "02_runs", "03_annotations", "04_processed", "05_statistics", "06_figures", "07_logs"),
    )


def import_modules(target_w3: Path):
    exp1_root = target_w3 / "Exp1_User_Context_Embedding"
    rq3_root = target_w3 / "RQ3" / "RQ3-AControlledVerification"
    for path in [str(DEMO_ROOT), str(exp1_root), str(rq3_root)]:
        if path not in sys.path:
            sys.path.insert(0, path)
    local_llama31 = load_module("local_llama31_xllms_rq3", DEMO_ROOT / "01_local_llama31.py")
    exp1 = load_module("exp1_pipeline", exp1_root / "exp1_pipeline.py")
    exp1.AGENTDOJO_REPO = TRACING_ROOT / "2-AgentDojo" / "agentdojo"
    exp1.AGENTDOJO_SRC = exp1.AGENTDOJO_REPO / "src"
    exp1.DEFAULT_MODEL = MODEL_LABEL
    rq3 = load_module("rq3_controlled_verification_xllms", rq3_root / "rq3_controlled_verification.py")
    rq3.DEFAULT_MODEL = MODEL_LABEL
    rq3a = load_module("rq3a_aggregate_analysis_xllms", rq3_root / "rq3a_aggregate_analysis.py")
    return local_llama31, exp1, rq3, rq3a


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RQ3 E_M_H3 with local Llama-3.1-8B-Instruct.")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--dtype", default="bfloat16", choices=["float32", "float16", "bfloat16"])
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--pair-id", default=None)
    parser.add_argument("--condition", choices=["all", "E_M_H2", "E_M_H3"], default="all")
    parser.add_argument("--include-e-m-h2", action="store_true", help="Deprecated; E_M_H2 is included by default.")
    parser.add_argument("--h3-only", action="store_true", help="Diagnostic mode: run only E_M_H3.")
    parser.add_argument("--no-hidden-states", dest="save_hidden_states", action="store_false")
    parser.set_defaults(save_hidden_states=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = args.model_path.expanduser().resolve()
    if not model_path.is_dir():
        raise SystemExit(f"Missing local model snapshot: {model_path}")

    base_runner = load_module("llama31_w3_base_runner", XLLMS_ROOT / "rerun_llama31_w3.py")
    base_runner.prepare_environment(model_path)
    target_w3 = args.output_root.expanduser().resolve()
    base_runner.prepare_workspace(target_w3, reset=False)
    prepare_rq3_workspace(target_w3)
    os.environ["EXP1_ROOT"] = str(SOURCE_W3 / "Exp1_User_Context_Embedding")
    os.environ["RQ2_EXP2_ROOT"] = str(SOURCE_W3 / "RQ2" / "Exp2_SafetyIntent")
    os.environ["RQ3_INCLUDE_E_M_H2"] = "0" if args.h3_only else "1"

    write_json(
        target_w3 / f"00_{MODEL_LABEL}_rq3_manifest.json",
        {
            "created_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source_w3": str(SOURCE_W3),
            "target_w3": str(target_w3),
            "model_label": MODEL_LABEL,
            "model_path": str(model_path),
            "stage": "rq3_controlled_verification_e_m_h3",
            "limit": args.limit,
            "force": args.force,
            "device": args.device,
            "dtype": args.dtype,
            "max_new_tokens": args.max_new_tokens,
            "save_hidden_states": args.save_hidden_states,
        },
    )

    local_llama31, exp1, rq3, rq3a = import_modules(target_w3)
    rq3.EXP1_ROOT = SOURCE_W3 / "Exp1_User_Context_Embedding"
    rq3a.EXP1_ROOT = SOURCE_W3 / "Exp1_User_Context_Embedding"
    rq3a.RQ2_EXP2_ROOT = SOURCE_W3 / "RQ2" / "Exp2_SafetyIntent"
    random.seed(0)
    base_runner.LocalLlama31LLM.install(
        exp1,
        local_llama31=local_llama31,
        model_path=model_path,
        device=args.device,
        dtype=args.dtype,
        max_new_tokens=args.max_new_tokens,
        save_hidden_states=args.save_hidden_states,
    )

    rq3.setup_dirs()
    rq3.build_dataset()
    rq3.validate_dataset()
    rq3.make_run_queue()
    rq3.run_selected(RunArgs(limit=args.limit, force=args.force, run_id=args.run_id, pair_id=args.pair_id, condition=args.condition))
    rq3.process_results()
    rq3.statistics()
    rq3.figures()
    rq3a.main()

    write_json(
        target_w3 / f"01_{MODEL_LABEL}_rq3_done.json",
        {
            "finished_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "target_w3": str(target_w3),
            "stage": "rq3_controlled_verification_e_m_h3",
        },
    )
    print(f"\nRQ3 Llama workspace: {target_w3 / 'RQ3' / 'RQ3-AControlledVerification'}")


if __name__ == "__main__":
    main()
