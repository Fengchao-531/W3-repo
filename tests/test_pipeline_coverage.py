import json
from pathlib import Path
from types import SimpleNamespace

from reproduction.reproduce_all import commands
from reproduction.reproduce_rq2 import discovery_holdout
from source_relocation.prompts import experiment_conditions
from analysis.rq1_controls import CONTRASTS, evaluate
from analysis.rq2_regions import summarize


def test_rq1_experiment_conditions():
    assert len(experiment_conditions("rq1", "relocation")) == 3
    assert len(experiment_conditions("rq1", "position")) == 6
    assert len(experiment_conditions("rq1", "preference")) == 4
    assert len(experiment_conditions("rq1", "instruction")) == 2
    assert len(experiment_conditions("rq1", "reliability")) == 4
    assert len(experiment_conditions("rq1", "source_label")) == 3
    assert len(CONTRASTS) == 6


def test_rq2_discovery_and_heldout_units():
    items = [
        {"unit_id": f"{role}-{i}", "artifact_type": role}
        for role in ("M", "BM") for i in range(31)
    ]
    discovery, heldout = discovery_holdout(items, seed=1234, per_type=9)
    assert len(discovery) == 18
    assert len(heldout) == 44
    assert {x["unit_id"] for x in discovery}.isdisjoint(
        {x["unit_id"] for x in heldout}
    )
    assert discovery_holdout(items, seed=1234, per_type=9)[0] == discovery


def test_rq1_control_statistics(tmp_path):
    root = tmp_path / "rq1" / "relocation" / "travel" / "gpt4o" / "none"
    for idx in (1, 2):
        for cond, selected in (("E", "BM"), ("UC_M", "M"), ("UC_BM", "BM")):
            target = root / cond / f"case-{idx}"
            target.mkdir(parents=True)
            row = {
                "pair_id": f"case-{idx}", "base_task_id": f"task-{idx}",
                "model": "gpt4o", "domain": "travel",
                "condition": cond, "selected": selected,
            }
            (target / "result.json").write_text(json.dumps(row), encoding="utf-8")
    result = evaluate(tmp_path / "rq1", resamples=15)
    assert len(result) == 2
    m = next(x for x in result if x["candidate"] == "M")
    assert m["paired_units"] == 2
    assert m["right_rate"] == 1


def test_rq2_region_postprocessing(tmp_path):
    file = tmp_path / "attention.jsonl"
    payload = {
        "unit_id": "case-1", "artifact_type": "M",
        "E": [
            {"layer": 25, "head": 1, "region": "target_artifact", "mass": 0.2, "density": 0.2},
            {"layer": 25, "head": 1, "region": "surrounding_context", "mass": 0.8, "density": 0.4},
        ],
        "UC": [
            {"layer": 25, "head": 1, "region": "target_artifact", "mass": 0.7, "density": 0.7},
            {"layer": 25, "head": 1, "region": "surrounding_context", "mass": 0.3, "density": 0.15},
        ],
    }
    file.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    table = summarize(file)
    target = table[table["region"] == "target_artifact"].iloc[0]
    assert abs(target["delta_mass"] - 0.5) < 1e-9
    assert abs(target["delta_artifact_share"] - 0.5) < 1e-9


def test_end_to_end_invocation_order():
    args = SimpleNamespace(
        domain="travel", rq1_model="gpt4o",
        rq2_model="llama31", rq3_model="gpt4o",
        defense="all", deployed_input="service_observations.jsonl",
        sweep_first=20, sweep_last=32, window_first=25, window_last=28,
    )
    plan = commands(args)
    paths = [line[1] for line in plan]
    assert paths[:5] == [
        "reproduction/reproduce_rq1.py",
        "reproduction/build_contexts.py",
        "reproduction/build_contexts.py",
        "reproduction/reproduce_rq2.py",
        "reproduction/reproduce_rq3.py",
    ]
    assert paths[-1] == "-m"


def test_experiment_files_present():
    root = Path(__file__).resolve().parents[1]
    for kind, names in {
        "rq1": ("relocation", "position", "preference", "instruction", "reliability", "source_label"),
        "rq2": ("representation", "patching", "heads", "heldout", "attention", "code_control"),
        "rq3": ("defenses", "verification"),
    }.items():
        for name in names:
            assert (root / "experiments" / kind / f"{name}.py").is_file()
    for file in (
        "analysis/rq1_controls.py", "analysis/rq2.py",
        "analysis/rq2_heads.py", "analysis/rq2_regions.py",
        "analysis/rq3_results.py", "reproduction/build_contexts.py",
        "reproduction/reproduce_rq2.py", "reproduction/reproduce_all.py",
    ):
        assert (root / file).is_file()


def test_base_task_count_creates_180_configurations(tmp_path, monkeypatch):
    from source_relocation import manifest
    from source_relocation.cli import build
    tasks = [
        {"id": f"task-{i:02d}", "prompt": "Book the requested hotel."}
        for i in range(25)
    ]
    monkeypatch.setattr(manifest, "load_tasks", lambda *args: tasks)
    output = tmp_path / "travel.jsonl"
    build(SimpleNamespace(
        tasks_jsonl=None, domain="travel", benchmark_version="v1",
        base_tasks=20, manifest=str(output),
    ))
    assert len(output.read_text(encoding="utf-8").splitlines()) == 180


def test_reliability_span_not_tagged_as_artifact():
    from source_relocation.attention import assign_regions

    class OffsetTokenizer:
        def __call__(self, text, return_offsets_mapping=True):
            return SimpleNamespace(offset_mapping=[
                (i, i + 1) for i in range(len(text))
            ])

    reliab = "The official promotion does not list SAVE20."
    text = "Book. SAVE20 appears. " + reliab + " Promo code:"
    regions = assign_regions(
        OffsetTokenizer(), text, "SAVE20", "Book.",
        reliability=reliab,
    )
    first = text.index("SAVE20")
    second = text.rindex("SAVE20")
    assert regions[first] == "target_artifact"
    assert regions[second] == "reliability_evidence"


def test_deployed_browser_case_matrix():
    from reproduction.deployed_capture import planned_cases
    agents = [{"name": "Trip"}, {"name": "MindTrip"}]
    tasks = [
        {"task_id": "t1", "prompt": "Book hotel A."},
        {"task_id": "t2", "prompt": "Book hotel B."},
    ]
    cases = planned_cases(agents, tasks, rounds=3)
    assert len(cases) == 2 * 2 * 3 * 3
    assert {case["guidance"] for case in cases} == {"H1", "H2", "H3"}
    assert cases[0]["prompt"] == "Book hotel A."
    assert any("verify the safety" in case["prompt"].lower() for case in cases)


def test_semantic_regions_cover_serialized_agent_messages():
    from source_relocation.attention import assign_regions

    class OffsetTokenizer:
        def __call__(self, text, return_offsets_mapping=True):
            return SimpleNamespace(offset_mapping=[
                (i, i + 1) for i in range(len(text))
            ])

    messages = [
        {"role": "system", "content": "System policy."},
        {"role": "user", "content": "Book the hotel. Online offer is SAVE20."},
        {"role": "tool", "content": "Verified hotel results. " + "X" * 80 + " SAVE20."},
        {"role": "assistant", "content": "I considered SAVE20 as an offer."},
    ]
    serial = json.dumps(messages, ensure_ascii=False) + "\nPromo code:"
    labels = assign_regions(OffsetTokenizer(), serial, "SAVE20", "Book the hotel.")
    assert labels[serial.index("Book the hotel.")] == "user_task"
    assert labels[serial.index("Verified hotel results")] == "external_content"
    assert labels[serial.index('"role": "tool"')] == "source_marker"
    assert labels[serial.index("I considered")] == "other_trajectory"
    assert labels[serial.index("SAVE20", serial.index("I considered"))] == "generated_prefix"
    assert labels[serial.rfind("Promo code:")] == "forced_decision"
