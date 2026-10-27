"""Axis order is the classic GIS bug: a swapped Vienna lands in Somalia (48 E, 16 N)."""

import json

import pytest

from kp import geo


def test_feature_writes_lon_lat():
    f = geo.feature(48.2082, 16.3738, name="Wien")
    assert f["geometry"]["coordinates"] == [16.3738, 48.2082]


def test_feature_rejects_out_of_range():
    with pytest.raises(ValueError):
        geo.feature(148.2, 16.37)


def test_wkt_point_is_lon_lat_in_returns_lat_lon_out():
    lat, lon = geo.parse_wkt_point("Point ( +016.371690 +048.208199 )")
    assert (round(lat, 2), round(lon, 2)) == (48.21, 16.37)


def test_csv_has_latitude_longitude_in_the_right_columns(tmp_path):
    p = geo.write_csv_latlon([geo.feature(48.2, 16.37, name="Wien")], tmp_path / "x.csv")
    header, row = p.read_text(encoding="utf-8").splitlines()
    assert header.startswith("latitude,longitude")
    assert row.startswith("48.2,16.37")


def test_geojson_roundtrip(tmp_path):
    p = geo.write_geojson([geo.feature(47.07, 15.44, name="Graz")], tmp_path / "x.geojson", "test")
    fc = json.loads(p.read_text(encoding="utf-8"))
    assert fc["type"] == "FeatureCollection"
    assert fc["features"][0]["geometry"]["coordinates"] == [15.44, 47.07]


def test_placeholders_and_parts():
    assert geo.is_placeholder("o.O.")
    assert geo.is_placeholder("[unbekannt]")
    assert not geo.is_placeholder("Wien")
    assert geo.name_parts("[Wien]") == ["Wien"]
    assert geo.name_parts("Wien, Künstlerhaus")[1] == "Wien"
    assert geo.name_parts("AUT / BL Oberösterreich / PB Linz")[1] == "PB Linz"
    # Team vault style: historic name with stated modern name, modern first
    assert geo.name_parts("Batavia (heut. Jakarta, Indonesien)")[:2] == ["Jakarta", "Batavia"]
    assert geo.name_parts("Bombay (Indien, Heut. Mumbai)")[:2] == ["Mumbai", "Bombay"]
    assert geo.name_parts("Agra, (U.P.), Indien")[0] == "Agra"
    assert "Indien" in geo.name_parts("Calcutta (Indien)")


def _gaz(records):
    g = geo.Gazetteer.__new__(geo.Gazetteer)
    g.index = {}
    for r in records:
        g.index.setdefault(geo.norm(r["name"]), []).append(r)
    return g


def _rec(gid, name, fclass, country, pop):
    return {
        "geonameid": gid,
        "name": name,
        "lat": 48.0,
        "lon": 16.0,
        "fclass": fclass,
        "fcode": "",
        "country": country,
        "population": pop,
    }


def test_lookup_prefers_town_over_district_and_austria_over_abroad():
    g = _gaz(
        [
            _rec("1", "Baden", "A", "AT", 145235),  # Politischer Bezirk: bigger, but an admin area
            _rec("2", "Baden", "P", "AT", 25000),
            _rec("3", "Baden", "P", "CH", 19000),
        ]
    )
    m = g.lookup("Baden")
    assert m["geonameid"] == "2" and m["ambiguous"] and m["candidates"] == 3
    assert g.lookup("o.O.") is None
    assert g.lookup("[Baden]")["geonameid"] == "2"
    # A named country must agree with the match
    assert g.lookup("Baden, Schweiz")["geonameid"] == "3"
    assert g.lookup("Baden, Nepal") is None
    assert geo.country_hints("Bombay (Indien, Heut. Mumbai)") == {"IN"}


def test_historic_names():
    assert geo.historic_names("Qingdao (hist. Tsingtau), China") == ["Tsingtau"]
    assert geo.historic_names("Batavia (heut. Jakarta, Indonesien)") == ["Batavia"]
    assert geo.historic_names("Bombay (Indien, Heut. Mumbai)") == ["Bombay"]
    assert geo.historic_names("Peking, China") == []


def test_country_names_only_match_city_state_capitals():
    sg = _rec("9", "Singapur", "P", "SG", 5_000_000)
    sg["fcode"] = "PPLC"
    jp = _rec("8", "Japan", "P", "US", 20_000)  # a town called Japan elsewhere
    g = _gaz([sg, jp])
    assert g.lookup("Singapur")["geonameid"] == "9"
    assert g.lookup("Japan") is None


def test_norm_and_gnd_id():
    assert geo.norm("  WIEN ") == geo.norm("wien")
    assert geo.norm("Großenzersdorf") == geo.norm("grossenzersdorf")
    assert geo.norm("Pöchlarn") == geo.norm("Pochlarn")
    assert geo.gnd_id("http://d-nb.info/gnd/4066009-6") == "4066009-6"
    assert geo.gnd_id("https://d-nb.info/gnd/4066009-6/") == "4066009-6"
