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
    subprocess.run([sys.executable, "plotting/rq1_figures.py", "--summary", args.summary, "--figure", "position", "--out", "outputs/figures/rq1_position.pdf"], check=True)
    if args.rq2_input:
        subprocess.run([sys.executable, "plotting/rq2_figures.py", "--input", args.rq2_input], check=True)
        from pathlib import Path
        directory = str(Path(args.rq2_input).parent)
        subprocess.run([sys.executable, "plotting/rq2_additional.py", "--rq2-dir", directory], check=True)


if __name__ == "__main__":
    main()
