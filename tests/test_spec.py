from source_relocation.spec import BENEFITS, CARRIERS, make_artifacts


def test_artifact_pairing():
    for benefit in BENEFITS:
        group = make_artifacts("travel", benefit, "task0")
        assert set(group) == {"M", "BM", "BW"}
        assert group["M"].code == group["BM"].code
        assert group["M"].benefit == group["BM"].benefit
        assert group["M"].url != group["BM"].url
        assert group["BW"].benefit < group["M"].benefit


def test_carriers():
    assert CARRIERS == ("promotion", "tip", "resource")
