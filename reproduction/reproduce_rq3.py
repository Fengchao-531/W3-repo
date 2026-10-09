import argparse
from source_relocation.cli import main


def reproduce():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt4o")
    parser.add_argument("--domain", default="travel")
    parser.add_argument("--defense", default="all", choices=("all", "none", "sandwich", "struq", "secalign", "perplexity", "datasentinel", "causalarmor"))
    args = parser.parse_args()
    main(["build", "--domain", args.domain, "--manifest", f"outputs/manifests/{args.domain}.jsonl"])
    for experiment in ("verification", "defenses"):
        cmd = ["run", "--rq", "rq3", "--experiment", experiment, "--model", args.model, "--domain", args.domain, "--manifest", f"outputs/manifests/{args.domain}.jsonl"]
        if experiment == "defenses":
            cmd.extend(["--defense", args.defense])
        main(cmd)
    main(["analyze"])
    import subprocess
    import sys
    subprocess.run([sys.executable, "analysis/rq3_results.py"], check=True)


if __name__ == "__main__":
    reproduce()
