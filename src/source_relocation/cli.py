import argparse
import csv
import json
from pathlib import Path


def save_jsonl(rows, path):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("".join(json.dumps(row, ensure_ascii=False, default=str) + "\n" for row in rows), encoding="utf-8")


def build(args):
    from .manifest import load_tasks, make_manifest, save_manifest
    tasks = load_tasks(args.tasks_jsonl, args.domain, args.benchmark_version)
    if args.base_tasks is not None:
        if len(tasks) < args.base_tasks:
            raise ValueError(f"Requested {args.base_tasks} base tasks, found {len(tasks)}")
        tasks = tasks[:args.base_tasks]
    rows = make_manifest(tasks, args.domain)
    save_manifest(rows, args.manifest)
    print(json.dumps({"manifest": args.manifest, "base_tasks": len(tasks), "matched_units": len(rows)}))


def run(args):
    from .manifest import load_manifest
    from .prompts import experiment_conditions, render_condition
    from .agent import execute
    from .defenses import DEFENSES
    manifest = load_manifest(args.manifest)
    if args.limit:
        manifest = manifest[:args.limit]
    cases = experiment_conditions(args.rq, args.experiment)
    for row in manifest:
        for case in cases:
            rendered = render_condition(row, case, row["task"])
            defenses = (
                DEFENSES if args.defense == "all" else (args.defense,)
            ) if args.rq == "rq3" and args.experiment == "defenses" else ("none",)
            for defense in defenses:
                out = Path(args.outputs) / args.rq / args.experiment / args.domain / args.model / defense / rendered["condition"] / row["pair_id"]
                if (out / "result.json").exists() and not args.force and not args.preview:
                    continue
                if args.preview:
                    print(json.dumps({"pair_id": row["pair_id"], "condition": rendered["condition"], "defense": defense, "prompt": rendered["prompt"]}, ensure_ascii=False))
                    continue
                result = execute(row, rendered, args.model, str(out), defense, args.benchmark_version)
                print(json.dumps({key: result[key] for key in ("pair_id", "condition", "selected", "task_success", "malicious_action_executed")}))


def collect(args):
    from .evaluation import save_summary
    rows = save_summary(args.outputs, args.summary)
    print(json.dumps({"summaries": len(rows), "file": args.summary}))


def read_contexts(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def analyze_internal(args):
    from .tracing import InternalProbe, matched_gap, bidirectional_patch, head_set_effect, selected_heads, evaluate_head_sets
    from .spec import MODEL_IDS
    probe = InternalProbe(MODEL_IDS.get(args.model, args.model))
    values = []
    for row in read_contexts(args.contexts):
        if args.experiment == "sweep":
            for component in ("attention", "mlp"):
                for layer in range(args.first_layer, args.last_layer + 1):
                    patch = bidirectional_patch(probe, row["E"], row["UC"], row["code"], component, layer)
                    values.append({"unit_id": row["unit_id"], "base_task_id": row["base_task_id"], "artifact_type": row["artifact_type"], **patch})
            continue
        if args.experiment == "headsets":
            import random
            from .tracing import evaluate_head_sets
            selection = json.loads(Path(args.headsets).read_text(encoding="utf-8"))["selected"]
            top = [tuple(pair) for pair in selection["top"]]
            counteracting = tuple(selection["counteracting"])
            n_heads = probe.model.config.num_attention_heads
            full = [(layer, head) for layer in range(args.first_layer, args.last_layer + 1) for head in range(n_heads)]
            rng = random.Random(args.random_seed)
            random_set = rng.sample(full, len(top))
            combinations = {
                "Top3": top, "Top3_counteracting": list(dict.fromkeys([*top, counteracting])),
                "FullWindow": full, "Random3": random_set,
            }
            result_set = evaluate_head_sets(probe, [row], combinations)
            values.extend({"base_task_id": row["base_task_id"], "artifact_type": row["artifact_type"], **value} for value in result_set)
            continue
        if args.experiment == "representation":
            result = matched_gap(probe, row["E"], row["UC"], row["code"])
        elif args.experiment == "patching":
            result = bidirectional_patch(probe, row["E"], row["UC"], row["code"], args.component, args.layer, args.head)
        elif args.experiment == "heads":
            indices = list(range(args.first_layer, args.last_layer + 1))
            results = [bidirectional_patch(probe, row["E"], row["UC"], row["code"], "attention", layer, head) for layer in indices for head in range(probe.model.config.num_attention_heads)]
            result = {"head_effects": results}
        elif args.experiment == "code_control":
            result = {code: matched_gap(probe, row["E"], row["UC"], code) for code in ("QUALITY95", "SAVE20", "VIEWPLUS")}
        elif args.experiment == "attention":
            from .attention import assign_regions, attention_by_region
            results = {}
            for source in ("E", "UC"):
                text = row[source].rstrip() + "\nPromo code:"
                regions = assign_regions(probe.tokenizer, text, row["code"], row.get("user_task", ""), reliability=row.get("reliability", ""))
                heads = [(int(item.split(":")[0]), int(item.split(":")[1])) for item in args.heads.split(",")]
                results[source] = attention_by_region(probe, text, regions, heads)
            result = results
        elif args.experiment == "heldout":
            heads = [(int(item.split(":")[0]), int(item.split(":")[1])) for item in args.heads.split(",")]
            result = evaluate_head_sets(probe, [row], {"selected": heads})[0]
        else:
            raise ValueError(args.experiment)
        values.append({"unit_id": row["unit_id"], "base_task_id": row["base_task_id"], "artifact_type": row["artifact_type"], **result})
    save_jsonl(values, args.out)
    print(json.dumps({"model": args.model, "units": len(values), "file": args.out}))


def collect_deployed(args):
    from .deployment import summarize_deployment, round_average
    from .evaluation import load_results
    import pandas as pd
    input_path = Path(args.inputs)
    data = [dict(row) for row in csv.DictReader(input_path.open(encoding="utf-8"))] if input_path.suffix == ".csv" else read_contexts(args.inputs)
    for row in data:
        for label in ("E1", "E2", "E3", "C1", "C2", "C3"):
            for term in ("applicable", "violation"):
                k = label + "_" + term
                row[k] = str(row.get(k, "")).lower() in ("1", "true", "yes")
    report = round_average(summarize_deployment(data))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(report).to_csv(args.out, index=False)
    print(json.dumps({"agents": len({x['agent'] for x in report}), "file": args.out}))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="source-relocation")
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--tasks-jsonl")
    b.add_argument("--base-tasks", type=int, default=20)
    b.add_argument("--domain", choices=("travel", "workspace", "banking", "slack"), default="travel")
    b.add_argument("--benchmark-version", default="v1")
    b.add_argument("--manifest", default="outputs/manifests/travel.jsonl")
    b.set_defaults(func=build)
    r = sub.add_parser("run")
    r.add_argument("--rq", choices=("rq1", "rq3"), required=True)
    r.add_argument("--experiment", required=True)
    r.add_argument("--model", default="gpt4o")
    r.add_argument("--domain", default="travel")
    r.add_argument("--benchmark-version", default="v1")
    r.add_argument("--manifest", default="outputs/manifests/travel.jsonl")
    r.add_argument("--outputs", default="outputs/runs")
    r.add_argument("--limit", type=int)
    r.add_argument("--defense", choices=("all", "none", "sandwich", "struq", "secalign", "perplexity", "datasentinel", "causalarmor"), default="all")
    r.add_argument("--force", action="store_true")
    r.add_argument("--preview", action="store_true")
    r.set_defaults(func=run)
    a = sub.add_parser("analyze")
    a.add_argument("--outputs", default="outputs/runs")
    a.add_argument("--summary", default="outputs/analysis/summary.csv")
    a.set_defaults(func=collect)
    i = sub.add_parser("internal")
    i.add_argument("--model", default="llama31")
    i.add_argument("--experiment", choices=("representation", "patching", "sweep", "heads", "headsets", "code_control", "attention", "heldout"), required=True)
    i.add_argument("--contexts", required=True)
    i.add_argument("--component", choices=("attention", "mlp"), default="attention")
    i.add_argument("--layer", type=int, default=25)
    i.add_argument("--head", type=int)
    i.add_argument("--heads", default="25:0,25:1,25:2")
    i.add_argument("--headsets", default="outputs/internal/selected_heads.json")
    i.add_argument("--random-seed", type=int, default=1234)
    i.add_argument("--first-layer", type=int, default=20)
    i.add_argument("--last-layer", type=int, default=27)
    i.add_argument("--out", default="outputs/internal/results.jsonl")
    i.set_defaults(func=analyze_internal)
    d = sub.add_parser("deployed")
    d.add_argument("--inputs", required=True)
    d.add_argument("--out", default="outputs/analysis/deployed.csv")
    d.set_defaults(func=collect_deployed)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    main()
