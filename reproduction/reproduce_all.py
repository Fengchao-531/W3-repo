import argparse
import subprocess
import sys
from pathlib import Path


def commands(args):
    manifest = f"outputs/manifests/{args.domain}.jsonl"
    contexts = f"outputs/internal/{args.domain}_contexts.jsonl"
    reliability = f"outputs/internal/{args.domain}_reliability_contexts.jsonl"
    from source_relocation.models import select_models
    rq1_context_model = select_models(args.rq1_model, getattr(args, "rq1_models", None))[0]
    rq2_selected = select_models(args.rq2_model, getattr(args, "rq2_models", None), internal=True)
    rq2_dir = f"outputs/internal/{args.rq2_model}" if not getattr(args, "rq2_models", None) else "outputs/internal"
    rq2_figure_model = rq2_selected[0]
    plan = [
        [sys.executable, "reproduction/reproduce_rq1.py",
         "--model", args.rq1_model, "--domain", args.domain] + (["--models", args.rq1_models] if getattr(args, "rq1_models", None) else []),
        [sys.executable, "analysis/rq2_exposure.py",
         "--manifest", manifest, "--runs", "outputs/runs/rq1/relocation",
         "--out", "outputs/analysis/rq2_exposure.csv"],
        [sys.executable, "reproduction/build_contexts.py",
         "--manifest", manifest, "--model", rq1_context_model,
         "--experiment", "relocation", "--out", contexts],
        [sys.executable, "reproduction/build_contexts.py",
         "--manifest", manifest, "--model", rq1_context_model,
         "--experiment", "reliability", "--out", reliability],
        [sys.executable, "reproduction/reproduce_rq2.py",
         "--model", args.rq2_model, "--contexts", contexts,
         "--reliability-contexts", reliability,
         "--outdir", rq2_dir,
         "--sweep-first", str(args.sweep_first),
         "--sweep-last", str(args.sweep_last),
         "--window-first", str(args.window_first),
         "--window-last", str(args.window_last)] + (["--models", args.rq2_models] if getattr(args, "rq2_models", None) else []),
        [sys.executable, "reproduction/reproduce_rq3.py",
         "--model", args.rq3_model, "--domain", args.domain,
         "--defense", args.defense] + (["--models", args.rq3_models] if getattr(args, "rq3_models", None) else []),
        [sys.executable, "reproduction/reproduce_figures.py",
         "--rq2-input", f"outputs/internal/{rq2_figure_model}/representation.jsonl"],
        [sys.executable, "reproduction/reproduce_tables.py"],
    ]
    if args.deployed_input:
        plan.append([sys.executable, "-m", "source_relocation.cli",
                     "deployed", "--inputs", args.deployed_input,
                     "--out", "outputs/analysis/deployed.csv"])
    return plan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="travel")
    parser.add_argument("--rq1-model", default="gpt4o")
    parser.add_argument("--rq1-models")
    parser.add_argument("--rq2-model", default="llama31")
    parser.add_argument("--rq2-models")
    parser.add_argument("--rq3-model", default="gpt4o")
    parser.add_argument("--rq3-models")
    parser.add_argument("--defense", default="all")
    parser.add_argument("--deployed-input")
    parser.add_argument("--sweep-first", type=int, default=20)
    parser.add_argument("--sweep-last", type=int, default=32)
    parser.add_argument("--window-first", type=int, default=25)
    parser.add_argument("--window-last", type=int, default=28)
    parser.add_argument("--print-commands", action="store_true")
    args = parser.parse_args()
    for cmd in commands(args):
        if args.print_commands:
            print(" ".join(cmd))
        else:
            subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
