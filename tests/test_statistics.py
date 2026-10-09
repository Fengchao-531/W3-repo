from source_relocation.statistics import summary, paired_difference, cluster_bootstrap
from source_relocation.deployment import summarize_deployment


def test_paired_bootstrap():
    rows = []
    for n in range(20):
        for condition, adopted in (("E", False), ("UC", True)):
            rows.append({"base_task_id": f"task{n}", "pair_id": f"task{n}", "domain": "travel", "model": "gpt4o", "condition": condition, "artifact_adopted": adopted, "malicious_action_executed": adopted, "task_success": True, "safe_completion": not adopted})
    assert paired_difference(rows, "E", "UC", "artifact_adopted") == 1.0
    ci = cluster_bootstrap(rows, "E", "UC", "artifact_adopted", 100)
    assert ci["lower"] == 1.0 == ci["upper"]
    assert len(summary(rows)) == 2


def test_deployed_macro():
    rows = [{"agent": "Trip", "round": "r1", "guidance": "H1", **{f"{key}_applicable": True for key in ("E1", "E2", "E3", "C1", "C2", "C3")}, **{f"{key}_violation": key in ("E1", "C2") for key in ("E1", "E2", "E3", "C1", "C2", "C3")}}]
    result = summarize_deployment(rows)
    assert abs(result[0]["environment_bypass"] - 1 / 3) < 1e-9
    assert abs(result[0]["commonsense_bypass"] - 1 / 3) < 1e-9
