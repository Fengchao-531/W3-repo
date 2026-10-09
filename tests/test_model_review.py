import csv
import json

from source_relocation.models import select_models
from reproduction.review_trajectories import template, merge


def test_model_families_and_selection():
    behavioral = select_models(models="all")
    internal = select_models(models="all", internal=True)
    assert len(behavioral) == 8
    assert len(internal) == 5
    assert select_models(models="qwen,gemma", internal=True) == ["qwen", "gemma"]


def test_annotation_sheet_and_merge(tmp_path):
    root = tmp_path / "runs"
    run = root / "rq1" / "relocation" / "travel" / "gpt4o" / "none" / "UC_M" / "p01"
    run.mkdir(parents=True)
    record = {
        "pair_id": "p01", "model": "gpt4o", "condition": "UC_M",
        "artifact_type": "M", "defense": "none", "task_success": True,
        "malicious_action_executed": False, "safe_completion": True,
        "artifact_exposed": True, "artifact_mentioned": False,
        "artifact_used_in_plan": False, "artifact_adopted": False,
        "artifact_action_executed": False, "selected": "None",
    }
    (run / "result.json").write_text(json.dumps(record), encoding="utf-8")
    sheet = tmp_path / "labels.csv"
    template(root, sheet)
    with sheet.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
        fields = list(rows[0])
    rows[0]["artifact_mentioned"] = "true"
    rows[0]["reviewer_code"] = "reviewer_1"
    rows[0]["mention_evidence"] = "assistant message 4"
    with sheet.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    output = tmp_path / "annotated.jsonl"
    merge(root, sheet, output)
    new = json.loads(output.read_text(encoding="utf-8").strip())
    assert new["artifact_mentioned"] is True
    assert new["annotation_status"] == "manual_reviewed"
    assert new["safe_completion"] is True
    assert json.loads((run / "result.json").read_text(encoding="utf-8")) == record


def test_multiple_model_aliases():
    assert select_models(models='llama31,qwen') == ['llama31', 'qwen']
    assert select_models(models='mistral,gemma', internal=True) == ['mistral', 'gemma']
