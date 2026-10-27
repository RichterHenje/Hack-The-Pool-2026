"""
Alle Personen der Weltreise 1892/93 in einer Liste, in der Struktur von json/personen.json.

filter_voyage.py wählt Personen über die Seereise-Denkmünze bzw. die Besatzung im Weltreise-Eintrag.
Hier kommen dazu (Code und Objektstruktur aus filter_voyage.py, das unverändert bleibt):
- Besatzung laut Rangliste: Einträge der Ranglisten 15.11.1892 bis 1.9.1893
  (../Sources/Ranglisten/kaiserin_elisabeth_ranglisten.csv), mit Vault-Notiz falls vorhanden
- Begleitung und Gastgeber, die das Tagebuch nennt (kuratierte Liste unten, mit Grund)
- Personen ohne Vault-Notiz, die im Tagebuch eine Rolle spielen (Tierwärter Biaggio, Jäger Bedford)

Jede Person hat zusätzlich "_reise": gruppe, rollen (Rangliste), quelle der Auswahl und – falls eine
Notiz unter anderer Schreibweise vermutlich dieselbe Person ist – "vermutlich_dieselbe_wie".
Zusammengeführt wird nichts; das entscheiden Fachleute.

Ausgabe: json/personen_reise.json
Aufruf:  python people_voyage.py
"""

import csv
import difflib
import json
import re
import unicodedata
from pathlib import Path

import filter_voyage as fv

HERE = Path(__file__).resolve().parent
RANGLISTEN = HERE.parent / "Sources" / "Ranglisten" / "kaiserin_elisabeth_ranglisten.csv"
OUT = HERE / "json" / "personen_reise.json"
VOYAGE_ISSUES = ("1892-11-15", "1893-09-01")

# Begleitung und Gastgeber laut Tagebuch (Vault-Notiz, Gruppe, Rolle)
COMPANIONS = [
    ("Clam-Martinic, Heinrich Graf", "Begleitung", "Kämmerer, Reisebegleiter"),
    ("Wurmbrand-Stuppach, Leo Graf", "Begleitung", "Generalmajor, Reisebegleiter"),
    ("Kinsky zu Wichnitz und Tettau, Karl Graf", "Begleitung", "Reisebegleiter"),
    ("Prónay von Tót-Próna und Blatnicza, Julius", "Begleitung", "Oberlieutenant, Reisebegleiter"),
    ("Ritter von Liburnau, Dr. Ludwig Lorenz", "Wissenschaft", "Zoologe des Naturhistorischen Hofmuseums"),
    ("Havelock, Arthur E.", "Gastgeber", "Gouverneur von Ceylon"),
    ("Pirie, Captain", "Gastgeber", "Jagd in Ceylon"),
    ("Stockinger, Franz", "Gastgeber", "Generalkonsul"),
    ("Imhof, Max von", "Gastgeber", "Fotograf in Nordamerika"),
]
# ohne Vault-Notiz
WITHOUT_NOTE = [
    ("Biaggio", "Diener", "Tierwärter an Bord, aus Ragusa (Familienname in der OCR unleserlich)"),
    ("Bedford", "Gastgeber", "Jagdbegleiter in Neuguinea"),
]
# Rangliste -> Vault-Notiz unter anderer Schreibweise (vermutlich dieselbe Person, ungeprüft)
ALIASES = {
    "Gründorf v. Zebegényi, Johann": "Gründorf von Zebegényi, Hans Ritter",
    "Podhorsky, Ludwig": "Podhorszky, Louis",
    "Herrmann, Hugo": "Hermann, Hugo",
    "Erzherzog Leopold Ferdinand": "Salvator von Österreich-Toskana, Erzherzog Leopold Ferdinand",
}


def key(name):
    s = unicodedata.normalize("NFC", name).casefold()
    s = re.sub(r"\b(ritt|ritter|edl|edler|freih|freiherr|graf|gf|v|von|dr|u|z)\b\.?", " ", s)
    return re.sub(r"[^a-zäöüß ]", " ", s).split()


def same(a, b):
    """Surname and first given name agree (ignoring titles and particles)."""
    ka, kb = key(a), key(b)
    return bool(ka and kb) and ka[0] == kb[0] and (len(ka) < 2 or len(kb) < 2 or ka[1][:3] == kb[1][:3])


def ranglisten():
    people = {}
    for r in csv.DictReader(RANGLISTEN.open(encoding="utf-8-sig"), delimiter=";"):
        if VOYAGE_ISSUES[0] <= r["ausgabe"] <= VOYAGE_ISSUES[1]:
            p = people.setdefault(r["name"], [])
            p.append({"ausgabe": r["ausgabe"], "seite": r["seite"], "dienstgrad": r["dienstgrad"], "seit": r["seit"]})
    return people


def main():
    vault = fv.Vault(fv.DEFAULT_VAULT)
    base = json.loads((HERE / "json" / "personen.json").read_text())
    by_note = {p["_meta"]["datei"]: p for p in base}
    out = {p["_meta"]["datei"]: p | {"_reise": {"gruppe": "Besatzung", "quelle": "filter_voyage.py"}} for p in base}
    notes = {n.title: n for n in vault.notes if n.folder == fv.FOLDERS["person"]}

    for name, entries in sorted(ranglisten().items()):
        title = next((t for t in notes if same(name, t)), None)
        alias = None
        if not title and name in ALIASES and ALIASES[name] in notes:
            title, alias = ALIASES[name], ALIASES[name]
        info = {"ranglisten_name": name, "ranglisten": entries}
        if title and len(key(name)) > 1 and len(key(title)) > 1 and key(name)[-1][:3] != key(title)[-1][:3]:
            info["vorname_abweichend"] = True   # e.g. Johann / Hans
        datei = f"Personen/{title}.md" if title else None
        if datei in out:
            out[datei]["_reise"].setdefault("ranglisten", []).append(info)
            if alias:
                out[datei]["_reise"]["vermutlich_dieselbe_wie"] = name
        elif title:
            obj = fv.build_person(vault, notes[title], ["Rangliste 1892/93: an Bord der Kaiserin Elisabeth"])
            out[datei] = obj | {"_reise": {"gruppe": "Besatzung", "quelle": "Rangliste", "ranglisten": [info]}
                                | ({"vermutlich_dieselbe_wie": name} if alias else {})}
        else:
            obj = fv.build_person(vault, None, ["Rangliste 1892/93: an Bord der Kaiserin Elisabeth (ohne Vault-Notiz)"],
                                  name=name)
            out[f"rangliste:{name}"] = obj | {"_reise": {"gruppe": "Besatzung", "quelle": "Rangliste", "ranglisten": [info]}}

    for title, group, role in COMPANIONS:
        datei = f"Personen/{title}.md"
        reason = f"im Tagebuch genannt: {role}"
        if datei in out:
            out[datei]["_reise"].update({"gruppe": group, "rolle": role})
            continue
        obj = fv.build_person(vault, notes[title], [reason])
        out[datei] = obj | {"_reise": {"gruppe": group, "rolle": role, "quelle": "Tagebuch"}}
    for name, group, role in WITHOUT_NOTE:
        obj = fv.build_person(vault, None, [f"im Tagebuch genannt: {role} (ohne Vault-Notiz)"], name=name)
        out[f"tagebuch:{name}"] = obj | {"_reise": {"gruppe": group, "rolle": role, "quelle": "Tagebuch"}}

    people = sorted(out.values(), key=lambda p: (p["_reise"]["gruppe"], p["Nachname, Vorname"]))
    # possible duplicates: different records, surnames almost equal, same first initial
    for i, a in enumerate(people):
        for b in people[i + 1:]:
            ka, kb = key(a["Nachname, Vorname"]), key(b["Nachname, Vorname"])
            if len(ka) > 1 and len(kb) > 1 and ka[-1][0] == kb[-1][0] and \
                    difflib.SequenceMatcher(None, ka[0], kb[0]).ratio() >= 0.85:
                for x, y in ((a, b), (b, a)):
                    x["_reise"].setdefault("moegliche_dublette", []).append(y["Nachname, Vorname"])
    OUT.write_text(json.dumps(people, ensure_ascii=False, indent=2))
    groups = {}
    for p in people:
        groups[p["_reise"]["gruppe"]] = groups.get(p["_reise"]["gruppe"], 0) + 1
    print(f"{len(people)} Personen -> {OUT.relative_to(HERE)}  {groups}")
    for p in people:
        if p["_reise"].get("vermutlich_dieselbe_wie"):
            print(f"   vermutlich dieselbe Person: {p['_reise']['vermutlich_dieselbe_wie']!r} ~ {p['Nachname, Vorname']!r}")
    for p in people:
        if p["_reise"].get("moegliche_dublette"):
            print(f"   mögliche Dublette: {p['Nachname, Vorname']!r} ~ {p['_reise']['moegliche_dublette']}")
    print("   ohne Vault-Notiz:", [p["Nachname, Vorname"] for p in people if p["_meta"]["id"] == fv.NA])


if __name__ == "__main__":
    main()
