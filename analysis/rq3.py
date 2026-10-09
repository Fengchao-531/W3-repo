import argparse
from source_relocation.evaluation import save_summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", default="outputs/runs/rq3")
    parser.add_argument("--out", default="outputs/analysis/rq3_summary.csv")
    args = parser.parse_args()
    save_summary(args.runs, args.out)


if __name__ == "__main__":
    main()
