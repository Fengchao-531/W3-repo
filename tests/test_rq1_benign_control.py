from source_relocation.statistics import paired_difference


def test_bm_reference_uses_bm_not_m():
    rows = [{"pair_id": "a", "base_task_id": "a", "condition": "E", "selected": "BM"}, {"pair_id": "a", "base_task_id": "a", "condition": "UC_BM", "selected": "BM"}]
    for row in rows:
        row["M_adopted"] = row["selected"] == "M"
        row["BM_adopted"] = row["selected"] == "BM"
    assert paired_difference(rows, "E", "UC_BM", "BM_adopted") == 0
