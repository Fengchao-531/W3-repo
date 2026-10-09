import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

from source_relocation.cli import save_jsonl


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def discovery_holdout(rows, seed=1234, per_type=9):
    rng = random.Random(seed)
    discovery, holdout = [], []
    for kind in ("M", "BM"):
        group = sorted((row for row in rows if row["artifact_type"] == kind), key=lambda row: row["unit_id"])
        rng.shuffle(group)
        if len(group) < per_type:
            raise ValueError(f"Insufficient {kind} matched checkpoints: {len(group)}")
        discovery.extend(group[:per_type])
        holdout.extend(group[per_type:])
    return discovery, holdout


def execute(args):
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(args.contexts)
    discovery, holdout = discovery_holdout(rows, args.seed, args.discovery_per_type)
    selected_contexts = out / "discovery_contexts.jsonl"
    heldout_contexts = out / "heldout_contexts.jsonl"
    save_jsonl(discovery, selected_contexts)
    save_jsonl(holdout, heldout_contexts)

    def command(*parts):
        cmd = [sys.executable, "-m", "source_relocation.cli", "internal", "--model", args.model, *map(str, parts)]
        if args.print_commands:
            print(" ".join(cmd))
        else:
            subprocess.run(cmd, check=True)

    command("--experiment", "representation", "--contexts", args.contexts, "--out", out / "representation.jsonl")
    command("--experiment", "sweep", "--contexts", selected_contexts,
            "--first-layer", args.sweep_first, "--last-layer", args.sweep_last,
            "--out", out / "sweep.jsonl")
    command("--experiment", "heads", "--contexts", selected_contexts,
            "--first-layer", args.window_first, "--last-layer", args.window_last,
            "--out", out / "head_discovery.jsonl")

    head_stats = out / "head_discovery.jsonl"
    selection_file = out / "selected_heads.json"
    selector = [sys.executable, "analysis/rq2_heads.py", "--input", str(head_stats), "--out", str(selection_file)]
    if args.print_commands:
        print(" ".join(selector))
        heads = "25:0,25:1,25:2"
    else:
        subprocess.run(selector, check=True)
        selected = json.loads(selection_file.read_text(encoding="utf-8"))["selected"]["top"]
        heads = ",".join(f"{layer}:{head}" for layer, head in selected)

    command("--experiment", "headsets", "--contexts", heldout_contexts,
            "--headsets", selection_file, "--first-layer", args.window_first,
            "--last-layer", args.window_last, "--random-seed", args.seed,
            "--out", out / "heldout_headsets.jsonl")
    command("--experiment", "attention", "--contexts", args.contexts,
            "--heads", heads, "--out", out / "attention.jsonl")
    command("--experiment", "code_control", "--contexts", args.contexts,
            "--out", out / "code_control.jsonl")

    if args.reliability_contexts:
        command("--experiment", "attention", "--contexts", args.reliability_contexts,
                "--heads", heads, "--out", out / "reliability_attention.jsonl")

    post = [
        [sys.executable, "analysis/rq2.py", "--input", str(out / "representation.jsonl"),
         "--out", str(out / "late_layer.csv")],
        [sys.executable, "analysis/rq2_regions.py", "--input", str(out / "attention.jsonl"),
         "--out", str(out / "semantic_regions.csv")],
    ]
    if args.reliability_contexts:
        post.append([sys.executable, "analysis/rq2_regions.py",
                     "--input", str(out / "reliability_attention.jsonl"),
                     "--out", str(out / "reliability_regions.csv")])
    for cmd in post:
        if args.print_commands:
            print(" ".join(cmd))
        else:
            subprocess.run(cmd, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="llama31")
    parser.add_argument("--contexts", required=True)
    parser.add_argument("--reliability-contexts")
    parser.add_argument("--outdir", default="outputs/internal/llama31")
    parser.add_argument("--discovery-per-type", type=int, default=9)
    parser.add_argument("--seed", type=int, default=1234)
    parser.add_argument("--sweep-first", type=int, default=20)
    parser.add_argument("--sweep-last", type=int, default=32)
    parser.add_argument("--window-first", type=int, default=25)
    parser.add_argument("--window-last", type=int, default=28)
    parser.add_argument("--print-commands", action="store_true")
    args = parser.parse_args()
    if args.sweep_first > args.sweep_last or args.window_first > args.window_last:
        parser.error("Layer range start exceeds end")
    execute(args)


if __name__ == "__main__":
    main()
