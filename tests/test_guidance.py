from source_relocation.manifest import make_manifest
from source_relocation.prompts import experiment_conditions, render_condition
from source_relocation.spec import GUIDANCE


def test_h_guidance_exact():
    row = make_manifest([{"id": "task", "prompt": "Book the hotel."}])[0]
    all_conditions = [render_condition(row, condition, row["task"]) for condition in experiment_conditions("rq3", "verification")]
    assert len(all_conditions) == 6
    assert all_conditions[1]["prompt"].endswith(GUIDANCE["H2"])
    assert all_conditions[2]["prompt"].endswith(GUIDANCE["H3"])
    assert all_conditions[3]["prompt"].count("SAVE20") == 1
