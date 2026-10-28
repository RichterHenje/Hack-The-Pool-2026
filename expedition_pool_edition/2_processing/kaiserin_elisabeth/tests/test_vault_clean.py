"""Unit cases for scripts/vault_clean.py on a tiny constructed vault (not the blind loops)."""

import json

from scripts import vault_clean as vc


def make(tmp_path):
    v = tmp_path / "vault"
    for d in ("Personen", "Ortschaften", "Schiffe"):
        (v / d).mkdir(parents=True)
    files = {
        "Personen/Skala, Karl.md": "- Rolle: Linienschiff Leutnant (seit 28. Februar 1994)\n"
        "- Quelle: RangUndEinteilungslisteMarine_1894-05-15__pages1-1.pdf\n",
        "Personen/Becker, Alois Ritter von.md": "- Kapitän der [[Kaiserin Elisabeth, Kreuzer]]\n",
        "Personen/Svoboda, Václav.md": "- Arzt. Erwähnt 1996 in einem Buch.\n",
        "Personen/Hermann, Hugo.md": "- Seecad.\n",
        "Personen/Herrmann, Hugo.md": "- Seecad.\n",
        "Personen/S.M.S. Zenta.md": "- Schiff\n",
        "Ortschaften/Japan.md": "- Land\n",
        "Ortschaften/Dakna Bâgh, Nepal.md": "- Jagdlager\n",
        "Schiffe/Kaiserin Elisabeth, Kreuzer.md": "Kapitän [[Alois Becker]], Arzt [[Svoboda, Vaclav]]; "
        "[[Kowalski, Anton]]. Route [Dakna Bâgh, (Nepal])] und [Japan].\n"
        "3 Reise: 04.10.2888-23.12.1889\n",
        "Personen/Null, Person.md": "---\ntype: person\nid: null-1\ncreated_by: human\nchecked: false\n---\n"
        "- sauber, siehe [[Japan]]\n",
    }
    for rel, text in files.items():
        (v / rel).write_text(text, encoding="utf-8", newline="")
    # one CRLF + BOM note
    (v / "Personen/Gratzl, August.md").write_bytes(b"\xef\xbb\xbf- Rolle: x\r\n- y\r\n")
    return v


def run(v, tmp_path, *extra):
    rep = tmp_path / "r.json"
    assert vc.main([str(v), "--report", str(rep), *extra]) == 0
    return json.loads(rep.read_text(encoding="utf-8"))


def read(v, rel):
    return (v / rel).read_text(encoding="utf-8")


def test_rules(tmp_path):
    v = make(tmp_path)
    r = run(v, tmp_path)
    assert "(seit 28. Februar 1894)" in read(v, "Personen/Skala, Karl.md")
    assert "1996" in read(v, "Personen/Svoboda, Václav.md")  # decoy: no list year, unchanged
    ship = read(v, "Schiffe/Kaiserin Elisabeth, Kreuzer.md")
    assert "[[Becker, Alois Ritter von|Alois Becker]]" in ship
    assert "[[Svoboda, Václav|Svoboda, Vaclav]]" in ship
    assert "[[Kowalski, Anton]]" in ship  # no target: untouched, flagged
    assert "[[Dakna Bâgh, Nepal]]" in ship and "[[Japan]]" in ship
    assert "04.10.1888-23.12.1889" in ship
    fl = r["flags"]
    assert any("Dublette" in f["message"] for f in fl["Personen/Hermann, Hugo.md"])
    assert any("Dublette" in f["message"] for f in fl["Personen/Herrmann, Hugo.md"])
    assert any(f["rule"] == "F2" for f in fl["Personen/S.M.S. Zenta.md"])
    assert any(f["rule"] == "F2" for f in fl["Ortschaften/Japan.md"])
    assert any("Kowalski" in f["message"] for f in fl["Schiffe/Kaiserin Elisabeth, Kreuzer.md"])
    assert read(v, "Personen/Skala, Karl.md").startswith("---\ntype: person\n")
    assert "created_by: ai-assisted" in read(v, "Personen/Skala, Karl.md")


def test_null_identical_bom_crlf_and_idempotent(tmp_path):
    v = make(tmp_path)
    null_before = (v / "Personen/Null, Person.md").read_bytes()
    run(v, tmp_path)
    assert (v / "Personen/Null, Person.md").read_bytes() == null_before
    raw = (v / "Personen/Gratzl, August.md").read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf---\r\n") and b"\n- y\r\n" in raw and b"\r\r" not in raw
    r2 = run(v, tmp_path)
    assert r2["changed_files"] == {}


def test_loop1_false_positives_fixed(tmp_path):
    v = make(tmp_path)
    (v / "Personen/Ritter, Franz von.md").write_text("- x\n", encoding="utf-8")
    (v / "Personen/Weltreise Erzherzog Franz Ferdinand (1892-1893).md").write_text(
        "- y\n", encoding="utf-8"
    )
    (v / "Personen/Kapitän Franz Mirtl.md").write_text("- z\n", encoding="utf-8")
    (v / "Personen/Kommandant Linienschiffs- Kapitän Mirtl.md").write_text(
        "- w\n", encoding="utf-8"
    )
    (v / "Ortschaften/Singapur.md").write_text("- Hafen\n", encoding="utf-8")
    r = run(v, tmp_path)
    fl = r["flags"]
    assert not any(f["rule"] == "F1" for f in fl.get("Personen/Ritter, Franz von.md", []))
    assert any("Mirtl" in f["message"] for f in fl["Personen/Kapitän Franz Mirtl.md"])
    assert "Ortschaften/Singapur.md" not in fl


def test_second_run_does_not_reread_review_entries(tmp_path):
    v = make(tmp_path)
    r1 = run(v, tmp_path)
    r2 = run(v, tmp_path)
    assert r2["changed_files"] == {}
    count = lambda r, rule: sum(f["rule"] == rule for fl in r["flags"].values() for f in fl)
    assert count(r2, "R3") == count(r1, "R3") and count(r2, "R2") == count(r1, "R2")
    ship = read(v, "Schiffe/Kaiserin Elisabeth, Kreuzer.md")
    assert '"Link ohne Ziel: Kowalski, Anton"' in ship  # no [[…]] inside frontmatter


def test_layers_page_break_does_not_swallow_next_sentence(tmp_path):
    from scripts import ke_layers

    src = tmp_path / "src"
    src.mkdir()
    day = (
        "### 1893-07-25 · Kanton\n"
        "Ein Rundgang wirkte bald so anwidernd, dass ich an Bord zurückkehrte.\n"
        "m r-^'t -v.f -^9^v .^\n"
        "*S. 227 · Scan 240*\n"
        "Bei einem Händler erstand ich nach langem Feilschen eine alte Bronzefigur.\n"
    )
    (src / "FF Tagebuch Bd. 1.md").write_text(day, encoding="utf-8")
    (src / "FF Tagebuch Bd. 2.md").write_text("", encoding="utf-8")
    d = ke_layers.parse_diary(src)[0]
    text = "\n".join(d["text"])
    assert "Scan 240" not in text and "^" not in text
    assert "erstand ich" in text


def test_disable_rule_leaves_class_unfixed(tmp_path):
    v = make(tmp_path)
    run(v, tmp_path, "--disable", "R2,R3")
    assert "1994" in read(v, "Personen/Skala, Karl.md")
    assert "[[Alois Becker]]" in read(v, "Schiffe/Kaiserin Elisabeth, Kreuzer.md")
