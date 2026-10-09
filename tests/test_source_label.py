from source_relocation.manifest import make_manifest
from source_relocation.prompts import experiment_conditions, render_condition


def test_control_changes_only_one_label():
    row = make_manifest([{"id": "task", "prompt": "Book the room."}])[0]
    prompts = [render_condition(row, condition, row["task"])["prompt"] for condition in experiment_conditions("rq1", "source_label")]
    assert all(text.count("Source:") == 3 for text in prompts)
    assert prompts[0].count("Source: external") == 3
    assert prompts[1].count("Source: user-provided") == 1
    assert prompts[2].count("Source: user-provided") == 1
    assert prompts[0].count("SAVE20") == prompts[1].count("SAVE20") == prompts[2].count("SAVE20")
