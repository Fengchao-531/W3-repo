import argparse
import subprocess
import sys
from pathlib import Path

from source_relocation.evaluation import save_summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rq1-runs", default="outputs/runs/rq1")
    parser.add_argument("--rq3-runs", default="outputs/runs/rq3/defenses")
    parser.add_argument("--rq2-input")
    args = parser.parse_args()
    rq1 = Path(args.rq1_runs)
    rq3 = Path(args.rq3_runs)
    if rq1.exists():
        rq1_csv = "outputs/analysis/rq1_only_summary.csv"
        save_summary(str(rq1), rq1_csv)
        for figure, filename in (
            ("adoption", "outputs/figures/rq1.pdf"),
            ("position", "outputs/figures/rq1_position.pdf"),
        ):
            subprocess.run(
                [sys.executable, "plotting/rq1_figures.py", "--summary", rq1_csv,
                 "--figure", figure, "--out", filename], check=True,
            )
    if rq3.exists():
        rq3_csv = "outputs/analysis/rq3_defenses_only_summary.csv"
        save_summary(str(rq3), rq3_csv)
        subprocess.run(
            [sys.executable, "plotting/rq3_figures.py", "--summary", rq3_csv,
             "--out", "outputs/figures/rq3.pdf"], check=True,
        )
    if args.rq2_input:
        subprocess.run(
            [sys.executable, "plotting/rq2_figures.py",
             "--input", args.rq2_input,
             "--out", "outputs/figures/rq2.pdf"], check=True,
        )
        directory = str(Path(args.rq2_input).parent)
        subprocess.run(
            [sys.executable, "plotting/rq2_additional.py",
             "--rq2-dir", directory], check=True,
        )


if __name__ == "__main__":
    main()
