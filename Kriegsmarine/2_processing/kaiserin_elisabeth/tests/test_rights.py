from kp.rights import is_open, label, open_only


def test_mixed_policy_list_is_not_open():
    # Real v2 shape, 2026-10-27: one record with two rights statements.
    assert not is_open({"edmRightsReusePolicy": ["OPEN", "RESTRICTED"]})


def test_closed_is_not_open():
    # Third value seen 2026-10-27; 874 records mix OPEN and CLOSED.
    assert not is_open({"edmRightsReusePolicy": ["OPEN", "CLOSED"]})


def test_all_open_list_is_open():
    assert is_open({"edmRightsReusePolicy": ["OPEN"]})
    assert is_open({"edmRightsReusePolicy": ["OPEN", "OPEN"]})


def test_scalar_and_missing():
    assert is_open({"edmRightsReusePolicy": "OPEN"})
    assert not is_open({"edmRightsReusePolicy": "RESTRICTED"})
    assert not is_open({})
    assert not is_open({"edmRightsReusePolicy": []})


def test_open_only_and_label():
    docs = [{"edmRightsReusePolicy": ["OPEN"]}, {"edmRightsReusePolicy": ["RESTRICTED"]}]
    assert len(open_only(docs)) == 1
    assert label({"edmRightsName": ["CC0", "CC BY-NC"]}) == "CC0 / CC BY-NC"
    assert label({}) == "rights unknown"
