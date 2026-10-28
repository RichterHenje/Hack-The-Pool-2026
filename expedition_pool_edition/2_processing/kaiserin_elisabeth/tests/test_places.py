from kp import places


def test_overlap_boundaries():
    assert places.overlaps(places.timespan(1898, 1914), 1912, 1916) is True  # ends inside
    assert places.overlaps(places.timespan(1898, 1911), 1912, 1916) is False
    assert places.overlaps(places.timespan(None, 1914), 1912, 1916) is True  # unknown start
    assert places.overlaps(None, 1912, 1916) is None  # undated: unknown, not false


def test_missing_end_means_during_start_per_lpf_spec():
    # LPF README: '{"start":{"in":"1832"}} indicates during 1832'
    during = places.timespan(1949, None)
    assert "end" not in during["timespans"][0]
    assert places.overlaps(during, 1949, 1949) is True
    assert places.overlaps(during, 1950, 1960) is False
    # still valid since 1949: explicit open end
    since = places.timespan(1949, None, ongoing=True)
    assert since["timespans"][0]["end"] == {"earliest": places.NOW}
    assert places.overlaps(since, 1950, 1960) is True
    assert places.overlaps(since, 1912, 1916) is False


def test_timespan_shape_has_start():
    ts = places.timespan(None, 1914)["timespans"][0]
    assert ts["start"] == {"latest": "1914"} and ts["end"] == {"in": "1914"}


def _n(t, kind, when=None, lang=None):
    n = {"toponym": t, "lang": lang, "citations": [{"label": f"x [{kind}]"}]}
    if when:
        n["when"] = when
    return n


def test_query_names_respect_validity():
    f = {
        "names": [
            _n("Batavia", "attested", places.timespan(1892, 1893)),
            _n("Batavia", "historic", places.timespan(1619, 1949), "en"),
            _n("Djakarta", "historic", places.timespan(1949, 1972), "en"),
            _n("Jakarta", "dated", places.timespan(1972, None, ongoing=True), "en"),
            _n("Jakarta", "current"),
            _n("Sunda Kelapa", "historic", places.timespan(669, 1527), "en"),
            _n("ジャカルタ", "label", None, "ja"),
        ]
    }
    assert places.query_names(f, 1890, 1895) == ["Batavia"]
    assert places.query_names(f, 1975, 1980) == ["Batavia", "Jakarta"]  # attested always kept


def test_latin_filter():
    assert places.is_latin("Tsingtau")
    assert places.is_latin("Pōla")
    assert not places.is_latin("青島")
    assert not places.is_latin("Пула")
