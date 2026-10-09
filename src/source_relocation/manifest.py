import json
from pathlib import Path
from .spec import BENEFITS, CARRIERS, ORDER_PATTERNS, make_artifacts


def make_manifest(tasks: list[dict], domain: str = "travel") -> list[dict]:
    rows = []
    for task_index, task in enumerate(tasks):
        for desire_index, benefit in enumerate(BENEFITS, start=1):
            for carrier_index, carrier in enumerate(CARRIERS, start=1):
                pair_id = f"{domain.upper()}_T{task_index:03d}_D{desire_index:02d}_C{carrier_index:02d}"
                artifacts = make_artifacts(domain, benefit, pair_id)
                order = ORDER_PATTERNS[(task_index + desire_index + carrier_index) % len(ORDER_PATTERNS)]
                rows.append({"pair_id": pair_id, "base_task_id": task["id"], "task": task["prompt"], "benefit": benefit, "carrier": carrier, "artifacts": artifacts, "candidate_order": order, "seed": 1234 + task_index * 100 + desire_index * 10 + carrier_index, "domain": domain})
    return rows


def load_tasks(path: str | None, domain: str, version: str = "v1") -> list[dict]:
    if path:
        return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    from agentdojo.task_suite.load_suites import get_suite
    suite = get_suite(version, domain)
    return [{"id": task_id, "prompt": task.PROMPT} for task_id, task in sorted(suite.user_tasks.items())]


def serializable(row: dict) -> dict:
    return {**row, "artifacts": {key: vars(artifact) for key, artifact in row["artifacts"].items()}}


def save_manifest(rows: list[dict], path: str) -> None:
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("".join(json.dumps(serializable(row), ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def load_manifest(path: str) -> list[dict]:
    from .spec import Artifact
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line:
            row = json.loads(line)
            row["artifacts"] = {key: Artifact(**item) for key, item in row["artifacts"].items()}
            rows.append(row)
    return rows
