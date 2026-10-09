import random
from collections import defaultdict
import numpy as np


def rate(rows: list[dict], field: str) -> float:
    return sum(bool(row[field]) for row in rows) / len(rows) if rows else float("nan")


def paired_difference(rows: list[dict], left: str, right: str, field: str, key: str = "pair_id") -> float:
    groups = defaultdict(dict)
    for row in rows:
        groups[row[key]][row["condition"]] = row
    values = [float(value[right][field]) - float(value[left][field]) for value in groups.values() if left in value and right in value]
    return float(np.mean(values)) if values else float("nan")


def cluster_bootstrap(rows: list[dict], left: str, right: str, field: str, iterations: int = 2000, seed: int = 1234) -> dict:
    groups = defaultdict(list)
    for row in rows:
        groups[row["base_task_id"]].append(row)
    clusters = sorted(groups)
    rng = random.Random(seed)
    estimates = []
    for cluster in clusters:
        value = paired_difference(groups[cluster], left, right, field)
        if value == value:
            estimates.append(value)
    if not estimates:
        raise ValueError((left, right, field))
    values = [sum(rng.choice(estimates) for _ in estimates) / len(estimates) for _ in range(iterations)]
    return {"difference": float(np.mean(estimates)), "lower": float(np.percentile(values, 2.5)), "upper": float(np.percentile(values, 97.5)), "iterations": iterations, "seed": seed}


def summary(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["domain"], row["model"], row["condition"], row.get("defense", "none"))].append(row)
    return [{"domain": key[0], "model": key[1], "condition": key[2], "defense": key[3], "n": len(items), "adoption": rate(items, "artifact_adopted"), "attack": rate(items, "malicious_action_executed"), "utility": rate(items, "task_success"), "safe_completion": rate(items, "safe_completion")} for key, items in sorted(grouped.items())]
