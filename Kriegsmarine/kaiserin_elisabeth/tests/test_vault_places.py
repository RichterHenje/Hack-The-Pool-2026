from scripts import vault_places as vp


def test_wikilinks_variants():
    text = "[[Pola, Istrien]] und [[Kaiserin Elisabeth, Kreuzer|SMS KE]] siehe [[Indien#Bombay]]"
    assert vp.wikilinks(text) == ["Pola, Istrien", "Kaiserin Elisabeth, Kreuzer", "Indien"]


def test_backlinks_count_by_folder(tmp_path):
    (tmp_path / "Ortschaften").mkdir()
    (tmp_path / "Personen").mkdir()
    (tmp_path / "Schiffe").mkdir()
    (tmp_path / "Ortschaften/Pola, Istrien.md").write_text("[[Pola, Istrien]]", encoding="utf-8")
    (tmp_path / "Personen/A.md").write_text("[[Pola, Istrien]] [[Pola, Istrien]]", encoding="utf-8")
    (tmp_path / "Schiffe/S.md").write_text("[[Pola, Istrien|Pola]]", encoding="utf-8")
    bl = vp.backlinks(tmp_path)["Pola, Istrien"]
    assert bl == {"Personen": 1, "Schiffe": 1}  # self-link and duplicates not counted
