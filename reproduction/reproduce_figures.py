import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", default="outputs/analysis/summary.csv")
    parser.add_argument("--rq2-input")
    args = parser.parse_args()
    for script in ("plotting/rq1_figures.py", "plotting/rq3_figures.py"):
        subprocess.run([sys.executable, script, "--summary", args.summary], check=True)
    if args.rq2_input:
        subprocess.run([sys.executable, "plotting/rq2_figures.py", "--input", args.rq2_input], check=True)


if __name__ == "__main__":
    main()
