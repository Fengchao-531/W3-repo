import json
from pathlib import Path
from .statistics import summary


def load_results(root: str):
    return [json.loads(path.read_text(encoding="utf-8")) for path in Path(root).rglob("result.json")]


def save_summary(root: str, destination: str):
    import pandas as pd
    items = summary(load_results(root))
    out = Path(destination)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(items, columns=["domain", "model", "condition", "defense", "n", "adoption", "attack", "utility", "safe_completion"]).to_csv(out, index=False)
    return items
