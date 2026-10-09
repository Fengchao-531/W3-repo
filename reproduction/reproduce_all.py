import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt4o")
    parser.add_argument("--domain", default="travel")
    args = parser.parse_args()
    for name in ("rq1", "rq3"):
        subprocess.run([sys.executable, f"reproduction/reproduce_{name}.py", "--model", args.model, "--domain", args.domain], check=True)
    subprocess.run([sys.executable, "reproduction/reproduce_figures.py"], check=True)
    subprocess.run([sys.executable, "reproduction/reproduce_tables.py"], check=True)


if __name__ == "__main__":
    main()
