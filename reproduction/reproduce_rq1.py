import argparse
from source_relocation.cli import main


def reproduce():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt4o")
    parser.add_argument("--domain", default="travel")
    args = parser.parse_args()
    main(["build", "--domain", args.domain, "--manifest", f"outputs/manifests/{args.domain}.jsonl"])
    for experiment in ("relocation", "position", "preference", "instruction", "reliability", "source_label"):
        main(["run", "--rq", "rq1", "--experiment", experiment, "--model", args.model, "--domain", args.domain, "--manifest", f"outputs/manifests/{args.domain}.jsonl"])
    main(["analyze"])
    import subprocess
    import sys
    subprocess.run([sys.executable, "analysis/rq1_controls.py"], check=True)


if __name__ == "__main__":
    reproduce()
