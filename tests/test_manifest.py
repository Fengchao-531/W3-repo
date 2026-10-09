from source_relocation.manifest import make_manifest


def test_full_manifest():
    tasks = [{"id": f"task-{i}", "prompt": f"Complete task {i}."} for i in range(20)]
    rows = make_manifest(tasks)
    assert len(rows) == 180
    assert len(set(item["pair_id"] for item in rows)) == 180
    assert {x["benefit"] for x in rows} == {"saving", "quality", "experience"}
    assert all(len(x["candidate_order"]) == 3 for x in rows)
