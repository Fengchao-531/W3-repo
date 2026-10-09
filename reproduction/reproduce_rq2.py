import argparse
from source_relocation.cli import main


def reproduce():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="llama31")
    parser.add_argument("--contexts", required=True)
    args = parser.parse_args()
    for experiment in ("representation", "patching"):
        params = ["internal", "--model", args.model, "--contexts", args.contexts, "--experiment", experiment, "--out", f"outputs/internal/{args.model}_{experiment}.jsonl"]
        if experiment == "patching":
            params.extend(["--component", "attention", "--layer", "25"])
        main(params)


if __name__ == "__main__":
    reproduce()
