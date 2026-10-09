import argparse
import json
import pandas as pd
from source_relocation.tracing import late_layer_summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", default="outputs/analysis/rq2_late.csv")
    args = parser.parse_args()
    rows = [json.loads(line) for line in open(args.input, encoding="utf-8") if line.strip()]
    results = [{"unit_id": row["unit_id"], "base_task_id": row["base_task_id"], "artifact_type": row["artifact_type"], "late_gap": late_layer_summary(row["gap"])} for row in rows]
    from pathlib import Path
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(args.out, index=False)


if __name__ == "__main__":
    main()
